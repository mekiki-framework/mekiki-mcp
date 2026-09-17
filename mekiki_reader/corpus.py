"""同梱コーパスの読込と起動時検査（施工段階1）。

標準ライブラリだけを使い、gradio を import しない。起動時に一度だけ data/ を読み、
以後はメモリ上の値だけを使う。検査の順序と失敗の種類は docs/rules/BUNDLE.md、
行・言語・節・英訳対応の規則は docs/rules/ の LINES・LANG・SECTION・T4MAP に記す。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
BUNDLE_MANIFEST = "bundle_manifest.json"

# 版固定（Q01・Q03）。main は読みに行かない。
CORPUS_REPOSITORY = "https://github.com/mekiki-framework/mekiki-framework.github.io"
CORPUS_GIT_REF = "refs/tags/v3.5.0"
CORPUS_REF_TYPE = "lightweight-tag"
CORPUS_COMMIT = "67480613108cf72c29d5691e3d7a6c7e6553eb9b"
CORPUS_TREE = "7c50a4fc2bf20f1529aebe8a8b7898e26332f1a1"
CORPUS_VERSION = "3.5.0"
PAGES_BASE = "https://mekiki-framework.github.io/"  # 返す文字列としてだけ使う（取得しない）
RAW_BASE = f"https://raw.githubusercontent.com/mekiki-framework/mekiki-framework.github.io/{CORPUS_COMMIT}/"

# 同梱許可一覧：SPEC §3 の16本＋LICENSE・CITATION.md（Q06・Q07）。
ALLOWED_PATHS: tuple[str, ...] = tuple(sorted((
    "source_manifest.json",
    "papers/T1.md",
    "papers/T2.md",
    "papers/T3.md",
    "papers/T4.md",
    "papers/T5.md",
    "THEORY_MAP.md",
    "FOR_AI_READERS.md",
    "SOURCE_INDEX.md",
    "claims/t5.json",
    "T5_CLAIM_STATUS.md",
    "tests/reading_cases.json",
    "AI_READING_TESTS.md",
    "translations/T4.en.md",
    "translations/T4.en.manifest.json",
    "llms.txt",
    "LICENSE",
    "CITATION.md",
)))

# data/bundle_manifest.json のバイト列の SHA-256（Q03。事故検出用で、改竄耐性は主張しない）。
EXPECTED_BUNDLE_SHA256 = "40a09c5ba422582c951928f873f5729a420514a46409359559d7e6123c1224d5"

BUNDLE_RULE = "BUNDLE-1.0.0"
BUNDLE_FORMAT = "mekiki-reader-bundle-manifest"
BUNDLE_FORMAT_VERSION = 1  # BUNDLE 規則の MAJOR と一致させる
LINES_RULE = "LINES-1.0.0"
LANG_RULE = "LANG-1.0.0"
SECTION_RULE = "SECTION-1.0.0"
T4MAP_RULE = "T4MAP-1.0.0"

PAPER_IDS: tuple[str, ...] = ("T1", "T2", "T3", "T4", "T5")
# LANG-1.0.0：原文の言語（Q21・Q22）。ガイド類は en。
PAPER_LANGUAGE: Mapping[str, str] = MappingProxyType(
    {"T1": "en", "T2": "en", "T3": "en", "T4": "ja", "T5": "en"}
)
GUIDE_LANGUAGE = "en"

T5_LEDGER_PATH = "claims/t5.json"
READING_CASES_PATH = "tests/reading_cases.json"
SOURCE_MANIFEST_PATH = "source_manifest.json"
T4_PATH = "papers/T4.md"
T4EN_PATH = "translations/T4.en.md"
T4EN_MANIFEST_PATH = "translations/T4.en.manifest.json"

BUNDLE_ERROR_KINDS = frozenset({
    "manifest_invalid",
    "bundle_hash_mismatch",
    "disallowed",
    "extra",
    "missing",
    "not_regular",
    "size_mismatch",
    "hash_mismatch",
    "internal_mismatch",
    "index_invalid",
})

_HEADING_RE = re.compile(r"^(#{1,6}) (.+)$")
_MARKER_RE = re.compile(r"^<!-- t4-source-unit:(\d+) -->\s*$")
_TN_OPEN_RE = re.compile(r'^<details class="translation-note" id="(tn-\d+)">$')
_CLAIM_ID_RE = re.compile(r"^T5-[A-Z]+[0-9]+$")
_CASE_ID_RE = re.compile(r"^R[0-9]{2}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


class BundleError(Exception):
    """起動を拒否する検査の失敗。kind は BUNDLE_ERROR_KINDS のいずれか。"""

    def __init__(self, kind: str, path: str | None = None, detail: str = "") -> None:
        if kind not in BUNDLE_ERROR_KINDS:
            raise ValueError(f"unknown BundleError kind: {kind}")
        self.kind = kind
        self.path = path
        self.detail = detail
        super().__init__(f"{kind}: {path or '-'}{': ' + detail if detail else ''}")


# ---------------------------------------------------------------- データ型


@dataclass(frozen=True)
class FileEntry:
    path: str
    bytes: int
    git_blob_sha1: str
    sha256: str


@dataclass(frozen=True)
class CorpusRef:
    repository: str
    git_ref: str
    ref_type: str
    commit: str
    tree: str
    corpus_version: str


@dataclass(frozen=True)
class BundleManifest:
    corpus: CorpusRef
    files: tuple[FileEntry, ...]
    not_bundled_references: tuple[str, ...]
    bundle_hash: str


@dataclass(frozen=True)
class Section:
    paper_id: str
    id: str
    title: str
    level: int
    line_start: int
    line_end: int
    parent_id: str | None
    child_ids: tuple[str, ...]
    heading_only: bool


@dataclass(frozen=True)
class Paper:
    paper_id: str
    title: str
    alternate_title: str | None
    preprint_version: str
    canonical_doi: str
    language: str
    path: str
    sha256: str
    lines: tuple[str, ...]
    sections: tuple[Section, ...]

    def section(self, section_id: str) -> Section | None:
        for s in self.sections:
            if s.id == section_id:
                return s
        return None

    def section_for_line(self, line: int) -> Section | None:
        for s in self.sections:
            if s.line_start <= line <= s.line_end:
                return s
        return None


@dataclass(frozen=True)
class TranslationUnit:
    source_line: int
    source_end_line: int
    source_kind: str
    treatment: str
    section: str | None  # manifest の記録どおり（節の決定には使わない。T4MAP）
    target_id: str | None
    t_line_start: int | None
    t_line_end: int | None
    source_sha256: str
    segment_sha256: str | None
    derived_anchor: str  # sourceLine を T4 の節範囲に当てて決めた節 id
    description: str | None


@dataclass(frozen=True)
class TranslatorNote:
    id: str
    line_start: int
    line_end: int
    unit_source_line: int


@dataclass(frozen=True)
class TranslationIndex:
    units: tuple[TranslationUnit, ...]
    notes: tuple[TranslatorNote, ...]
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Corpus:
    bundle: BundleManifest
    raw: Mapping[str, bytes]
    texts: Mapping[str, str]
    lines: Mapping[str, tuple[str, ...]]
    source_manifest: Mapping[str, Any]
    papers: Mapping[str, Paper]
    ledger: Mapping[str, Any]
    reading_cases: Mapping[str, Any]
    t4en_manifest: Mapping[str, Any]
    t4en: TranslationIndex


# ---------------------------------------------------------------- 小道具


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# LINES-1.0.0：空行＝次の文字だけからなる行（空文字を含む）。str.strip() は Unicode の版に依存するので使わない。
BLANK_CHARS = frozenset(map(chr, (0x09, 0x0D, 0x20, 0xA0, 0x200B, 0x202F, 0x205F, 0x2060, 0x3000, 0xFEFF,
                                  *range(0x2000, 0x200B))))


def is_blank(s: str) -> bool:
    return all(c in BLANK_CHARS for c in s)


def split_lines(text: str) -> tuple[str, ...]:
    """LINES-1.0.0：LF で分け、末尾の空要素を1個だけ除く。"""
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return tuple(parts)


def canonical_manifest_bytes(obj: Mapping[str, Any]) -> bytes:
    """BUNDLE-1.0.0 の直列化：キー整列・非 ASCII はそのまま・字下げ2・末尾 LF 1個。"""
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def is_safe_relpath(p: object) -> bool:
    if not isinstance(p, str) or not p or "\\" in p or "\0" in p:
        return False
    if p.startswith("/"):
        return False
    parts = p.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return str(PurePosixPath(p)) == p


def _freeze(obj: Any) -> Any:
    if isinstance(obj, dict):
        return MappingProxyType({k: _freeze(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return tuple(_freeze(v) for v in obj)
    return obj


def _read_regular(path: Path, rel: str) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        raise BundleError("missing", rel) from None
    except OSError as e:
        raise BundleError("not_regular", rel, str(e.strerror)) from None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise BundleError("not_regular", rel)
        chunks = []
        while True:
            b = os.read(fd, 1 << 20)
            if not b:
                break
            chunks.append(b)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _load_json(raw: bytes, rel: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise BundleError("index_invalid", rel, f"json: {e}") from None


def _decode(raw: bytes, rel: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise BundleError("index_invalid", rel, f"utf-8: {e}") from None


def _find_line_span(text: str, quote: str) -> tuple[int, int, int]:
    """quote の出現回数と、一意なら 1 始まりの開始行・終了行を返す。"""
    count = text.count(quote)
    if count != 1:
        return count, 0, 0
    offset = text.index(quote)
    start = text.count("\n", 0, offset) + 1
    return 1, start, start + quote.count("\n")


# ---------------------------------------------------------------- ①〜④ bundle


def parse_bundle_manifest(raw: bytes, bundle_hash: str) -> BundleManifest:
    """② 形式・許可一覧の検査。失敗は manifest_invalid か disallowed。"""
    rel = BUNDLE_MANIFEST
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise BundleError("manifest_invalid", rel, f"json: {e}") from None
    if not isinstance(obj, dict):
        raise BundleError("manifest_invalid", rel, "top level is not an object")
    if canonical_manifest_bytes(obj) != raw:
        raise BundleError("manifest_invalid", rel, "not in canonical serialization (BUNDLE-1.0.0)")
    expected_keys = {"format", "format_version", "corpus", "hash_algorithm", "files", "not_bundled_references"}
    if set(obj) != expected_keys:
        raise BundleError("manifest_invalid", rel, f"keys {sorted(obj)}")
    if obj["format"] != BUNDLE_FORMAT or obj["format_version"] != BUNDLE_FORMAT_VERSION:
        raise BundleError("manifest_invalid", rel, "format")
    if obj["hash_algorithm"] != "sha256":
        raise BundleError("manifest_invalid", rel, "hash_algorithm")
    expected_corpus = {
        "repository": CORPUS_REPOSITORY,
        "git_ref": CORPUS_GIT_REF,
        "ref_type": CORPUS_REF_TYPE,
        "commit": CORPUS_COMMIT,
        "tree": CORPUS_TREE,
        "corpus_version": CORPUS_VERSION,
    }
    if obj["corpus"] != expected_corpus:
        raise BundleError("manifest_invalid", rel, "corpus reference")
    files = obj["files"]
    if not isinstance(files, list):
        raise BundleError("manifest_invalid", rel, "files")
    entries: list[FileEntry] = []
    for f in files:
        if not isinstance(f, dict) or set(f) != {"path", "bytes", "git_blob_sha1", "sha256"}:
            raise BundleError("manifest_invalid", rel, "file entry keys")
        p = f["path"]
        if not is_safe_relpath(p) or p == BUNDLE_MANIFEST:
            raise BundleError("manifest_invalid", rel, f"path {p!r}")
        if (not isinstance(f["bytes"], int) or isinstance(f["bytes"], bool) or f["bytes"] < 0
                or not isinstance(f["git_blob_sha1"], str) or not _HEX40_RE.match(f["git_blob_sha1"])
                or not isinstance(f["sha256"], str) or not _HEX64_RE.match(f["sha256"])):
            raise BundleError("manifest_invalid", rel, f"file entry values for {p}")
        entries.append(FileEntry(p, f["bytes"], f["git_blob_sha1"], f["sha256"]))
    paths = [e.path for e in entries]
    if len(set(paths)) != len(paths):
        raise BundleError("manifest_invalid", rel, "duplicate path")
    if paths != sorted(paths):
        raise BundleError("manifest_invalid", rel, "files not sorted by path")
    disallowed = sorted(set(paths) - set(ALLOWED_PATHS))
    if disallowed:
        raise BundleError("disallowed", disallowed[0])
    lacking = sorted(set(ALLOWED_PATHS) - set(paths))
    if lacking:
        raise BundleError("manifest_invalid", rel, f"allowed path not listed: {lacking[0]}")
    refs = obj["not_bundled_references"]
    if (not isinstance(refs, list) or not all(is_safe_relpath(r) for r in refs)
            or refs != sorted(set(refs)) or set(refs) & set(ALLOWED_PATHS)):
        raise BundleError("manifest_invalid", rel, "not_bundled_references")
    c = obj["corpus"]
    return BundleManifest(
        corpus=CorpusRef(c["repository"], c["git_ref"], c["ref_type"], c["commit"], c["tree"], c["corpus_version"]),
        files=tuple(entries),
        not_bundled_references=tuple(refs),
        bundle_hash=bundle_hash,
    )


def check_tree(data_dir: Path, files: tuple[FileEntry, ...]) -> None:
    """③ 欠落・通常ファイル以外・余剰の検査。"""
    paths = {e.path for e in files}
    parent_dirs = {str(a) for p in paths for a in PurePosixPath(p).parents if str(a) != "."}
    for p in sorted(paths):
        # 親ディレクトリが symlink などでないこと
        for anc in reversed(PurePosixPath(p).parents):
            if str(anc) == ".":
                continue
            try:
                st = os.lstat(data_dir / str(anc))
            except FileNotFoundError:
                raise BundleError("missing", p) from None
            if not stat.S_ISDIR(st.st_mode):
                raise BundleError("not_regular", str(anc))
        try:
            st = os.lstat(data_dir / p)
        except FileNotFoundError:
            raise BundleError("missing", p) from None
        if not stat.S_ISREG(st.st_mode):
            raise BundleError("not_regular", p)
    extras: list[str] = []
    for dirpath, dirnames, filenames in os.walk(data_dir, followlinks=False):
        dirnames.sort()
        for name in sorted(dirnames + filenames):
            full = Path(dirpath) / name
            rel = full.relative_to(data_dir).as_posix()
            st = os.lstat(full)
            if stat.S_ISDIR(st.st_mode):
                if rel not in parent_dirs:
                    extras.append(rel)
            elif rel != BUNDLE_MANIFEST and rel not in paths:
                extras.append(rel)
    if extras:
        raise BundleError("extra", sorted(extras)[0])


def read_bundle_files(data_dir: Path, files: tuple[FileEntry, ...]) -> dict[str, bytes]:
    """④ バイト数・SHA-256・git blob の照合。読んだバイト列だけを以後使う。"""
    raw: dict[str, bytes] = {}
    for e in files:
        data = _read_regular(data_dir / e.path, e.path)
        if len(data) != e.bytes:
            raise BundleError("size_mismatch", e.path, f"{len(data)} != {e.bytes}")
        if sha256_hex(data) != e.sha256:
            raise BundleError("hash_mismatch", e.path, "sha256")
        if git_blob_sha1(data) != e.git_blob_sha1:
            raise BundleError("hash_mismatch", e.path, "git blob")
        raw[e.path] = data
    return raw


# ---------------------------------------------------------------- ⑤ 内部の記録


def verify_internal_hashes(
    raw: Mapping[str, bytes],
    source_manifest: Mapping[str, Any],
    ledger: Mapping[str, Any],
    t4en_manifest: Mapping[str, Any],
) -> None:
    """コーパス内に記録されたハッシュ・バイト数・行数を同梱ファイルと照合する（internal_mismatch）。

    同梱しないファイルの記録（統合MD・HTML・inputs の外部ファイル）は照合しない。
    """
    try:
        _verify_internal_hashes(raw, source_manifest, ledger, t4en_manifest)
    except (KeyError, TypeError, AttributeError) as e:
        raise BundleError("index_invalid", None, f"record structure: {e!r}") from None


def _lines_of(raw: Mapping[str, bytes], rel: str) -> tuple[str, ...]:
    return split_lines(_decode(raw[rel], rel))


def _verify_internal_hashes(raw, src, ledger, t4m) -> None:
    def need(rel: str, where: str) -> bytes:
        if rel not in raw:
            raise BundleError("internal_mismatch", SOURCE_MANIFEST_PATH, f"{where} refers to unbundled {rel}")
        return raw[rel]

    if src["corpus_version"] != CORPUS_VERSION:
        raise BundleError("internal_mismatch", SOURCE_MANIFEST_PATH, "corpus_version")
    for p in src["papers"]:
        rel = p["markdown"]
        data = need(rel, f"papers[{p['paper']}]")
        if sha256_hex(data) != p["sha256"]:
            raise BundleError("internal_mismatch", rel, "source_manifest papers[].sha256")
        if len(data) != p["bytes"]:
            raise BundleError("internal_mismatch", rel, "source_manifest papers[].bytes")
        if len(_lines_of(raw, rel)) != p["lines"]:
            raise BundleError("internal_mismatch", rel, "source_manifest papers[].lines")
    frozen = src["inputs"]["release_3_5_0_inputs"]["frozen_text_sha256"]
    for rel in sorted(frozen):
        if rel in raw and sha256_hex(raw[rel]) != frozen[rel]:
            raise BundleError("internal_mismatch", rel, "frozen_text_sha256")

    led_src = ledger["source_path"]
    if sha256_hex(need(led_src, "claims")) != ledger["source_sha256"]:
        raise BundleError("internal_mismatch", T5_LEDGER_PATH, "source_sha256")
    for c in ledger["claims"]:
        quotes = [(c["source_quote"], c["source_locator"])]
        quotes += [(a["quote"], a["source_locator"]) for a in c.get("additional_source_quotes", [])]
        for q, loc in quotes:
            if sha256_hex(q.encode("utf-8")) != loc["quote_sha256"]:
                raise BundleError("internal_mismatch", T5_LEDGER_PATH, f"quote_sha256 of {c['id']}")

    s_rel = t4m["source"]["path"]
    if sha256_hex(need(s_rel, "T4.en source")) != t4m["source"]["sha256"]:
        raise BundleError("internal_mismatch", T4EN_MANIFEST_PATH, "source.sha256")
    e_rel = t4m["translation"]["markdown"]
    if sha256_hex(need(e_rel, "T4.en translation")) != t4m["translation"]["sha256"]:
        raise BundleError("internal_mismatch", T4EN_MANIFEST_PATH, "translation.sha256")
    src_lines = _lines_of(raw, s_rel)
    en_lines = _lines_of(raw, e_rel)
    for u in t4m["sourceUnits"]:
        s, e = u["sourceLine"], u["sourceEndLine"]
        if not (1 <= s <= e <= len(src_lines)):
            raise BundleError("internal_mismatch", T4EN_MANIFEST_PATH, f"sourceLine range {s}-{e}")
        if sha256_hex("\n".join(src_lines[s - 1:e]).encode("utf-8")) != u["sourceSha256"]:
            raise BundleError("internal_mismatch", T4EN_MANIFEST_PATH, f"sourceSha256 of unit {s}")
        if "translationSegmentSha256" in u:
            ts, te = u["translationLineStart"], u["translationLineEnd"]
            if not (1 <= ts <= te <= len(en_lines)):
                raise BundleError("internal_mismatch", T4EN_MANIFEST_PATH, f"translation range {ts}-{te}")
            seg = "\n".join(en_lines[ts - 1:te]) + "\n"
            if sha256_hex(seg.encode("utf-8")) != u["translationSegmentSha256"]:
                raise BundleError("internal_mismatch", T4EN_MANIFEST_PATH, f"translationSegmentSha256 of unit {s}")


# ---------------------------------------------------------------- ⑥ 索引


def build_section_index(source_manifest: Mapping[str, Any], texts: Mapping[str, str]) -> dict[str, Paper]:
    """SECTION-1.0.0：節は source_manifest の記録をそのまま使い、親は直前の水準の小さい節。"""
    try:
        identity = source_manifest["inputs"]["release_3_5_0_inputs"]["canonical_identity"]
        papers: dict[str, Paper] = {}
        for p in source_manifest["papers"]:
            pid = p["paper"]
            if pid not in PAPER_IDS or pid in papers:
                raise BundleError("index_invalid", SOURCE_MANIFEST_PATH, f"paper id {pid!r}")
            rel = p["markdown"]
            lines = split_lines(texts[rel])
            raw_sections = list(p["sections"])
            parents: list[str | None] = []
            stack: list[tuple[int, str]] = []
            for s in raw_sections:
                while stack and stack[-1][0] >= s["level"]:
                    stack.pop()
                parents.append(stack[-1][1] if stack else None)
                stack.append((s["level"], s["id"]))
            sections = []
            for s, parent in zip(raw_sections, parents):
                children = tuple(c["id"] for c, cp in zip(raw_sections, parents) if cp == s["id"])
                body = [n for n in range(s["line_start"], s["line_end"] + 1)
                        if 1 <= n <= len(lines) and not is_blank(lines[n - 1])]
                sections.append(Section(
                    paper_id=pid, id=s["id"], title=s["title"], level=s["level"],
                    line_start=s["line_start"], line_end=s["line_end"],
                    parent_id=parent, child_ids=children,
                    heading_only=body == [s["line_start"]],
                ))
            ident = identity[pid]
            papers[pid] = Paper(
                paper_id=pid,
                title=ident["name"],
                alternate_title=ident.get("alternateName"),
                preprint_version=p["preprint_version"],
                canonical_doi=p["canonical_doi"],
                language=PAPER_LANGUAGE[pid],
                path=rel,
                sha256=p["sha256"],
                lines=lines,
                sections=tuple(sections),
            )
            if ident["sameAs"] != p["canonical_doi"] or ident["version"] != p["preprint_version"]:
                raise BundleError("index_invalid", SOURCE_MANIFEST_PATH, f"canonical_identity of {pid}")
    except (KeyError, TypeError) as e:
        raise BundleError("index_invalid", SOURCE_MANIFEST_PATH, f"structure: {e!r}") from None
    if tuple(sorted(papers)) != PAPER_IDS:
        raise BundleError("index_invalid", SOURCE_MANIFEST_PATH, "papers are not T1..T5")
    return papers


def validate_section_index(paper: Paper, text: str) -> None:
    """D04①：節の id・見出し・範囲の連続・行数の検査（index_invalid）。"""
    rel = paper.path
    lines = paper.lines
    if len(lines) != len(text.splitlines()):
        raise BundleError("index_invalid", rel, "LINES-1.0.0 count differs from splitlines()")
    secs = paper.sections
    if not secs:
        raise BundleError("index_invalid", rel, "no sections")
    ids = [s.id for s in secs]
    if len(set(ids)) != len(ids):
        raise BundleError("index_invalid", rel, "duplicate section id")
    if secs[0].line_start != 1 or secs[-1].line_end != len(lines):
        raise BundleError("index_invalid", rel, "sections do not cover the file")
    for a, b in zip(secs, secs[1:]):
        if b.line_start != a.line_end + 1:
            raise BundleError("index_invalid", rel, f"gap or overlap between {a.id} and {b.id}")
    heading_lines = set()
    for n, line in enumerate(lines, 1):
        if _HEADING_RE.match(line):
            heading_lines.add(n)
    if heading_lines != {s.line_start for s in secs}:
        raise BundleError("index_invalid", rel, "heading lines differ from section starts")
    for s in secs:
        if not (1 <= s.level <= 6) or s.line_start > s.line_end:
            raise BundleError("index_invalid", rel, f"section {s.id} range/level")
        m = _HEADING_RE.match(lines[s.line_start - 1])
        if not m or len(m.group(1)) != s.level or m.group(2) != s.title:
            raise BundleError("index_invalid", rel, f"heading of {s.id}")


def build_translation_index(
    t4en_manifest: Mapping[str, Any], t4: Paper, en_lines: tuple[str, ...]
) -> TranslationIndex:
    """T4MAP-1.0.0：英訳 unit の節は sourceLine を T4 の節範囲に当てて決める（unit.section は使わない）。"""
    try:
        units = []
        for u in t4en_manifest["sourceUnits"]:
            sec = t4.section_for_line(u["sourceLine"])
            if sec is None:
                raise BundleError("index_invalid", T4EN_MANIFEST_PATH, f"unit {u['sourceLine']} outside sections")
            units.append(TranslationUnit(
                source_line=u["sourceLine"],
                source_end_line=u["sourceEndLine"],
                source_kind=u["sourceKind"],
                treatment=u["treatment"],
                section=u.get("section"),
                target_id=u.get("targetId"),
                t_line_start=u.get("translationLineStart"),
                t_line_end=u.get("translationLineEnd"),
                source_sha256=u["sourceSha256"],
                segment_sha256=u.get("translationSegmentSha256"),
                derived_anchor=sec.id,
                description=u.get("description"),
            ))
    except (KeyError, TypeError) as e:
        raise BundleError("index_invalid", T4EN_MANIFEST_PATH, f"structure: {e!r}") from None
    notes = []
    n = 0
    while n < len(en_lines):
        m = _TN_OPEN_RE.match(en_lines[n])
        if m:
            start = n + 1
            end = None
            for k in range(n + 1, len(en_lines)):
                if en_lines[k] == "</details>":
                    end = k + 1
                    break
                if en_lines[k].startswith("<details"):
                    break
            if end is None:
                raise BundleError("index_invalid", T4EN_PATH, f"unclosed translator note {m.group(1)}")
            owner = [u for u in units if u.t_line_start is not None and u.t_line_start <= start and end <= u.t_line_end]
            if len(owner) != 1:
                raise BundleError("index_invalid", T4EN_PATH, f"translator note {m.group(1)} not inside one unit")
            notes.append(TranslatorNote(m.group(1), start, end, owner[0].source_line))
            n = end
        else:
            n += 1
    return TranslationIndex(units=tuple(units), notes=tuple(notes), lines=en_lines)


def validate_translation_index(
    idx: TranslationIndex, t4en_manifest: Mapping[str, Any], t4: Paper
) -> None:
    """D04④：英訳の位置対応・マーカー・訳注の構造検査（index_invalid）。ハッシュは⑤で照合済み。"""
    rel = T4EN_MANIFEST_PATH
    m = t4en_manifest
    try:
        header_ok = (
            m["format"] == "mekiki-translation-manifest"
            and m["translationId"] == "T4.en"
            and m["corpusVersion"] == CORPUS_VERSION
            and m["originalLanguage"] == "ja"
            and m["inLanguage"] == "en"
            and m["source"]["path"] == T4_PATH
            and m["translation"]["markdown"] == T4EN_PATH
            and m["source"]["doi"] == t4.canonical_doi
            and m["source"]["preprintVersion"] == t4.preprint_version
        )
    except (KeyError, TypeError):
        header_ok = False
    if not header_ok:
        raise BundleError("index_invalid", rel, "manifest header")
    units = idx.units
    for a, b in zip(units, units[1:]):
        if not a.source_end_line < b.source_line:
            raise BundleError("index_invalid", rel, f"source units not ordered/disjoint at {b.source_line}")
    covered = {n for u in units for n in range(u.source_line, u.source_end_line + 1)}
    nonblank = {n for n, line in enumerate(t4.lines, 1) if not is_blank(line)}
    if not nonblank <= covered:
        raise BundleError("index_invalid", rel, f"source line {min(nonblank - covered)} not covered")
    positioned = [u for u in units if u.t_line_start is not None]
    for u in units:
        has_pos = (u.t_line_start is not None, u.t_line_end is not None, u.segment_sha256 is not None, u.target_id is not None)
        if len(set(has_pos)) != 1:
            raise BundleError("index_invalid", rel, f"unit {u.source_line} has partial translation keys")
        if not has_pos[0] and u.treatment not in ("wrapper", "separator"):
            raise BundleError("index_invalid", rel, f"unit {u.source_line} without position is {u.treatment}")
        end_sec = t4.section_for_line(u.source_end_line)
        if end_sec is None or end_sec.id != u.derived_anchor:
            raise BundleError("index_invalid", rel, f"unit {u.source_line} spans sections")
    en = idx.lines
    for a, b in zip(positioned, positioned[1:]):
        if b.t_line_start != a.t_line_end + 1:
            raise BundleError("index_invalid", rel, f"translation ranges not contiguous at unit {b.source_line}")
    for u in positioned:
        mm = _MARKER_RE.match(en[u.t_line_start - 1])
        if not mm or int(mm.group(1)) != u.source_line:
            raise BundleError("index_invalid", T4EN_PATH, f"marker of unit {u.source_line}")
        seg = "\n".join(en[u.t_line_start - 1:u.t_line_end])
        if f'id="{u.target_id}"' not in seg and "{#" + u.target_id + "}" not in seg:
            raise BundleError("index_invalid", T4EN_PATH, f"targetId {u.target_id} not in its range")
    markers = sum(1 for line in en if _MARKER_RE.match(line))
    if markers != len(positioned):
        raise BundleError("index_invalid", T4EN_PATH, "marker count differs from positioned units")
    note_ids = [t.id for t in idx.notes]
    if len(set(note_ids)) != len(note_ids):
        raise BundleError("index_invalid", T4EN_PATH, "duplicate translator note id")
    for t in idx.notes:
        owner = next(u for u in units if u.source_line == t.unit_source_line)
        if owner.treatment != "translated":
            raise BundleError("index_invalid", T4EN_PATH, f"translator note {t.id} inside {owner.treatment} unit")
    targets = [u.target_id for u in positioned]
    if (len(idx.notes) != m["translatorNotes"]
            or sum(1 for x in targets if x.startswith("author-note-")) != m["originalAuthorNotes"]
            or sum(1 for x in targets if x.startswith("ref-")) != m["referenceRecords"]):
        raise BundleError("index_invalid", rel, "note/reference counts differ from manifest")


def _t5_anchor(section: str) -> str:
    return "t5-" + section.replace(".", "-")


def validate_ledger(ledger: Mapping[str, Any], papers: Mapping[str, Paper], texts: Mapping[str, str]) -> None:
    """D04②：主張台帳の引用位置・節・URL の構造検査（index_invalid）。"""
    rel = T5_LEDGER_PATH
    t5 = papers["T5"]
    try:
        if (ledger["format"] != "mekiki-claim-ledger" or ledger["paper"] != "T5"
                or ledger["source_path"] != t5.path
                or ledger["canonical_doi"] != t5.canonical_doi
                or ledger["preprint_version"] != t5.preprint_version):
            raise BundleError("index_invalid", rel, "ledger header")
        text = texts[t5.path]
        ids = [c["id"] for c in ledger["claims"]]
        if len(set(ids)) != len(ids) or not all(_CLAIM_ID_RE.match(i) for i in ids):
            raise BundleError("index_invalid", rel, "claim ids")
        allowed_loc = {"path", "line_start", "line_end", "section", "section_url", "quote_sha256", "canonical_doi", "footnote_url"}
        for c in ledger["claims"]:
            if not {"id", "status", "claim", "section", "source_quote", "not_claimed", "source_locator"} <= set(c):
                raise BundleError("index_invalid", rel, f"{c.get('id')} lacks required keys")
            if not isinstance(c["status"], str) or not c["status"]:
                raise BundleError("index_invalid", rel, f"{c['id']} status")
            if not isinstance(c["not_claimed"], list) or not all(isinstance(x, str) for x in c["not_claimed"]):
                raise BundleError("index_invalid", rel, f"{c['id']} not_claimed")
            quotes = [(c["section"], c["source_quote"], c["source_locator"], "footnote" in c)]
            quotes += [(a["section"], a["quote"], a["source_locator"], False) for a in c.get("additional_source_quotes", [])]
            for section, quote, loc, may_footnote in quotes:
                if not set(loc) <= allowed_loc or ("footnote_url" in loc and not may_footnote):
                    raise BundleError("index_invalid", rel, f"{c['id']} locator keys")
                if "footnote_url" in loc and loc["footnote_url"] != f"{PAGES_BASE}papers/T5.html#fn{c['footnote']}":
                    raise BundleError("index_invalid", rel, f"{c['id']} footnote_url")
                count, start, end = _find_line_span(text, quote)
                if count != 1:
                    raise BundleError("index_invalid", rel, f"{c['id']} quote occurs {count} times")
                anchor = _t5_anchor(section)
                sec = t5.section(anchor)
                if (loc["path"] != t5.path or loc["canonical_doi"] != t5.canonical_doi
                        or loc["section"] != section
                        or (loc["line_start"], loc["line_end"]) != (start, end)
                        or sec is None or not (sec.line_start <= start and end <= sec.line_end)
                        or loc["section_url"] != f"{PAGES_BASE}papers/T5.html#{anchor}"):
                    raise BundleError("index_invalid", rel, f"{c['id']} locator ({anchor})")
    except (KeyError, TypeError) as e:
        raise BundleError("index_invalid", rel, f"structure: {e!r}") from None


def validate_reading_cases(
    cases: Mapping[str, Any], papers: Mapping[str, Paper], texts: Mapping[str, str], ledger: Mapping[str, Any]
) -> None:
    """D04③：読解試験の追加根拠の位置と claim_ids の実在（index_invalid）。"""
    rel = READING_CASES_PATH
    try:
        if cases["format"] != "mekiki-reading-probes":
            raise BundleError("index_invalid", rel, "format")
        claim_ids = {c["id"] for c in ledger["claims"]}
        ids = [c["id"] for c in cases["cases"]]
        if len(set(ids)) != len(ids) or not all(_CASE_ID_RE.match(i) for i in ids):
            raise BundleError("index_invalid", rel, "case ids")
        for c in cases["cases"]:
            if not set(c["claim_ids"]) <= claim_ids:
                raise BundleError("index_invalid", rel, f"{c['id']} unknown claim id")
            for a in c["additional_sources"]:
                paper = papers.get(a["paper"])
                if paper is None:
                    raise BundleError("index_invalid", rel, f"{c['id']} unknown paper")
                count, start, end = _find_line_span(texts[paper.path], a["quote"])
                anchor = a["paper"].lower() + "-" + a["section"].replace(".", "-")
                sec = paper.section(anchor)
                if count != 1 or sec is None or not (sec.line_start <= start and end <= sec.line_end):
                    raise BundleError("index_invalid", rel, f"{c['id']} additional source ({anchor}, {count})")
    except (KeyError, TypeError) as e:
        raise BundleError("index_invalid", rel, f"structure: {e!r}") from None


# ---------------------------------------------------------------- 入口


def load_corpus(data_dir: Path = DATA_DIR, expected_bundle_sha256: str = EXPECTED_BUNDLE_SHA256) -> Corpus:
    """起動時の読込と検査。失敗は BundleError（app.py は非ゼロで終了する）。

    data_dir と expected_bundle_sha256 はテストだけが差し替える内部引数（Q12）。
    検査順：①bundle_manifest.json のハッシュ → ②形式・許可一覧 → ③欠落・種別・余剰 →
    ④各ファイルのバイト数・ハッシュ → ⑤コーパス内部の記録 → ⑥索引。
    """
    data_dir = Path(data_dir)
    try:
        st = os.lstat(data_dir)
    except FileNotFoundError:
        raise BundleError("missing", ".") from None
    if not stat.S_ISDIR(st.st_mode):
        raise BundleError("not_regular", ".")
    manifest_raw = _read_regular(data_dir / BUNDLE_MANIFEST, BUNDLE_MANIFEST)  # ①
    bundle_hash = sha256_hex(manifest_raw)
    if bundle_hash != expected_bundle_sha256:
        raise BundleError("bundle_hash_mismatch", BUNDLE_MANIFEST, bundle_hash)
    bundle = parse_bundle_manifest(manifest_raw, bundle_hash)  # ②
    check_tree(data_dir, bundle.files)  # ③
    raw = read_bundle_files(data_dir, bundle.files)  # ④

    source_manifest = _load_json(raw[SOURCE_MANIFEST_PATH], SOURCE_MANIFEST_PATH)  # ⑤
    ledger = _load_json(raw[T5_LEDGER_PATH], T5_LEDGER_PATH)
    reading_cases = _load_json(raw[READING_CASES_PATH], READING_CASES_PATH)
    t4en_manifest = _load_json(raw[T4EN_MANIFEST_PATH], T4EN_MANIFEST_PATH)
    verify_internal_hashes(raw, source_manifest, ledger, t4en_manifest)

    texts = {p: _decode(b, p) for p, b in raw.items()}  # ⑥
    lines = {p: split_lines(t) for p, t in texts.items()}
    papers = build_section_index(source_manifest, texts)
    for pid in PAPER_IDS:
        validate_section_index(papers[pid], texts[papers[pid].path])
    t4en = build_translation_index(t4en_manifest, papers["T4"], lines[T4EN_PATH])
    validate_translation_index(t4en, t4en_manifest, papers["T4"])
    validate_ledger(ledger, papers, texts)
    validate_reading_cases(reading_cases, papers, texts, ledger)

    return Corpus(
        bundle=bundle,
        raw=MappingProxyType(dict(raw)),
        texts=MappingProxyType(texts),
        lines=MappingProxyType(lines),
        source_manifest=_freeze(source_manifest),
        papers=MappingProxyType(papers),
        ledger=_freeze(ledger),
        reading_cases=_freeze(reading_cases),
        t4en_manifest=_freeze(t4en_manifest),
        t4en=t4en,
    )


def get_lines(corpus: Corpus, path: str, line_start: int, line_end: int) -> tuple[str, ...]:
    """1 始まり・終端を含む行範囲を返す。範囲外や未同梱のパスは ValueError。"""
    if path not in corpus.lines:
        raise ValueError(f"not bundled: {path!r}")
    lines = corpus.lines[path]
    if not (isinstance(line_start, int) and isinstance(line_end, int) and 1 <= line_start <= line_end <= len(lines)):
        raise ValueError(f"line range out of bounds: {line_start}-{line_end}")
    return lines[line_start - 1:line_end]
