"""施工段階2の完了条件 T01〜T12・R01（SPEC §7）。実データは読むだけ。"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest

from mekiki_reader import corpus as C
from mekiki_reader import normalize as N
from mekiki_reader import patterns as PAT
from mekiki_reader import prompts as PR
from mekiki_reader import schema as S
from mekiki_reader import terms as TM
from mekiki_reader import tools as T
from tests.fixtures.patterns_fixture import FORM_CASES, TEST_PATTERNS
from tests.fixtures.terms_fixture import TEST_TERMS
from tests._support import r01_calls

FIX = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parent.parent
_CORPUS = C.load_corpus()
ALL_SECTIONS = [(pid, s.id) for pid in C.PAPER_IDS for s in _CORPUS.papers[pid].sections]
FROZEN = (
    ("AI can deliver the state of affairs; it cannot deliver the fact of participation.", 13, "t5-abstract"),
    ("AI can assist play. It cannot take one's place in it.", 223, "t5-5-4"),
)


@pytest.fixture(scope="module")
def reader() -> T.Reader:
    return T.Reader(_CORPUS)


def rt(env: dict) -> dict:
    """JSON に直列化して戻し、外枠の形を確かめる。"""
    obj = json.loads(S.to_json(env))
    S.validate_envelope(obj)
    return obj


def lims(env: dict, code: str) -> list[str]:
    return [x for x in env["limitations"] if x.startswith(code + ": ")]


# ---------------------------------------------------------------- 起動の前提


def test_empty_patterns_and_terms_start(reader):
    assert PAT.PATTERNS == () and PAT.PATTERNS_VERSION == "PATTERNS-0.0.0"
    assert TM.TERMS == () and TM.TERMS_VERSION == "TERMS-0.0.0"
    assert reader.patterns == () and len(reader.terms.entries) == 0
    assert N.table_sha256() == N.NORM_TABLE_SHA256
    assert [f.anchor for f in reader.frames] == ["translation-guide", "edition-integrity"]


def test_prompts_are_drafts_with_guard(reader):
    assert PR.PROMPTS_STATUS == "draft" and PR.APPROVED_ON is None
    assert [t.name for t in PR.TEMPLATES] == ["read_with_guards", "four_modes", "answer_format"]
    for t in PR.TEMPLATES:
        assert PR.GUARD_SENTENCE in t.text
    headings = {line[4:] for line in _CORPUS.lines["FOR_AI_READERS.md"] if line.startswith("### Mode")}
    for line in PR.FOUR_MODES.text.split("\n"):
        if line.startswith("- Mode"):
            assert line[2:] in headings


def test_reading_guide(reader):
    env = rt(T.get_reading_guide(reader, "modes"))
    assert env["status"] == "ok"
    r = env["results"][0]
    assert r["source_kind"] == "reading_guide" and r["canonical_doi"] is None and r["paper_id"] is None
    assert (r["locator"]["line_start"], r["locator"]["line_end"]) == (42, 61)
    assert r["payload"]["text"].startswith("## Four practical response modes")
    assert env["templates"]["status"] == "draft" and len(env["templates"]["items"]) == 3
    assert rt(T.get_reading_guide(reader, "all"))["results"][0]["locator"]["line_end"] == 73
    ranges = {p: reader.guide_ranges[p][:2] for p, _ in T.GUIDE_PARTS}
    assert ranges["interpretation"] == (5, 41) and ranges["core-terms"] == (7, 29)
    assert ranges["boundaries"] == (62, 73) and ranges["mode-4"] == (58, 61)
    for bad in ("unknown", "", None, 3, "../FOR_AI_READERS.md"):
        assert rt(T.get_reading_guide(reader, bad))["status"] == "invalid_input"


# ---------------------------------------------------------------- T01


def test_t01_list_papers(reader):
    env = rt(T.list_papers(reader))
    assert env["status"] == "ok" and env["candidates"] == []
    rs = env["results"]
    assert [r["paper_id"] for r in rs] == list(C.PAPER_IDS)
    assert [r["paper_version"] for r in rs] == ["1", "2", "2", "1", "3"]
    manifest = {p["paper"]: p for p in _CORPUS.source_manifest["papers"]}
    for r in rs:
        pid = r["paper_id"]
        p = r["payload"]
        assert r["canonical_doi"] == manifest[pid]["canonical_doi"] == p["canonical_doi"]
        assert r["source_kind"] == "paper_md" and r["derivative_of"] is None
        assert r["snapshot_url"] == C.RAW_BASE + f"papers/{pid}.md"
        assert p["language"] == C.PAPER_LANGUAGE[pid]
        assert p["available_editions"] == (["original", "en"] if pid == "T4" else ["original"])
        assert len(p["sections"]) == len(manifest[pid]["sections"])
        for s, m in zip(p["sections"], manifest[pid]["sections"]):
            assert (s["id"], s["title"], s["level"], s["line_start"], s["line_end"]) == (
                m["id"], m["title"], m["level"], m["line_start"], m["line_end"])
        assert p["record"]["path"] == "source_manifest.json"
    assert rs[2]["canonical_doi"].startswith("https://doi.org/10.35542/")
    assert [len(r["payload"]["sections"]) for r in rs] == [40, 39, 25, 25, 29]


# ---------------------------------------------------------------- T02


@pytest.mark.parametrize("pid,sid", ALL_SECTIONS)
def test_t02_get_section_exact(reader, pid, sid):
    paper = _CORPUS.papers[pid]
    sec = paper.section(sid)
    env = rt(T.get_section(reader, pid, sid))
    assert env["status"] == "ok" and len(env["results"]) == 1
    r = env["results"][0]
    assert r["payload"]["text"] == "\n".join(paper.lines[sec.line_start - 1:sec.line_end])
    assert (r["locator"]["line_start"], r["locator"]["line_end"]) == (sec.line_start, sec.line_end)
    assert r["section_anchor"] == sid and r["payload"]["is_excerpt"] is False
    children = [s.id for s in paper.sections if s.parent_id == sid]
    assert r["payload"]["child_ids"] == children
    assert r["payload"]["heading_only"] == sec.heading_only
    assert r["source_url"] == f"https://mekiki-framework.github.io/papers/{pid}.html#{sid}"
    if pid == "T4":
        assert rt(T.get_section(reader, pid, sid, "ja"))["results"] == env["results"]


def test_t02_parent_contract(reader):
    env = rt(T.get_section(reader, "T4", "paper-t4"))
    r = env["results"][0]
    assert r["payload"]["child_ids"] == ["t4-1", "t4-2", "t4-3", "t4-4", "t4-5", "t4-6", "t4-notes", "t4-references"]
    assert r["payload"]["heading_only"] is False and lims(env, "PARENT")
    env = rt(T.get_section(reader, "T1", "t1-2"))
    r = env["results"][0]
    assert (r["locator"]["line_start"], r["locator"]["line_end"], r["payload"]["heading_only"]) == (46, 47, True)
    assert r["payload"]["child_ids"][0] == "t1-2-1"
    leaf = rt(T.get_section(reader, "T1", "t1-2-1"))
    assert leaf["results"][0]["payload"]["child_ids"] == [] and not lims(leaf, "PARENT")


# ---------------------------------------------------------------- T03


@pytest.mark.parametrize("pid,anchor,status,ncand", [
    ("T1", "t1-nonexistent", "unknown_id", 5),
    ("T1", "4.2節", "unknown_id", 5),
    ("T1", "t1-2-9", "unknown_id", 5),
    ("T6", "x", "unknown_id", 5),
    ("t1", "t1-abstract", "unknown_id", 5),
    ("T1", "../x", "invalid_input", 0),
    ("T1", "papers/T1.md", "invalid_input", 0),
    ("T1", "https://example.com/x", "invalid_input", 0),
    ("T1", "file:///etc/hosts", "invalid_input", 0),
    ("../../.env", "x", "invalid_input", 0),
    ("/etc/passwd", "x", "invalid_input", 0),
    ("T1", "a" + chr(0) + "b", "invalid_input", 0),
    ("T1", "", "invalid_input", 0),
    ("T1", "x" * 129, "invalid_input", 0),
    (None, "t1-abstract", "invalid_input", 0),
    ("T1", 3, "invalid_input", 0),
])
def test_t03_unknown_and_invalid(reader, pid, anchor, status, ncand):
    env = rt(T.get_section(reader, pid, anchor))
    assert env["status"] == status
    assert env["results"] == [] and len(env["candidates"]) == ncand
    for c in env["candidates"]:
        paper = _CORPUS.papers[c["paper_id"]]
        assert paper.section(c["section_anchor"]) is not None
        assert "text" not in c["payload"]
    text = S.to_json(env)
    for leak in (".env", "/etc/", "example.com", "file://"):
        assert leak not in text


def test_t03_near_ranking(reader):
    env = rt(T.get_section(reader, "T1", "t1-2-9"))
    got = [c["section_anchor"] for c in env["candidates"]]
    assert got[0].startswith("t1-2-") and len(set(got)) == 5
    assert rt(T.get_section(reader, "T1", "t1-2-9")) == env


def test_t03_unknown_claim(reader):
    env = rt(T.get_claim_record(reader, "T5-Z9"))
    assert env["status"] == "unknown_id" and env["results"] == []
    assert [c["payload"]["id"] for c in env["candidates"]] == [c["id"] for c in _CORPUS.ledger["claims"]]
    for bad in ("T5A1", "../T5-A1", "t5-a1", "T6-A1", "T5-A1 ", 5):
        assert rt(T.get_claim_record(reader, bad))["status"] == "invalid_input"


def test_t03_en_unknown_anchor(reader):
    env = rt(T.get_section(reader, "T4", "t4-9", "en"))
    assert env["status"] == "unknown_id" and env["results"] == []
    known = {s.id for s in _CORPUS.papers["T4"].sections} | {"translation-guide", "edition-integrity"}
    assert {c["section_anchor"] for c in env["candidates"]} <= known


# ---------------------------------------------------------------- T04


def _keyed(rs):
    return [(-r["payload"]["rank_key"]["distinct_terms"], -r["payload"]["rank_key"]["occurrences"],
             -r["payload"]["rank_key"]["direct_terms"], r["payload"]["rank_key"]["paper_order"],
             r["payload"]["rank_key"]["line"]) for r in rs]


def test_t04_hit_and_order(reader):
    env = rt(T.search_passages(reader, "answerability", k=20))
    assert env["status"] == "ok" and len(env["results"]) == 20
    keys = _keyed(env["results"])
    assert keys == sorted(keys) and len(set(keys)) == len(keys)
    assert [r["payload"]["rank"] for r in env["results"]] == list(range(1, 21))
    for r in env["results"]:
        assert r["payload"]["match_via"] == ["query"] and r["payload"]["is_excerpt"] is True
        line = _CORPUS.lines[r["source_path"]][r["locator"]["line_start"] - 1]
        c0, c1 = r["locator"]["char_start"], r["locator"]["char_end"]
        assert line[c0:c1].lower() == "answerability"
        route = r["payload"]["route"]
        assert _CORPUS.papers[route["paper_id"]].section(route["anchor"]) is not None
    assert lims(env, "SCORE") and lims(env, "TOTAL")
    assert rt(T.search_passages(reader, "answerability", k=20)) == env


def test_t04_zero(reader):
    word = "zzqxjvw"
    assert all(word not in ln.fold.text for ln in reader.orig_lines)
    env = rt(T.search_passages(reader, word))
    assert env["status"] == "no_lexical_match" and env["results"] == [] and env["candidates"] == []
    assert lims(env, "ZERO") and lims(env, "LANG")


def test_t04_ties_are_stable(reader):
    env = rt(T.search_passages(reader, "アドヒアランス", k=20))
    keys = _keyed(env["results"])
    assert keys == sorted(keys)
    ties = [k for k in keys if k[:3] == keys[-1][:3]]
    assert len(ties) >= 2  # 同点群の中は論文順・行番号の昇順で決まる
    env2 = rt(T.search_passages(reader, "アドヒアランス", k=5))
    assert env2["results"] == [dict(r, payload=r["payload"]) for r in env["results"][:5]]


def test_t04_partial_goes_to_candidates(reader):
    env = rt(T.search_passages(reader, "アドヒアランス zzqxjvw"))
    assert env["status"] == "no_lexical_match" and env["results"] == []
    assert env["candidates"] and all(c["payload"]["partial"] for c in env["candidates"])
    both = rt(T.search_passages(reader, "アドヒアランス 自分ごと化"))
    assert both["status"] == "ok"
    for r in both["results"]:
        assert r["payload"]["matched_terms"] == ["アドヒアランス", "自分ごと化"]


def test_t04_word_boundary(reader):
    env = rt(T.search_passages(reader, "play", k=20))
    assert env["status"] == "ok"
    for r in env["results"]:
        line = _CORPUS.lines[r["source_path"]][r["locator"]["line_start"] - 1].lower()
        assert re.search(r"(?<![a-z0-9'-])play(?![a-z0-9'-])", line)
    hyph = rt(T.search_passages(reader, "transferability", k=20))
    for r in hyph["results"]:
        line = _CORPUS.lines[r["source_path"]][r["locator"]["line_start"] - 1].lower()
        assert re.search(r"(?<![a-z0-9'-])transferability", line)


def test_t04_input_limits(reader):
    for bad_k in (0, 21, -1, True, "5", 5.0, None, 10 ** 9):
        assert rt(T.search_passages(reader, "answerability", k=bad_k))["status"] == "invalid_input"
    assert rt(T.search_passages(reader, "answerability", k=20))["status"] == "ok"
    for bad in ("", "   ", "の", "の と は", "!!!", "x" * 201, " ".join(f"w{i}" for i in range(9)), None, 3, "x" * 1001):
        assert rt(T.search_passages(reader, bad))["status"] == "invalid_input", bad
    assert rt(T.search_passages(reader, " ".join(["answerability"] * 10)))["status"] == "ok"  # 重複は1断片
    assert rt(T.search_passages(reader, "answerability", paper_id="T9"))["status"] == "unknown_id"
    assert rt(T.search_passages(reader, "answerability", paper_id="../T1"))["status"] == "invalid_input"
    scoped = rt(T.search_passages(reader, "answerability", paper_id="T3", k=20))
    assert {r["paper_id"] for r in scoped["results"]} == {"T3"}


def test_t04_term_map_via_fixture(reader):
    tr = T.Reader(_CORPUS, terms=TEST_TERMS)
    env = rt(T.search_passages(tr, "尊厳", k=20))
    assert env["status"] == "ok"
    assert all(r["payload"]["match_via"] == ["term_map:M90"] for r in env["results"])
    assert {r["paper_id"] for r in env["results"]} >= {"T5"}
    assert "RULES: SEARCH-1.0.0 NORM-1.0.0 TERMS-TEST LIMITS-1.0.0 LINES-1.0.0" in env["limitations"]
    direct = rt(T.search_passages(tr, "dignity", k=20))
    assert all("query" in r["payload"]["match_via"] for r in direct["results"])
    multi = rt(T.search_passages(tr, "Spec. cost", paper_id="T1", k=20))
    assert multi["status"] == "ok"
    assert any(r["locator"]["line_start"] == 78 and "query" in r["payload"]["match_via"] for r in multi["results"])
    ja = rt(T.search_passages(tr, "仕様化費用", paper_id="T1"))
    assert ja["status"] == "ok" and all(r["payload"]["match_via"] == ["term_map:M91"] for r in ja["results"])
    plain = rt(T.search_passages(reader, "尊厳"))
    assert plain["status"] == "no_lexical_match"


# ---------------------------------------------------------------- T05


@pytest.mark.parametrize("i", range(11))
def test_t05_claim_fields(reader, i):
    raw = json.loads(_CORPUS.raw["claims/t5.json"])
    c = raw["claims"][i]
    env = rt(T.get_claim_record(reader, c["id"]))
    assert env["status"] == "ok" and len(env["results"]) == 1
    r = env["results"][0]
    p = r["payload"]
    for key in ("id", "status", "claim", "source_quote", "not_claimed", "section", "source_locator"):
        assert p[key] == c[key]
    assert p["additional_source_quotes"] == c.get("additional_source_quotes")
    assert p["footnote"] == c.get("footnote")
    assert p["author_answerable"] is None and p["author_answerable_note"]
    assert p["claim_note"]
    assert p["ledger_sha256"] == S.file_hash(_CORPUS, "claims/t5.json") == r["source_hash"]
    assert p["cited_paper_sha256"] == _CORPUS.papers["T5"].sha256 != p["ledger_sha256"]
    assert [n["json_pointer"] for n in p["ledger_notes"]] == ["/editorial_status", "/source_role"]
    assert r["source_kind"] == "claims" and r["locator"]["json_pointer"] == f"/claims/{i}"
    assert r["canonical_doi"] == _CORPUS.papers["T5"].canonical_doi and r["paper_version"] == "3"
    anchor = c["source_locator"]["section_url"].split("#")[1]
    assert r["section_anchor"] == anchor and r["derivative_of"] == [f"papers/T5.md#{anchor}"]
    loc = c["source_locator"]
    assert c["source_quote"] in _CORPUS.lines["papers/T5.md"][loc["line_start"] - 1]
    assert lims(env, "LABEL")


def test_t05_additional_and_null_fields(reader):
    with_add = {c["id"] for c in _CORPUS.ledger["claims"] if "additional_source_quotes" in c}
    assert with_add == {"T5-A3", "T5-A4", "T5-N1", "T5-N2", "T5-H1"}
    lengths = [len(rt(T.get_claim_record(reader, c["id"]))["results"][0]["payload"]["not_claimed"])
               for c in _CORPUS.ledger["claims"]]
    assert lengths == [3, 3, 3, 2, 4, 5, 4, 4, 2, 3, 3]
    for c in _CORPUS.ledger["claims"]:
        p = rt(T.get_claim_record(reader, c["id"]))["results"][0]["payload"]
        if c["id"] not in with_add:
            assert p["additional_source_quotes"] is None
        assert (p["footnote"] is None) == (c["id"] != "T5-N3")


def test_t05_query_path(reader):
    env = rt(T.get_claim_record(reader, query="dignity"))
    assert env["status"] == "ok" and env["results"]
    assert all(r["payload"]["match"]["matched_terms"] == ["dignity"] for r in env["results"])
    assert lims(env, "LEDGER") and lims(env, "LABEL")
    zero = rt(T.get_claim_record(reader, query="zzqxjvw"))
    assert zero["status"] == "no_lexical_match" and zero["results"] == [] and lims(zero, "LEDGER")
    for kwargs in ({}, {"claim_id": "T5-A1", "query": "dignity"}):
        assert rt(T.get_claim_record(reader, **kwargs))["status"] == "invalid_input"
    assert rt(T.get_claim_record(reader, query="の"))["status"] == "invalid_input"


# ---------------------------------------------------------------- T06


@pytest.mark.parametrize("cid", ["T1-A1", "T2-X1", "T3-A1", "T4-A1"])
def test_t06_ledger_not_available(reader, cid):
    env = rt(T.get_claim_record(reader, cid))
    assert env["status"] == "ledger_not_available" and env["results"] == []
    pid = cid.split("-")[0]
    assert {c["paper_id"] for c in env["candidates"]} == {pid}
    assert len(env["candidates"]) == len(_CORPUS.papers[pid].sections)
    assert all(c["source_kind"] == "paper_md" and "text" not in c["payload"] for c in env["candidates"])
    text = S.to_json(env)
    for c in _CORPUS.ledger["claims"]:
        assert c["status"] not in text
    assert lims(env, "LEDGER") and lims(env, "ROUTE")


# ---------------------------------------------------------------- T07


@pytest.mark.parametrize("sentence,line,anchor", FROZEN)
@pytest.mark.parametrize("pid", [None, "T5"])
def test_t07_frozen_sentences_exact(reader, sentence, line, anchor, pid):
    env = rt(T.verify_quote(reader, sentence, paper_id=pid))
    assert env["status"] == "ok" and env["match"] == "exact" and env["normalization_applied"] == []
    assert len(env["results"]) == 1 and env["candidates"] == []
    r = env["results"][0]
    assert (r["source_path"], r["locator"]["line_start"], r["section_anchor"]) == ("papers/T5.md", line, anchor)
    assert r["payload"]["matched_text"] == sentence
    assert r["canonical_doi"] == _CORPUS.papers["T5"].canonical_doi


# ---------------------------------------------------------------- T08


VARIANTS = json.loads((FIX / "quote_variants.json").read_text(encoding="utf-8"))["variants"]


@pytest.mark.parametrize("v", VARIANTS, ids=[v["id"] for v in VARIANTS])
def test_t08_normalized(reader, v):
    env = rt(T.verify_quote(reader, v["input"]))
    assert env["status"] == "ok" and env["match"] == "normalized"
    got = [{"path": r["source_path"], "line": r["locator"]["line_start"]} for r in env["results"]]
    assert got == v["expect_locations"]
    assert set(v["expect_rules"]) <= set(env["normalization_applied"])
    assert set(env["normalization_applied"]) <= set(N.RULE_IDS)
    for r in env["results"]:
        line = _CORPUS.lines[r["source_path"]][r["locator"]["line_start"] - 1]
        c0, c1 = r["locator"]["char_start"], r["locator"]["char_end"]
        assert r["payload"]["matched_text"] == line[c0:c1]
        assert r["payload"]["normalization_applied"]
        for d in r["payload"]["diffs"]:
            assert d["source"] == line[d["source_char_start"]:d["source_char_start"] + len(d["source"])]
    assert lims(env, "NORMALIZED") and "RULES: NORM-1.0.0 LIMITS-1.0.0 LINES-1.0.0" in env["limitations"]


def test_t08_rule_details():
    q = N.normalize_quote
    assert q("75.6% と 4．1節 と .05", is_input=True).text == "75.6% と 4．1節と .05"
    assert q("75，6", is_input=True).text == "75，6" and q("a，b", is_input=True).text == "a、b"
    assert q("－0.26＜＝＞～＋", is_input=True).text == "－0.26＜＝＞～＋"
    assert q("＜ ＝", is_input=True).text == "＜＝"  # 全角形は CJK の範囲なので間の空白は WS-CJK で消える
    assert q(chr(0x2212) + "1 ≦ ≤", is_input=True).text == chr(0x2212) + "1 ≦ ≤"
    assert q("ＡＢＣ（x）", is_input=True).text == "ABC(x)"
    assert q("ﾊﾟﾊﾞｰｽ ｶ", is_input=True).text == "パバース カ"
    assert q("「引用」『書名』", is_input=True).text == "「引用」『書名』"
    assert q("Case Sensitive", is_input=True).text == "Case Sensitive"
    nfd = unicodedata.normalize("NFD", "ガ")
    assert q(nfd, is_input=True).nfc_applied and not q(nfd, is_input=False).nfc_applied


# ---------------------------------------------------------------- T09


MUTATIONS = json.loads((FIX / "quote_mutations.json").read_text(encoding="utf-8"))["mutations"]


@pytest.mark.parametrize("m", MUTATIONS, ids=[m["id"] for m in MUTATIONS])
def test_t09_mutations_not_found(reader, m):
    text = m["input"]
    inp = N.normalize_quote(text, is_input=True).text
    for ln in (*reader.orig_lines, *reader.en_lines):  # 前提：照合範囲の全体に生でも正規化後でも無い
        assert text not in ln.text and inp not in ln.quote.text, (m["id"], ln.path, ln.no)
    env = rt(T.verify_quote(reader, text))
    assert env["status"] == "quote_not_found" and env["match"] == "none" and env["results"] == []
    assert lims(env, "NOT_FOUND") and lims(env, "CAND")
    for c in env["candidates"]:
        assert c["payload"]["match"] == "none"
    en = rt(T.verify_quote(reader, text, language="en"))
    assert en["status"] == "quote_not_found"


# ---------------------------------------------------------------- T10


@pytest.mark.parametrize("text", ["", "   ", chr(0x3000), chr(0x200B), " " + chr(0x200B) + chr(0x3000) + "\n",
                                  "AI can", "参加の非", "x" * 2001, None, 5])
def test_t10_invalid(reader, text):
    env = rt(T.verify_quote(reader, text))
    assert env["status"] == "invalid_input" and env["results"] == [] and env["match"] == "none"


def test_t10_min_length_boundary(reader):
    assert rt(T.verify_quote(reader, "参加の非移"))["status"] != "invalid_input"
    assert rt(T.verify_quote(reader, "Spec. cost"))["status"] != "invalid_input"  # 10字
    assert rt(T.verify_quote(reader, "Spec. cos"))["status"] == "invalid_input"  # 9字（「.」は写像後も数えるが仮名・漢字ではない）
    assert rt(T.verify_quote(reader, "ＳＤの目"))["status"] == "invalid_input"  # 仮名・漢字を含み、正規化後4字


def test_t10_ambiguous(reader):
    env = rt(T.verify_quote(reader, "Spec. cost"))
    assert env["status"] == "ok" and env["match"] == "exact"
    assert [r["locator"]["line_start"] for r in env["results"]] == [78, 80]
    assert "AMBIGUOUS: total=2（同じ文字列が複数箇所にある）" in env["limitations"]


def test_t10_over_limit(reader):
    total = sum(ln.text.count("specification") for ln in reader.orig_lines)
    assert total > T.QUOTE_MAX_RESULTS
    env = rt(T.verify_quote(reader, "specification"))
    assert env["status"] == "invalid_input" and env["results"] == [] and env["candidates"] == []
    assert any(x.startswith("TOTAL: total=") for x in env["limitations"])


@pytest.mark.parametrize("text,exact_at,near_at", [
    ("the author's r", ("papers/T1.md", 225), ("papers/T1.md", 337)),
    ("Management Review,", ("papers/T1.md", 389), ("papers/T4.md", 250)),
])
def test_t10_exact_with_normalized_elsewhere(reader, text, exact_at, near_at):
    env = rt(T.verify_quote(reader, text))
    assert env["status"] == "ok" and env["match"] == "exact"
    assert [(r["source_path"], r["locator"]["line_start"]) for r in env["results"]] == [exact_at]
    near = [(c["source_path"], c["locator"]["line_start"]) for c in env["candidates"]]
    assert near_at in near
    for c in env["candidates"]:
        assert c["payload"]["match"] == "normalized" and c["payload"]["candidate_reason"]
    assert lims(env, "NEARBY")


def test_t10_language_and_paper(reader):
    s = FROZEN[0][0]
    assert rt(T.verify_quote(reader, s, paper_id="T1"))["status"] == "quote_not_found"
    assert rt(T.verify_quote(reader, s, paper_id="T5", language="en"))["status"] == "invalid_input"
    assert rt(T.verify_quote(reader, s, paper_id="T5", language="ja"))["status"] == "invalid_input"
    assert rt(T.verify_quote(reader, s, language="ja"))["status"] == "invalid_input"
    assert rt(T.verify_quote(reader, s, language="fr"))["status"] == "invalid_input"
    assert rt(T.verify_quote(reader, s, paper_id="T9"))["status"] == "unknown_id"
    assert rt(T.verify_quote(reader, s, paper_id="../T5"))["status"] == "invalid_input"
    r11 = "従業員が遭遇から結晶化させた向きを，正式な検討の回路に入れ"
    assert rt(T.verify_quote(reader, r11, paper_id="T4", language="ja"))["match"] == "exact"


# ---------------------------------------------------------------- T11


@pytest.fixture(scope="module")
def preader() -> T.Reader:
    return T.Reader(_CORPUS, patterns=TEST_PATTERNS)


JUDGMENT_KEYS = {"correct", "incorrect", "error", "verdict", "valid", "is_misreading", "misreading", "judgment", "score"}


@pytest.mark.parametrize("case,text", FORM_CASES, ids=[c for c, _ in FORM_CASES])
def test_t11_forms_are_flagged_the_same_way(preader, case, text):
    env = rt(T.check_compressions(preader, text))
    assert env["status"] == "ok" and len(env["results"]) == 1
    r = env["results"][0]
    p = r["payload"]
    assert p["pattern_id"] == "P-T01" and p["pattern_version"] == "TEST-1"
    assert p["needs_context_review"] is True
    assert p["source_excerpt"] == _CORPUS.lines["papers/T5.md"][222]
    assert (r["source_path"], r["locator"]["line_start"], r["section_anchor"]) == ("papers/T5.md", 223, "t5-5-4")
    for m in p["matched"]:
        assert N.fold_search(text[m["char_start"]:m["char_end"]], is_input=True).text == \
            N.fold_search(m["form"], is_input=False).text
    assert not (set(p) & JUDGMENT_KEYS)
    assert T.CONTRACT in env["limitations"] and T.FORMS in env["limitations"]


def test_t11_multiple_sources_and_guide(preader):
    env = rt(T.check_compressions(preader, "遊びは last stronghold だという。"))
    assert [r["source_kind"] for r in env["results"]] == ["paper_md", "reading_guide"]
    g = env["results"][1]
    assert g["canonical_doi"] is None and g["paper_id"] is None and g["section_anchor"] is None
    assert g["derivative_of"] == [f"papers/T{i}.md" for i in range(1, 6)]
    none = rt(T.check_compressions(preader, "無関係な文です。"))
    assert none["status"] == "ok" and none["results"] == []
    assert "PATTERNS: 承認済みパターン 2 件（PATTERNS-TEST）・該当 0 件" in none["limitations"]


def test_t11_zero_patterns(reader):
    env = rt(T.check_compressions(reader, "AIは遊べない"))
    assert env["status"] == "ok" and env["results"] == []
    assert "PATTERNS: 承認済みパターン 0 件（PATTERNS-0.0.0）・該当 0 件" in env["limitations"]
    assert T.CONTRACT in env["limitations"]
    for bad in ("", "  ", "x" * 2001, None):
        assert rt(T.check_compressions(reader, bad))["status"] == "invalid_input"


def test_t11_invalid_pattern_rejected():
    bad = PAT.Pattern(id="P-T09", version="TEST-1", surface_forms=("x",),
                      related_sources=(PAT.RelatedSource("papers/T5.md", 223, 223, "t5-abstract"),),
                      approved_on="2026-09-18")
    with pytest.raises(ValueError):
        T.Reader(_CORPUS, patterns=(bad,))
    ledger_src = PAT.Pattern(id="P-T10", version="TEST-1", surface_forms=("x",),
                             related_sources=(PAT.RelatedSource("claims/t5.json", 1, 1),), approved_on="2026-09-18")
    with pytest.raises(ValueError):
        T.Reader(_CORPUS, patterns=(ledger_src,))


# ---------------------------------------------------------------- T12


def test_t12_translation_section(reader):
    env = rt(T.get_section(reader, "T4", "t4-1-1", "en"))
    assert env["status"] == "ok" and env["results"]
    manifest = json.loads(_CORPUS.raw["translations/T4.en.manifest.json"])
    for r in env["results"]:
        assert r["source_kind"] in ("translation", "translation_note") and r["language"] == "en"
        assert r["source_path"] == "translations/T4.en.md" and r["paper_id"] == "T4" and r["paper_version"] == "1"
        p = r["payload"]
        assert p["original_locator"]["path"] == "papers/T4.md" and p["original_locator"]["section"] == "t4-1-1"
        assert p["preparation"]["text"] == manifest["preparation"]
        assert p["authority"]["text"] == manifest["authority"]
        assert p["translation_version"] == "1.0.0" and p["source_corpus_version"] == "3.2.1"
        if r["source_kind"] == "translation":
            assert r["canonical_doi"] == _CORPUS.papers["T4"].canonical_doi
            assert r["derivative_of"] == ["papers/T4.md#t4-1-1"]
    assert lims(env, "TRANSLATION") and lims(env, "UNIT")


def test_t12_translator_notes_are_separate(reader):
    seen = []
    for sec in _CORPUS.papers["T4"].sections:
        env = rt(T.get_section(reader, "T4", sec.id, "en"))
        for r in env["results"]:
            assert r["source_kind"] != "paper_md"
            if r["source_kind"] == "translation_note":
                seen.append(r["section_anchor"])
                assert r["canonical_doi"] is None
                assert r["derivative_of"][0].startswith("translations/T4.en.md#")
                assert r["payload"]["text"].startswith('<details class="translation-note"')
            else:
                assert '<details class="translation-note"' not in r["payload"].get("text", "")
    assert sorted(seen) == [f"tn-{i:02d}" for i in range(1, 17)]


def test_t12_front_matter_and_notes(reader):
    env = rt(T.get_section(reader, "T4", "paper-t4", "en"))
    kinds = [(r["source_kind"], r["source_path"]) for r in env["results"]]
    assert ("translation_note", "translations/T4.en.md") in kinds
    wrappers = [r for r in env["results"] if r["source_path"] == "translations/T4.en.manifest.json"]
    assert wrappers and all(r["locator"]["json_pointer"].startswith("/sourceUnits/") for r in wrappers)
    assert all(r["section_anchor"] == "t4en-u017" for r in wrappers)
    notes = rt(T.get_section(reader, "T4", "t4-notes", "en"))
    targets = [r["payload"]["unit"]["target_id"] for r in notes["results"] if r["source_kind"] == "translation"]
    assert [t for t in targets if t.startswith("author-note-")] == [f"author-note-{i}" for i in range(1, 6)]
    for frame, lines in (("translation-guide", (1, 22)), ("edition-integrity", (1098, 1105))):
        fe = rt(T.get_section(reader, "T4", frame, "en"))
        r = fe["results"][0]
        assert r["payload"]["frame"] is True and (r["locator"]["line_start"], r["locator"]["line_end"]) == lines
        assert lims(fe, "FRAME")


def test_t12_language_selection(reader):
    for pid in ("T1", "T2", "T3", "T5"):
        sid = _CORPUS.papers[pid].sections[1].id
        for lang in ("en", "ja"):
            assert rt(T.get_section(reader, pid, sid, lang))["status"] == "invalid_input"
    assert rt(T.get_section(reader, "T4", "t4-1", "ja"))["results"][0]["source_kind"] == "paper_md"
    assert rt(T.get_section(reader, "T4", "t4-1", "fr"))["status"] == "invalid_input"


def test_t12_verify_quote_translation_note(reader):
    tn_line = next(t for t in _CORPUS.t4en.notes if t.id == "tn-01").line_start + 3
    sentence = _CORPUS.lines["translations/T4.en.md"][tn_line - 1][:60]
    env = rt(T.verify_quote(reader, sentence, language="en"))
    assert env["status"] == "ok"
    r = env["results"][0]
    assert r["source_kind"] == "translation_note" and r["section_anchor"] == "tn-01"
    assert r["canonical_doi"] is None and r["payload"]["translator_note_id"] == "tn-01"
    orig = rt(T.verify_quote(reader, sentence))
    assert orig["status"] == "quote_not_found"
    note_lines = {n for t in _CORPUS.t4en.notes for n in range(t.line_start, t.line_end + 1)}
    prose = next(ln for ln in reader.en_lines if ln.no not in note_lines and ln.kind == "translation"
                 and len(ln.text) > 80 and ln.text[0].isalpha())
    text = prose.text[:40]
    tr = rt(T.verify_quote(reader, text, paper_id="T4", language="en"))
    assert tr["status"] == "ok" and all(x["source_kind"] == "translation" for x in tr["results"])


# ---------------------------------------------------------------- R01


def _r01_outputs(seed: str) -> str:
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "SYSTEMROOT")}
    env["PYTHONHASHSEED"] = seed
    out = subprocess.run([sys.executable, "-m", "tests._support.r01_calls"], cwd=REPO_ROOT, env=env,
                         capture_output=True, check=True, timeout=120)
    return out.stdout.decode("utf-8")


def test_r01_reproducible_across_processes(reader):
    a = _r01_outputs("0")
    b = _r01_outputs("4242")
    c = _r01_outputs("random")
    assert a == b == c
    assert len(a.splitlines()) == len(r01_calls.CALLS)
    assert "\n".join(r01_calls.outputs(reader)) + "\n" == a
    assert r01_calls.outputs(reader) == r01_calls.outputs(reader)
