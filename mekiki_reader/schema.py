"""応答の共通外枠と結果ごとの出典（SPEC §4・docs/rules/SCHEMA.md・docs/rules/JSON.md）。"""

from __future__ import annotations

import json
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from . import corpus as C

SCHEMA_VERSION = "1.0.0"
JSON_RULE = "JSON-1.0.0"

STATUSES = ("ok", "unknown_id", "quote_not_found", "no_lexical_match", "invalid_input", "ledger_not_available")
SOURCE_KINDS = ("paper_md", "theory_map", "claims", "reading_guide", "reading_test", "translation", "translation_note")
PAPER_BOUND_KINDS = frozenset({"paper_md", "claims", "translation", "translation_note"})
DOI_KINDS = frozenset({"paper_md", "claims", "translation"})  # translation_note・ガイド類は null（Q88）
LANGUAGES = ("ja", "en")

# 同梱ファイル → source_kind（Q38⑦の起草。著者承認待ち）。ツールの結果に出すのは paper_md・claims・
# translation・translation_note・reading_guide。ほかは表として定めるだけ。
SOURCE_KIND_BY_PATH: Mapping[str, str] = MappingProxyType({
    "papers/T1.md": "paper_md",
    "papers/T2.md": "paper_md",
    "papers/T3.md": "paper_md",
    "papers/T4.md": "paper_md",
    "papers/T5.md": "paper_md",
    "translations/T4.en.md": "translation",  # 訳注の区間は translation_note
    "translations/T4.en.manifest.json": "translation",
    "claims/t5.json": "claims",
    "T5_CLAIM_STATUS.md": "claims",
    "THEORY_MAP.md": "theory_map",
    "FOR_AI_READERS.md": "reading_guide",
    "SOURCE_INDEX.md": "reading_guide",
    "llms.txt": "reading_guide",
    "AI_READING_TESTS.md": "reading_test",
    "tests/reading_cases.json": "reading_test",
})

ENVELOPE_KEYS = ("schema_version", "corpus_version", "source_commit", "bundle_hash",
                 "status", "results", "candidates", "limitations")
RESULT_KEYS = ("source_id", "source_kind", "derivative_of", "paper_id", "paper_version", "language",
               "source_path", "source_hash", "section_anchor", "locator", "canonical_doi",
               "source_url", "snapshot_url", "payload")
LOCATOR_KEYS = ("path", "line_start", "line_end", "char_start", "char_end", "json_pointer", "note")
_LIMITATION_RE = re.compile(r"^[A-Z][A-Z0-9_-]*: .+", re.S)
ALL_PAPERS_DERIVATIVE = tuple(f"papers/{p}.md" for p in C.PAPER_IDS)


class SchemaError(Exception):
    """応答の組み立ての誤り（施工側の不具合）。利用者の入力の誤りは status で返す。"""


def thaw(obj: Any) -> Any:
    """読み取り専用の値（MappingProxyType・tuple）を JSON にできる形へ写す。"""
    if isinstance(obj, Mapping):
        return {str(k): thaw(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [thaw(v) for v in obj]
    return obj


def to_json(obj: Mapping[str, Any]) -> str:
    """JSON-1.0.0：キー整列・非 ASCII はそのまま・区切りは "," と ":"・NaN 不可。"""
    return json.dumps(thaw(obj), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def locator(path: str, line_start: int | None = None, line_end: int | None = None,
            char_start: int | None = None, char_end: int | None = None,
            json_pointer: str | None = None, note: str | None = None) -> dict:
    return {"path": path, "line_start": line_start, "line_end": line_end, "char_start": char_start,
            "char_end": char_end, "json_pointer": json_pointer, "note": note}


def file_hash(corpus: C.Corpus, path: str) -> str:
    for f in corpus.bundle.files:
        if f.path == path:
            return f.sha256
    raise SchemaError(f"not bundled: {path}")


def result(corpus: C.Corpus, *, source_kind: str, source_path: str, fragment: str | None,
           language: str, locator_: dict, payload: Mapping[str, Any],
           paper_id: str | None = None, section_anchor: str | None = None,
           source_url: str | None = None, derivative_of: Iterable[str] | None = None) -> dict:
    """出典付きの結果を一つ作る。paper_version と canonical_doi は paper_id と種別から決める。"""
    paper = corpus.papers.get(paper_id) if paper_id else None
    if paper_id and paper is None:
        raise SchemaError(f"unknown paper {paper_id}")
    doi = paper.canonical_doi if (paper is not None and source_kind in DOI_KINDS) else None
    r = {
        "source_id": f"{source_path}#{fragment}" if fragment else source_path,
        "source_kind": source_kind,
        "derivative_of": sorted(set(derivative_of)) if derivative_of else None,
        "paper_id": paper_id,
        "paper_version": paper.preprint_version if paper is not None else None,
        "language": language,
        "source_path": source_path,
        "source_hash": file_hash(corpus, source_path),
        "section_anchor": section_anchor,
        "locator": locator_,
        "canonical_doi": doi,
        "source_url": source_url,
        "snapshot_url": C.RAW_BASE + source_path,
        "payload": thaw(payload),
    }
    validate_result(corpus, r)
    return r


_T4EN_IDS: dict[str, frozenset[str]] = {}


def _t4en_ids(corpus: C.Corpus) -> frozenset[str]:
    key = corpus.bundle.bundle_hash
    if key not in _T4EN_IDS:
        text = corpus.texts[C.T4EN_PATH]
        _T4EN_IDS[key] = frozenset(re.findall(r'id="([^"]+)"', text)) | frozenset(re.findall(r"\{#([^}]+)\}", text))
    return _T4EN_IDS[key]


def validate_result(corpus: C.Corpus, r: Mapping[str, Any]) -> None:
    """SPEC §2.4・§4 の出典の規則を一件ごとに確かめる（違反は SchemaError）。"""
    if tuple(sorted(r)) != tuple(sorted(RESULT_KEYS)):
        raise SchemaError(f"result keys {sorted(r)}")
    kind = r["source_kind"]
    if kind not in SOURCE_KINDS:
        raise SchemaError(f"source_kind {kind}")
    path = r["source_path"]
    if r["source_hash"] != file_hash(corpus, path) or r["snapshot_url"] != C.RAW_BASE + path:
        raise SchemaError("source_hash/snapshot_url")
    if not str(r["source_id"]).startswith(path):
        raise SchemaError("source_id")
    if r["language"] not in LANGUAGES:
        raise SchemaError("language")
    loc = r["locator"]
    if not isinstance(loc, dict) or tuple(sorted(loc)) != tuple(sorted(LOCATOR_KEYS)) or loc["path"] != path:
        raise SchemaError("locator")
    if loc["line_start"] is not None:
        lines = corpus.lines[path]
        if not (1 <= loc["line_start"] <= loc["line_end"] <= len(lines)):
            raise SchemaError("locator lines")
    if loc["line_start"] is None and loc["json_pointer"] is None:
        raise SchemaError("locator has no position")
    if kind in PAPER_BOUND_KINDS:
        pid = r["paper_id"]
        paper = corpus.papers.get(pid)
        if paper is None or r["paper_version"] != paper.preprint_version or not r["section_anchor"]:
            raise SchemaError("paper-bound result lacks paper/version/anchor")
        anchor = r["section_anchor"]
        if kind in ("translation", "translation_note"):
            if anchor not in _t4en_ids(corpus):
                raise SchemaError(f"translation anchor {anchor} not in T4.en")
        elif paper.section(anchor) is None:
            raise SchemaError(f"section anchor {anchor} not in {pid}")
        expected_doi = paper.canonical_doi if kind in DOI_KINDS else None
        if r["canonical_doi"] != expected_doi:
            raise SchemaError("canonical_doi")
    else:
        if r["paper_id"] is not None or r["paper_version"] is not None or r["canonical_doi"] is not None:
            raise SchemaError("non-paper result carries paper fields")
    if (kind == "paper_md") != (r["derivative_of"] is None):
        raise SchemaError("derivative_of")
    url = r["source_url"]
    if url is not None and not str(url).startswith(C.PAGES_BASE):
        raise SchemaError("source_url")


def envelope(corpus: C.Corpus, status: str, results: Iterable[dict] = (), candidates: Iterable[dict] = (),
             limitations: Iterable[str] = (), extra: Mapping[str, Any] | None = None) -> dict:
    """全ツール共通の外枠。status が ok でなければ results は空（SPEC §4）。"""
    results = list(results)
    candidates = list(candidates)
    lims = sorted(set(limitations))
    if status not in STATUSES:
        raise SchemaError(f"status {status}")
    if status != "ok" and results:
        raise SchemaError("results must be empty unless status is ok")
    for r in (*results, *candidates):
        validate_result(corpus, r)
    for lim in lims:
        if not _LIMITATION_RE.match(lim):
            raise SchemaError(f"limitation format: {lim!r}")
    env = {
        "schema_version": SCHEMA_VERSION,
        "corpus_version": C.CORPUS_VERSION,
        "source_commit": C.CORPUS_COMMIT,
        "bundle_hash": corpus.bundle.bundle_hash,
        "status": status,
        "results": results,
        "candidates": candidates,
        "limitations": lims,
    }
    for k, v in (extra or {}).items():
        if k in env:
            raise SchemaError(f"extra key {k} collides")
        env[k] = thaw(v)
    return env


def validate_envelope(obj: Mapping[str, Any]) -> None:
    """JSON から戻した応答の形を確かめる（M01・テスト用。jsonschema に依存しない）。"""
    for k in ENVELOPE_KEYS:
        if k not in obj:
            raise SchemaError(f"missing {k}")
    allowed_extra = {"match", "normalization_applied", "templates"}
    if set(obj) - set(ENVELOPE_KEYS) - allowed_extra:
        raise SchemaError(f"unexpected keys {sorted(set(obj) - set(ENVELOPE_KEYS) - allowed_extra)}")
    if obj["schema_version"] != SCHEMA_VERSION or obj["corpus_version"] != C.CORPUS_VERSION:
        raise SchemaError("versions")
    if obj["source_commit"] != C.CORPUS_COMMIT or obj["status"] not in STATUSES:
        raise SchemaError("commit/status")
    if obj["status"] != "ok" and obj["results"]:
        raise SchemaError("results must be empty unless ok")
    for r in (*obj["results"], *obj["candidates"]):
        if tuple(sorted(r)) != tuple(sorted(RESULT_KEYS)) or r["source_kind"] not in SOURCE_KINDS:
            raise SchemaError("result shape")
    if list(obj["limitations"]) != sorted(set(obj["limitations"])):
        raise SchemaError("limitations must be sorted and unique")
