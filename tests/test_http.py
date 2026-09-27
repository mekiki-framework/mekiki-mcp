"""HTTP 併設の試験 H01〜H04（SPEC v2.5.2 §2.12・§7・docs/rules/HTTP.md の HTTP-1.2.0）。

サーバを local と spaces の二つのモードで起動し、同じ試験を両方で通す。spaces は SPACE_HOST 宛ての Host で
要求する（待ち受けは試験のため loopback。MEKIKI_TEST_BIND）。
"""

from __future__ import annotations

import http.client
import json
import socket
import sys
import time
import urllib.parse
from pathlib import Path

import pytest

import app
from mekiki_reader import corpus as C
from mekiki_reader import http_api as H
from mekiki_reader import schema as S
from tests._support import mcp_client as MC
from tests._support import r01_calls
from tests._support.server import Server

pytestmark = pytest.mark.server

REPO_ROOT = Path(__file__).resolve().parent.parent
SPACE_HOST = "owner-mekiki-reader.hf.space"
MODE_ENV = {
    "local": {},
    "spaces": {"MEKIKI_READER_MODE": "spaces", "SPACE_HOST": SPACE_HOST, "MEKIKI_TEST_BIND": "127.0.0.1"},
}
MD = {"Accept": "text/markdown"}
T5_QUOTE = "AI can assist play. It cannot take one's place in it."
T4_EN_QUOTE = "At the center of undertaking sits a relation independent of ability"  # translations/T4.en.md L293


class Api:
    """一つのモードのサーバと、そのモードの Host で送る素の HTTP。"""

    def __init__(self, srv: Server, mode: str):
        self.srv, self.mode = srv, mode
        self.host = SPACE_HOST if mode == "spaces" else f"127.0.0.1:{srv.port}"

    def call(self, method: str, path: str, body: "bytes | None" = None, headers=None,
             host: "str | None" = None) -> tuple[int, dict, bytes]:
        """headers は dict か (名前, 値) の列（同名ヘッダを複数行で送るとき）。"""
        conn = http.client.HTTPConnection("127.0.0.1", self.srv.port, timeout=30)
        try:
            conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            conn.putheader("Host", self.host if host is None else host)
            items = headers.items() if isinstance(headers, dict) else (headers or ())
            for k, v in items:
                conn.putheader(k, v)
            if body is not None:
                conn.putheader("Content-Length", str(len(body)))
            conn.endheaders(body)
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, {k.lower(): v for k, v in resp.getheaders()}, data
        finally:
            conn.close()

    def get(self, path: str, **params) -> tuple[int, dict, bytes]:
        query = urllib.parse.urlencode(params)
        return self.call("GET", path + ("?" + query if query else ""))

    def post(self, path: str, obj, headers: "dict | None" = None) -> tuple[int, dict, bytes]:
        return self.call("POST", path, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                         {"Content-Type": "application/json", **(headers or {})})


@pytest.fixture(scope="module", params=["local", "spaces"])
def api(request, tmp_path_factory):
    mode = request.param
    srv = Server(tmp_path_factory.mktemp(f"http-{mode}") / "audit.json", env_extra=MODE_ENV[mode])
    srv.start()
    try:
        yield Api(srv, mode)
    finally:
        srv.stop()


def _env(data: bytes) -> dict:
    obj = json.loads(data.decode("utf-8"))
    S.validate_envelope(obj)
    return obj


# ---------------------------------------------------------------- 経路の表（S01 と共通の固定）

NINE = (("GET", "/api/v1/"), ("GET", "/api/v1/papers"), ("GET", "/api/v1/papers/{paper_id}/sections/{anchor}"),
        ("GET", "/api/v1/search"), ("GET", "/api/v1/claims"), ("GET", "/api/v1/guide"),
        ("GET", "/api/v1/verify"), ("POST", "/api/v1/verify"), ("POST", "/api/v1/check"))


def test_h_routes_are_pinned():
    assert tuple((r.method, r.path) for r in H.ROUTES) == NINE
    assert {r.tool for r in H.ROUTES} - {None} == set(app.TOOL_NAMES)  # 七ツールがどれも HTTP から呼べる
    assert H.HTTP_VERSION == "HTTP-1.2.0"
    assert app.T.LIMITS_VERSION == "LIMITS-3.3.0"
    assert H.PREFIX in app.PRE_READ_PREFIXES
    assert app._admission_kind("POST", "/api/v1/check") == "other"  # 受付枠は「その他」
    assert app._admission_kind("GET", "/api/v1/papers") == "other"


# ---------------------------------------------------------------- H01（MCP と同一の JSON・R01 の HTTP 版）

# (ツール, MCP の引数, HTTP のメソッド, 経路, 問い合わせか本文, HTTP の状態コード)
H01_CASES = (
    ("list_papers", {}, "GET", "/api/v1/papers", None, 200),
    ("get_section", {"paper_id": "T4", "anchor": "t4-2-4"}, "GET", "/api/v1/papers/T4/sections/t4-2-4", None, 200),
    ("get_section", {"paper_id": "T5", "anchor": "t5-5-4"}, "GET", "/api/v1/papers/T5/sections/t5-5-4", None, 200),
    ("get_section", {"paper_id": "T4", "anchor": "paper-t4", "language": "en"},
     "GET", "/api/v1/papers/T4/sections/paper-t4", {"language": "en"}, 200),
    ("get_section", {"paper_id": "T4", "anchor": "t4-2-4", "language": "en"},
     "GET", "/api/v1/papers/T4/sections/t4-2-4", {"language": "en"}, 200),
    ("get_section", {"paper_id": "T1", "anchor": "t1-2-9"}, "GET", "/api/v1/papers/T1/sections/t1-2-9", None, 404),
    ("get_section", {"paper_id": "T9", "anchor": "x"}, "GET", "/api/v1/papers/T9/sections/x", None, 404),
    ("get_section", {"paper_id": "T1", "anchor": "t1-2", "language": "en"},
     "GET", "/api/v1/papers/T1/sections/t1-2", {"language": "en"}, 400),
    ("search_passages", {"query": "answerability", "k": 20}, "GET", "/api/v1/search",
     {"q": "answerability", "k": "20"}, 200),
    ("search_passages", {"query": "answerability"}, "GET", "/api/v1/search", {"q": "answerability"}, 200),
    ("search_passages", {"query": "answerability", "paper_id": "T3", "k": 3}, "GET", "/api/v1/search",
     {"q": "answerability", "paper_id": "T3", "k": "3"}, 200),
    ("search_passages", {"query": "アドヒアランス 自分ごと化 zzqxjvw", "k": 20}, "GET", "/api/v1/search",
     {"q": "アドヒアランス 自分ごと化 zzqxjvw", "k": "20"}, 200),
    ("search_passages", {"query": "zzqxjvw"}, "GET", "/api/v1/search", {"q": "zzqxjvw"}, 200),
    ("search_passages", {"query": "answerability", "k": 0}, "GET", "/api/v1/search",
     {"q": "answerability", "k": "0"}, 400),
    ("get_claim_record", {"claim_id": "T5-N3"}, "GET", "/api/v1/claims", {"claim_id": "T5-N3"}, 200),
    ("get_claim_record", {"query": "dignity"}, "GET", "/api/v1/claims", {"query": "dignity"}, 200),
    ("get_claim_record", {"claim_id": "T2-A1"}, "GET", "/api/v1/claims", {"claim_id": "T2-A1"}, 200),
    ("get_claim_record", {"claim_id": "T5-Z99"}, "GET", "/api/v1/claims", {"claim_id": "T5-Z99"}, 404),
    ("get_claim_record", {}, "GET", "/api/v1/claims", None, 400),
    ("get_reading_guide", {}, "GET", "/api/v1/guide", None, 200),
    ("get_reading_guide", {"part": "mode-1"}, "GET", "/api/v1/guide", {"part": "mode-1"}, 200),
    ("get_reading_guide", {"part": "nope"}, "GET", "/api/v1/guide", {"part": "nope"}, 400),
    ("get_reading_guide", {"part": ""}, "GET", "/api/v1/guide", {"part": ""}, 400),   # 空文字は既定にしない（F5）
    ("verify_quote", {"text": T5_QUOTE}, "GET", "/api/v1/verify", {"text": T5_QUOTE}, 200),
    ("verify_quote", {"text": T5_QUOTE}, "POST", "/api/v1/verify", {"text": T5_QUOTE}, 200),
    ("verify_quote", {"text": T5_QUOTE, "paper_id": "T5"}, "GET", "/api/v1/verify",
     {"text": T5_QUOTE, "paper_id": "T5"}, 200),
    ("verify_quote", {"text": T5_QUOTE, "paper_id": "T1"}, "POST", "/api/v1/verify",
     {"text": T5_QUOTE, "paper_id": "T1"}, 200),
    ("verify_quote", {"text": "従業員が遭遇から結晶化させた向きを、正式な検討の回路に入れ"}, "POST", "/api/v1/verify",
     {"text": "従業員が遭遇から結晶化させた向きを、正式な検討の回路に入れ"}, 200),
    ("verify_quote", {"text": "AI can deliver the fact of participation."}, "GET", "/api/v1/verify",
     {"text": "AI can deliver the fact of participation."}, 200),
    # T4 英訳の照合（HTTP-1.1.0 で verify に language。MCP と同じ検証：en は T4 のみ）
    ("verify_quote", {"text": T4_EN_QUOTE, "paper_id": "T4", "language": "en"}, "GET", "/api/v1/verify",
     {"text": T4_EN_QUOTE, "paper_id": "T4", "language": "en"}, 200),
    ("verify_quote", {"text": T4_EN_QUOTE, "language": "en"}, "POST", "/api/v1/verify",
     {"text": T4_EN_QUOTE, "language": "en"}, 200),
    ("verify_quote", {"text": T4_EN_QUOTE, "paper_id": "T4"}, "GET", "/api/v1/verify",
     {"text": T4_EN_QUOTE, "paper_id": "T4"}, 200),                               # 原文（日本語）には無い
    ("verify_quote", {"text": T5_QUOTE, "paper_id": "T5", "language": "en"}, "GET", "/api/v1/verify",
     {"text": T5_QUOTE, "paper_id": "T5", "language": "en"}, 400),                # T5 に英訳の版は無い
    ("verify_quote", {"text": T5_QUOTE, "language": "fr"}, "POST", "/api/v1/verify",
     {"text": T5_QUOTE, "language": "fr"}, 400),
    ("verify_quote", {"text": "the author's r"}, "GET", "/api/v1/verify", {"text": "the author's r"}, 200),
    ("verify_quote", {"text": "short"}, "GET", "/api/v1/verify", {"text": "short"}, 400),
    ("check_compressions", {"text": "AIは遊べない"}, "POST", "/api/v1/check", {"text": "AIは遊べない"}, 200),
    ("check_compressions", {"text": "The papers are about reading."}, "POST", "/api/v1/check",
     {"text": "The papers are about reading."}, 200),
    ("check_compressions", {"text": ""}, "POST", "/api/v1/check", {"text": ""}, 400),
)


def _http(api: Api, method: str, path: str, params) -> tuple[int, dict, bytes]:
    if method == "POST":
        return api.post(path, params or {})
    return api.get(path, **(params or {}))


def test_h01_http_json_is_the_mcp_json(api):
    """同じ入力で、HTTP の本文が MCP のツールの応答（text）とバイト単位で一致する（七ツール・八つのツール経路）。"""
    async def body(s):
        out = []
        for tool, args, *_ in H01_CASES:
            result = await s.call_tool(tool, args)
            assert not result.isError, (tool, args)
            out.append(result.content[0].text)
        return out

    mcp_texts = MC.session(api.srv.mcp_url, body, timeout=120)
    seen_routes, seen_tools = set(), set()
    for (tool, args, method, path, params, code), mcp_text in zip(H01_CASES, mcp_texts):
        status, headers, data = _http(api, method, path, params)
        assert status == code, (tool, args, status)
        assert headers["content-type"] == "application/json; charset=utf-8"
        assert data.decode("utf-8") == mcp_text, (tool, args)
        env = _env(data)
        assert status == H.http_status(env["status"])
        if (tool, args.get("language")) == ("verify_quote", "en") and code == 200:
            assert env["match"] == "exact" and env["results"][0]["source_kind"] == "translation"
            assert env["results"][0]["source_path"] == "translations/T4.en.md"
        name = H.match(path)[0]
        seen_routes.add((method, H.route(name, method).path))
        seen_tools.add(tool)
    assert seen_tools == set(app.TOOL_NAMES)
    assert seen_routes == set(NINE) - {("GET", "/api/v1/")}  # 一覧はツールでない（下の試験）


R01_HTTP = {
    "list_papers": lambda: ("GET", "/api/v1/papers", None),
    "get_section": lambda pid, anchor, language=None: (
        "GET", f"/api/v1/papers/{pid}/sections/{anchor}", {"language": language} if language else None),
    "search_passages": lambda q, pid=None, k=5: (
        "GET", "/api/v1/search", {"q": q, **({"paper_id": pid} if pid else {}), "k": str(k)}),
    "get_claim_record": lambda claim_id=None, query=None: (
        "GET", "/api/v1/claims", {k: v for k, v in (("claim_id", claim_id), ("query", query)) if v}),
    "verify_quote": lambda text: ("POST", "/api/v1/verify", {"text": text}),
    "check_compressions": lambda text: ("POST", "/api/v1/check", {"text": text}),
    "get_reading_guide": lambda part: ("GET", "/api/v1/guide", {"part": part}),
}


def test_h01_r01_over_http(api, reader):
    """R01 の HTTP 版：R01 の固定の呼び出しを HTTP で二度送り、どちらも別プロセス（この試験）で作った
    結果データとバイト単位で一致する。GET の verify も POST と同じ本文になる。"""
    expected = r01_calls.outputs(reader)
    for (name, args), want in zip(r01_calls.CALLS, expected):
        method, path, params = R01_HTTP[name](*args)
        first = _http(api, method, path, params)
        second = _http(api, method, path, params)
        assert first[2] == second[2], (name, args)
        assert first[2].decode("utf-8") == want, (name, args)
        if name == "verify_quote":
            assert api.get("/api/v1/verify", text=args[0])[2] == first[2]
        if method == "GET":
            assert first[1]["etag"] == second[1]["etag"] if first[0] == 200 else "etag" not in first[1]


def test_h01_index_lists_the_nine_routes(api):
    status, headers, data = api.get("/api/v1/")
    doc = json.loads(data)
    assert status == 200 and headers["content-type"] == "application/json; charset=utf-8"
    assert [(r["method"], r["path"]) for r in doc["routes"]] == list(NINE)
    assert doc["api_version"] == H.HTTP_VERSION and doc["corpus_version"] == C.CORPUS_VERSION
    assert doc["source_commit"] == C.CORPUS_COMMIT and doc["bundle_hash"] == C.EXPECTED_BUNDLE_SHA256
    assert data.decode("utf-8") == S.to_json(doc)  # JSON-1.0.0 の直列化
    status, headers, data = api.call("GET", "/api/v1/", headers=MD)
    text = data.decode("utf-8")
    assert status == 200 and headers["content-type"] == "text/markdown; charset=utf-8"
    assert text.startswith(f"Source: api_version={H.HTTP_VERSION} · corpus_version={C.CORPUS_VERSION}")
    assert all(f"| {m} | `{p}` |" in text for m, p in NINE)


# ---------------------------------------------------------------- H02（Markdown）


def _file_lines(path: str, start: int, end: int) -> str:
    raw = (C.DATA_DIR / path).read_bytes().decode("utf-8").split("\n")
    return "\n".join(raw[start - 1:end])


def test_h02_section_markdown_has_source_line_and_unchanged_lines(api):
    for pid, anchor in (("T5", "t5-5-4"), ("T4", "t4-2-4"), ("T1", "t1-2-1")):
        env = _env(api.get(f"/api/v1/papers/{pid}/sections/{anchor}")[2])
        r = env["results"][0]
        status, headers, data = api.call("GET", f"/api/v1/papers/{pid}/sections/{anchor}", headers=MD)
        text = data.decode("utf-8")
        assert status == 200 and headers["content-type"] == "text/markdown; charset=utf-8"
        first = text.split("\n", 1)[0]
        loc = r["locator"]
        assert first == H.source_line(r, env)
        for part in (f"paper_id={pid}", f"paper_version={r['paper_version']}", f"section_anchor={anchor}",
                     f"lines={loc['line_start']}-{loc['line_end']}", f"corpus_version={C.CORPUS_VERSION}",
                     f"source_commit={C.CORPUS_COMMIT}"):
            assert part in first, (pid, anchor, part)
        # 本文は原文の行のまま（記録範囲の行を改変せずに入れる）
        original = _file_lines(loc["path"], loc["line_start"], loc["line_end"]).rstrip("\n")
        assert r["payload"]["text"].rstrip("\n") == original
        assert text.split("\n", 2)[2].startswith(original + "\n"), (pid, anchor)


def test_h02_translation_markdown_keeps_every_segment(api):
    env = _env(api.get("/api/v1/papers/T4/sections/t4-2-4", language="en")[2])
    text = api.call("GET", "/api/v1/papers/T4/sections/t4-2-4?language=en", headers=MD)[2].decode("utf-8")
    assert len(env["results"]) >= 2
    for r in env["results"]:
        assert H.source_line(r, env) in text
        loc = r["locator"]
        assert r["payload"]["text"].rstrip("\n") in text
        assert _file_lines(loc["path"], loc["line_start"], loc["line_end"]).rstrip("\n") in text


def test_h02_tables_for_search_verify_check_claims(api):
    cases = (
        ("GET", "/api/v1/search?" + urllib.parse.urlencode({"q": "answerability", "k": "3"}), None),
        ("GET", "/api/v1/verify?" + urllib.parse.urlencode({"text": T5_QUOTE}), None),
        ("POST", "/api/v1/check", json.dumps({"text": "AIは遊べない"}).encode("utf-8")),
        ("GET", "/api/v1/claims?claim_id=T5-N3", None),
        ("GET", "/api/v1/papers", None),
    )
    for method, path, body in cases:
        env = _env(api.call(method, path, body)[2])
        status, headers, data = api.call(method, path, body, MD)
        text = data.decode("utf-8")
        assert status == 200 and headers["content-type"] == "text/markdown; charset=utf-8", path
        first = text.split("\n", 1)[0]
        assert first.startswith("Source: ") and f"corpus_version={C.CORPUS_VERSION}" in first
        assert f"source_commit={C.CORPUS_COMMIT}" in first and "status=ok" in first
        rows = [line for line in text.splitlines() if line.startswith("| ") and not line.startswith("| # ")]
        assert len(rows) == len(env["results"]) >= 1, path
        for i, (row, r) in enumerate(zip(rows, env["results"]), 1):
            cells = [c.strip() for c in row.split(" | ")]
            assert cells[0] == f"| {i}" and cells[1] == r["paper_id"] and cells[2] == r["paper_version"]
            assert cells[3] == (r["section_anchor"] or "-") and cells[5] == r["locator"]["path"]
        assert "\n\nstatus: ok\n" in text
        assert all(f"- {lim}\n" in text for lim in env["limitations"])
    # verify の行の本文は原文の文字列そのもの
    text = api.call("GET", cases[1][1], headers=MD)[2].decode("utf-8")
    assert f"match=exact — {T5_QUOTE} |" in text


def test_h02_non_ok_and_negotiation(api):
    status, headers, data = api.call("GET", "/api/v1/papers/T9/sections/x", headers=MD)
    text = data.decode("utf-8")
    assert status == 404 and "status=unknown_id" in text.split("\n", 1)[0] and "\ncandidates:\n" in text
    status, _h, data = api.call("GET", "/api/v1/search?q=answerability&k=0", headers=MD)
    assert status == 400 and "status: invalid_input" in data.decode("utf-8")
    # 交渉：text/markdown が q>0 で含まれれば Markdown、ほかは JSON
    for accept, markdown in (("text/markdown", True), ("application/json, text/markdown;q=0.5", True),
                             ("text/markdown;q=0", False), ("*/*", False), ("application/json", False),
                             ("TEXT/MARKDOWN; charset=utf-8", True), ("", False)):
        _s, headers, _d = api.call("GET", "/api/v1/papers", headers={"Accept": accept} if accept else {})
        want = "text/markdown; charset=utf-8" if markdown else "application/json; charset=utf-8"
        assert headers["content-type"] == want, accept


def test_h02_guide_markdown_has_text_and_templates(api):
    env = _env(api.get("/api/v1/guide", part="all")[2])
    text = api.call("GET", "/api/v1/guide?part=all", headers=MD)[2].decode("utf-8")
    r = env["results"][0]
    assert text.split("\n", 1)[0] == H.source_line(r, env)
    assert r["payload"]["text"].rstrip("\n") in text
    for item in env["templates"]["items"]:
        assert f"### {item['name']} ({item['language']})" in text and item["text"].rstrip("\n") in text


# ---------------------------------------------------------------- H03（400・404・405・上限・受付枠・受信期限）


def test_h03_invalid_input_is_400(api):
    long_q = "a" * 1001
    long_text = "a" * 2001
    cases = (
        ("GET", "/api/v1/search?" + urllib.parse.urlencode({"q": long_q}), None),
        ("GET", "/api/v1/search?q=answerability&k=21", None),
        ("GET", "/api/v1/search?q=answerability&k=abc", None),
        ("GET", "/api/v1/search?q=answerability&k=-1", None),
        ("GET", "/api/v1/search?q=answerability&k=999999999999", None),
        ("GET", "/api/v1/search", None),
        ("POST", "/api/v1/verify", json.dumps({"text": long_text}).encode()),
        ("POST", "/api/v1/check", json.dumps({"text": long_text}).encode()),
        ("GET", "/api/v1/verify", None),
        ("GET", "/api/v1/papers/T1/sections/t1-2?language=ja", None),
        ("POST", "/api/v1/check", b'{"text": "\\ud800 lone"}'),                   # 孤立サロゲート（ツールの検査）
        # HTTP の形（名前・重複・文字コード・本文）
        ("GET", "/api/v1/search?query=answerability", None),
        ("GET", "/api/v1/search?q=a&q=b", None),
        ("GET", "/api/v1/verify?text=" + "%FF" * 12, None),
        ("GET", "/api/v1/verify?text=%ED%A0%80abcdefghij", None),
        ("GET", "/api/v1/verify?lang=en&text=" + urllib.parse.quote(T5_QUOTE), None),
        ("GET", "/api/v1/papers?x=1", None),
        ("GET", "/api/v1/guide?" + "&".join(["part=all"] * 9), None),
        ("POST", "/api/v1/check?text=x", json.dumps({"text": "AIは遊べない"}).encode()),
        ("POST", "/api/v1/check", b"not json"),
        ("POST", "/api/v1/check", b""),
        ("POST", "/api/v1/check", b'["AI"]'),
        ("POST", "/api/v1/check", b'{"text": 5}'),
        ("POST", "/api/v1/check", b'{"text": "a", "text": "b"}'),
        ("POST", "/api/v1/check", b'{"text": "a", "paper_id": "T1"}'),
        ("POST", "/api/v1/verify", json.dumps({"text": T5_QUOTE, "lang": "en"}).encode()),
        ("POST", "/api/v1/check", b"\xff\xfe"),
    )
    for method, path, body in cases:
        status, headers, data = api.call(method, path, body)
        assert status == 400, (method, path, body, status)
        env = _env(data)
        assert env["status"] == "invalid_input" and env["results"] == [], (method, path)
        assert any(lim.startswith("INPUT: ") for lim in env["limitations"])
        assert headers["cache-control"] == "no-store" and "etag" not in headers


def test_h03_unknown_ids_and_routes_are_404(api):
    for path in ("/api/v1/papers/T9/sections/x", "/api/v1/papers/T1/sections/nope",
                 "/api/v1/papers/T1/sections/%C2%A73.1", "/api/v1/claims?claim_id=T5-Z99"):
        status, headers, data = api.call("GET", path)
        assert status == 404 and _env(data)["status"] == "unknown_id", path
        assert headers["content-type"] == "application/json; charset=utf-8"
    for path in ("/api/v1", "/api/v1/papers/", "/api/v1//papers", "/api/v1/nope", "/api/v2/papers", "/api/",
                 "/api/v1/papers/T1", "/api/v1/papers/T1/sections", "/api/v1/papers/T1/sections/",
                 "/api/v1/papers/T1/sections/t1-2/x", "/api/v1/search/", "/api/v1/verify/", "/api/v1/check/",
                 "/api/v1/papers/T1/sections/..", "/api/v1/papers/T1/sections/a%2Fb",
                 "/api/v1/papers/..%5C/sections/x", "/api/v1/papers/T1/sections/a:b", "/API/V1/papers"):
        for method in ("GET", "POST"):
            status, headers, data = api.call(method, path, b"{}" if method == "POST" else None)
            assert status == 404, (method, path, status)
            assert "location" not in headers and not data.startswith(b"{"), path


def test_h03_methods_are_405(api):
    for method, path in NINE:
        concrete = path.replace("{paper_id}", "T1").replace("{anchor}", "t1-2")
        allowed = sorted(m for m, p in NINE if p == path)
        for other in ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
            if other in allowed:
                continue
            body = b"{}" if other in ("POST", "PUT", "PATCH") else None
            status, headers, _data = api.call(other, concrete, body)
            assert status == 405, (other, concrete, status)
            assert headers["allow"] == ", ".join(m for m, p in NINE if p == path), (other, concrete)
            assert "location" not in headers
    # check は POST のみ（利用者の文章を URL に載せない）
    status, headers, _ = api.call("GET", "/api/v1/check?" + urllib.parse.urlencode({"text": "AIは遊べない"}))
    assert status == 405 and headers["allow"] == "POST"


def test_h03_body_limit(api):
    base = b'{"text": "'
    over = base + b"a" * (app.MAX_BODY_BYTES + 1 - len(base) - 2) + b'"}'
    assert len(over) == app.MAX_BODY_BYTES + 1
    for path in ("/api/v1/check", "/api/v1/verify"):
        assert api.call("POST", path, over)[0] == 413, path
    exact = over[:-3] + b'"}'
    assert len(exact) == app.MAX_BODY_BYTES
    status, _h, data = api.call("POST", "/api/v1/check", exact)
    assert status == 400 and _env(data)["status"] == "invalid_input"  # 本文は通り、ツールの上限（2000字）で断る


def test_h03_slow_body_is_cut(api):
    body = json.dumps({"text": "AIは遊べない"}).encode("utf-8")
    head = (f"POST /api/v1/check HTTP/1.1\r\nHost: {api.host}\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode()
    sock = socket.create_connection(("127.0.0.1", api.srv.port), timeout=app.BODY_READ_SECONDS + 20)
    started = time.monotonic()
    try:
        sock.sendall(head + body[:3])
        sock.settimeout(app.BODY_READ_SECONDS + 10)
        answer = sock.recv(200).decode("latin-1", "replace")
    finally:
        sock.close()
    elapsed = time.monotonic() - started
    assert " 408 " in answer.split("\r\n", 1)[0], answer[:80]
    assert app.BODY_READ_SECONDS - 1 <= elapsed < app.BODY_READ_SECONDS * 2, elapsed


@pytest.mark.parametrize("mode", ["local", "spaces"])
def test_h03_admission_and_busy_are_transport_errors(tmp_path, mode):
    """受付枠（「その他」）と実行枠の超過は 503 の素の文で返り、JSON の status に混ざらない。"""
    env = dict(MODE_ENV[mode], MEKIKI_TEST_ADMISSION="other=1:0", MEKIKI_TEST_CONCURRENCY="0")
    with Server(tmp_path / "audit.json", env_extra=env) as srv:
        a = Api(srv, mode)
        assert a.get("/api/v1/")[0] == 200                    # 一覧はツールを呼ばない
        status, headers, data = a.get("/api/v1/papers")        # 実行枠が0：通信層で 503
        assert status == 503 and data == b"busy" and headers["content-type"].startswith("text/plain")
        # 本文を送り切らない POST で「その他」の受付枠（1・順番待ち0）を埋める
        sock = socket.create_connection(("127.0.0.1", srv.port), timeout=10)
        sock.sendall((f"POST /api/v1/check HTTP/1.1\r\nHost: {a.host}\r\nContent-Type: application/json\r\n"
                      f"Content-Length: 100\r\n\r\n").encode() + b'{"text":')
        time.sleep(0.5)
        status, _h, data = a.get("/api/v1/")
        assert status == 503 and data == b"busy"
        sock.close()
        time.sleep(1.5)
        assert a.get("/api/v1/")[0] == 200                    # 切った要求の枠は返る
        audit = srv.stop()
    other = audit["admission"]["other"]
    assert other["rejected"] >= 1 and (other["active"], other["waiting"]) == (0, 0), other


def test_h03_percent_encoding_and_utf8_are_400_not_500(api):
    """百分率符号化（自前の復号）：崩れた `%`・UTF-8 でない列は 400（invalid_input）で、500 にならない。
    `+` は空白、`%2B` はリテラルの `+`。経路の中の崩れた符号化は HTTP の層（uvicorn）が復号し、404 か 400 になる。"""
    bad = ("%", "%G1", "%4", "abc%", "%%41", "%zz", "%E3%81", "%FF%FE", "%C0%AF", "%ED%A0%80", "%F4%90%80%80",
           "%E3%81%82%")
    for value in bad:
        for path in (f"/api/v1/verify?text={value}-quote-text-here", f"/api/v1/search?q=abc&paper_id={value}",
                     f"/api/v1/guide?part{value}=all"):
            status, headers, data = api.call("GET", path)
            assert status == 400, (path, status)
            env = _env(data)
            assert env["status"] == "invalid_input" and env["limitations"][0].startswith("INPUT: "), path
            assert "RULES: " + H.HTTP_VERSION in env["limitations"]
    # 生の（百分率符号化していない）非 ASCII のバイト列は、UTF-8 でも HTTP の層（h11）が先に 400 で断る（実測）
    for raw, want in (("text=AI can assist play.".encode().replace(b" ", b"+"), 200),
                      ("q=アドヒアランス".encode("utf-8"), 400), (b"q=\xff\xfe", 400), (b"q=\xe3\x81", 400)):
        path = b"/api/v1/search?" + raw if raw.startswith(b"q=") else b"/api/v1/verify?" + raw
        sock = socket.create_connection(("127.0.0.1", api.srv.port), timeout=10)
        try:
            sock.sendall(b"GET " + path + b" HTTP/1.1\r\nHost: " + api.host.encode() + b"\r\nConnection: close\r\n\r\n")
            head = sock.recv(64)
        finally:
            sock.close()
        assert head.startswith(b"HTTP/1.1 %d " % want), (raw, head)
    # `+` は空白（二つの断片）、`%2B` は `+` の文字、`%20` も空白
    plus = _env(api.call("GET", "/api/v1/search?q=answerability+dignity")[2])
    space = _env(api.call("GET", "/api/v1/search?q=answerability%20dignity")[2])
    assert plus == space and any("QUERY: 断片 answerability / dignity" == lim for lim in plus["limitations"])
    literal = _env(api.call("GET", "/api/v1/search?q=Spec.cost%2BExt.cost")[2])
    assert any(lim.startswith("QUERY: 断片 ") and "+" in lim for lim in literal["limitations"]), literal["limitations"]
    # 経路の中（uvicorn が復号する）：崩れた符号化も 500 にしない
    for path in ("/api/v1/papers/%FF/sections/x", "/api/v1/papers/T1/sections/%", "/api/v1/papers/T1/sections/%G1",
                 "/api/v1/papers/%E3%81/sections/x", "/api/v1/papers/T1/sections/%ED%A0%80"):
        status, _h, _d = api.call("GET", path)
        assert status in (400, 404), (path, status)


# ---------------------------------------------------------------- H04（cache・ETag・転送なし・Origin・Host）


def test_h04_cache_headers_and_etag(api):
    gets = ("/api/v1/", "/api/v1/papers", "/api/v1/papers/T5/sections/t5-5-4", "/api/v1/search?q=answerability",
            "/api/v1/claims?claim_id=T5-N3", "/api/v1/guide?part=mode-1",
            "/api/v1/verify?" + urllib.parse.urlencode({"text": T5_QUOTE}),
            "/api/v1/verify?text=zzzz%20qqqq%20xxxx", "/api/v1/search?q=zzqxjvw")
    tags = set()
    for path in gets:
        for headers in ({}, MD):
            status, h, data = api.call("GET", path, headers=headers)
            assert status == 200, path
            assert h["cache-control"] == "public, max-age=3600" and h["vary"] == "Accept", path
            tag = h["etag"]
            assert tag.startswith('"') and tag.endswith('"') and len(tag) == 34 and not tag.startswith("W/")
            assert api.call("GET", path, headers=headers)[1]["etag"] == tag  # 決定的
            tags.add(tag)
            # 条件付き GET：一致すれば 304（本文なし・同じ ETag）、弱い比較・* も一致、違えば 200
            for inm in (tag, "W/" + tag, '"x", ' + tag, "*"):
                s304, h304, d304 = api.call("GET", path, headers={**headers, "If-None-Match": inm})
                assert s304 == 304 and d304 == b"" and h304["etag"] == tag and "location" not in h304, (path, inm)
            assert api.call("GET", path, headers={**headers, "If-None-Match": '"other"'})[0] == 200
    assert len(tags) == 2 * len(gets)  # 経路・引数・表現ごとに違う
    # 同じ URL・Accept 違い：ETag が表現（JSON／Markdown）ごとに異なり、どちらも Vary: Accept（SPEC v2.5.1）
    for path in gets:
        by_accept = {}
        for accept in ("application/json", "text/markdown", "text/markdown;q=0.9, application/json;q=0.1", "*/*"):
            _s, h, _d = api.call("GET", path, headers={"Accept": accept})
            assert h["vary"] == "Accept", (path, accept)
            by_accept[accept] = (h["content-type"], h["etag"])
        assert by_accept["application/json"][1] != by_accept["text/markdown"][1], path
        assert by_accept["text/markdown;q=0.9, application/json;q=0.1"] == by_accept["text/markdown"], path
        assert by_accept["*/*"] == by_accept["application/json"], path
        # 別の表現の ETag では 304 にならない（キャッシュが表現を取り違えない）
        s, h, _d = api.call("GET", path, headers={"Accept": "text/markdown",
                                                  "If-None-Match": by_accept["application/json"][1]})
        assert s == 200 and h["content-type"].startswith("text/markdown"), path
    # 304 と 400・404 にも Vary: Accept
    tag = api.call("GET", "/api/v1/papers")[1]["etag"]
    assert api.call("GET", "/api/v1/papers", headers={"If-None-Match": tag})[1]["vary"] == "Accept"
    assert api.call("GET", "/api/v1/papers/T9/sections/x")[1]["vary"] == "Accept"
    # 既定を埋めた後の引数が同じなら同じ ETag・同じ本文（k の省略と k=5・空の paper_id と省略）
    a = api.call("GET", "/api/v1/search?q=answerability")
    b = api.call("GET", "/api/v1/search?q=answerability&k=5&paper_id=")
    assert a[1]["etag"] == b[1]["etag"] and a[2] == b[2]
    # POST・400・404 は保存させない（ETag なし）
    for method, path, body in (("POST", "/api/v1/check", '{"text":"AIは遊べない"}'.encode("utf-8")),
                               ("POST", "/api/v1/verify", json.dumps({"text": T5_QUOTE}).encode()),
                               ("GET", "/api/v1/search?q=answerability&k=0", None),
                               ("GET", "/api/v1/papers/T9/sections/x", None)):
        status, h, _ = api.call(method, path, body, {"If-None-Match": "*"})
        assert status in (200, 400, 404) and h["cache-control"] == "no-store" and "etag" not in h, path


def test_h04_no_redirects_and_no_cors(api):
    probes = ("/api/v1", "/api/v1/", "/api/v1//", "/api/v1/papers", "/api/v1/papers/", "/api/v1/papers/T1/sections/t1-2",
              "/api/v1/papers/T1/sections/t1-2/", "/api/v1/check", "/api/v1/verify", "/api/v1/verify/", "/api")
    origin = {"Origin": "http://evil.example"}
    for path in probes:
        for method in ("GET", "HEAD", "POST", "OPTIONS", "DELETE"):
            body = b"{}" if method == "POST" else None
            status, headers, _ = api.call(method, path, body, origin)
            assert not 300 <= status < 400 and "location" not in headers, (method, path, status)
            assert not any(k.startswith("access-control-") or k == "timing-allow-origin" for k in headers), \
                (method, path)
    # 事前確認（OPTIONS）も 405 で、許可ヘッダは返さない
    status, headers, _ = api.call("OPTIONS", "/api/v1/check", headers={
        **origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert status == 405 and not any(k.startswith("access-control-") for k in headers)
    status, headers, _ = api.call("GET", "/api/v1/papers", headers=origin)
    assert status == 200 and not any(k.startswith("access-control-") for k in headers)


def test_h04_host_is_checked_as_before(api):
    for host in ("evil.example", "127.0.0.1.evil.com", SPACE_HOST + ".evil.com"):
        assert api.call("GET", "/api/v1/papers", host=host)[0] == 400, host
    assert api.call("GET", "/api/v1/papers", host=f"localhost:{api.srv.port}")[0] == 200
    if api.mode == "spaces":
        assert api.call("GET", "/api/v1/papers", host=SPACE_HOST + ":443")[0] == 200
        assert api.call("GET", "/api/v1/papers", host="[::1]")[0] == 400  # spaces では ::1 を許可しない
    else:
        assert api.call("GET", "/api/v1/papers", host=SPACE_HOST)[0] == 400
        assert api.call("GET", "/api/v1/papers", host=f"[::1]:{api.srv.port}")[0] == 200


def test_h04_inputs_do_not_reach_the_logs(api):
    """HTTP の引数（問い合わせ・本文・経路の値）が標準出力・標準エラーに出ない。"""
    marker = "zqxmarkerHTTP" + str(int(time.time()))
    api.get("/api/v1/verify", text=marker + " quote text")
    api.get("/api/v1/search", q=marker)
    api.post("/api/v1/check", {"text": marker})
    api.post("/api/v1/check", {"text": marker, "unknown_" + marker: 1})
    api.call("GET", f"/api/v1/papers/{marker}/sections/{marker}")
    api.call("GET", f"/api/v1/{marker}")
    api.call("PUT", f"/api/v1/papers?x={marker}", b"{}")
    time.sleep(0.5)
    assert marker not in api.srv.log()



# ---------------------------------------------------------------- Codex⑤ の反映（HTTP-1.2.0）

EARLY_HEADERS = {"cache-control": "no-store", "vary": "Accept", "x-content-type-options": "nosniff"}


def _assert_common(headers: dict, where) -> None:
    for k, v in EARLY_HEADERS.items():
        assert headers.get(k) == v, (where, k, headers.get(k))
    assert "etag" not in headers, where


def test_h01_empty_part_and_k_are_not_defaults(api, reader):
    """F5：part・k は省略時だけ既定値。空文字は invalid_input（HTTP だけの既定値補完をしない）。
    MCP では k は整数型なので空文字はスキーマ検査の isError になる。HTTP の問い合わせは文字列なので、
    同じ入口（空の paper_id は省略）を経てツールの検査で invalid_input になる。"""
    omitted = api.get("/api/v1/search", q="answerability")
    empty = api.call("GET", "/api/v1/search?q=answerability&k=")
    assert omitted[0] == 200 and empty[0] == 400
    assert empty[2].decode("utf-8") == S.to_json(app.T.search_passages(reader, "answerability", None, ""))

    async def body(s):
        r = await s.call_tool("search_passages", {"query": "answerability", "k": ""})
        part_empty = await s.call_tool("get_reading_guide", {"part": ""})
        part_omitted = await s.call_tool("get_reading_guide", {})
        return r.isError, part_empty.content[0].text, part_omitted.content[0].text

    k_is_error, part_empty, part_omitted = MC.session(api.srv.mcp_url, body)
    assert k_is_error  # MCP：スキーマ（integer）で弾く
    assert api.call("GET", "/api/v1/guide?part=")[2].decode("utf-8") == part_empty
    assert api.call("GET", "/api/v1/guide")[2].decode("utf-8") == part_omitted
    assert _env(part_empty.encode())["status"] == "invalid_input" and _env(part_omitted.encode())["status"] == "ok"


def test_h03_json_key_errors_are_fixed_and_utf8(api):
    """F1：重複・不正な JSON キー（直下・入れ子・上位／下位サロゲート）は 400 で、応答は有効な UTF-8。
    エラー文に入力のキーを入れない。"""
    bodies = (b'{"\\ud800":1,"\\ud800":2}', b'{"text":{"\\ud800":1,"\\ud800":2}}',
              b'{"\\udc00":1,"\\udc00":2}', b'{"text":{"\\udc00":1,"\\udc00":2}}',
              b'{"\\ud800":1}', b'{"text":{"\\udfff":1}}', b'{"\\udbff\\udfff":1,"\\udbff\\udfff":2}',
              b'{"text":"AI can assist play.","text":"x"}', b'{"text":"a","zz\\ud800":1}')
    for path in ("/api/v1/verify", "/api/v1/check"):
        for accept in ({}, MD):
            for body in bodies:
                status, headers, data = api.call("POST", path, body, accept)
                assert status == 400, (path, body, status)
                text = data.decode("utf-8")  # 厳格に読めること（孤立サロゲートが出ない）
                assert "\\ud8" not in text.lower() and "\\udc" not in text.lower() and "zz" not in text
                if accept:
                    assert headers["content-type"].startswith("text/markdown") and "status: invalid_input" in text
                else:
                    env = _env(data)
                    assert env["status"] == "invalid_input", (path, body)
                    assert any(lim in ("INPUT: 本文の JSON に重複したキーがある", "INPUT: 本文の JSON の値は文字列か null")
                               or lim.startswith("INPUT: この経路の引数は ") for lim in env["limitations"]), env
    assert api.get("/api/v1/papers")[0] == 200  # 後続は通る


def test_h04_repeated_accept_and_if_none_match_are_joined(api):
    """F2：同名の Accept・If-None-Match は全行を順序どおり結合して解釈する（一行と複数行で同じ）。"""
    pairs = (
        ("text/markdown, application/json", [("Accept", "text/markdown"), ("Accept", "application/json")]),
        ("application/json, text/markdown", [("Accept", "application/json"), ("Accept", "text/markdown")]),
        ("text/markdown;q=0, application/json", [("Accept", "text/markdown;q=0"), ("Accept", "application/json")]),
        ("application/json, text/markdown;q=0", [("accept", "application/json"), ("ACCEPT", "text/markdown;q=0")]),
        ("text/markdown, */*", [("accept", "text/markdown"), ("Accept", "*/*")]),
    )
    for path in ("/api/v1/papers", "/api/v1/papers/T5/sections/t5-5-4"):
        for one, many in pairs:
            a = api.call("GET", path, headers={"Accept": one})
            b = api.call("GET", path, headers=many)
            assert a[0] == b[0] == 200, (path, one)
            assert a[1]["content-type"] == b[1]["content-type"] and a[2] == b[2], (path, one)
            assert a[1]["etag"] == b[1]["etag"] and b[1]["vary"] == "Accept", (path, one)
            assert ("markdown" in a[1]["content-type"]) == ("text/markdown;q=0" not in one), (path, one)
    tag = api.call("GET", "/api/v1/papers")[1]["etag"]
    for inm in ([("If-None-Match", tag), ("If-None-Match", '"other"')],
                [("If-None-Match", '"other"'), ("If-None-Match", tag)],
                [("If-None-Match", '"a", ' + tag), ("If-None-Match", '"b"')]):
        status, headers, data = api.call("GET", "/api/v1/papers", headers=inm)
        assert status == 304 and data == b"" and headers["etag"] == tag, inm
    assert api.call("GET", "/api/v1/papers", headers=[("If-None-Match", '"a"'), ("If-None-Match", '"b"')])[0] == 200
    md_tag = api.call("GET", "/api/v1/papers", headers=MD)[1]["etag"]  # 別の表現の ETag は結合しても一致しない
    assert api.call("GET", "/api/v1/papers", headers=[("If-None-Match", md_tag), ("Accept", "application/json")])[0] == 200


def test_h04_early_rejections_carry_common_headers(api):
    """F3：HTTP の名前空間の早期拒否（許可外 Host・未知経路・パス形の値・405・413・414）にも共通ヘッダ。"""
    cases = (
        ("GET", "/api/v1/papers", None, {}, "evil.example", 400),
        ("GET", "/api/v1/nope", None, {}, None, 404),
        ("POST", "/api/v1/nope", b"{}", {}, None, 404),
        ("GET", "/api/v1/papers/", None, {}, None, 404),
        ("GET", "/api", None, {}, None, 404),
        ("GET", "/api/v2/papers", None, {}, None, 404),
        ("GET", "/api/v1/papers/T1/sections/..", None, {}, None, 404),
        ("GET", "/api/v1/check", None, {}, None, 405),
        ("PUT", "/api/v1/papers", b"{}", {}, None, 405),
        ("POST", "/api/v1/check", b"x" * (app.MAX_BODY_BYTES + 1), {}, None, 413),
        ("GET", "/api/v1/papers?" + "&" * H.REQUEST_TARGET_MAX, None, {}, None, 414),
    )
    for method, path, body, headers, host, code in cases:
        status, h, _ = api.call(method, path, body, headers, host)
        assert status == code, (method, path[:40], status)
        _assert_common(h, (method, path[:40]))
    # 名前空間の外は従来どおり（Gradio 側の経路の拒否には付けない）
    status, h, _ = api.call("GET", "/gradio_api/nope")
    assert status == 404 and "vary" not in h


def _raw(api: Api, head: bytes, rest: bytes = b"", split: bool = False) -> bytes:
    req = head + rest
    sock = socket.create_connection(("127.0.0.1", api.srv.port), timeout=app.BODY_READ_SECONDS + 20)
    try:
        try:
            if split:
                for i in range(0, len(req), 1000):
                    sock.sendall(req[i:i + 1000])
                    time.sleep(0.003)
            else:
                sock.sendall(req)
        except OSError:
            pass  # 先に断られた
        sock.settimeout(app.BODY_READ_SECONDS + 10)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
        except OSError:
            pass
        return data
    finally:
        sock.close()


def _status_headers(data: bytes) -> tuple[int, dict]:
    head = data.split(b"\r\n\r\n", 1)[0].decode("latin-1")
    lines = head.split("\r\n")
    status = int(lines[0].split(" ")[1]) if lines and lines[0].startswith("HTTP/1.1 ") else 0
    return status, {k.strip().lower(): v.strip() for k, _, v in (ln.partition(":") for ln in lines[1:])}


def test_h03_request_target_limit_is_414(api):
    """要求行（経路＋問い合わせ）16 KiB（16,384 バイト）まで。16,385 で 414。一括でも分割でも同じ。
    それより長い分割送信は HTTP の層（h11）が先に 400 で断る（Guard に届かない。実測・2026-09-27）。"""
    base = b"/api/v1/papers?"

    def target(n: int) -> bytes:
        return base + b"&" * (n - len(base))

    assert H.target_length(b"/api/v1/papers", b"&" * (16384 - 15)) == 16384
    for split in (False, True):
        for n, want in ((16384, 200), (16385, 414)):
            head = b"GET " + target(n) + b" HTTP/1.1\r\nHost: " + api.host.encode() + b"\r\nConnection: close\r\n\r\n"
            status, headers = _status_headers(_raw(api, head, split=split))
            assert status == want, (n, split, status)
            if want == 414:
                _assert_common(headers, (n, split))
        head = b"GET " + target(65536) + b" HTTP/1.1\r\nHost: " + api.host.encode() + b"\r\nConnection: close\r\n\r\n"
        status, _ = _status_headers(_raw(api, head, split=split))
        assert status == (400 if split else 414), (split, status)  # 分割は h11 の 400
    # POST も本文より先に 414
    head = (b"POST " + base.rstrip(b"?").replace(b"papers", b"check") + b"?" + b"a" * 16400 + b" HTTP/1.1\r\nHost: "
            + api.host.encode() + b"\r\nContent-Length: 2\r\nConnection: close\r\n\r\n")
    assert _status_headers(_raw(api, head, b"{}"))[0] == 414


def test_h03_method_case_is_exact(api):
    """F4：メソッドは ASGI の文字列のまま照合する。get・Get・post・Post は九経路で 405 と正しい Allow。"""
    for method, path in NINE:
        concrete = path.replace("{paper_id}", "T1").replace("{anchor}", "t1-2")
        allow = ", ".join(m for m, p in NINE if p == path)
        for variant in ("get", "Get", "gET", "post", "Post", "pOST"):
            body = b"{}" if variant.upper() == "POST" else None
            status, headers, _ = api.call(variant, concrete, body)
            assert status == 405 and headers["allow"] == allow, (variant, concrete, status)
            _assert_common(headers, (variant, concrete))
    assert api.get("/api/v1/papers")[0] == 200 and api.post("/api/v1/check", {"text": "AIは遊べない"})[0] == 200


def test_h03_slow_body_and_busy_carry_common_headers(api):
    """F3：408（本文の受信期限）にも共通ヘッダ。"""
    head = (f"POST /api/v1/check HTTP/1.1\r\nHost: {api.host}\r\nContent-Type: application/json\r\n"
            f"Content-Length: 50\r\nConnection: close\r\n\r\n").encode()
    status, headers = _status_headers(_raw(api, head, b'{"text":'))
    assert status == 408
    _assert_common(headers, "408")


@pytest.mark.parametrize("mode", ["local", "spaces"])
def test_h03_busy_503_carries_common_headers(tmp_path, mode):
    env = dict(MODE_ENV[mode], MEKIKI_TEST_CONCURRENCY="0")
    with Server(tmp_path / "audit.json", env_extra=env) as srv:
        status, headers, data = Api(srv, mode).get("/api/v1/papers")
    assert status == 503 and data == b"busy"
    _assert_common(headers, "503")


# ---------------------------------------------------------------- CLAUDE.md 規則12：既知の入力の種類を九経路に当てる

KNOWN_KINDS = ("孤立サロゲート（問い合わせ・本文の値・本文のキー）", "重複（Host・Content-Length・Accept・引数・JSON キー）",
               "TE と CL の併記", "巨大入力（本文 64 KiB 超・要求行 16 KiB 超・値の上限超え）",
               "不正な符号化（崩れた %・UTF-8 でない列・生の非 ASCII）")


def test_h03_known_input_kinds_on_every_route(api):
    """DECISIONS に記録済みの入力の種類を九経路すべてに当て、どれも 5xx にならず、応答が UTF-8 で読めることを固定する。"""
    seen: dict[tuple[str, str], list[int]] = {}
    host = api.host.encode()
    for method, path in NINE:
        concrete = path.replace("{paper_id}", "T1").replace("{anchor}", "t1-2")
        name = H.match(concrete)[0]
        params = H.route(name, method).params
        first = params[0] if params else "x"
        codes = []

        def note(status, data=b""):
            assert status and status < 500, (method, concrete, status)
            data.decode("utf-8")
            codes.append(status)

        if method == "GET":
            for q in (f"{first}=%ED%A0%80abcdefghij", f"{first}=%G1", f"{first}=%FF%FE", f"{first}=a&{first}=b",
                      f"{first}=" + "a" * 3000):
                status, _h, data = api.call("GET", concrete + "?" + q)
                note(status, data)
        else:
            for body in (b'{"text":"\\ud800abcdefghijk"}', b'{"\\ud800":1,"\\ud800":2}', b'{"text":"a","text":"b"}',
                         json.dumps({"text": "a" * 3000}).encode(), b"\xff\xfe", b'{"text":"%G1"}'):
                status, _h, data = api.call("POST", concrete, body)
                note(status, data)
            status, _h, data = api.call("POST", concrete, b"x" * (app.MAX_BODY_BYTES + 1))
            assert status == 413
            note(status, data)
        for extra in (b"Host: " + host + b"\r\n", b"Content-Length: 0\r\nContent-Length: 5\r\n",
                      b"Transfer-Encoding: chunked\r\nContent-Length: 5\r\n"):
            head = (method.encode() + b" " + concrete.encode() + b" HTTP/1.1\r\nHost: " + host + b"\r\n" + extra
                    + b"Connection: close\r\n\r\n")
            status, _ = _status_headers(_raw(api, head))
            assert status == 400, (method, concrete, extra, status)
            codes.append(status)
        status, _ = _status_headers(_raw(api, method.encode() + b" " + concrete.encode() + b"?q=\xe3\x81\x82 HTTP/1.1\r\nHost: "
                                         + host + b"\r\nConnection: close\r\n\r\n"))
        note(status)
        status, _ = _status_headers(_raw(api, method.encode() + b" " + concrete.encode() + b"?" + b"&" * 16500
                                         + b" HTTP/1.1\r\nHost: " + host + b"\r\nConnection: close\r\n\r\n"))
        assert status == 414, (method, concrete, status)
        codes.append(status)
        seen[(method, path)] = codes
    assert set(seen) == set(NINE)
    print("規則12の当て込み：", {f"{m} {p}": sorted(set(c)) for (m, p), c in seen.items()})


# ---------------------------------------------------------------- 要求行の上限を全経路に（SPEC v2.5.3）

TARGET_FAR_BELOW = 1024  # 内部クライアント・MCP の要求行はこの長さに収まる（上限 16 KiB に遠く及ばない）


@pytest.mark.parametrize("mode", ["local", "spaces"])
def test_h03_request_target_limit_on_every_route(tmp_path, mode):
    """414 は Guard が受ける全経路に掛かる。それでも MCP（initialize と七ツール）・resources／prompts の自己呼び出し・
    heartbeat・`/` は従来どおり通り、受けた要求行の最長（経路の種類ごと）は 1 KiB 未満に収まる。"""
    with Server(tmp_path / "audit.json", env_extra=MODE_ENV[mode]) as srv:
        a = Api(srv, mode)

        async def body(s):
            tools = [t.name for t in (await s.list_tools()).tools]
            calls = [(await s.call_tool(tool, args)) for tool, args, *_ in H01_CASES[:1]]
            for tool, args in (("get_section", {"paper_id": "T5", "anchor": "t5-5-4"}),
                               ("search_passages", {"query": "answerability"}),
                               ("get_claim_record", {"claim_id": "T5-N3"}),
                               ("verify_quote", {"text": T5_QUOTE}),
                               ("check_compressions", {"text": "AIは遊べない"}),
                               ("get_reading_guide", {"part": "mode-1"})):
                calls.append(await s.call_tool(tool, args))
            resources = (await s.list_resources()).resources
            read = [await s.read_resource(r.uri) for r in resources]
            prompts = (await s.list_prompts()).prompts
            got = [await s.get_prompt(p.name) for p in prompts]
            return tools, calls, read, got

        tools, calls, read, got = MC.session(srv.mcp_url, body, timeout=120)
        assert tools == list(app.TOOL_NAMES) and len(calls) == 7
        assert all(not c.isError and _env(c.content[0].text.encode())["status"] == "ok" for c in calls)
        assert len(read) == len(app.RESOURCES) and all(r.contents[0].text for r in read)
        assert len(got) == len(app.PR.TEMPLATES) and all(g.messages[0].content.text for g in got)
        # `/` と自己呼び出しの読み先（loopback 宛て）は従来どおり
        for method in ("GET", "HEAD"):
            assert a.call(method, "/", host=f"127.0.0.1:{srv.port}")[0] == 200
        assert a.call("GET", "/gradio_api/info", host=f"127.0.0.1:{srv.port}")[0] == 200
        # 境界：16,384 バイトは通り、16,385 バイトは 414（API 以外の経路でも）
        info = "/gradio_api/info?"
        assert a.call("GET", info + "&" * (16384 - len(info)), host=f"127.0.0.1:{srv.port}")[0] == 200
        for method, path in (("GET", "/"), ("HEAD", "/"), ("GET", "/gradio_api/info"), ("GET", "/gradio_api/mcp/"),
                             ("POST", "/gradio_api/mcp/"), ("POST", "/gradio_api/queue/join"),
                             ("GET", "/gradio_api/queue/data"), ("GET", "/gradio_api/heartbeat/abc"),
                             ("GET", "/gradio_api/nope"), ("GET", "/config")):
            long_path = path + "?" + "&" * (16385 - len(path) - 1)
            status, headers, _ = a.call(method, long_path, b"{}" if method == "POST" else None,
                                        host=f"127.0.0.1:{srv.port}")
            assert status == 414 and "location" not in headers, (method, path, status)
        audit = srv.stop()
    seen = audit["target_seen"]
    for key in ("/", "/gradio_api/info", "/gradio_api/queue/join", "/gradio_api/queue/data",
                "/gradio_api/heartbeat/*", "/gradio_api/mcp/"):
        assert key in seen, (key, seen)  # 内部クライアントと MCP の経路を実際に通った
    over = {k: v for k, v in seen.items() if v >= TARGET_FAR_BELOW and not (k == "/gradio_api/info" and v == 16384)}
    assert not over, over
    assert audit["guard_counts"].get("414", audit["guard_counts"].get(414, 0)) >= 10
    print(f"要求行の最長（{mode}）：", seen)
