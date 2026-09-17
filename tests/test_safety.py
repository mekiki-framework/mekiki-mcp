"""施工段階3の完了条件 S01〜S03（SPEC §7・docs/PLAN.md A-4）。サーバを起動して確かめる。"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import pytest

import app
from mekiki_reader import corpus as C
from mekiki_reader import prompts as PR
from mekiki_reader import schema as S
from mekiki_reader import tools as T
from tests._support import mcp_client as MC
from tests._support.server import Server

pytestmark = pytest.mark.server

FIX = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parent.parent
INSTRUCTION_LIKE = json.loads((FIX / "instruction_like.json").read_text(encoding="utf-8"))["cases"]

PATHY_IDS = ("../../.env", "/etc/passwd", "T1/../../.env", "https://example.com/x",
             "file:///etc/hosts", "data/papers/T1.md", "T1\x00", "~/.ssh/id_rsa", "..\\..\\.env")

# 遮断する経路と、実測した応答コード（Q66）。
BLOCKED_ROUTES = (
    ("GET", "/gradio_api/file=../../.env", 403),
    ("GET", "/gradio_api/file=/etc/passwd", 403),
    ("GET", "/gradio_api/file=app.py", 403),
    ("GET", "/gradio_api/file=https://example.com/", 403),
    ("GET", "/file=app.py", 403),
    ("GET", "/gradio_api/proxy=https://example.com/", 403),
    ("POST", "/gradio_api/upload", 403),
    ("GET", "/gradio_api/run-history/connect", 403),
    ("POST", "/gradio_api/run-history/records", 403),
    ("GET", "/gradio_api/monitoring", 403),
    ("GET", "/gradio_api/component_server", 403),
    ("POST", "/gradio_api/component_server", 403),
    ("GET", "/gradio_api/dev/reload", 403),
    ("GET", "/vibe-edit", 403),
    ("GET", "/gradio_api/queue/status", 404),
    ("GET", "/gradio_api/openapi.json", 404),
    ("GET", "/gradio_api/app_id", 404),
    ("GET", "/assets/index.js", 404),
    ("GET", "/static/x.css", 404),
    ("GET", "/theme.css", 404),
    ("GET", "/manifest.json", 404),
    ("GET", "/gradio_api/../etc/passwd", 404),
)
OPEN_ROUTES = (("GET", "/", 200), ("GET", "/config", 200), ("GET", "/gradio_api/info", 200))

CALL_BODY = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "list_papers", "arguments": {}}}).encode("utf-8")
MCP_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def _write_flags(flags: str) -> bool:
    """open の flags に書き込みの意図が入っているか（O_WRONLY・O_RDWR・O_CREAT・O_APPEND）。"""
    if not flags or not flags.lstrip("-").isdigit():
        return False
    value = int(flags)
    return bool(value & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND))


def _sse_json(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise AssertionError(f"not an SSE message: {text[:120]}")


# ---------------------------------------------------------------- S01（関数の層）


def test_s01_pathlike_ids_are_invalid(reader):
    """パスや URL の形の ID は invalid_input。エラー文にその文字列が混ざらない。"""
    for bad in PATHY_IDS:
        for env in (T.get_section(reader, bad, "t4-1"), T.get_section(reader, "T4", bad),
                    T.get_claim_record(reader, bad), T.search_passages(reader, "dignity", bad),
                    T.get_reading_guide(reader, bad)):
            assert env["status"] == "invalid_input", (bad, env["status"])
            assert env["results"] == [] and env["candidates"] == []
            text = S.to_json(env)
            assert bad not in text and bad.replace("\\", "\\\\") not in text


def test_s01_huge_inputs_are_bounded(reader):
    import time

    big = "a" * (1024 * 1024)
    for call in (lambda: T.search_passages(reader, big), lambda: T.verify_quote(reader, big),
                 lambda: T.check_compressions(reader, big), lambda: T.get_claim_record(reader, None, big)):
        start = time.perf_counter()
        env = call()
        assert env["status"] == "invalid_input"
        assert time.perf_counter() - start < 1.0  # Q85（最悪ケースの実測は 44 ms）
    for bad_k in (-1, 0, 21, 10 ** 9, True, "5", 5.0):
        assert T.search_passages(reader, "dignity", None, bad_k)["status"] == "invalid_input"


def test_s01_concurrency_is_bounded_in_process(reader):
    """上限を超えた呼び出しは status ではなく例外（通信層）になる（Q65）。"""
    app.READER = reader
    taken = [app._SLOTS.acquire(blocking=False) for _ in range(app.MAX_CONCURRENCY)]
    try:
        assert all(taken)
        with pytest.raises(RuntimeError) as err:
            app.list_papers()
        assert app.BUSY_MESSAGE in str(err.value)
    finally:
        for _ in taken:
            app._SLOTS.release()
    assert json.loads(app.list_papers())["status"] == "ok"


def test_s01_port_env_is_checked():
    assert app.read_port(None) == app.DEFAULT_PORT and app.read_port("7861") == 7861
    for bad in ("0", "80", "65536", "-1", " 7861", "7861a", "０", "7861;ls", "99999"):
        with pytest.raises(ValueError):
            app.read_port(bad)


# ---------------------------------------------------------------- S01（HTTP の層）


def test_s01_standard_routes_are_blocked(server):
    seen = []
    for method, path, want in BLOCKED_ROUTES + OPEN_ROUTES:
        status, _text = server.request(method, path)
        seen.append((method, path, status))
        assert status == want, (method, path, status)
    assert all(s in (200, 403, 404) for _m, _p, s in seen)


def test_s01_host_and_body_limits(server):
    assert server.request("GET", "/config", headers={"Host": "evil.example.com"})[0] == 400
    assert server.request("GET", "/config", headers={"Host": "127.0.0.1.evil.com"})[0] == 400
    assert server.request("GET", "/config", headers={"Host": f"127.0.0.1:{server.port}"})[0] == 200
    assert server.request("GET", "/config", headers={"Host": f"localhost:{server.port}"})[0] == 200
    big = b"x" * (app.MAX_BODY_BYTES + 1)
    status, _ = server.request("POST", "/gradio_api/mcp/", body=big, headers=MCP_HEADERS)
    assert status == 413


def _burst(srv, n: int) -> list[dict]:
    """同じ呼び出しを n 本同時に送り、(status, 本文) を集める。"""
    text = ("answerability " * 140)[:1990]  # 上限近くまで伸ばして所要時間を稼ぐ
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "verify_quote", "arguments": {"text": text}}}).encode()
    results: list[dict] = []
    lock = threading.Lock()

    def call() -> None:
        status, raw = srv.request("POST", "/gradio_api/mcp/", body=body, headers=MCP_HEADERS,
                                  timeout=60, limit=None)
        with lock:
            results.append({"status": status, "raw": raw})

    threads = [threading.Thread(target=call) for _ in range(n)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert len(results) == n
    return results


def _busy_count(results) -> int:
    busy = 0
    for item in results:
        assert item["status"] == 200
        result = _sse_json(item["raw"]).get("result", {})
        if result.get("isError"):
            busy += 1
            text = json.dumps(result, ensure_ascii=False)
            assert "busy" in text and "status" not in json.loads(text).get("content", [{}])[0].get("text", "")
        else:
            assert json.loads(result["content"][0]["text"])["status"] in ("ok", "quote_not_found")
    return busy


def test_s01_blocked_routes_with_body(server):
    """遮断する経路に本文を付けて送っても、待たされずに拒まれる（本文の先読みで詰まらない）。"""
    payload = b"x" * 1024
    heavy = {"Content-Type": "application/octet-stream"}
    assert server.request("POST", "/gradio_api/upload", body=payload, headers=heavy)[0] == 403
    assert server.request("POST", "/gradio_api/queue/status", body=payload, headers=heavy)[0] == 404
    for method, path, want in (("HEAD", "/", 200), ("OPTIONS", "/config", 405), ("DELETE", "/config", 405)):
        assert server.request(method, path)[0] == want, (method, path)
    # 本文なしの POST も、先読みの待ちに入らない（MCP は 400 を返す）。
    assert server.request("POST", "/gradio_api/mcp/", body=b"", headers=MCP_HEADERS)[0] == 400


def test_s01_host_variants(server):
    """Host の欠落・重複・IPv6（Codex① P1-2 の敵対的試験）。"""
    port = str(server.port).encode()
    cases = [
        (b"GET /config HTTP/1.1\r\nConnection: close\r\n\r\n", (400,)),                        # 欠落
        (b"GET /config HTTP/1.1\r\nHost: 127.0.0.1\r\nHost: evil.example\r\nConnection: close\r\n\r\n",
         (400,)),                                                                                # 重複
        (b"GET /config HTTP/1.1\r\nHost: [::1]:" + port + b"\r\nConnection: close\r\n\r\n", (200,)),  # IPv6
        (b"GET /config HTTP/1.1\r\nHost: [::1]\r\nConnection: close\r\n\r\n", (200,)),          # IPv6・ポートなし
        (b"GET /config HTTP/1.1\r\nHost: 127.0.0.1.evil.example\r\nConnection: close\r\n\r\n", (400,)),
        (b"GET /config HTTP/1.1\r\nHost: \r\nConnection: close\r\n\r\n", (400,)),               # 空
        (b"GET /config HTTP/1.1\r\nHost: LocalHost:" + port + b"\r\nConnection: close\r\n\r\n", (200,)),  # 大小
        (b"GET /config HTTP/1.1\r\nHost: 127.0.0.1.\r\nConnection: close\r\n\r\n", (400,)),       # 末尾の点
    ]
    for request, want in cases:
        status, head = server.raw(request)
        assert status in want, (request.split(b"\r\n")[1], status, head[:80])


def test_s01_framing_is_checked(server):
    """Content-Length と Transfer-Encoding の形（Codex① P1-2）。"""
    body = b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
    head = f"POST /gradio_api/mcp/ HTTP/1.1\r\nHost: 127.0.0.1:{server.port}\r\n".encode()
    common = b"Content-Type: application/json\r\nAccept: application/json, text/event-stream\r\nConnection: close\r\n"
    cases = [
        # TE と CL の併記（要求の密輸の形）
        (head + common + b"Transfer-Encoding: chunked\r\nContent-Length: " + str(len(body)).encode()
         + b"\r\n\r\n" + body, 400),
        # CL の重複
        (head + common + b"Content-Length: " + str(len(body)).encode() + b"\r\nContent-Length: 5\r\n\r\n" + body, 400),
        # CL が ASCII 数字でない（全角）
        (head + common + "Content-Length: １０\r\n\r\n".encode("utf-8") + body, 400),
        # CL に符号や空白（+45 / 0x2d）
        (head + common + b"Content-Length: +45\r\n\r\n" + body, 400),
    ]
    for request, want in cases:
        status, text = server.raw(request)
        assert status == want, (request[:120], status, text[:80])
    ok = head + common + b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
    assert server.raw(ok)[0] == 200


def test_s01_body_size_boundary(server):
    """本文の大きさのちょうど境界（65,535／65,536／65,537 バイト）。"""
    for size, over in ((app.MAX_BODY_BYTES - 1, False), (app.MAX_BODY_BYTES, False), (app.MAX_BODY_BYTES + 1, True)):
        status, _ = server.request("POST", "/gradio_api/mcp/", body=b"x" * size, headers=MCP_HEADERS, timeout=60)
        assert (status == 413) is over, (size, status)


def test_s01_concurrency_slots_are_held(reader):
    """Event で4枠を埋め、5件目が通信層のエラーになることを確かめる（Codex① の敵対的試験）。"""
    app.READER = reader
    gate = threading.Event()
    entered = threading.Semaphore(0)

    def hold() -> None:
        def body():
            entered.release()
            gate.wait(20)
            return "held"

        try:
            app._in_slot(body)
        except RuntimeError:  # 枠が取れなかった分（この試験では起きない想定）
            entered.release()

    threads = [threading.Thread(target=hold, daemon=True) for _ in range(app.MAX_CONCURRENCY)]
    try:
        for thread in threads:
            thread.start()
        for _ in threads:
            assert entered.acquire(timeout=20)
        with pytest.raises(RuntimeError) as err:  # 5件目
            app.list_papers()
        assert app.BUSY_MESSAGE in str(err.value)
        with pytest.raises(RuntimeError):  # resources・prompts も同じ枠を使う
            app._in_slot(lambda: "x")
    finally:
        gate.set()
        for thread in threads:
            thread.join(timeout=20)
    assert json.loads(app.list_papers())["status"] == "ok"  # 解放された


def test_s01_concurrency_over_http(server):
    """上限＋4 を同時に送る。結果はどれも通常の応答か、通信層のエラー（status には混ざらない）。"""
    results = _burst(server, app.MAX_CONCURRENCY + 4)
    print(f"S01 同時実行（上限 {app.MAX_CONCURRENCY}）：{len(results)} 件中 busy {_busy_count(results)} 件")


def test_s01_concurrency_limit_is_reached_over_http(tmp_path):
    """上限を1に下げると、超過分が通信層のエラーで返ることを実測できる（Q65）。"""
    with Server(tmp_path / "audit.json", env_extra={"MEKIKI_TEST_CONCURRENCY": "1"}) as srv:
        busy = _busy_count(_burst(srv, 8))
        srv.stop()
    assert busy >= 1
    print(f"S01 同時実行（上限 1）：8 件中 busy {busy} 件")


def test_s01_env_vars_do_not_change_binding(tmp_path):
    """GRADIO_* を設定したまま起動しても、bind 先も vibe/dev/allowed_paths も変わらない（Q67・Q93）。"""
    hostile = {"GRADIO_SERVER_NAME": "0.0.0.0", "GRADIO_SERVER_PORT": "7999", "GRADIO_VIBE_MODE": "1",
               "GRADIO_WATCH_DIRS": str(REPO_ROOT), "GRADIO_ALLOWED_PATHS": "/",
               "GRADIO_ANALYTICS_ENABLED": "True", "GRADIO_SHARE": "True", "GRADIO_ROOT_PATH": "/evil",
               "MEKIKI_DATA_DIR": "/tmp", "MEKIKI_READER_DATA": "/tmp"}
    with Server(tmp_path / "audit.json", env_extra=hostile) as srv:
        assert srv.ready_line and f"127.0.0.1:{srv.port}" in srv.ready_line
        status, _ = srv.request("GET", "/config")
        assert status == 200
        env = MC.session(srv.mcp_url, lambda s: s.call_tool("list_papers", {}))
        assert MC.payload(env)["bundle_hash"] == C.EXPECTED_BUNDLE_SHA256  # データ根は固定（Q12）
        audit = srv.stop()
    assert audit["server_name"] == "127.0.0.1"
    assert audit["vibe_mode"] is False and audit["dev_mode"] is False
    assert audit["allowed_paths"] == [] and audit["analytics_enabled"] is False
    assert set(hostile) - set(audit["removed_env"]) == {"MEKIKI_DATA_DIR", "MEKIKI_READER_DATA"}
    assert audit["local_url"].startswith(f"http://127.0.0.1:{srv.port}")


# ---------------------------------------------------------------- S02


def test_s02_instruction_like_text_is_data(server, reader):
    """命令風テキストを入れても、状態も欄の構成も権限も変わらない（Q40）。"""
    async def body(s):
        out = {}
        for case in INSTRUCTION_LIKE:
            out[case["id"]] = {
                "search": MC.payload(await s.call_tool("search_passages", {"query": case["text"][:150]})),
                "quote": MC.payload(await s.call_tool("verify_quote", {"text": case["text"][:1990]})),
                "check": MC.payload(await s.call_tool("check_compressions", {"text": case["text"][:1990]})),
                "claim": MC.payload(await s.call_tool("get_claim_record", {"query": case["text"][:150]})),
            }
        return out

    async def baseline_body(s):
        return {
            "search": MC.payload(await s.call_tool("search_passages", {"query": "dignity"})),
            "quote": MC.payload(await s.call_tool("verify_quote", {"text": "AI can assist play."})),
            "check": MC.payload(await s.call_tool("check_compressions", {"text": "AIは遊べない"})),
            "claim": MC.payload(await s.call_tool("get_claim_record", {"query": "dignity"})),
        }

    got = MC.session(server.mcp_url, body)
    baseline = MC.session(server.mcp_url, baseline_body)
    for case_id, envs in got.items():
        for name, env in envs.items():
            S.validate_envelope(env)
            # 欄の構成は、命令風でない同じツールの結果と同じ（増えも減りもしない）。
            assert set(env) == set(baseline[name]), (case_id, name)
            assert env["status"] in ("ok", "invalid_input", "quote_not_found", "no_lexical_match"), (case_id, name)
            assert env["bundle_hash"] == C.EXPECTED_BUNDLE_SHA256
            for result in env["results"] + env["candidates"]:
                assert result["source_path"] in C.ALLOWED_PATHS, (case_id, name)


def test_s02_corpus_commands_are_returned_as_data(server):
    """コーパス内の命令風の文（台帳の maintenance 欄など）は、出典つきのデータとして返るだけ。"""
    async def body(s):
        return (MC.payload(await s.call_tool("get_claim_record", {"claim_id": "T5-N3"})),
                MC.payload(await s.call_tool("get_reading_guide", {"part": "cautions"})),
                (await s.get_prompt("read_with_guards")).messages[0].content.text)

    claim, guide, prompt_text = MC.session(server.mcp_url, body)
    for env in (claim, guide):
        for result in env["results"]:
            assert result["source_kind"] in S.SOURCE_KINDS and result["locator"]["path"] in C.ALLOWED_PATHS
    assert PR.GUARD_SENTENCE in prompt_text and PR.MATERIAL_SENTENCE in prompt_text


# ---------------------------------------------------------------- S03


def test_s03_no_outbound_traffic(tmp_path, reader):
    """起動から全ツール・全 resource・全 prompt の呼び出しまで、loopback 以外への通信が無い。"""
    with Server(tmp_path / "audit.json") as srv:
        async def body(s):
            for name, args, _want in _ALL_CALLS:
                await s.call_tool(name, args)
            for path in _RESOURCE_PATHS:
                await s.read_resource(f"mekiki://v{C.CORPUS_VERSION}/{path}")
            for template in PR.TEMPLATES:
                await s.get_prompt(template.name)
            return True

        assert MC.session(srv.mcp_url, body) is True
        audit = srv.stop()
    # 自己接続（loopback かつ自分の待ち受けポート）以外は一つも無い。
    assert audit["outbound"] == [], audit["outbound"]
    targets = sorted({record[1] for record in audit["net"] if record[2] != "stopping"})
    for target in targets:
        host, _, port = target.rpartition(":")
        assert not target.startswith("unix:"), target
        assert host in ("127.0.0.1", "::1", "localhost", "0.0.0.0", ""), target
        if host in ("127.0.0.1", "::1") and port.isdigit():
            assert port == str(audit["port"]), target
    # 陽性対照：フックが効いていること（外向きは止まり、自己接続は通る）。
    assert audit["control"]["getaddrinfo"].startswith("blocked"), audit["control"]
    assert audit["control"]["connect"].startswith("blocked"), audit["control"]
    assert audit["control"]["self"] == "allowed", audit["control"]
    assert {r[1] for r in audit["control_net"]} == {"mekiki-control.invalid:80", "203.0.113.1:80"}
    # 配信中に開くのは、遅延 import される Python 本体と site-packages のファイルだけ。
    # data/ を含むリポジトリのファイルは開かず、書き込みで開いたものも無い（Q12・SPEC §2.2）。
    prefixes = (sys.base_prefix, sys.prefix, str(REPO_ROOT / ".venv"), "/dev/")
    serving = [row for row in audit["opened"] if row[3] == "serving"]
    # 利用者のホームのファイル（HF のトークンなど）を開かない。値は読まず、開いたかどうかだけを見る。
    assert not [r for r in serving if r[0].startswith(str(Path.home() / ".cache"))]
    writes = [r[0] for r in serving if any(c in r[1] for c in "wax+") or _write_flags(r[2])]
    outside = [r[0] for r in serving if not r[0].startswith(prefixes)]
    assert writes == [] and outside == [], (writes[:5], outside[:5])
    # どの段階でも、リポジトリの中（とくに data/）を書き込みで開かない。
    # 起動前に Gradio が一時領域へ書くこと自体はあるので、そこは対象にしない（記録には残る）。
    every_write = [r[0] for r in audit["opened"] if any(c in r[1] for c in "wax+") or _write_flags(r[2])]
    assert not [p for p in every_write if p.startswith(str(REPO_ROOT))], every_write[:5]
    assert audit["mcp_server"] is True and audit["share"] is False and audit["run_history"] is False
    assert audit["queue_max_size"] == app.QUEUE_MAX_SIZE and audit["queue_concurrency"] == app.MAX_CONCURRENCY
    # 番兵は endpoint 一覧の最後（prompts/get の取りこぼしを受け止める位置。Q64）。
    assert audit["endpoints"][-1].endswith("mekiki_sentinel")


def test_s03_reader_has_no_network_imports():
    """mekiki_reader が通信・外部モデル・シェルの module を import していない（静的検査）。"""
    forbidden = ("openai", "anthropic", "transformers", "huggingface_hub", "socket", "urllib",
                 "httpx", "requests", "subprocess", "random", "gradio", "mcp")
    for path in sorted((REPO_ROOT / "mekiki_reader").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text, (path.name, name)


def test_s03_app_launch_arguments():
    """app.py が環境変数を整え、loopback で起動し、標準経路を遮断していること（静的検査）。"""
    text = (REPO_ROOT / "app.py").read_text(encoding="utf-8")
    for needed in ('HF_TOKEN_PATH": os.devnull', 'HF_HUB_DISABLE_IMPLICIT_TOKEN', 'server_name=SERVER_NAME', 'SERVER_NAME = "127.0.0.1"', "share=False",
                   "run_history=False", "ssr_mode=False", "enable_monitoring=False",
                   "analytics_enabled=False", "allowed_paths=[]", "blocked_paths=[]",
                   'GRADIO_ANALYTICS_ENABLED": "False"', 'HF_HUB_DISABLE_TELEMETRY": "1"',
                   "app_kwargs=", "prevent_thread_lock=True"):
        assert needed in text, needed
    assert text.index("REMOVED_GRADIO_ENV = sanitize_environ()") < text.index("import gradio as gr")


_ALL_CALLS = (
    ("list_papers", {}, "ok"),
    ("get_section", {"paper_id": "T1", "anchor": "t1-2-9"}, "ok"),
    ("search_passages", {"query": "dignity", "k": 3}, "ok"),
    ("get_claim_record", {"query": "dignity"}, "ok"),
    ("verify_quote", {"text": "AI can assist play. It cannot take one's place in it."}, "ok"),
    ("check_compressions", {"text": "AIは遊べない"}, "ok"),
    ("get_reading_guide", {"part": "all"}, "ok"),
)
_RESOURCE_PATHS = ("llms.txt", "FOR_AI_READERS.md", "THEORY_MAP.md", "SOURCE_INDEX.md",
                   "papers/T1.md", "papers/T2.md", "papers/T3.md", "papers/T4.md", "papers/T5.md",
                   "translations/T4.en.md", "AI_READING_TESTS.md", "claims/t5.json")
