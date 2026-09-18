"""施工段階3の完了条件 S01〜S03（SPEC §7・docs/PLAN.md A-4）。サーバを起動して確かめる。"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

import anyio
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
    ("GET", "/config", 404),                      # 塞いだ（SPEC v2.3 との照合。要らないと実測）
    ("GET", "/config/", 404),
    ("GET", "/gradio_api/mcp/sse", 404),          # 旧 SSE の予備経路を閉じた（Streamable HTTP だけで動くと実測）
    ("POST", "/gradio_api/mcp/messages/", 404),
    ("POST", "/gradio_api/mcp/messages/?session_id=0", 404),
    ("GET", "/gradio_api/mcp/sse/", 404),
    ("POST", "/gradio_api/mcp/http", 404),        # 上流の Streamable HTTP の別名（前方一致をやめて閉じた）
    ("GET", "/gradio_api/mcp/http/", 404),
)
OPEN_ROUTES = (("GET", "/", 200), ("GET", "/gradio_api/info", 200), ("GET", "/gradio_api/info/", 200),
               ("GET", "/gradio_api/startup-events", 200), ("GET", "/gradio_api/mcp/schema", 200))

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


LONE = "dign" + chr(0xD800) + "ity"  # 孤立サロゲート（JSON の "\\ud800" から入りうる）
SURROGATE_CALLS = (
    ("get_section", {"paper_id": "T4", "anchor": "t4-2" + chr(0xDC00)}),
    ("search_passages", {"query": LONE}),
    ("get_claim_record", {"query": LONE}),
    ("verify_quote", {"text": LONE * 3}),
    ("check_compressions", {"text": LONE}),
    ("get_reading_guide", {"part": "modes" + chr(0xDBFF)}),  # これは part の許可一覧（11個）で弾かれる
)


@pytest.mark.parametrize("name,args", SURROGATE_CALLS, ids=[c[0] for c in SURROGATE_CALLS])
def test_s01_lone_surrogates_are_invalid(reader, name, args):
    """孤立サロゲートを含む入力は invalid_input で、応答は UTF-8 に直せる（関数の層・6ツール）。"""
    env = getattr(T, name)(reader, **args)
    assert env["status"] == "invalid_input" and env["results"] == [] and env["candidates"] == []
    S.to_json(env).encode("utf-8")  # 直列化と UTF-8 化で落ちない
    assert not any(0xD800 <= ord(ch) <= 0xDFFF for ch in S.to_json(env))  # 応答に写し返さない


def test_s01_lone_surrogates_over_mcp(server):
    """同じ入力を JSON の \\ud800 形式で MCP に送っても、通信は切れず invalid_input が返る（通信の層）。"""
    problems = []
    for name, args in SURROGATE_CALLS:
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                              "params": {"name": name, "arguments": args}})  # ensure_ascii で \\udXXX になる
        assert any(mark in payload.lower() for mark in ("\\ud8", "\\udb", "\\udc"))
        status, raw = server.request("POST", "/gradio_api/mcp/", body=payload.encode("ascii"),
                                     headers=MCP_HEADERS, timeout=60, limit=None)
        if status != 200:
            problems.append((name, "http", status))
            continue
        if any(mark in raw.lower() for mark in ("\\ud8", "\\udb", "\\udc")):
            problems.append((name, "echoed", raw[:80]))  # 応答にサロゲートを写し返さない
        result = _sse_json(raw)["result"]
        if result.get("isError") is not False:
            problems.append((name, "isError", result))
            continue
        status_value = json.loads(result["content"][0]["text"])["status"]
        if status_value != "invalid_input":
            problems.append((name, "status", status_value))
    assert problems == []  # 最初の失敗で止めず、全ツールの結果をまとめて見る
    assert MC.payload(MC.session(server.mcp_url, lambda s: s.call_tool("list_papers", {})))["status"] == "ok"


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


def test_s01_allowlist_is_pinned():
    """通す経路の一覧を固定する（README・LIMITS の一覧と同じ。変えるときは文書と一緒に変える）。"""
    assert app.ALLOWED_EXACT == frozenset({"/", "/gradio_api/info", "/gradio_api/info/", "/gradio_api/startup-events",
                                           "/gradio_api/queue/join", "/gradio_api/queue/data",
                                           "/gradio_api/mcp", "/gradio_api/mcp/", "/gradio_api/mcp/schema"})
    assert app.ALLOWED_PREFIXES == ("/gradio_api/heartbeat/",)
    assert app.STREAM_LIMITS == {"heartbeat": 8, "queue_data": 8, "mcp_get": 32}
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    limits = (REPO_ROOT / "docs" / "rules" / "LIMITS.md").read_text(encoding="utf-8")
    for doc in (readme, limits):
        assert "で始まる経路" not in doc  # 前方一致で MCP の下を通していた頃の書き方が残っていない
    def table(header: str) -> list[str]:  # README の表（見出し行の次の区切り行より後、表が終わるまで）
        lines = readme.splitlines()
        start = lines.index(header) + 2
        end = next(i for i in range(start, len(lines)) if not lines[i].startswith("|"))
        return lines[start:end]

    open_rows = {line.split("|")[1].strip() for line in table("| 経路 | 通す理由 |")}
    assert open_rows == {"`/`", "`/gradio_api/startup-events`", "`/gradio_api/info`（末尾 `/` 付きも）",
                         "`/gradio_api/queue/join`", "`/gradio_api/queue/data`", "`/gradio_api/heartbeat/*`",
                         "`/gradio_api/mcp/`", "`/gradio_api/mcp/schema`"}, open_rows
    closed = [line for line in table("| 経路 | 応答 |") if "`/gradio_api/mcp/sse`" in line]
    assert len(closed) == 1 and closed[0].endswith("| 404 |") and "`/gradio_api/mcp/http`" in closed[0]
    assert [line.split("|")[1:3] for line in table("| 種類 | 同時数 | 実測（2026-09-19） |")] == [
        [" `/gradio_api/heartbeat/*` ", " 8 "], [" `/gradio_api/queue/data` ", " 8 "],
        [" `GET /gradio_api/mcp/`（Streamable HTTP の待ち受け） ", " 32 "]]
    open_cell = next(line for line in limits.splitlines() if line.startswith("| 開放経路 |"))
    assert "`/gradio_api/mcp/sse`・`/gradio_api/mcp/messages/`・`/gradio_api/mcp/http`" in open_cell
    assert "を閉じた" in open_cell
    stream_cell = next(line for line in limits.splitlines() if line.startswith("| 長時間接続"))
    assert all(s in stream_cell for s in ("`/gradio_api/heartbeat/*` 8", "`/gradio_api/queue/data` 8",
                                          "`GET /gradio_api/mcp/` 32"))


def test_s01_standard_routes_are_blocked(server):
    seen = []
    for method, path, want in BLOCKED_ROUTES + OPEN_ROUTES:
        status, _text = server.request(method, path)
        seen.append((method, path, status))
        assert status == want, (method, path, status)
    assert all(s in (200, 403, 404) for _m, _p, s in seen)


def test_s01_host_and_body_limits(server):
    assert server.request("GET", "/gradio_api/info", headers={"Host": "evil.example.com"})[0] == 400
    assert server.request("GET", "/gradio_api/info", headers={"Host": "127.0.0.1.evil.com"})[0] == 400
    assert server.request("GET", "/gradio_api/info", headers={"Host": f"127.0.0.1:{server.port}"})[0] == 200
    assert server.request("GET", "/gradio_api/info", headers={"Host": f"localhost:{server.port}"})[0] == 200
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
    for method, path, want in (("HEAD", "/", 200), ("OPTIONS", "/gradio_api/info", 405), ("DELETE", "/gradio_api/info", 405)):
        assert server.request(method, path)[0] == want, (method, path)
    # 本文なしの POST も、先読みの待ちに入らない（MCP は 400 を返す）。
    assert server.request("POST", "/gradio_api/mcp/", body=b"", headers=MCP_HEADERS)[0] == 400


def test_s01_slow_body_is_cut(server):
    """本文を少しずつ送り続けても、受信ループ全体の期限で切られる（Codex② 3）。"""
    body = b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
    head = (f"POST /gradio_api/mcp/ HTTP/1.1\r\nHost: 127.0.0.1:{server.port}\r\n"
            f"Content-Type: application/json\r\nAccept: application/json, text/event-stream\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode()
    sock = socket.create_connection(("127.0.0.1", server.port), timeout=app.BODY_READ_SECONDS + 20)
    started = time.monotonic()
    try:
        sock.sendall(head)
        try:  # 1バイトずつ、期限より長くかけて送る
            for byte in body:
                sock.sendall(bytes([byte]))
                time.sleep(app.BODY_READ_SECONDS / 8)
        except OSError:
            pass  # 期限で閉じられた
        sock.settimeout(20)
        try:
            answer = sock.recv(200).decode("latin-1", "replace")
        except OSError:
            answer = ""
    finally:
        sock.close()
    elapsed = time.monotonic() - started
    assert elapsed < app.BODY_READ_SECONDS * 2.5, elapsed
    assert answer == "" or " 408 " in answer, answer[:80]


def test_s01_queue_waiting_is_capped(tmp_path):
    """受付も待機も塞がっているときは、通信層で断る（status には混ぜない。Codex② 1）。"""
    env = {"MEKIKI_TEST_QUEUE_INFLIGHT": "0", "MEKIKI_TEST_QUEUE_WAITING": "0"}
    with Server(tmp_path / "audit.json", env_extra=env) as srv:
        body = json.dumps({"data": [], "fn_index": 0, "session_hash": "capped",
                           "trigger_id": None, "event_data": None}).encode()
        codes = [srv.request("POST", "/gradio_api/queue/join", body=body,
                             headers={"Content-Type": "application/json"})[0] for _ in range(6)]
        assert codes == [503] * 6, codes
        assert srv.request("GET", "/gradio_api/info")[0] == 200  # ほかの経路は生きている
        assert MC.payload(MC.session(srv.mcp_url, lambda s: s.call_tool("list_papers", {})))["status"] == "ok"
        audit = srv.stop()
    assert audit["queue_state"]["rejected"] == 6
    assert audit["guard_counts"].get("503") == 6 or audit["guard_counts"].get(503) == 6


def _hold_stream(port: int, path: str, accept: str = "text/event-stream") -> tuple[socket.socket, int]:
    """長時間接続を開いたままにする（状態行だけ読んで返す）。"""
    sock = socket.create_connection(("127.0.0.1", port), timeout=10)
    sock.sendall(f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nAccept: {accept}\r\n\r\n".encode())
    head = b""
    while b"\r\n" not in head:
        chunk = sock.recv(1)
        if not chunk:
            break
        head += chunk
    return sock, int(head.split(b" ")[1]) if head.startswith(b"HTTP/1.1 ") else 0


def test_s01_long_lived_streams_are_capped(tmp_path):
    """塞げない長時間接続は種類ごとに同時数を絞り、超えた分は通信層で 503。内部クライアントは断らない。"""
    with Server(tmp_path / "audit.json", env_extra={"MEKIKI_TEST_STREAMS": "0"}) as srv:
        assert srv.request("GET", "/gradio_api/heartbeat/outsider")[0] == 503
        assert srv.request("GET", "/gradio_api/queue/data?session_hash=outsider")[0] == 503
        status, text = srv.request("GET", "/gradio_api/mcp/", headers={"Accept": "text/event-stream"})
        assert (status, text) == (503, "too many open streams")

        def body(s):  # 上限0でも、内部クライアントを通る resources/read・prompts/get は動く
            async def run():
                listed = await s.call_tool("list_papers", {})
                read = await s.read_resource("mekiki://v3.5.0/llms.txt")
                prompt = await s.get_prompt("four_modes")
                return listed, read, prompt
            return run()

        listed, read, prompt = MC.session(srv.mcp_url, body)
        assert MC.payload(listed)["status"] == "ok"
        assert read.contents[0].text == (REPO_ROOT / "data" / "llms.txt").read_text(encoding="utf-8")
        assert prompt.messages and prompt.messages[0].content.text == PR.FOUR_MODES.text
        time.sleep(1)
        audit = srv.stop()
    streams = audit["streams"]
    assert streams["internal_peak"]["heartbeat"] == 1 and streams["internal_peak"]["queue_data"] >= 1
    assert streams["rejected"]["queue_data"] == 1 and streams["rejected"]["mcp_get"] == 1
    # 内部クライアントが作られる一瞬（セッションが分かる前）に heartbeat が断られても、再試行の嵐にならない
    assert 1 <= streams["rejected"]["heartbeat"] < 20, streams
    assert sum(int(n) for n in audit["guard_counts"].values()) < 25, audit["guard_counts"]


def test_s01_stream_slots_are_released(tmp_path):
    """上限まで開くと次は 503、一本閉じれば枠が戻る（heartbeat と GET /gradio_api/mcp/）。

    heartbeat は起動時に作った内部クライアントの1本も数に入るので、外から開けるのは上限3のうち2本。
    """
    with Server(tmp_path / "audit.json", env_extra={"MEKIKI_TEST_STREAMS": "3"}) as srv:
        for path, room in (("/gradio_api/heartbeat/outsider", 2), ("/gradio_api/mcp/", 3)):
            held = [_hold_stream(srv.port, path) for _ in range(room)]
            assert [code for _s, code in held] == [200] * room, (path, held)
            assert srv.request("GET", path, headers={"Accept": "text/event-stream"})[0] == 503, path
            held[0][0].close()
            deadline = time.monotonic() + 5
            while True:
                again, code = _hold_stream(srv.port, path)
                again.close()
                if code == 200 or time.monotonic() > deadline:
                    break
                time.sleep(0.2)
            assert code == 200, path
            for sock, _code in held[1:]:
                sock.close()
            time.sleep(0.5)
        audit = srv.stop()
    assert audit["streams"]["peak"]["mcp_get"] == 3 and audit["streams"]["peak"]["heartbeat"] == 3
    assert audit["streams"]["internal_peak"]["heartbeat"] == 1
    assert audit["streams"]["rejected"]["mcp_get"] >= 1 and audit["streams"]["rejected"]["heartbeat"] >= 1


def test_s01_one_internal_client(tmp_path):
    """起動直後に resources/read・prompts/get が同時に80本来ても、すべて通り、内部クライアントは一つだけ。

    上流は最初の呼び出しのときに鍵なしで作るため、同時に来ると複数でき（16本同時で2〜16個）、
    同時40本を超えると作成の自己要求が thread pool の空きを待って失敗した（検算）。起動時に作っておく。
    """
    with Server(tmp_path / "audit.json") as srv:
        results = []

        async def first_calls():
            async def one(i):
                async with MC.streamablehttp_client(srv.mcp_url) as (r, w, _):
                    async with MC.ClientSession(r, w) as s:
                        await s.initialize()
                        if i % 4 == 3:
                            got = await s.get_prompt("four_modes")
                            results.append(got.messages[0].content.text == PR.FOUR_MODES.text)
                        else:
                            got = await s.read_resource("mekiki://v3.5.0/llms.txt")
                            results.append(bool(got.contents and got.contents[0].text))
            with anyio.fail_after(90):
                async with anyio.create_task_group() as tg:
                    for i in range(80):
                        tg.start_soon(one, i)
        anyio.run(first_calls)
        time.sleep(1)
        audit = srv.stop()
    assert results.count(True) == 80, results.count(True)
    streams = audit["streams"]
    assert streams["peak"]["heartbeat"] == 1 and streams["internal_peak"]["heartbeat"] == 1, streams
    assert streams["rejected"] == {"heartbeat": 0, "queue_data": 0, "mcp_get": 0}


def test_s01_uncollected_results_are_dropped(tmp_path):
    """結果を回収しない join を繰り返しても、溜め込まずに捨てる（Codex② 1）。"""
    with Server(tmp_path / "audit.json", env_extra={"MEKIKI_TEST_SWEEP": "1"}) as srv:
        body = json.dumps({"data": [], "fn_index": 0, "session_hash": "never-collected",
                           "trigger_id": None, "event_data": None}).encode()
        for _ in range(12):
            status, _ = srv.request("POST", "/gradio_api/queue/join", body=body,
                                    headers={"Content-Type": "application/json"})
            assert status == 200, status
        assert MC.payload(MC.session(srv.mcp_url, lambda s: s.call_tool("list_papers", {})))["status"] == "ok"
        time.sleep(5)  # 掃除（この試験では1秒間隔）が回るのを待つ
        audit = srv.stop()
    assert audit["sweep"]["runs"] >= 1
    assert audit["sweep"]["dropped"] >= 1, audit["sweep"]


def test_sweep_results_drops_by_count_size_and_age():
    """掃除の判定（件数・大きさ・期限）を、作り物の待ち行列で確かめる。"""
    class Fake:
        def __init__(self):
            self.pending_messages_per_session = {}
            self.pending_event_ids_session = {}
            self.event_ids_to_events = {}

    class Pending:
        def __init__(self, items):
            self._queue = list(items)

    app._SWEEP["first_seen"] = {}
    queue = Fake()
    queue.pending_messages_per_session["fresh"] = Pending(["x"])
    queue.pending_messages_per_session["many"] = Pending(["x"] * (app.RESULT_MESSAGES_MAX + 1))
    queue.pending_messages_per_session["big"] = Pending(["y" * (app.RESULT_BYTES_MAX + 10)])
    queue.pending_messages_per_session["old"] = Pending(["x"])
    for session in queue.pending_messages_per_session:
        queue.pending_event_ids_session[session] = {f"e-{session}"}
        queue.event_ids_to_events[f"e-{session}"] = object()
    assert app.sweep_results(queue, 0.0) == 2                     # many と big
    app._SWEEP["first_seen"]["old"] = -(app.RESULT_TTL_SECONDS + 1)
    assert app.sweep_results(queue, 0.0) == 1                     # old（期限）
    assert list(queue.pending_messages_per_session) == ["fresh"]  # 新しいものは残る
    assert list(queue.event_ids_to_events) == ["e-fresh"]
    assert app.sweep_results(None, 0.0) == 0                      # 待ち行列が無くても落ちない


def test_s01_host_variants(server):
    """Host の欠落・重複・IPv6（Codex① P1-2 の敵対的試験）。"""
    port = str(server.port).encode()
    cases = [
        (b"GET /gradio_api/info HTTP/1.1\r\nConnection: close\r\n\r\n", (400,)),                        # 欠落
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: 127.0.0.1\r\nHost: evil.example\r\nConnection: close\r\n\r\n",
         (400,)),                                                                                # 重複
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: [::1]:" + port + b"\r\nConnection: close\r\n\r\n", (200,)),  # IPv6
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: [::1]\r\nConnection: close\r\n\r\n", (200,)),          # IPv6・ポートなし
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: 127.0.0.1.evil.example\r\nConnection: close\r\n\r\n", (400,)),
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: \r\nConnection: close\r\n\r\n", (400,)),               # 空
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: LocalHost:" + port + b"\r\nConnection: close\r\n\r\n", (200,)),  # 大小
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: 127.0.0.1.\r\nConnection: close\r\n\r\n", (400,)),       # 末尾の点
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: localhost:0\r\nConnection: close\r\n\r\n", (400,)),      # ポート0
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: localhost:99999\r\nConnection: close\r\n\r\n", (400,)),  # 範囲外
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: localhost:abc\r\nConnection: close\r\n\r\n", (400,)),    # 数字でない
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: localhost:\r\nConnection: close\r\n\r\n", (400,)),       # ポート空
        (b"GET /gradio_api/info HTTP/1.1\r\nHost: [::1]x80\r\nConnection: close\r\n\r\n", (400,)),         # 括弧の後の接尾辞
    ]
    for request, want in cases:
        status, head = server.raw(request)
        assert status in want, (request.split(b"\r\n")[1], status, head[:80])


def test_s01_no_cors_for_origin_requests(server):
    """Origin 付きの要求に CORS の許可を返さない（ブラウザから応答を読ませない）。"""
    origins = ("http://localhost:3000", "http://127.0.0.1:1234", "https://evil.example", "null",
               f"http://localhost:{server.port}")
    for origin in origins:
        for method, path in (("GET", "/"), ("GET", "/gradio_api/info"), ("POST", "/gradio_api/mcp/")):
            body = b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}' if method == "POST" else None
            headers = {"Origin": origin}
            if body:
                headers.update(MCP_HEADERS)
            status, text = server.raw(_request(method, path, server.port, headers, body), timeout=30)
            assert status in (200, 400, 405), (origin, path, status)
            assert "access-control" not in text.lower(), (origin, path, text[:120])
    # 事前確認（preflight）も許可を返さない。
    head = _request("OPTIONS", "/gradio_api/mcp/", server.port,
                    {"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    status, text = server.raw(head)
    assert "access-control" not in text.lower(), text[:200]
    # Origin が無い要求は普通に通る（MCP クライアントは Origin を送らない）。
    assert server.request("GET", "/gradio_api/info")[0] == 200


def _request(method: str, path: str, port: int, headers: dict, body: bytes | None = None) -> bytes:
    lines = [f"{method} {path} HTTP/1.1", f"Host: 127.0.0.1:{port}", "Connection: close"]
    lines += [f"{k}: {v}" for k, v in headers.items()]
    if body is not None:
        lines.append(f"Content-Length: {len(body)}")
    raw = ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")
    return raw + (body or b"")


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
        status, _ = srv.request("GET", "/gradio_api/info")
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
    # 陽性対照：フックが効いていること（外向き・子プロセス・sendmsg・別の IPv6・data/ への rename は止まり、
    # 自己接続は通る）。検出漏れとして挙がった経路を一つずつ当てる（Codex② 4）。
    control = audit["control"]
    for key in ("getaddrinfo", "connect", "child_process", "sendmsg", "ipv6_other_port", "rename_into_data"):
        assert control[key].startswith("blocked"), (key, control[key])
    assert control["self"] == "allowed", control
    assert control["rename_did_nothing"] == "True" and control["rename_target_recorded"] == "True", control
    assert {r[1] for r in audit["control_net"]} == {"mekiki-control.invalid:80", "203.0.113.1:80",
                                                    "203.0.113.2:9", "::1:9"}
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
    # 子プロセス・open 以外の書き換え・記録の取りこぼしが無いこと（検算⑥・⑨）。
    # 子プロセスは起こさない（陽性対照で自分から試した分だけが "stopping" に残る）。
    assert [row for row in audit["process"] if row[2] != "stopping"] == [], audit["process"][:3]
    # 書き換えの記録は [event, 元, 先, …, 段階]。data/ には一切触れず、配信中はリポジトリ配下を書き換えない。
    def repo_paths(row):
        return [str(p) for p in row[1:-1]
                if str(p).startswith(str(REPO_ROOT)) and "__pycache__" not in str(p)]

    while_serving = [m for m in audit["mutated"] if m[-1] == "serving" and repo_paths(m)]
    assert while_serving == [], while_serving[:3]
    touched_data = [m for m in audit["mutated"] if m[-1] != "stopping"
                    and any(p.startswith(str(REPO_ROOT / "data")) for p in repo_paths(m))]
    assert touched_data == [], touched_data[:3]
    # 起動中に Gradio が作業ディレクトリへ一時ファイルを作って消すこと自体は記録に残る（README の既知の制約）。
    at_import = {Path(p).name for m in audit["mutated"] if m[-1] == "import" for p in repo_paths(m)}
    assert at_import <= {"probe-source", "probe-link"}, at_import
    assert audit["open_dropped"] == 0
    assert any(b[1].startswith("('127.0.0.1'") for b in audit["bound"]), audit["bound"]
    # 自己呼び出しの内部クライアントが、塞いだ経路に再試行を繰り返していないこと（heartbeat を塞ぐと
    # 毎秒約1,000回の 404 になり一時ポートを使い果たした。2026-09-18 の実測）。
    assert sum(int(v) for v in audit["guard_counts"].values()) < 20, (audit["guard_counts"], audit["guard"][:5])
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
