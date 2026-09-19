"""試験用サーバの起動・停止・素の HTTP 要求（S01〜S03・M01〜M03）。

`tests/_support/server_launcher.py` を子プロセスで動かす。経路の検査は `http.client` で行う
（URL の正規化を挟まず、`/gradio_api/file=../../.env` のような要求行をそのまま送るため）。
"""

from __future__ import annotations

import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "tests" / "_support" / "server_launcher.py"
START_TIMEOUT = 120.0
STOP_TIMEOUT = 60.0


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class Server:
    """子プロセスのサーバ。with 文で起動と停止を行う。"""

    def __init__(self, audit_log: Path, env_extra: dict[str, str] | None = None, port: int | None = None):
        self.port = free_port() if port is None else port
        self.audit_log = audit_log
        self.env_extra = dict(env_extra or {})
        self.proc: subprocess.Popen | None = None
        self.lines: list[str] = []
        self.ready_line: str | None = None
        self.audit: dict | None = None

    # ---- 起動と停止 ----

    def start(self) -> "Server":
        return self.spawn().wait_ready()

    def spawn(self) -> "Server":
        """起動だけして、準備が済むのを待たない（待ち受け直後の要求を試すため。Codex③ 5）。"""
        env = {k: v for k, v in os.environ.items() if not k.startswith("GRADIO_")}
        env.update({"MEKIKI_READER_PORT": str(self.port), "MEKIKI_AUDIT_LOG": str(self.audit_log),
                    "PYTHONHASHSEED": "0"})
        env.update(self.env_extra)
        self.proc = subprocess.Popen([sys.executable, "-u", str(LAUNCHER)], cwd=str(REPO_ROOT), env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        return self

    def wait_ready(self) -> "Server":
        assert self.proc is not None
        deadline = time.monotonic() + START_TIMEOUT
        while time.monotonic() < deadline:
            for line in list(self.lines):
                if line.startswith("READY "):
                    self.ready_line = line.strip()
                    return self
                if line.startswith("VERIFY-FAILED"):
                    raise RuntimeError(line.strip())
            if self.proc.poll() is not None:
                raise RuntimeError("server died:\n" + "".join(self.lines[-20:]))
            time.sleep(0.2)
        raise TimeoutError("server did not start:\n" + "".join(self.lines[-20:]))

    def _read(self) -> None:
        assert self.proc is not None and self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.append(line)

    def stop(self) -> dict:
        if self.proc is None:
            return {}
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(timeout=STOP_TIMEOUT)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=STOP_TIMEOUT)
        reader = getattr(self, "reader", None)
        if reader is not None:
            reader.join(timeout=5)  # 出力を読み切ってから返す（標準出力・標準エラーの検査のため）
        self.audit = json.loads(self.audit_log.read_text(encoding="utf-8")) if self.audit_log.exists() else {}
        return self.audit

    def __enter__(self) -> "Server":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()

    # ---- 素の HTTP ----

    @property
    def mcp_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/gradio_api/mcp/"

    def request(self, method: str, raw_path: str, body: bytes | None = None,
                headers: dict[str, str] | None = None, timeout: float = 30.0,
                limit: int | None = 200) -> tuple[int, str]:
        """要求行をそのまま送る（パスを正規化しない）。(status, 本文) を返す。limit=None で全文。"""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        try:
            conn.request(method, raw_path, body=body, headers=headers or {})
            resp = conn.getresponse()
            text = resp.read().decode("utf-8", "replace")
            return resp.status, (text if limit is None else text[:limit])
        finally:
            conn.close()

    def raw(self, request: bytes, timeout: float = 30.0) -> tuple[int, str]:
        """要求をバイト列のまま送る（重複ヘッダなど http.client で作れない形のため）。"""
        with socket.create_connection(("127.0.0.1", self.port), timeout=timeout) as sock:
            sock.sendall(request)
            data = b""
            while b"\r\n\r\n" not in data and len(data) < (1 << 20):
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
        if not data.startswith(b"HTTP/"):
            return 0, data[:200].decode("latin-1", "replace")
        return int(data.split(b" ", 2)[1]), data[:300].decode("latin-1", "replace")

    def log(self) -> str:
        return "".join(self.lines)
