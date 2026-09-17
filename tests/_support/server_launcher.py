"""試験用の起動器（S01〜S03）。監査フックを入れてから app を起動し、記録をファイルに書く。

`sys.addaudithook` は import gradio より前に入れる。loopback 以外への接続は例外にして記録する。
環境変数：MEKIKI_AUDIT_LOG（記録の書き出し先）・MEKIKI_READER_PORT（app.py が読む）。
"""

import json
import os
import signal
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

AUDIT_LOG = Path(os.environ["MEKIKI_AUDIT_LOG"])
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "ip6-localhost", ""})
NET_EVENTS = ("socket.connect", "socket.getaddrinfo", "socket.sendto", "socket.gethostbyname",
              "socket.gethostbyname_ex", "urllib.Request", "http.client.connect")

STATE = {"serving": False}
NET: list[list] = []          # 外向き通信の記録（起動前も含めて全部）
OUTBOUND: list[list] = []     # loopback 以外（例外にした分）
OPENED: list[list] = []       # 起動後に開いたファイル（[パス, モード]）


def _host_of(event: str, args) -> str:
    if event in ("socket.connect", "socket.sendto"):
        address = args[1] if len(args) > 1 else None
        if isinstance(address, tuple) and address:
            return str(address[0])
        return "" if address is None else str(address)[:80]
    return str(args[0]) if args else ""


def _audit(event, args) -> None:
    if event in NET_EVENTS:
        host = _host_of(event, args)
        record = [event, host, STATE["serving"]]
        NET.append(record)
        if host not in LOOPBACK_HOSTS and not host.startswith("/"):  # Unix ソケットは除く
            OUTBOUND.append(record)
            raise RuntimeError(f"outbound connection blocked in the test launcher: {event}")
    elif event == "open" and STATE["serving"]:
        path, mode = args[0], (args[1] if len(args) > 1 else "")
        if isinstance(path, (str, bytes, os.PathLike)):
            name = path.decode("utf-8", "replace") if isinstance(path, bytes) else os.fspath(path)
            OPENED.append([str(name), str(mode)])


sys.addaudithook(_audit)

import app  # noqa: E402  （監査フックの後に読み込む）


def _write_log() -> None:
    AUDIT_LOG.write_text(json.dumps({
        "net": NET, "outbound": OUTBOUND, "opened": OPENED,
        "guard": [list(x) for x in app.GUARD_LOG],
        "removed_env": app.REMOVED_GRADIO_ENV,
        "server_name": app.SERVER_NAME,
        "vibe_mode": getattr(DEMO, "vibe_mode", "missing"),
        "dev_mode": getattr(DEMO, "dev_mode", "missing"),
        "allowed_paths": list(getattr(DEMO, "allowed_paths", []) or []),
        "analytics_enabled": getattr(DEMO, "analytics_enabled", "missing"),
        "mcp_server": bool(getattr(DEMO, "mcp_server", False)),
        "local_url": getattr(DEMO, "local_url", None),
    }, ensure_ascii=False), encoding="utf-8")


DEMO = None


def main() -> int:
    global DEMO
    limit = os.environ.get("MEKIKI_TEST_CONCURRENCY")  # 試験だけが同時実行の上限を下げる（S01）
    if limit:
        app.MAX_CONCURRENCY = int(limit)
        app.BUSY_MESSAGE = f"busy: this reader accepts at most {limit} concurrent calls"
        app._SLOTS = threading.BoundedSemaphore(int(limit))
    app.READER = app.T.Reader(app.C.load_corpus())
    DEMO = app.build_blocks()
    problems = app.verify_blocks(DEMO)
    if problems:
        print("VERIFY-FAILED " + "・".join(problems), flush=True)
        return 4
    app.launch(DEMO, app.read_port(os.environ.get(app.PORT_ENV)))
    STATE["serving"] = True
    print(f"READY {DEMO.local_url}", flush=True)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    try:
        stop.wait()
    except KeyboardInterrupt:
        pass
    STATE["serving"] = False
    _write_log()
    DEMO.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
