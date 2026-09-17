"""施工段階3の完了条件 M01〜M03（SPEC §7・docs/PLAN.md A-4）。mcp 1.30.0 の SDK で接続する。"""

from __future__ import annotations

import hashlib
import json

import pytest

from mekiki_reader import corpus as C
from mekiki_reader import prompts as PR
from mekiki_reader import schema as S
from tests._support import mcp_client as MC

pytestmark = pytest.mark.server

_CORPUS = C.load_corpus()

TOOL_NAMES = ("list_papers", "get_section", "search_passages", "get_claim_record",
              "verify_quote", "check_compressions", "get_reading_guide")
REQUIRED = {
    "list_papers": [],
    "get_section": ["paper_id", "anchor"],
    "search_passages": ["query"],
    "get_claim_record": [],
    "verify_quote": ["text"],
    "check_compressions": ["text"],
    "get_reading_guide": [],
}
TYPES = {
    "get_section": {"paper_id": "string", "anchor": "string", "language": "string"},
    "search_passages": {"query": "string", "paper_id": "string", "k": "integer"},
    "get_claim_record": {"claim_id": "string", "query": "string"},
    "verify_quote": {"text": "string", "paper_id": "string", "language": "string"},
    "check_compressions": {"text": "string"},
    "get_reading_guide": {"part": "string"},
}
CALLS = (
    ("list_papers", {}, "ok"),
    ("get_section", {"paper_id": "T4", "anchor": "t4-2-4"}, "ok"),
    ("get_section", {"paper_id": "T4", "anchor": "paper-t4", "language": "en"}, "ok"),
    ("search_passages", {"query": "answerability", "k": 3}, "ok"),
    ("get_claim_record", {"claim_id": "T5-N3"}, "ok"),
    ("verify_quote", {"text": "AI can assist play. It cannot take one's place in it."}, "ok"),
    ("check_compressions", {"text": "AIは遊べない"}, "ok"),
    ("get_reading_guide", {"part": "modes"}, "ok"),
)
RESOURCE_PATHS = ("llms.txt", "FOR_AI_READERS.md", "THEORY_MAP.md", "SOURCE_INDEX.md",
                  "papers/T1.md", "papers/T2.md", "papers/T3.md", "papers/T4.md", "papers/T5.md",
                  "translations/T4.en.md", "AI_READING_TESTS.md", "claims/t5.json")
LEAKS = ("/Users/", "Traceback", "site-packages", "mekiki_reader/", ".venv", "data/")


def _bundle_hash(path: str) -> str:
    return next(f.sha256 for f in _CORPUS.bundle.files if f.path == path)


# ---------------------------------------------------------------- M01


def test_m01_tools_list_and_call(server):
    async def body(s):
        tools = (await s.list_tools()).tools
        results = [await s.call_tool(name, args) for name, args, _ in CALLS]
        return tools, results

    tools, results = MC.session(server.mcp_url, body)
    # Spaces ではツール名に接頭辞が付く（Q69）。ローカルでは付かないことを確かめる。
    assert len(tools) == 7 and [t.name for t in tools] == list(TOOL_NAMES)
    by_name = {t.name: t for t in tools}
    for name in TOOL_NAMES:
        schema = by_name[name].inputSchema
        assert schema["type"] == "object"
        assert schema.get("required", []) == REQUIRED[name]
        for arg, kind in TYPES.get(name, {}).items():
            assert schema["properties"][arg]["type"] == kind, (name, arg)
        assert by_name[name].description
    assert by_name["search_passages"].inputSchema["properties"]["k"]["default"] == 5
    assert by_name["get_reading_guide"].inputSchema["properties"]["part"]["default"] == "all"
    for (name, _args, want), result in zip(CALLS, results):
        assert result.isError is False, (name, MC.error_text(result))
        env = MC.payload(result)
        S.validate_envelope(env)
        assert env["status"] == want, (name, env["status"])


def test_m01_same_bytes_as_local_call(server, reader):
    """通信を通した結果が、同じ入力に対する関数の戻り値とバイト単位で同じ（R01 の延長）。"""
    from mekiki_reader import tools as T

    async def body(s):
        return [MC.payload(await s.call_tool(name, args)) for name, args, _ in CALLS]

    over_mcp = MC.session(server.mcp_url, body)
    for (name, args, _want), env in zip(CALLS, over_mcp):
        local = S.to_json(getattr(T, name)(reader, *_positional(name, args)))
        assert S.to_json(env) == local, name


def _positional(name: str, args: dict) -> list:
    order = {"list_papers": [], "get_section": ["paper_id", "anchor", "language"],
             "search_passages": ["query", "paper_id", "k"], "get_claim_record": ["claim_id", "query"],
             "verify_quote": ["text", "paper_id", "language"], "check_compressions": ["text"],
             "get_reading_guide": ["part"]}[name]
    defaults = {"k": 5, "part": "all"}
    return [args.get(key, defaults.get(key)) for key in order]


# ---------------------------------------------------------------- M02


def test_m02_resources(server):
    async def body(s):
        listed = (await s.list_resources()).resources
        templates = (await s.list_resource_templates()).resourceTemplates
        contents = {}
        for path in RESOURCE_PATHS:
            got = await s.read_resource(f"mekiki://v{C.CORPUS_VERSION}/{path}")
            contents[path] = got.contents[0]
        return listed, templates, contents

    listed, templates, contents = MC.session(server.mcp_url, body)
    assert len(listed) == 12 and templates == []
    assert {str(r.uri) for r in listed} == {f"mekiki://v{C.CORPUS_VERSION}/{p}" for p in RESOURCE_PATHS}
    for resource in listed:
        assert resource.mimeType in ("text/markdown", "text/plain") and resource.description
    for path, content in contents.items():
        assert hashlib.sha256(content.text.encode("utf-8")).hexdigest() == _bundle_hash(path), path


def test_m02_unknown_resource_uri(server):
    async def body(s):
        out = []
        for uri in (f"mekiki://v{C.CORPUS_VERSION}/../app.py", "mekiki://v3.5.0/papers/T9.md",
                    "file:///etc/passwd", "https://example.com/x"):
            try:
                await s.read_resource(uri)
                out.append((uri, "returned"))
            except Exception as exc:  # noqa: BLE001（挙動の記録が目的）
                out.append((uri, type(exc).__name__))
        return out

    for uri, outcome in MC.session(server.mcp_url, body):
        assert outcome != "returned", uri


def test_m02_prompts(server):
    async def body(s):
        listed = (await s.list_prompts()).prompts
        got = {t.name: await s.get_prompt(t.name) for t in PR.TEMPLATES}
        try:
            unknown = ("returned", (await s.get_prompt("no_such_prompt")).messages[0].content.text)
        except Exception as exc:  # noqa: BLE001（Q64 の挙動の記録）
            unknown = ("raised", f"{type(exc).__name__}: {exc}")
        return listed, got, unknown

    listed, got, unknown = MC.session(server.mcp_url, body)
    assert [p.name for p in listed] == [t.name for t in PR.TEMPLATES] and len(listed) == 3
    for template in PR.TEMPLATES:
        assert got[template.name].messages[0].content.text == template.text
        assert PR.GUARD_SENTENCE in got[template.name].messages[0].content.text
    # Q64：名前が一致しないとき、上流は endpoint 一覧の最後を実行する。番兵が例外にする。
    assert unknown[0] == "raised", unknown
    assert not any(t.text in unknown[1] for t in PR.TEMPLATES)


# ---------------------------------------------------------------- M03


def test_m03_schema_layer_violation(server):
    async def body(s):
        bad_type = await s.call_tool("search_passages", {"query": "dignity", "k": "abc"})
        bad_arg = await s.call_tool("search_passages", {"query": "dignity", "no_such_arg": 1})
        after = await s.call_tool("list_papers", {})
        return bad_type, bad_arg, after

    bad_type, bad_arg, after = MC.session(server.mcp_url, body)
    for result in (bad_type, bad_arg):
        assert result.isError is True
        text = MC.error_text(result)
        assert not any(mark in text for mark in LEAKS), text
    assert after.isError is False and MC.payload(after)["status"] == "ok"


def test_m03_app_layer_violation(server):
    async def body(s):
        return {
            "k0": await s.call_tool("search_passages", {"query": "dignity", "k": 0}),
            "anchor": await s.call_tool("get_section", {"paper_id": "T4", "anchor": "t4-9"}),
            "zero": await s.call_tool("search_passages", {"query": "zzqxjvw"}),
            "path": await s.call_tool("get_section", {"paper_id": "../../.env", "anchor": "t4-1"}),
            "after": await s.call_tool("list_papers", {}),
        }

    out = MC.session(server.mcp_url, body)
    want = {"k0": "invalid_input", "anchor": "unknown_id", "zero": "no_lexical_match",
            "path": "invalid_input", "after": "ok"}
    for key, status in want.items():
        assert out[key].isError is False, key
        env = MC.payload(out[key])
        S.validate_envelope(env)
        assert env["status"] == status, (key, env["status"])
        assert "../../.env" not in json.dumps(env, ensure_ascii=False)
