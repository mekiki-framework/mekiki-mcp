"""施工段階1の完了条件 D01〜D04（SPEC §7）。

改変は一時コピー（tmp_path）かメモリ上の構造にだけ行い、実物の data/ は読むだけ。
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
import shutil
from types import MappingProxyType

import pytest

from mekiki_reader import corpus as C
from tests._support import copy_bundle, resync_entry, rewrite_manifest, same_length_change

PAPER_PATHS = [f"papers/T{i}.md" for i in range(1, 6)]
OTHER_PATHS = [p for p in C.ALLOWED_PATHS if p not in PAPER_PATHS]


def expect_kind(kind: str, data_dir, expected=C.EXPECTED_BUNDLE_SHA256, path=None):
    with pytest.raises(C.BundleError) as ei:
        C.load_corpus(data_dir, expected)
    assert ei.value.kind == kind, str(ei.value)
    if path is not None:
        assert ei.value.path == path, str(ei.value)
    return ei.value


@pytest.fixture(scope="module")
def corpus() -> C.Corpus:
    return C.load_corpus()


@pytest.fixture
def bundle(tmp_path):
    return copy_bundle(tmp_path)


# ---------------------------------------------------------------- 陽性対照


def test_real_data_loads(corpus):
    assert corpus.bundle.bundle_hash == C.EXPECTED_BUNDLE_SHA256
    assert [f.path for f in corpus.bundle.files] == list(C.ALLOWED_PATHS)
    assert len(C.ALLOWED_PATHS) == 18
    assert corpus.bundle.corpus.commit == "67480613108cf72c29d5691e3d7a6c7e6553eb9b"
    assert corpus.bundle.corpus.tree == "7c50a4fc2bf20f1529aebe8a8b7898e26332f1a1"


def test_copy_loads(bundle):
    c = C.load_corpus(bundle)
    assert c.bundle.bundle_hash == C.EXPECTED_BUNDLE_SHA256


def test_bundle_manifest_is_canonical_and_self_excluded():
    raw = (C.DATA_DIR / C.BUNDLE_MANIFEST).read_bytes()
    obj = json.loads(raw)
    assert C.canonical_manifest_bytes(obj) == raw
    assert C.BUNDLE_MANIFEST not in [f["path"] for f in obj["files"]]
    assert obj["not_bundled_references"] == [
        "mekiki-framework-t1-t5.md", "metadata.json",
        "papers/T1.html", "papers/T2.html", "papers/T3.html", "papers/T4.en.html", "papers/T4.html", "papers/T5.html",
        "tools/build_access.py", "tools/validate_corpus.py",
    ]


def test_corpus_is_read_only(corpus):
    with pytest.raises(TypeError):
        corpus.raw["papers/T1.md"] = b""  # type: ignore[index]
    with pytest.raises(TypeError):
        corpus.ledger["paper"] = "T1"  # type: ignore[index]
    with pytest.raises(dataclasses.FrozenInstanceError):
        corpus.papers["T1"].title = "x"  # type: ignore[misc]


# ---------------------------------------------------------------- D01 原論文の改変


@pytest.mark.parametrize("rel", PAPER_PATHS)
@pytest.mark.parametrize("mutation,kind", [
    ("same_length", "hash_mismatch"),
    ("trailing_space", "size_mismatch"),
    ("crlf", "size_mismatch"),
    ("empty", "size_mismatch"),
])
def test_d01_paper_modified(bundle, rel, mutation, kind):
    f = bundle / rel
    data = f.read_bytes()
    new = {
        "same_length": lambda d: same_length_change(d),
        "trailing_space": lambda d: d + b" ",
        "crlf": lambda d: d.replace(b"\n", b"\r\n"),
        "empty": lambda d: b"",
    }[mutation](data)
    assert new != data
    f.write_bytes(new)
    expect_kind(kind, bundle, path=rel)


# ---------------------------------------------------------------- D02 ガイド・主張JSONほかの改変


@pytest.mark.parametrize("rel", OTHER_PATHS)
def test_d02_other_file_modified(bundle, rel):
    f = bundle / rel
    f.write_bytes(same_length_change(f.read_bytes()))
    expect_kind("hash_mismatch", bundle, path=rel)


def test_d02_claim_status_changed(bundle):
    f = bundle / "claims/t5.json"
    data = f.read_bytes()
    old = b"analytic theorem (paper's classification)"
    assert data.count(old) == 1
    f.write_bytes(data.replace(old, b"analytic theorem (paper's classificatior)"))
    expect_kind("hash_mismatch", bundle, path="claims/t5.json")


def test_d02_manifest_entry_hash_only(bundle):
    def mutate(obj):
        e = next(f for f in obj["files"] if f["path"] == "claims/t5.json")
        e["sha256"] = "0" * 64

    rewrite_manifest(bundle, mutate)
    expect_kind("bundle_hash_mismatch", bundle, path=C.BUNDLE_MANIFEST)


def test_d02_file_and_manifest_changed_together(bundle):
    f = bundle / "claims/t5.json"
    f.write_bytes(same_length_change(f.read_bytes()))
    resync_entry(bundle, "claims/t5.json")
    expect_kind("bundle_hash_mismatch", bundle, path=C.BUNDLE_MANIFEST)


def test_d02_internal_record_changed_with_consistent_manifest(bundle):
    """同時改変を期待ハッシュの差し替えで通しても、コーパス内部の記録との照合で止まる。"""
    f = bundle / "source_manifest.json"
    data = f.read_bytes()
    old = b'"sha256": "2b027f11'
    assert data.count(old) == 1
    f.write_bytes(data.replace(old, b'"sha256": "2b027f12'))
    new_expected = resync_entry(bundle, "source_manifest.json")
    expect_kind("internal_mismatch", bundle, new_expected, path="papers/T1.md")


# ---------------------------------------------------------------- D03 欠落・余剰・許可外パス


@pytest.mark.parametrize("rel", ["papers/T1.md", "CITATION.md", "LICENSE", "tests/reading_cases.json"])
def test_d03_missing_file(bundle, rel):
    (bundle / rel).unlink()
    expect_kind("missing", bundle, path=rel)


def test_d03_missing_manifest(bundle):
    (bundle / C.BUNDLE_MANIFEST).unlink()
    expect_kind("missing", bundle, path=C.BUNDLE_MANIFEST)


def test_d03_missing_data_dir(tmp_path):
    expect_kind("missing", tmp_path / "nonexistent", path=".")


@pytest.mark.parametrize("rel", ["extra.md", ".DS_Store", "papers/T1.html", "translations/T4.en.meta.json"])
def test_d03_extra_file(bundle, rel):
    (bundle / rel).write_bytes(b"x")
    expect_kind("extra", bundle, path=rel)


def test_d03_extra_directory(bundle):
    (bundle / "emptydir").mkdir()
    expect_kind("extra", bundle, path="emptydir")


def test_d03_extra_symlink(bundle, tmp_path):
    target = tmp_path / "outside.md"
    target.write_bytes(b"outside")
    os.symlink(target, bundle / "papers/T6.md")
    expect_kind("extra", bundle, path="papers/T6.md")


def test_d03_disallowed_path(bundle):
    content = b"{}\n"
    (bundle / "metadata.json").write_bytes(content)

    def mutate(obj):
        obj["files"].append({"path": "metadata.json", "bytes": len(content),
                             "git_blob_sha1": C.git_blob_sha1(content), "sha256": C.sha256_hex(content)})
        obj["files"].sort(key=lambda f: f["path"])

    new_expected = rewrite_manifest(bundle, mutate)
    expect_kind("disallowed", bundle, new_expected, path="metadata.json")


def test_d03_file_replaced_by_symlink(bundle, tmp_path):
    rel = "papers/T1.md"
    outside = tmp_path / "T1_copy.md"
    shutil.copyfile(bundle / rel, outside)
    (bundle / rel).unlink()
    os.symlink(outside, bundle / rel)
    expect_kind("not_regular", bundle, path=rel)


def test_d03_file_replaced_by_directory(bundle):
    rel = "llms.txt"
    (bundle / rel).unlink()
    (bundle / rel).mkdir()
    expect_kind("not_regular", bundle, path=rel)


def test_d03_parent_directory_is_symlink(bundle, tmp_path):
    moved = tmp_path / "papers_elsewhere"
    shutil.move(bundle / "papers", moved)
    os.symlink(moved, bundle / "papers", target_is_directory=True)
    expect_kind("not_regular", bundle, path="papers")


def test_d03_manifest_is_symlink(bundle, tmp_path):
    outside = tmp_path / "bm.json"
    shutil.copyfile(bundle / C.BUNDLE_MANIFEST, outside)
    (bundle / C.BUNDLE_MANIFEST).unlink()
    os.symlink(outside, bundle / C.BUNDLE_MANIFEST)
    expect_kind("not_regular", bundle, path=C.BUNDLE_MANIFEST)


def test_d03_data_dir_is_symlink(bundle, tmp_path):
    link = tmp_path / "data_link"
    os.symlink(bundle, link, target_is_directory=True)
    expect_kind("not_regular", link, path=".")


def _replace_path(old, new):
    def mutate(obj):
        e = next(f for f in obj["files"] if f["path"] == old)
        e["path"] = new
    return mutate


@pytest.mark.parametrize("mutate", [
    _replace_path("LICENSE", "../x"),
    _replace_path("LICENSE", "/etc/hosts"),
    _replace_path("LICENSE", "papers/../LICENSE"),
    _replace_path("LICENSE", "papers\\T1.md"),
    _replace_path("LICENSE", "CITATION.md"),  # 重複
    lambda obj: obj["files"].pop(0),  # 許可ファイルを一覧から外す
    lambda obj: obj["files"].reverse(),  # 整列していない
    lambda obj: obj["corpus"].update(commit="0" * 40),
    lambda obj: obj["corpus"].update(git_ref="refs/heads/main"),
    lambda obj: obj.update(format_version=2),
    lambda obj: obj.update(extra_key=True),
    lambda obj: obj["files"][0].update(bytes=True),
    lambda obj: obj["not_bundled_references"].append("LICENSE"),
], ids=["dotdot", "absolute", "inner-dotdot", "backslash", "duplicate", "lacking", "unsorted",
        "commit", "git_ref", "format_version", "extra_key", "bool_bytes", "ref_is_bundled"])
def test_d03_manifest_invalid(bundle, mutate):
    new_expected = rewrite_manifest(bundle, mutate)
    expect_kind("manifest_invalid", bundle, new_expected, path=C.BUNDLE_MANIFEST)


def test_d03_manifest_not_canonical(bundle):
    path = bundle / C.BUNDLE_MANIFEST
    compact = json.dumps(json.loads(path.read_bytes()), sort_keys=True, ensure_ascii=False).encode() + b"\n"
    path.write_bytes(compact)
    expect_kind("manifest_invalid", bundle, hashlib.sha256(compact).hexdigest(), path=C.BUNDLE_MANIFEST)


def test_d03_manifest_not_json(bundle):
    path = bundle / C.BUNDLE_MANIFEST
    path.write_bytes(b"not json\n")
    expect_kind("manifest_invalid", bundle, hashlib.sha256(b"not json\n").hexdigest(), path=C.BUNDLE_MANIFEST)


# ---------------------------------------------------------------- D04 節ID・行範囲・引用位置の有効性（実データ）


def test_d04_sections(corpus):
    counts = {pid: len(p.sections) for pid, p in corpus.papers.items()}
    assert counts == {"T1": 40, "T2": 39, "T3": 25, "T4": 25, "T5": 29}
    assert {pid: len(p.lines) for pid, p in corpus.papers.items()} == {
        "T1": 442, "T2": 376, "T3": 251, "T4": 261, "T5": 325}
    for p in corpus.papers.values():
        assert len(p.lines) == len(corpus.texts[p.path].splitlines())
        ids = [s.id for s in p.sections]
        assert len(set(ids)) == len(ids)
        assert p.sections[0].line_start == 1 and p.sections[-1].line_end == len(p.lines)
        for a, b in zip(p.sections, p.sections[1:]):
            assert b.line_start == a.line_end + 1
        for s in p.sections:
            assert p.lines[s.line_start - 1] == "#" * s.level + " " + s.title
    all_secs = [s for p in corpus.papers.values() for s in p.sections]
    assert len(all_secs) == 158
    by_id = {(s.paper_id, s.id): s for s in all_secs}
    jumps = [s for s in all_secs if s.parent_id and by_id[(s.paper_id, s.parent_id)].level < s.level - 1]
    assert len(jumps) == 6 and {s.paper_id for s in jumps} == {"T4"}
    parents_with_body = [s for s in all_secs if s.child_ids and not s.heading_only]
    assert len(parents_with_body) == 13
    t1_2 = corpus.papers["T1"].section("t1-2")
    assert (t1_2.line_start, t1_2.line_end, t1_2.heading_only, t1_2.child_ids[0]) == (46, 47, True, "t1-2-1")
    paper_t4 = corpus.papers["T4"].section("paper-t4")
    assert paper_t4.child_ids == ("t4-1", "t4-2", "t4-3", "t4-4", "t4-5", "t4-6", "t4-notes", "t4-references")
    assert (paper_t4.line_start, paper_t4.line_end, paper_t4.heading_only) == (1, 24, False)
    assert {pid: p.language for pid, p in corpus.papers.items()} == {
        "T1": "en", "T2": "en", "T3": "en", "T4": "ja", "T5": "en"}
    assert {pid: p.preprint_version for pid, p in corpus.papers.items()} == {
        "T1": "1", "T2": "2", "T3": "2", "T4": "1", "T5": "3"}


def test_d04_claim_quotes(corpus):
    t5 = corpus.papers["T5"]
    text = corpus.texts[t5.path]
    claims = corpus.ledger["claims"]
    assert len(claims) == 11
    quotes = []
    for c in claims:
        quotes.append((c["id"], c["section"], c["source_quote"], c["source_locator"]))
        quotes += [(c["id"], a["section"], a["quote"], a["source_locator"]) for a in c.get("additional_source_quotes", ())]
    assert len(quotes) == 17
    for cid, section, quote, loc in quotes:
        assert text.count(quote) == 1, cid
        start = text[:text.index(quote)].count("\n") + 1
        assert (loc["line_start"], loc["line_end"]) == (start, start + quote.count("\n")), cid
        assert loc["quote_sha256"] == hashlib.sha256(quote.encode()).hexdigest(), cid
        anchor = "t5-" + section.replace(".", "-")
        sec = t5.section(anchor)
        assert sec is not None and sec.line_start <= start <= sec.line_end, cid
        assert loc["section_url"] == f"https://mekiki-framework.github.io/papers/T5.html#{anchor}", cid
    with_footnote_url = [cid for cid, _, _, loc in quotes if "footnote_url" in loc]
    assert with_footnote_url == ["T5-N3"]
    assert corpus.ledger["source_sha256"] == t5.sha256
    assert all("author_answerable" not in c for c in claims)


def test_d04_reading_cases(corpus):
    cases = corpus.reading_cases["cases"]
    assert [c["id"] for c in cases] == [f"R{i:02d}" for i in range(1, 18)]
    sources = [(c["id"], a) for c in cases for a in c["additional_sources"]]
    assert len(sources) == 15
    for cid, a in sources:
        paper = corpus.papers[a["paper"]]
        text = corpus.texts[paper.path]
        assert text.count(a["quote"]) == 1, cid
        line = text[:text.index(a["quote"])].count("\n") + 1
        sec = paper.section(a["paper"].lower() + "-" + a["section"].replace(".", "-"))
        assert sec is not None and sec.line_start <= line <= sec.line_end, cid
    r12 = [a for cid, a in sources if cid == "R12"]
    assert [corpus.papers["T5"].section("t5-references").id] == ["t5-references"] and r12[0]["section"] == "references"


def test_d04_t4_translation(corpus):
    idx = corpus.t4en
    units = idx.units
    assert len(units) == 137
    positioned = [u for u in units if u.t_line_start is not None]
    assert len(positioned) == 126
    assert sorted({u.treatment for u in units if u.t_line_start is None}) == ["separator", "wrapper"]
    wrappers = [u for u in units if u.treatment == "wrapper"]
    separators = [u for u in units if u.treatment == "separator"]
    assert len(wrappers) == 6 and all(u.description for u in wrappers)
    assert len(separators) == 5 and all(u.description is None for u in separators)
    t4_lines = corpus.lines["papers/T4.md"]
    en = corpus.lines["translations/T4.en.md"]
    assert len(en) == 1105
    no_strip = sum(hashlib.sha256("\n".join(t4_lines[u.source_line - 1:u.source_end_line]).encode()).hexdigest()
                   == u.source_sha256 for u in units)
    with_strip = sum(hashlib.sha256("\n".join(t4_lines[u.source_line - 1:u.source_end_line]).strip().encode()).hexdigest()
                     == u.source_sha256 for u in units)
    assert no_strip == with_strip == 137
    seg_lf = sum(hashlib.sha256(("\n".join(en[u.t_line_start - 1:u.t_line_end]) + "\n").encode()).hexdigest()
                 == u.segment_sha256 for u in positioned)
    seg_bare = sum(hashlib.sha256("\n".join(en[u.t_line_start - 1:u.t_line_end]).encode()).hexdigest()
                   == u.segment_sha256 for u in positioned)
    assert (seg_lf, seg_bare) == (126, 0)
    covered = {n for u in positioned for n in range(u.t_line_start, u.t_line_end + 1)}
    uncovered = sorted(set(range(1, len(en) + 1)) - covered)
    assert uncovered == list(range(1, 23)) + list(range(1098, 1106))
    assert len(idx.notes) == 16
    assert [t.id for t in idx.notes] == [f"tn-{i:02d}" for i in range(1, 17)]
    assert all(t.line_end - t.line_start + 1 == 6 for t in idx.notes)
    targets = [u.target_id for u in positioned]
    assert sorted(x for x in targets if x.startswith("author-note-")) == [f"author-note-{i}" for i in range(1, 6)]
    assert len([x for x in targets if x.startswith("ref-")]) == 28
    notes_units = [u for u in units if u.derived_anchor == "t4-notes"]
    assert {u.section for u in notes_units} == {"6"}  # 記録の unit.section は節の決定に使わない（T4MAP）
    assert corpus.papers["T4"].section("t4-notes") is not None


def test_get_lines(corpus):
    assert C.get_lines(corpus, "papers/T1.md", 1, 1) == (corpus.papers["T1"].lines[0],)
    for args in [("papers/T1.md", 0, 1), ("papers/T1.md", 1, 443), ("papers/T1.md", 5, 4),
                 ("metadata.json", 1, 1), ("../papers/T1.md", 1, 1)]:
        with pytest.raises(ValueError):
            C.get_lines(corpus, *args)


# ---------------------------------------------------------------- D04 陰性（メモリ上の改変）


def _json(corpus, rel):
    return json.loads(corpus.raw[rel])


def test_d04_negative_section_range_shifted(corpus):
    t1 = corpus.papers["T1"]
    secs = list(t1.sections)
    secs[3] = dataclasses.replace(secs[3], line_start=secs[3].line_start + 1)
    with pytest.raises(C.BundleError) as ei:
        C.validate_section_index(dataclasses.replace(t1, sections=tuple(secs)), corpus.texts[t1.path])
    assert ei.value.kind == "index_invalid"


def test_d04_negative_section_title_changed(corpus):
    t2 = corpus.papers["T2"]
    secs = list(t2.sections)
    secs[1] = dataclasses.replace(secs[1], title=secs[1].title + " ")
    with pytest.raises(C.BundleError) as ei:
        C.validate_section_index(dataclasses.replace(t2, sections=tuple(secs)), corpus.texts[t2.path])
    assert ei.value.kind == "index_invalid"


def test_d04_negative_claim_quote_changed(corpus):
    ledger = _json(corpus, "claims/t5.json")
    q = ledger["claims"][0]["source_quote"]
    ledger["claims"][0]["source_quote"] = q[:-1] + ("?" if q[-1] != "?" else "!")
    with pytest.raises(C.BundleError) as ei:
        C.validate_ledger(ledger, corpus.papers, corpus.texts)
    assert ei.value.kind == "index_invalid"


def test_d04_negative_claim_line_shifted(corpus):
    ledger = _json(corpus, "claims/t5.json")
    ledger["claims"][2]["source_locator"]["line_start"] += 1
    with pytest.raises(C.BundleError) as ei:
        C.validate_ledger(ledger, corpus.papers, corpus.texts)
    assert ei.value.kind == "index_invalid"


def test_d04_negative_reading_case_unknown_claim(corpus):
    cases = _json(corpus, "tests/reading_cases.json")
    cases["cases"][0]["claim_ids"].append("T5-Z9")
    with pytest.raises(C.BundleError) as ei:
        C.validate_reading_cases(cases, corpus.papers, corpus.texts, corpus.ledger)
    assert ei.value.kind == "index_invalid"


def test_d04_negative_translation_range_shifted(corpus):
    idx = corpus.t4en
    units = list(idx.units)
    k = next(i for i, u in enumerate(units) if u.t_line_start is not None)
    units[k] = dataclasses.replace(units[k], t_line_start=units[k].t_line_start + 1)
    with pytest.raises(C.BundleError) as ei:
        C.validate_translation_index(dataclasses.replace(idx, units=tuple(units)),
                                     _json(corpus, "translations/T4.en.manifest.json"), corpus.papers["T4"])
    assert ei.value.kind == "index_invalid"


@pytest.mark.parametrize("target", ["papers_sha256", "quote_sha256", "source_unit", "segment", "frozen"])
def test_d04_negative_internal_record(corpus, target):
    src = _json(corpus, "source_manifest.json")
    ledger = _json(corpus, "claims/t5.json")
    t4m = _json(corpus, "translations/T4.en.manifest.json")
    if target == "papers_sha256":
        src["papers"][4]["sha256"] = "0" * 64
    elif target == "quote_sha256":
        ledger["claims"][5]["source_locator"]["quote_sha256"] = "0" * 64
    elif target == "source_unit":
        t4m["sourceUnits"][40]["sourceSha256"] = "0" * 64
    elif target == "segment":
        u = next(u for u in t4m["sourceUnits"] if "translationSegmentSha256" in u)
        u["translationSegmentSha256"] = "0" * 64
    else:
        src["inputs"]["release_3_5_0_inputs"]["frozen_text_sha256"]["translations/T4.en.md"] = "0" * 64
    C.verify_internal_hashes(corpus.raw, _json(corpus, "source_manifest.json"),
                             _json(corpus, "claims/t5.json"), _json(corpus, "translations/T4.en.manifest.json"))
    with pytest.raises(C.BundleError) as ei:
        C.verify_internal_hashes(corpus.raw, src, ledger, t4m)
    assert ei.value.kind == "internal_mismatch"


def test_freeze_helpers():
    frozen = C._freeze({"a": [1, {"b": 2}]})
    assert isinstance(frozen, MappingProxyType) and frozen["a"][1]["b"] == 2
    assert C.split_lines("a\nb\n") == ("a", "b") and C.split_lines("a\nb") == ("a", "b") and C.split_lines("") == ()
    assert not C.is_safe_relpath("a//b") and not C.is_safe_relpath("./a") and C.is_safe_relpath("a/b.md")
    assert copy.deepcopy(C.ALLOWED_PATHS) == tuple(sorted(C.ALLOWED_PATHS))
