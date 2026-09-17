"""check_compressions の圧縮候補パターン（PATTERNS・docs/rules/PATTERNS.md）。

載せるのは著者が承認した、版番号つきの語形だけ（CLAUDE.md 絶対規則9・SPEC §5.6）。承認前は空で起動する。
候補は docs/candidates/patterns_candidates_v0.md（未承認）で、ここには載せない。
試験用のパターンは tests/fixtures/ にあり、テストが内部引数でだけ注入する。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .corpus import is_blank
from .schema import SOURCE_KIND_BY_PATH

PATTERNS_VERSION = "PATTERNS-0.0.0"
APPROVED_ON: str | None = None
MATCH_RULE = "PATTERNS-MATCH-1.0.0"
RELATED_KINDS = frozenset({"paper_md", "theory_map", "reading_guide"})

_ID_RE = re.compile(r"^P[0-9A-Z-]{1,16}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


@dataclass(frozen=True)
class RelatedSource:
    """一致時に source_excerpt として返す原文の位置（同梱ファイル・1 始まり・終端を含む）。"""

    path: str
    line_start: int
    line_end: int
    anchor: str | None = None  # 論文の節 id（論文以外は None）


@dataclass(frozen=True)
class Pattern:
    id: str
    version: str
    surface_forms: tuple[str, ...]
    related_sources: tuple[RelatedSource, ...]
    approved_on: str
    match_rule: str = MATCH_RULE


# 承認済みのパターンだけを載せる。初版は空。
PATTERNS: tuple[Pattern, ...] = ()


def validate_patterns(corpus, patterns: Iterable[Pattern]) -> tuple[Pattern, ...]:
    """パターンの形と関連原文の実在を検査する。不正なら ValueError。"""
    seen: set[str] = set()
    out = []
    for p in patterns:
        if not isinstance(p, Pattern) or not _ID_RE.match(p.id) or p.id in seen:
            raise ValueError(f"invalid or duplicate pattern id: {getattr(p, 'id', p)!r}")
        if p.match_rule != MATCH_RULE or not p.version or not _DATE_RE.match(p.approved_on or ""):
            raise ValueError(f"{p.id}: match_rule/version/approved_on")
        if not p.surface_forms or any(not isinstance(f, str) or is_blank(f) for f in p.surface_forms):
            raise ValueError(f"{p.id}: surface_forms")
        if not p.related_sources:
            raise ValueError(f"{p.id}: related_sources")
        for rs in p.related_sources:
            if SOURCE_KIND_BY_PATH.get(rs.path) not in RELATED_KINDS:
                raise ValueError(f"{p.id}: related source kind for {rs.path}")
            lines = corpus.lines.get(rs.path)
            if lines is None or not (1 <= rs.line_start <= rs.line_end <= len(lines)):
                raise ValueError(f"{p.id}: related source {rs.path}:{rs.line_start}-{rs.line_end}")
            paper = next((x for x in corpus.papers.values() if x.path == rs.path), None)
            if paper is not None:
                sec = paper.section(rs.anchor) if rs.anchor else None
                if sec is None or not (sec.line_start <= rs.line_start and rs.line_end <= sec.line_end):
                    raise ValueError(f"{p.id}: anchor {rs.anchor!r} does not contain the lines")
            elif rs.anchor is not None:
                raise ValueError(f"{p.id}: anchor is only for papers")
        seen.add(p.id)
        out.append(p)
    return tuple(sorted(out, key=lambda p: p.id))
