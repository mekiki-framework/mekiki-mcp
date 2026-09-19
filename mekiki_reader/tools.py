"""七ツール（SPEC §5）。

`Reader` は同梱コーパスと起動時に作る索引（正規化済みの行・用語対応表・パターン・ガイドの区分）を持つ。
各ツールは Reader を明示的に受け取る純関数で、ファイルも外部も読まない。同じ入力・同じデータ・同じ規則なら
同じ結果データを返す（SPEC §2.3）。規則は docs/rules/ の SEARCH・CAND・NEAR・GUIDE・LIMITS・SCHEMA・NORM。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Mapping, Sequence

from . import corpus as C
from . import normalize as N
from . import patterns as PAT
from . import prompts as PR
from . import schema as S
from . import terms as TM

# LIMITS-3.1.0（docs/rules/LIMITS.md。この層の値は 1.0.0 から変えていない。2.0.0 以降は通信層の変更）
ID_MAX = 128
QUERY_RAW_MAX = 1000
QUERY_NORM_MAX = 200
QUERY_FRAGMENTS_MAX = 8
TEXT_MAX = 2000
K_MIN, K_MAX, K_DEFAULT = 1, 20, 5
QUOTE_MIN_CHARS_CJK = 5  # 仮名・漢字を含む入力（実測：T4 の長さ5の部分文字列は出現回数の中央値が1）
QUOTE_MIN_CHARS_OTHER = 10  # それ以外（実測：英語の論文で長さ10のとき中央値が1）
QUOTE_MAX_RESULTS = 20
CAND_MAX = 5
POSITIONS_MAX = 20
DIFFS_MAX = 20
EXCERPT_RADIUS = 100
SOURCE_EXCERPT_MAX = 1000  # check_compressions の関連原文の抜粋

LIMITS_VERSION = "LIMITS-3.1.0"
SEARCH_VERSION = "SEARCH-1.1.0"
CAND_VERSION = "CAND-1.0.0"
NEAR_VERSION = "NEAR-1.0.0"
GUIDE_VERSION = "GUIDE-1.0.0"

# SEARCH-1.1.0 の区切り文字（畳み込んだ後の文字で判定する。空白は別に扱う。1.0.0 から不変）
SEPARATORS = frozenset("、。，．,.;:!?・「」『』()（）[]{}…；：！？［］｛｝") | {chr(0x22), chr(0xFF02)}
# 語境界（SEARCH-1.1.0・PATTERNS-MATCH-1.1.0 で共通）：英数字とアポストロフィを語の一部とみなし、
# ハイフンは境界とする（`ablation` が `domain-ablation` に、`playing seat` が `role-playing seat` に当たる）。
# ハイフン付きの語句そのものは、両端が境界であれば当たる（検収 E01 の観察 d・2026-09-18 著者承認）。
_WORD_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789'"

_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_CLAIM_ID_RE = re.compile(r"^T[1-5]-[A-Z]+[0-9]+$")

# GUIDE-1.0.0：part → FOR_AI_READERS.md の見出し（None は全体）
GUIDE_PARTS: tuple[tuple[str, str | None], ...] = (
    ("all", None),
    ("interpretation", "Interpretation first"),
    ("core-terms", "Core terms"),
    ("japanese-terms", "Japanese terms: preserve the paper's distinctions"),
    ("t4-languages", "T4 in two languages"),
    ("modes", "Four practical response modes"),
    ("mode-1", "Mode 1 — Deliverable"),
    ("mode-2", "Mode 2 — Learning"),
    ("mode-3", "Mode 3 — Inquiry"),
    ("mode-4", "Mode 4 — Play"),
    ("boundaries", "Application boundaries"),
)
GUIDE_PATH = "FOR_AI_READERS.md"


# ---------------------------------------------------------------- 索引


@dataclass(frozen=True)
class Line:
    """照合と検索の単位（行）。"""

    path: str
    paper_id: str
    no: int
    text: str
    quote: N.Normalized
    fold: N.Normalized
    kind: str  # paper_md | translation | translation_note
    anchor: str  # 論文の節 id、または T4.en の id（unit の targetId・訳注の id）
    unit: C.TranslationUnit | None = None
    note: C.TranslatorNote | None = None


@dataclass(frozen=True)
class Frame:
    anchor: str
    line_start: int
    line_end: int


class Reader:
    """起動時に一度だけ作る。terms と patterns はテストだけが差し替える内部引数。"""

    def __init__(self, corpus: C.Corpus, terms: Iterable[TM.TermEntry] | None = None,
                 patterns: Iterable[PAT.Pattern] | None = None) -> None:
        self.corpus = corpus
        self.terms = TM.build_term_index(TM.TERMS if terms is None else terms,
                                         TM.TERMS_VERSION if terms is None else "TERMS-TEST")
        self.patterns = PAT.validate_patterns(corpus, PAT.PATTERNS if patterns is None else patterns)
        self.patterns_version = PAT.PATTERNS_VERSION if patterns is None else "PATTERNS-TEST"
        self.paper_order = {pid: i for i, pid in enumerate(C.PAPER_IDS)}
        self.orig_lines = tuple(self._paper_lines())
        self.en_lines, self.frames = self._t4en_lines()
        self.guide_ranges = self._guide_ranges()
        self.t4en_meta = corpus.t4en_manifest

    def _paper_lines(self):
        for pid in C.PAPER_IDS:
            paper = self.corpus.papers[pid]
            for sec in paper.sections:
                for no in range(sec.line_start, sec.line_end + 1):
                    text = paper.lines[no - 1]
                    if C.is_blank(text):
                        continue
                    yield Line(paper.path, pid, no, text, N.normalize_quote(text, is_input=False),
                               N.fold_search(text, is_input=False), "paper_md", sec.id)

    def _t4en_lines(self):
        idx = self.corpus.t4en
        notes_by_line = {n: t for t in idx.notes for n in range(t.line_start, t.line_end + 1)}
        out, covered = [], set()
        for u in idx.units:
            if u.t_line_start is None:
                continue
            for no in range(u.t_line_start, u.t_line_end + 1):
                covered.add(no)
                text = idx.lines[no - 1]
                if C.is_blank(text):
                    continue
                note = notes_by_line.get(no)
                out.append(Line(C.T4EN_PATH, "T4", no, text, N.normalize_quote(text, is_input=False),
                                N.fold_search(text, is_input=False),
                                "translation_note" if note else "translation",
                                note.id if note else u.target_id, u, note))
        frames = []
        run: list[int] = []
        for no in range(1, len(idx.lines) + 2):
            if no <= len(idx.lines) and no not in covered:
                run.append(no)
                continue
            if run:
                ids = [m for n in run for m in re.findall(r"\{#([^}]+)\}", idx.lines[n - 1])]
                if len(ids) == 1:
                    frames.append(Frame(ids[0], run[0], run[-1]))
                run = []
        return tuple(out), tuple(frames)

    def _guide_ranges(self) -> dict[str, tuple[int, int, str]]:
        lines = self.corpus.lines[GUIDE_PATH]
        heads = []
        for no, text in enumerate(lines, 1):
            m = re.match(r"^(#{1,6}) (.+)$", text)
            if m:
                heads.append((no, len(m.group(1)), m.group(2)))
        ranges: dict[str, tuple[int, int, str]] = {}
        for part, title in GUIDE_PARTS:
            if title is None:
                ranges[part] = (1, len(lines), heads[0][2])
                continue
            found = [h for h in heads if h[2] == title]
            if len(found) != 1:
                raise C.BundleError("index_invalid", GUIDE_PATH, f"GUIDE heading {title!r}")
            no, level, _ = found[0]
            end = len(lines)
            for n2, l2, _t in heads:
                if n2 > no and l2 <= level:
                    end = n2 - 1
                    break
            ranges[part] = (no, end, title)
        return ranges


# ---------------------------------------------------------------- 共通の小道具


def has_lone_surrogate(value: str) -> bool:
    """孤立サロゲートを含むか（JSON の "\\udXXX" 経由で入りうる。Codex① P2-8）。

    整った Python の文字列にサロゲートは現れないので、一つでもあれば不正な入力とみなす。
    そのまま扱うと UTF-8 に直せず、応答の直列化で落ちる。
    """
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in value)


def _classify_id(value: Any) -> str:
    """'ok'・'invalid'（型・長さ・制御文字・サロゲート・パスや URL の形）・'malformed'（それ以外）。"""
    if not isinstance(value, str) or not value or len(value) > ID_MAX:
        return "invalid"
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in value):
        return "invalid"
    if has_lone_surrogate(value):
        return "invalid"
    if "/" in value or chr(0x5C) in value or ":" in value or ".." in value or value[0] in ".~":
        return "invalid"
    return "ok" if _ID_RE.match(value) else "malformed"


def _rules(*names: str) -> str:
    return "RULES: " + " ".join(names)


def _invalid(reader: Reader, reason: str, *extra: str) -> dict:
    return S.envelope(reader.corpus, "invalid_input", limitations=("INPUT: " + reason, *extra))


def _pages_url(path: str, anchor: str | None = None) -> str:
    return C.PAGES_BASE + path + (f"#{anchor}" if anchor else "")


def _paper_html(pid: str) -> str:
    return f"papers/{pid}.html"


def _excerpt(text: str, c0: int, c1: int) -> tuple[str, int, int]:
    start = max(0, c0 - EXCERPT_RADIUS)
    end = min(len(text), c1 + EXCERPT_RADIUS)
    return ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else ""), start, end


def _meta(reader: Reader, key: str) -> dict:
    return {"text": reader.t4en_meta[key], "record_path": C.T4EN_MANIFEST_PATH, "json_pointer": f"/{key}"}


def _translation_payload(reader: Reader, u: C.TranslationUnit) -> dict:
    return {
        "original_locator": {"path": C.T4_PATH, "line_start": u.source_line, "line_end": u.source_end_line,
                             "section": u.derived_anchor, "source_sha256": u.source_sha256},
        "unit": {"source_line": u.source_line, "source_kind": u.source_kind, "treatment": u.treatment,
                 "recorded_section": u.section, "target_id": u.target_id,
                 "translation_line_start": u.t_line_start, "translation_line_end": u.t_line_end},
        "translation_version": reader.t4en_meta["translationVersion"],
        "source_corpus_version": reader.t4en_meta["source"]["corpusVersion"],
        "preparation": _meta(reader, "preparation"),
        "authority": _meta(reader, "authority"),
    }


def _translation_limitations() -> tuple[str, ...]:
    return (
        "TRANSLATION: 英訳由来の結果。作成の経緯と原文との関係は payload.preparation と payload.authority（manifest の記載）を参照",
        "UNIT: 英訳の節は sourceLine を T4 の節範囲に当てて決めた（記録の unit.section は使わない）",
    )


# ---------------------------------------------------------------- 結果の組み立て


def _paper_ref(reader: Reader, pid: str, sections: bool = False) -> dict:
    corpus = reader.corpus
    paper = corpus.papers[pid]
    top = paper.sections[0]
    payload: dict[str, Any] = {
        "title": paper.title,
        "alternate_title": paper.alternate_title,
        "route": {"tool": "get_section", "paper_id": pid, "anchor": top.id},
    }
    if sections:
        idx = [p["paper"] for p in corpus.source_manifest["papers"]].index(pid)
        payload.update({
            "paper_version": paper.preprint_version,
            "canonical_doi": paper.canonical_doi,
            "language": paper.language,
            "available_editions": ["original", "en"] if pid == "T4" else ["original"],
            "line_count": len(paper.lines),
            "sections": [{"id": s.id, "title": s.title, "level": s.level, "line_start": s.line_start,
                          "line_end": s.line_end, "parent_id": s.parent_id, "child_ids": list(s.child_ids),
                          "heading_only": s.heading_only} for s in paper.sections],
            "record": {"path": C.SOURCE_MANIFEST_PATH, "json_pointer": f"/papers/{idx}"},
        })
    return S.result(corpus, source_kind="paper_md", source_path=paper.path, fragment=top.id,
                    language=paper.language, locator_=S.locator(paper.path, 1, len(paper.lines)),
                    payload=payload, paper_id=pid, section_anchor=top.id,
                    source_url=_pages_url(_paper_html(pid), top.id))


def _section_result(reader: Reader, paper: C.Paper, sec: C.Section, with_text: bool = True) -> dict:
    payload: dict[str, Any] = {
        "title": sec.title, "level": sec.level, "parent_id": sec.parent_id,
        "child_ids": list(sec.child_ids), "heading_only": sec.heading_only,
        "route": {"tool": "get_section", "paper_id": paper.paper_id, "anchor": sec.id},
    }
    if with_text:
        payload["text"] = "\n".join(paper.lines[sec.line_start - 1:sec.line_end])
        payload["is_excerpt"] = False
    return S.result(reader.corpus, source_kind="paper_md", source_path=paper.path, fragment=sec.id,
                    language=paper.language, locator_=S.locator(paper.path, sec.line_start, sec.line_end),
                    payload=payload, paper_id=paper.paper_id, section_anchor=sec.id,
                    source_url=_pages_url(_paper_html(paper.paper_id), sec.id))


def _line_result(reader: Reader, line: Line, c0: int, c1: int, payload: Mapping[str, Any]) -> dict:
    corpus = reader.corpus
    body = dict(payload)
    if line.kind == "paper_md":
        paper = corpus.papers[line.paper_id]
        return S.result(corpus, source_kind="paper_md", source_path=line.path, fragment=f"L{line.no}",
                        language=paper.language, locator_=S.locator(line.path, line.no, line.no, c0, c1),
                        payload=body, paper_id=line.paper_id, section_anchor=line.anchor,
                        source_url=_pages_url(_paper_html(line.paper_id), line.anchor))
    u = line.unit
    body.update(_translation_payload(reader, u))
    if line.kind == "translation_note":
        body["translator_note_id"] = line.note.id
        derivative = [f"{C.T4EN_PATH}#{u.target_id}"]
    else:
        derivative = [f"{C.T4_PATH}#{u.derived_anchor}"]
    return S.result(corpus, source_kind=line.kind, source_path=line.path, fragment=f"L{line.no}",
                    language="en", locator_=S.locator(line.path, line.no, line.no, c0, c1),
                    payload=body, paper_id="T4", section_anchor=line.anchor,
                    source_url=_pages_url("papers/T4.en.html", line.anchor), derivative_of=derivative)


# ---------------------------------------------------------------- 1. list_papers


def list_papers(reader: Reader) -> dict:
    results = [_paper_ref(reader, pid, sections=True) for pid in C.PAPER_IDS]
    return S.envelope(reader.corpus, "ok", results,
                      limitations=(_rules(C.SECTION_RULE, C.LANG_RULE, S.JSON_RULE),))


# ---------------------------------------------------------------- 2. get_section


def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _near(anchors: Sequence[str], query: str, n: int = CAND_MAX) -> list[str]:
    """NEAR-1.0.0：共通接頭辞の長さ↓・編集距離↑・並び順↑で上位 n 件。"""
    def prefix(a: str) -> int:
        k = 0
        while k < min(len(a), len(query)) and a[k] == query[k]:
            k += 1
        return k
    keyed = sorted((-prefix(a), _levenshtein(a, query), i, a) for i, a in enumerate(anchors))
    return [a for *_, a in keyed[:n]]


def _check_language(pid: str, language: Any) -> str | None:
    """版の選択（SPEC §5）。問題があれば理由の文字列を返す。"""
    if language is None:
        return None
    if not isinstance(language, str) or language not in S.LANGUAGES:
        return "language は None・\"ja\"・\"en\" のいずれか"
    if pid == "T4":
        return None
    return f"{pid} の版は原文（language=None）だけで、{language} 版はない"


def get_section(reader: Reader, paper_id: Any, anchor: Any, language: Any = None) -> dict:
    corpus = reader.corpus
    pcls = _classify_id(paper_id)
    if pcls == "invalid":
        return _invalid(reader, "paper_id の形式が不正（パス・URL・制御文字・長さ）")
    acls = _classify_id(anchor)
    if acls == "invalid":
        return _invalid(reader, "anchor の形式が不正（パス・URL・制御文字・長さ）")
    if pcls == "malformed" or paper_id not in corpus.papers:
        cands = [_paper_ref(reader, pid) for pid in C.PAPER_IDS]
        return S.envelope(corpus, "unknown_id", candidates=cands,
                          limitations=("NEAR: 未登録の paper_id。実在する五本を候補に挙げた", _rules(NEAR_VERSION)))
    reason = _check_language(paper_id, language)
    if reason:
        return _invalid(reader, reason)
    paper = corpus.papers[paper_id]
    if language == "en":
        return _get_section_en(reader, anchor, acls)
    sec = paper.section(anchor) if acls == "ok" else None
    if sec is None:
        near = _near([s.id for s in paper.sections], anchor)
        cands = [_section_result(reader, paper, paper.section(a), with_text=False) for a in near]
        return S.envelope(corpus, "unknown_id", candidates=cands,
                          limitations=("NEAR: 未登録の anchor。同じ論文の実在する節を候補に挙げた", _rules(NEAR_VERSION)))
    lims = [_rules(C.SECTION_RULE, C.LINES_RULE)]
    if sec.child_ids:
        lims.append("PARENT: 親節は記録された範囲だけを返す。子節は payload.child_ids から get_section で読む")
    return S.envelope(corpus, "ok", [_section_result(reader, paper, sec)], limitations=lims)


def _get_section_en(reader: Reader, anchor: str, acls: str) -> dict:
    corpus = reader.corpus
    t4 = corpus.papers["T4"]
    frame_ids = [f.anchor for f in reader.frames]
    known = [s.id for s in t4.sections] + frame_ids
    lims = [*_translation_limitations(), _rules(C.T4MAP_RULE, C.LINES_RULE)]
    if acls != "ok" or anchor not in known:
        near = _near(known, anchor)
        cands = []
        for a in near:
            if a in frame_ids:
                cands.append(_frame_result(reader, next(f for f in reader.frames if f.anchor == a), with_text=False))
            else:
                cands.append(_section_result(reader, t4, t4.section(a), with_text=False))
        return S.envelope(corpus, "unknown_id", candidates=cands,
                          limitations=("NEAR: 未登録の anchor。T4 の節と英訳の枠部分の id を候補に挙げた",
                                       _rules(NEAR_VERSION)))
    if anchor in frame_ids:
        frame = next(f for f in reader.frames if f.anchor == anchor)
        return S.envelope(corpus, "ok", [_frame_result(reader, frame)],
                          limitations=(*lims, "FRAME: 英訳にだけある枠部分（明示の要求に応じて返した）"))
    results = []
    units = [u for u in corpus.t4en.units if u.derived_anchor == anchor]
    for u in units:
        if u.t_line_start is None:
            results.append(_untranslated_unit_result(reader, u))
            continue
        for a, b, note in _segments(reader, u):
            results.append(_segment_result(reader, u, a, b, note))
    return S.envelope(corpus, "ok", results, limitations=lims)


def _segments(reader: Reader, u: C.TranslationUnit):
    """unit の英訳範囲を、訳注の区間とそれ以外の連続区間に分ける。"""
    notes = [t for t in reader.corpus.t4en.notes if u.t_line_start <= t.line_start and t.line_end <= u.t_line_end]
    cur = u.t_line_start
    for t in notes:
        if cur < t.line_start:
            yield cur, t.line_start - 1, None
        yield t.line_start, t.line_end, t
        cur = t.line_end + 1
    if cur <= u.t_line_end:
        yield cur, u.t_line_end, None


def _segment_result(reader: Reader, u: C.TranslationUnit, a: int, b: int, note: C.TranslatorNote | None) -> dict:
    corpus = reader.corpus
    lines = corpus.t4en.lines[a - 1:b]
    payload = {"text": "\n".join(lines), "is_excerpt": False, **_translation_payload(reader, u)}
    if note is not None:
        payload["translator_note_id"] = note.id
        kind, anchor, frag = "translation_note", note.id, note.id
        derivative = [f"{C.T4EN_PATH}#{u.target_id}"]
    else:
        kind, anchor, frag = "translation", u.target_id, f"L{a}-L{b}"
        derivative = [f"{C.T4_PATH}#{u.derived_anchor}"]
    return S.result(corpus, source_kind=kind, source_path=C.T4EN_PATH, fragment=frag, language="en",
                    locator_=S.locator(C.T4EN_PATH, a, b), payload=payload, paper_id="T4",
                    section_anchor=anchor, source_url=_pages_url("papers/T4.en.html", anchor),
                    derivative_of=derivative)


def _anchor_for_untranslated(reader: Reader, u: C.TranslationUnit) -> str:
    units = reader.corpus.t4en.units
    same = [x for x in units if x.derived_anchor == u.derived_anchor and x.target_id]
    if same:
        return same[0].target_id
    after = [x for x in units if x.source_line > u.source_line and x.target_id]
    return (after[0] if after else [x for x in units if x.target_id][-1]).target_id


def _untranslated_unit_result(reader: Reader, u: C.TranslationUnit) -> dict:
    corpus = reader.corpus
    i = corpus.t4en.units.index(u)
    anchor = _anchor_for_untranslated(reader, u)
    payload = {
        "description": u.description,
        "record": {"path": C.T4EN_MANIFEST_PATH, "json_pointer": f"/sourceUnits/{i}"},
        "note": "英訳側に位置を持たない unit（wrapper・separator）。description は manifest の記載",
        **_translation_payload(reader, u),
    }
    return S.result(corpus, source_kind="translation", source_path=C.T4EN_MANIFEST_PATH,
                    fragment=f"sourceUnits/{i}", language="en",
                    locator_=S.locator(C.T4EN_MANIFEST_PATH, json_pointer=f"/sourceUnits/{i}"),
                    payload=payload, paper_id="T4", section_anchor=anchor,
                    source_url=_pages_url("papers/T4.en.html", anchor),
                    derivative_of=[f"{C.T4_PATH}#{u.derived_anchor}"])


def _frame_result(reader: Reader, frame: Frame, with_text: bool = True) -> dict:
    corpus = reader.corpus
    payload: dict[str, Any] = {
        "frame": True,
        "route": {"tool": "get_section", "paper_id": "T4", "anchor": frame.anchor, "language": "en"},
        "translation_version": reader.t4en_meta["translationVersion"],
        "preparation": _meta(reader, "preparation"),
        "authority": _meta(reader, "authority"),
    }
    if with_text:
        payload["text"] = "\n".join(corpus.t4en.lines[frame.line_start - 1:frame.line_end])
        payload["is_excerpt"] = False
    return S.result(corpus, source_kind="translation", source_path=C.T4EN_PATH, fragment=frame.anchor,
                    language="en", locator_=S.locator(C.T4EN_PATH, frame.line_start, frame.line_end),
                    payload=payload, paper_id="T4", section_anchor=frame.anchor,
                    source_url=_pages_url("papers/T4.en.html", frame.anchor), derivative_of=[C.T4_PATH])


# ---------------------------------------------------------------- 語句の分割と照合（SEARCH・CAND）


def _meaningful(frag: str) -> bool:
    return any(ord(c) >= 128 or c.isascii() and c.isalnum() for c in frag)


def _split_fragments(folded: str) -> list[str]:
    out, cur = [], []
    for ch in folded:
        if ch == " " or ch in SEPARATORS:
            if cur:
                out.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


def _term_prepass(index: TM.TermIndex, folded: str) -> tuple[list[tuple[int, str]], str]:
    """用語対応表の語形（空白や記号を含むものも）を先に一語として取り出す（最左最長）。"""
    found: list[tuple[int, str]] = []
    work = list(folded)
    for form in index.forms_by_length():
        for k in _occurrences("".join(work), form):
            found.append((k, form))
            for m in range(k, k + len(form)):
                work[m] = " "
    return sorted(found), "".join(work)


def _parse_query(reader: Reader, query: str, terms: TM.TermIndex, limit: int | None) -> tuple[list[str], list[str]]:
    """クエリを断片に分ける。返り値は（断片、捨てた断片）。limit は断片数の上限（超過は呼び出し側で扱う）。"""
    folded = N.fold_search(query, is_input=True).text
    pre, rest = _term_prepass(terms, folded)
    ordered = [(k, f) for k, f in pre]
    pos = 0
    for f in _split_fragments(rest):
        k = rest.find(f, pos)
        ordered.append((k, f))
        pos = k + len(f)
    frags, dropped, seen = [], [], set()
    for _, f in sorted(ordered):
        if f in seen:
            continue
        seen.add(f)
        if N.is_hiragana_only(f) or not _meaningful(f):
            dropped.append(f)
        else:
            frags.append(f)
    if limit is not None:
        frags = frags[:limit]
    return frags, dropped


WORD_RE_CACHE_MAX = 512  # 語形ごとの正規表現の保持数（Codex① P2-5・Codex② 2）


@lru_cache(maxsize=WORD_RE_CACHE_MAX)
def _word_pattern(form: str) -> re.Pattern:
    """ASCII の語形に対する単語境界の正規表現を、容量つき LRU で使い回す。

    自前の dict と move_to_end では、取得と並べ替えの間に別のスレッドが追い出すと KeyError になった
    （Codex② 2）。`lru_cache` は取得・並べ替え・追加・追い出しが一つのロックの中で終わる。
    """
    w = re.escape(_WORD_CHARS)
    return re.compile(f"(?<![{w}]){re.escape(form)}(?![{w}])")


def _occurrences(hay: str, form: str) -> list[int]:
    """ASCII だけの語形は単語境界（`_WORD_CHARS` 以外）で、それ以外は部分文字列で、重ならない出現位置を返す。"""
    if not form:
        return []
    if N.is_ascii(form):
        return [m.start() for m in _word_pattern(form).finditer(hay)]
    out, start = [], 0
    while True:
        k = hay.find(form, start)
        if k < 0:
            return out
        out.append(k)
        start = k + len(form)


def _expansions(terms: TM.TermIndex, frag: str) -> list[tuple[str, str]]:
    out = set()
    for eid in terms.entry_ids_for(frag):
        for form in terms.folded[eid]:
            if form != frag:
                out.add((form, eid))
    return sorted(out)


@dataclass(frozen=True)
class Hit:
    line: Line
    distinct: int
    total: int
    direct: int
    positions: tuple[tuple[int, int, str, str], ...]  # (fold 上の開始, 終了, 断片, 経路)

    def key(self, paper_order: Mapping[str, int]) -> tuple:
        # 語の種類数↓→直接一致↓→総出現数↓→論文順↑→行番号↑（SEARCH-1.1.0。SPEC §5.3 は v2.2 で訂正）
        return (-self.distinct, -self.direct, -self.total, paper_order[self.line.paper_id], self.line.no)


def _match_lines(reader: Reader, lines: Iterable[Line], frags: Sequence[str], terms: TM.TermIndex) -> list[Hit]:
    exp = {f: _expansions(terms, f) for f in frags}
    hits = []
    for line in lines:
        hay = line.fold.text
        positions, distinct, direct = [], 0, 0
        for f in frags:
            found = [(k, k + len(f), f, "query") for k in _occurrences(hay, f)]
            if found:
                direct += 1
            for form, eid in exp[f]:
                found += [(k, k + len(form), f, f"term_map:{eid}") for k in _occurrences(hay, form)]
            if found:
                distinct += 1
                positions += found
        if distinct:
            hits.append(Hit(line, distinct, len(positions), direct, tuple(sorted(positions))))
    return hits


def _hit_payload(reader: Reader, hit: Hit, rank: int, extra: Mapping[str, Any] | None = None) -> tuple[dict, int, int]:
    line = hit.line
    spans = line.fold.spans
    orig = [(spans[a][0], spans[b - 1][1], f, via) for a, b, f, via in hit.positions]
    c0, c1 = orig[0][0], orig[0][1]
    excerpt, e0, e1 = _excerpt(line.text, c0, c1)
    payload = {
        "excerpt": excerpt,
        "is_excerpt": True,
        "excerpt_char_start": e0,
        "excerpt_char_end": e1,
        "match_positions": [{"term": f, "via": via, "char_start": a, "char_end": b} for a, b, f, via in orig[:POSITIONS_MAX]],
        "match_positions_total": len(orig),
        "matched_terms": sorted({f for *_, f, _v in hit.positions}),
        "match_via": sorted({via for *_, via in hit.positions}),
        "rank": rank,
        "rank_key": {"distinct_terms": hit.distinct, "occurrences": hit.total, "direct_terms": hit.direct,
                     "paper_order": reader.paper_order[line.paper_id] + 1, "line": line.no},
        "route": {"tool": "get_section", "paper_id": line.paper_id,
                  "anchor": line.anchor if line.kind == "paper_md" else line.unit.derived_anchor,
                  **({"language": "en"} if line.kind != "paper_md" else {})},
    }
    if extra:
        payload.update(extra)
    return payload, c0, c1


def _has_cjk(s: str) -> bool:
    return any(N.is_cjk(c) for c in s)


# ---------------------------------------------------------------- 3. search_passages


def search_passages(reader: Reader, query: Any, paper_id: Any = None, k: Any = K_DEFAULT) -> dict:
    return _search_passages(reader, query, paper_id, k, reader.terms)


def _search_passages(reader: Reader, query: Any, paper_id: Any, k: Any, terms: TM.TermIndex) -> dict:
    corpus = reader.corpus
    if not isinstance(query, str) or not query or len(query) > QUERY_RAW_MAX:
        return _invalid(reader, f"query は1〜{QUERY_RAW_MAX}字の文字列")
    if has_lone_surrogate(query):
        return _invalid(reader, "query に孤立サロゲートが含まれる")
    if not isinstance(k, int) or isinstance(k, bool) or not (K_MIN <= k <= K_MAX):
        return _invalid(reader, f"k は {K_MIN}〜{K_MAX} の整数")
    if paper_id is not None:
        pcls = _classify_id(paper_id)
        if pcls == "invalid":
            return _invalid(reader, "paper_id の形式が不正（パス・URL・制御文字・長さ）")
        if pcls == "malformed" or paper_id not in corpus.papers:
            cands = [_paper_ref(reader, pid) for pid in C.PAPER_IDS]
            return S.envelope(corpus, "unknown_id", candidates=cands,
                              limitations=("NEAR: 未登録の paper_id。実在する五本を候補に挙げた",))
    folded_len = len(N.fold_search(query, is_input=True).text)
    if folded_len == 0 or folded_len > QUERY_NORM_MAX:
        return _invalid(reader, f"query は正規化後1〜{QUERY_NORM_MAX}字（切り詰めない）")
    frags, dropped = _parse_query(reader, query, terms, None)
    if not frags:
        return _invalid(reader, "検索に使える断片がない（ひらがなだけの断片と記号だけの断片は捨てる）")
    if len(frags) > QUERY_FRAGMENTS_MAX:
        return _invalid(reader, f"断片は{QUERY_FRAGMENTS_MAX}個まで（{len(frags)}個）")
    scope = [ln for ln in reader.orig_lines if paper_id is None or ln.paper_id == paper_id]
    hits = _match_lines(reader, scope, frags, terms)
    full = sorted((h for h in hits if h.distinct == len(frags)), key=lambda h: h.key(reader.paper_order))
    part = sorted((h for h in hits if h.distinct < len(frags)), key=lambda h: h.key(reader.paper_order))
    results = []
    for rank, h in enumerate(full[:k], 1):
        payload, c0, c1 = _hit_payload(reader, h, rank)
        results.append(_line_result(reader, h.line, c0, c1, payload))
    candidates = []
    for rank, h in enumerate(part[:k], 1):
        payload, c0, c1 = _hit_payload(reader, h, rank, {"partial": True})
        candidates.append(_line_result(reader, h.line, c0, c1, payload))
    status = "ok" if full else "no_lexical_match"
    lims = [
        _rules(SEARCH_VERSION, N.NORM_VERSION, terms.version, LIMITS_VERSION, C.LINES_RULE),
        "SCOPE: " + ("論文五本" if paper_id is None else paper_id) + "の原文（参考文献を含む）・単位は行",
        "SCORE: rank_key は検索順位の鍵であって、意味的一致の確率ではない",
        f"TOTAL: 全語一致 {len(full)} 行・一部一致 {len(part)} 行（それぞれ上位 {k} 件まで返す）",
        "QUERY: 断片 " + " / ".join(frags) + (("（捨てた断片 " + " / ".join(dropped) + "）") if dropped else ""),
        f"TERMS: 用語対応表 {terms.version}（{len(terms.entries)} 項目。著者承認済みだけを載せる）",
    ]
    english_in_scope = paper_id is None or paper_id != "T4"
    if not full:
        lims.append("ZERO: 全語一致はゼロ。語句の照合であり、その概念の記述がないことを意味しない")
    if (_has_cjk(query) and english_in_scope) or not full:
        lims.append("LANG: T1〜T3・T5 は英語、T4 は日本語が原文。語句の照合なので、言語の違う原文には一致しにくい")
    return S.envelope(corpus, status, results, candidates, lims)


# ---------------------------------------------------------------- 4. get_claim_record


def _claim_result(reader: Reader, i: int, extra: Mapping[str, Any] | None = None) -> dict:
    corpus = reader.corpus
    ledger = corpus.ledger
    c = ledger["claims"][i]
    loc = c["source_locator"]
    anchor = loc["section_url"].split("#", 1)[1]
    payload = {
        "id": c["id"],
        "status": c["status"],
        "claim": c["claim"],
        "claim_note": "claim は台帳の要約であって、論文からの逐語の引用ではない",
        "source_quote": c["source_quote"],
        "not_claimed": c["not_claimed"],
        "section": c["section"],
        "source_locator": loc,
        "additional_source_quotes": c.get("additional_source_quotes"),
        "footnote": c.get("footnote"),
        "author_answerable": None,
        "author_answerable_note": "未記録（初版）。推定で埋めない",
        "ledger_sha256": S.file_hash(corpus, C.T5_LEDGER_PATH),
        "cited_paper_sha256": ledger["source_sha256"],
        "ledger_notes": [
            {"json_pointer": "/editorial_status", "text": ledger["editorial_status"]},
            {"json_pointer": "/source_role", "text": ledger["source_role"]},
        ],
    }
    if extra:
        payload.update(extra)
    return S.result(corpus, source_kind="claims", source_path=C.T5_LEDGER_PATH, fragment=c["id"],
                    language="en", locator_=S.locator(C.T5_LEDGER_PATH, json_pointer=f"/claims/{i}"),
                    payload=payload, paper_id="T5", section_anchor=anchor, source_url=loc["section_url"],
                    derivative_of=[f"papers/T5.md#{anchor}"])


def get_claim_record(reader: Reader, claim_id: Any = None, query: Any = None) -> dict:
    return _get_claim_record(reader, claim_id, query, reader.terms)


def _get_claim_record(reader: Reader, claim_id: Any, query: Any, terms: TM.TermIndex) -> dict:
    corpus = reader.corpus
    claims = corpus.ledger["claims"]
    label = "LABEL: status は本稿がどう位置づけたかの記録であって、真偽の判定ではない"
    if (claim_id is None) == (query is None):
        return _invalid(reader, "claim_id と query のどちらか一方だけを指定する")
    if claim_id is not None:
        if _classify_id(claim_id) != "ok" or not _CLAIM_ID_RE.match(claim_id):
            return _invalid(reader, "claim_id の形式は T[1-5]-英大文字+数字（例 T5-A1）")
        pid = claim_id.split("-", 1)[0]
        if pid != "T5":
            paper = corpus.papers[pid]
            cands = [_section_result(reader, paper, s, with_text=False) for s in paper.sections]
            return S.envelope(corpus, "ledger_not_available", candidates=cands, limitations=(
                f"LEDGER: 主張台帳は T5 のみ。{pid} の主張の位置づけは記録されていない（ラベルを作らない）",
                f"ROUTE: {pid} の原文は get_section・search_passages で読む。候補は {pid} の節の一覧（関連の判定はしていない）",
            ))
        ids = [c["id"] for c in claims]
        if claim_id not in ids:
            cands = [_claim_result(reader, i) for i in range(len(claims))]
            return S.envelope(corpus, "unknown_id", candidates=cands,
                              limitations=("NEAR: 未登録の claim_id。台帳の実在する項目を候補に挙げた", label))
        return S.envelope(corpus, "ok", [_claim_result(reader, ids.index(claim_id))],
                          limitations=(label, _rules(S.JSON_RULE)))
    # query の経路（CAND-1.0.0）
    if not isinstance(query, str) or not query or len(query) > QUERY_RAW_MAX:
        return _invalid(reader, f"query は1〜{QUERY_RAW_MAX}字の文字列")
    if has_lone_surrogate(query):
        return _invalid(reader, "query に孤立サロゲートが含まれる")
    folded_len = len(N.fold_search(query, is_input=True).text)
    if folded_len == 0 or folded_len > QUERY_NORM_MAX:
        return _invalid(reader, f"query は正規化後1〜{QUERY_NORM_MAX}字（切り詰めない）")
    frags, dropped = _parse_query(reader, query, terms, None)
    if not frags:
        return _invalid(reader, "検索に使える断片がない")
    if len(frags) > QUERY_FRAGMENTS_MAX:
        return _invalid(reader, f"断片は{QUERY_FRAGMENTS_MAX}個まで（{len(frags)}個）")
    scored = []
    for i, c in enumerate(claims):
        units = [("claim", c["claim"]), ("status", c["status"]), ("source_quote", c["source_quote"])]
        units += [(f"not_claimed/{j}", t) for j, t in enumerate(c["not_claimed"])]
        best = None
        for field, text in units:
            line = Line(C.T5_LEDGER_PATH, "T5", i, text, N.normalize_quote(text, is_input=False),
                        N.fold_search(text, is_input=False), "claims", field)
            hit = next(iter(_match_lines(reader, [line], frags, terms)), None)
            if hit is None:
                continue
            k = (-hit.distinct, -hit.direct, -hit.total, j_order(field))
            if best is None or k < best[0]:
                best = (k, field, hit)
        if best is not None:
            scored.append((best[0][:3] + (i,), i, best[1], best[2]))
    scored.sort()
    full = [s for s in scored if s[3].distinct == len(frags)]
    part = [s for s in scored if s[3].distinct < len(frags)]

    def with_match(s, rank):
        _, i, field, hit = s
        return _claim_result(reader, i, {"match": {
            "field": field, "matched_terms": sorted({f for *_, f, _v in hit.positions}),
            "match_via": sorted({v for *_, v in hit.positions}), "rank": rank}})

    results = [with_match(s, r) for r, s in enumerate(full, 1)]
    candidates = [with_match(s, r) for r, s in enumerate(part[:CAND_MAX], 1)]
    lims = [
        "LEDGER: 主張台帳は T5 のみ（T1〜T4 は原文を get_section・search_passages で読む）",
        label,
        _rules(CAND_VERSION, SEARCH_VERSION, terms.version, LIMITS_VERSION),
        "QUERY: 断片 " + " / ".join(frags) + (("（捨てた断片 " + " / ".join(dropped) + "）") if dropped else ""),
        "SCOPE: 照合の単位は claim・status・source_quote・not_claimed の各項目",
    ]
    if not full:
        lims.append("ZERO: 全語一致はゼロ。語句の照合であり、該当する主張がないことを意味しない")
    return S.envelope(corpus, "ok" if full else "no_lexical_match", results, candidates, lims)


def j_order(field: str) -> int:
    order = {"claim": 0, "status": 1, "source_quote": 2}
    if field in order:
        return order[field]
    return 3 + int(field.split("/", 1)[1])


# ---------------------------------------------------------------- 5. verify_quote


def verify_quote(reader: Reader, text: Any, paper_id: Any = None, language: Any = None) -> dict:
    return _verify_quote(reader, text, paper_id, language, reader.terms)


def _verify_scope(reader: Reader, paper_id: str | None, language: str | None) -> list[Line]:
    if language == "en":
        return list(reader.en_lines)
    return [ln for ln in reader.orig_lines if paper_id is None or ln.paper_id == paper_id]


def _verify_quote(reader: Reader, text: Any, paper_id: Any, language: Any, terms: TM.TermIndex) -> dict:
    corpus = reader.corpus
    none = {"match": "none", "normalization_applied": []}

    def _invalid(reader, reason, *extra):
        return S.envelope(reader.corpus, "invalid_input", limitations=("INPUT: " + reason, *extra), extra=none)

    if not isinstance(text, str) or len(text) > TEXT_MAX:
        return _invalid(reader, f"text は{TEXT_MAX}字までの文字列")
    if has_lone_surrogate(text):
        return _invalid(reader, "text に孤立サロゲートが含まれる")
    if paper_id is not None:
        pcls = _classify_id(paper_id)
        if pcls == "invalid":
            return _invalid(reader, "paper_id の形式が不正（パス・URL・制御文字・長さ）")
        if pcls == "malformed" or paper_id not in corpus.papers:
            cands = [_paper_ref(reader, pid) for pid in C.PAPER_IDS]
            return S.envelope(corpus, "unknown_id", candidates=cands,
                              limitations=("NEAR: 未登録の paper_id。実在する五本を候補に挙げた",), extra=none)
        reason = _check_language(paper_id, language)
        if reason:
            return _invalid(reader, reason)
    elif language is not None:
        if not isinstance(language, str) or language not in S.LANGUAGES:
            return _invalid(reader, "language は None・\"ja\"・\"en\" のいずれか")
        if language == "ja":
            return _invalid(reader, "paper_id=None では language=\"ja\" を選べない（T4 の原文は paper_id=\"T4\" で指定する）")
    inp = N.normalize_quote(text, is_input=True)
    if not inp.text:
        return _invalid(reader, "空文字・空白だけの引用は照合しない")
    min_chars = QUOTE_MIN_CHARS_CJK if N.has_kana_kanji(inp.source) else QUOTE_MIN_CHARS_OTHER
    if len(inp.text) < min_chars:
        return _invalid(reader, f"引用は正規化後{min_chars}字以上（仮名・漢字を含む入力は{QUOTE_MIN_CHARS_CJK}字、"
                        f"それ以外は{QUOTE_MIN_CHARS_OTHER}字）")
    scope = _verify_scope(reader, paper_id, language)
    rules = _rules(N.NORM_VERSION, LIMITS_VERSION, C.LINES_RULE,
                   *((C.T4MAP_RULE,) if language == "en" else ()))
    scope_lim = ("SCOPE: " + ("T4 英訳（translations/T4.en.md の unit 範囲）" if language == "en"
                             else ("論文五本" if paper_id is None else paper_id) + "の原文")
                 + "・単位は行（行をまたぐ引用は一致しない）")
    base_lims = [rules, scope_lim,
                 "HTML: HTML からコピーした引用は、強調記号の有無は MARK-EMPH で吸収するが、脚注の番号の違いは正規化の対象外"]
    if language == "en":
        base_lims += list(_translation_limitations())
    if inp.nfc_applied:
        base_lims.append("NFC: 入力を NFC に合成してから照合した（差分の位置は合成後の文字位置）")

    exact = [(ln, k) for ln in scope for k in N.find_all(ln.text, text)] if text else []
    norm_hits = []
    for ln in scope:
        for j in N.find_all(ln.quote.text, inp.text):
            c0, c1 = N.source_span(ln.quote, j, j + len(inp.text))
            norm_hits.append((ln, j, c0, c1))

    def exact_result(ln, k):
        return _line_result(reader, ln, k, k + len(text), {
            "match": "exact", "matched_text": ln.text[k:k + len(text)], "diffs": [], "diffs_total": 0})

    def norm_result(ln, j, c0, c1, as_candidate=False):
        rules_used, diffs, total = N.compare(inp, ln.quote, j, DIFFS_MAX)
        payload = {"match": "normalized", "matched_text": ln.text[c0:c1], "diffs": diffs,
                   "diffs_total": total, "normalization_applied": rules_used}
        if as_candidate:
            payload["candidate_reason"] = "exact 一致が別にあり、この箇所は正規化でだけ一致する"
        return _line_result(reader, ln, c0, c1, payload), rules_used

    if exact:
        if len(exact) > QUOTE_MAX_RESULTS:
            return S.envelope(corpus, "invalid_input", limitations=(
                *base_lims, f"TOTAL: total={len(exact)}（上限 {QUOTE_MAX_RESULTS} 件を超えた。部分的な結果は返さない）",
                "INPUT: より長い引用にするか paper_id を指定する"), extra=none)
        results = [exact_result(ln, k) for ln, k in exact]
        exact_keys = {(ln.path, ln.no, k) for ln, k in exact}
        others = [h for h in norm_hits if (h[0].path, h[0].no, h[2]) not in exact_keys]
        candidates = [norm_result(*h, as_candidate=True)[0] for h in others[:CAND_MAX]]
        lims = list(base_lims)
        if len(results) > 1:
            lims.append(f"AMBIGUOUS: total={len(results)}（同じ文字列が複数箇所にある）")
        if others:
            lims.append(f"NEARBY: 正規化でだけ一致する箇所 {len(others)} 件を candidates に出した（上位 {CAND_MAX} 件まで）")
        return S.envelope(corpus, "ok", results, candidates, lims,
                          extra={"match": "exact", "normalization_applied": []})
    if norm_hits:
        if len(norm_hits) > QUOTE_MAX_RESULTS:
            return S.envelope(corpus, "invalid_input", limitations=(
                *base_lims, f"TOTAL: total={len(norm_hits)}（上限 {QUOTE_MAX_RESULTS} 件を超えた。部分的な結果は返さない）",
                "INPUT: より長い引用にするか paper_id を指定する"), extra=none)
        results, applied = [], set()
        for h in norm_hits:
            r, used = norm_result(*h)
            results.append(r)
            applied.update(used)
        lims = list(base_lims)
        lims.append("NORMALIZED: 表記差を規則で吸収して一致した。payload.matched_text が原文の表記、payload.diffs が変換の記録")
        if len(results) > 1:
            lims.append(f"AMBIGUOUS: total={len(results)}（同じ文字列が複数箇所にある）")
        return S.envelope(corpus, "ok", results, (), lims,
                          extra={"match": "normalized", "normalization_applied": sorted(applied)})
    # 不一致：CAND-1.0.0 による語句上の近接候補
    frags, _dropped = _parse_query(reader, text, terms, QUERY_FRAGMENTS_MAX)
    hits = _match_lines(reader, scope, frags, terms) if frags else []
    hits.sort(key=lambda h: h.key(reader.paper_order))
    candidates = []
    for rank, h in enumerate(hits[:CAND_MAX], 1):
        payload, c0, c1 = _hit_payload(reader, h, rank, {"match": "none", "partial": h.distinct < len(frags)})
        candidates.append(_line_result(reader, h.line, c0, c1, payload))
    lims = [*base_lims,
            "NOT_FOUND: 指定の範囲と規則では一致しなかった",
            f"CAND: candidates は語句上の一部一致（{CAND_VERSION}・入力の先頭から最大{QUERY_FRAGMENTS_MAX}断片）。類似の主張があることを意味しない"]
    return S.envelope(corpus, "quote_not_found", (), candidates, lims,
                      extra={"match": "none", "normalization_applied": []})


# ---------------------------------------------------------------- 6. check_compressions


CONTRACT = "CONTRACT: 意味上の誤り、著者への不同意、読者の理解不足を判定しない。該当ゼロは正しい読解の証明ではない"
FORMS = "FORMS: 肯定文・否定文・引用・疑問文は同じ語形として拾いうる。該当は文脈の確認が要る箇所であって、誤りの判定ではない"


def check_compressions(reader: Reader, text: Any) -> dict:
    return _check_compressions(reader, text, reader.patterns, reader.patterns_version)


def _check_compressions(reader: Reader, text: Any, patterns: Sequence[PAT.Pattern], version: str) -> dict:
    corpus = reader.corpus
    if not isinstance(text, str) or len(text) > TEXT_MAX:
        return _invalid(reader, f"text は{TEXT_MAX}字までの文字列")
    if has_lone_surrogate(text):
        return _invalid(reader, "text に孤立サロゲートが含まれる")
    folded = N.fold_search(text, is_input=True)
    if not folded.text:
        return _invalid(reader, "空文字・空白だけの入力は照合しない")
    matches = []
    for p in patterns:
        found = []
        for form in p.surface_forms:
            ff = N.fold_search(form, is_input=False).text
            for k in _occurrences(folded.text, ff):
                c0, c1 = N.source_span(folded, k, k + len(ff))
                found.append({"form": form, "char_start": c0, "char_end": c1})
        if found:
            found.sort(key=lambda x: (x["char_start"], x["char_end"], x["form"]))
            matches.append((found[0]["char_start"], p.id, p, found))
    matches.sort(key=lambda m: (m[0], m[1]))
    results = []
    for _first, _pid, p, found in matches:
        for rs in p.related_sources:
            results.append(_related_result(reader, p, rs, found))
    lims = [CONTRACT, FORMS,
            _rules(PAT.MATCH_RULE, version, N.SEARCH_FOLD_VERSION, LIMITS_VERSION),
            f"PATTERNS: 承認済みパターン {len(patterns)} 件（{version}）・該当 {len(matches)} 件"]
    if folded.nfc_applied:
        lims.append("NFC: 入力を NFC に合成してから照合した（位置は合成後の文字位置）")
    return S.envelope(corpus, "ok", results, limitations=lims)


def _related_result(reader: Reader, p: PAT.Pattern, rs: PAT.RelatedSource, found: list[dict]) -> dict:
    corpus = reader.corpus
    kind = S.SOURCE_KIND_BY_PATH[rs.path]
    lines = corpus.lines[rs.path]
    if rs.char_start is not None:
        excerpt = lines[rs.line_start - 1][rs.char_start:rs.char_end]
    else:
        excerpt = "\n".join(lines[rs.line_start - 1:rs.line_end])
    truncated = len(excerpt) > SOURCE_EXCERPT_MAX
    if truncated:
        excerpt = excerpt[:SOURCE_EXCERPT_MAX] + "…"
    payload = {
        "pattern_id": p.id,
        "pattern_version": p.version,
        "matched": found[:POSITIONS_MAX],
        "matched_total": len(found),
        "needs_context_review": True,
        "source_excerpt": excerpt,
        "source_excerpt_truncated": truncated,
        "input_positions_note": "matched の位置は入力文字列（NFC 合成後）の文字位置",
    }
    if kind == "paper_md":
        paper = next(x for x in corpus.papers.values() if x.path == rs.path)
        return S.result(corpus, source_kind=kind, source_path=rs.path, fragment=f"L{rs.line_start}-L{rs.line_end}",
                        language=paper.language,
                        locator_=S.locator(rs.path, rs.line_start, rs.line_end, rs.char_start, rs.char_end),
                        payload=payload, paper_id=paper.paper_id, section_anchor=rs.anchor,
                        source_url=_pages_url(_paper_html(paper.paper_id), rs.anchor))
    return S.result(corpus, source_kind=kind, source_path=rs.path, fragment=f"L{rs.line_start}-L{rs.line_end}",
                    language=C.GUIDE_LANGUAGE, locator_=S.locator(rs.path, rs.line_start, rs.line_end),
                    payload=payload, source_url=_pages_url(rs.path), derivative_of=S.ALL_PAPERS_DERIVATIVE)


# ---------------------------------------------------------------- 7. get_reading_guide


def get_reading_guide(reader: Reader, part: Any = "all") -> dict:
    corpus = reader.corpus
    names = [p for p, _ in GUIDE_PARTS]
    if not isinstance(part, str) or part not in names:
        return _invalid(reader, "part は " + "・".join(names) + " のいずれか")
    start, end, title = reader.guide_ranges[part]
    payload = {"part": part, "title": title, "text": "\n".join(corpus.lines[GUIDE_PATH][start - 1:end]),
               "is_excerpt": part != "all"}
    res = S.result(corpus, source_kind="reading_guide", source_path=GUIDE_PATH, fragment=part,
                   language=C.GUIDE_LANGUAGE, locator_=S.locator(GUIDE_PATH, start, end), payload=payload,
                   source_url=_pages_url(GUIDE_PATH), derivative_of=S.ALL_PAPERS_DERIVATIVE)
    lims = (_rules(GUIDE_VERSION, PR.PROMPTS_VERSION),
            f"TEMPLATES: templates は読み方の雛形（{PR.PROMPTS_VERSION}・{PR.PROMPTS_STATUS}）。利用者が明示的に選んだときだけ使う",
            "GUIDE: ガイドは論文の派生物。学術的な引用先は各論文の DOI")
    return S.envelope(corpus, "ok", [res], limitations=lims, extra={"templates": PR.templates_payload()})
