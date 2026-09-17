"""用語対応表（TERMS・docs/rules/TERMS.md）。

著者が承認した項目だけを載せる（Q52）。範囲はコーパスが自ら示す対訳と表記揺れに限り、概念レベルの
対応は入れない（SPEC §11・Q53）。初版は空で、読み込みと照合の仕組みだけを持つ。
候補は docs/candidates/terms_candidates_v0.md（未承認）で、ここには載せない。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

from .corpus import is_blank
from .normalize import fold_search

TERMS_VERSION = "TERMS-0.0.0"
APPROVED_ON: str | None = None

_ID_RE = re.compile(r"^M[0-9]{2,3}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


@dataclass(frozen=True)
class TermEntry:
    id: str
    forms_ja: tuple[str, ...]
    forms_en: tuple[str, ...]
    sources: tuple[str, ...]  # コーパス内の出所（例 "papers/T4.md:41"）
    approved_on: str


# 承認済みの項目だけを載せる。初版は空。
TERMS: tuple[TermEntry, ...] = ()


@dataclass(frozen=True)
class TermIndex:
    version: str
    entries: Mapping[str, TermEntry]
    forms: Mapping[str, tuple[str, ...]]  # 畳み込んだ語形 → 項目ID（整列済み）
    folded: Mapping[str, tuple[str, ...]]  # 項目ID → 畳み込んだ全語形（整列済み）

    def entry_ids_for(self, folded_form: str) -> tuple[str, ...]:
        return self.forms.get(folded_form, ())

    def forms_by_length(self) -> tuple[str, ...]:
        """前処理で使う語形の並び（長い順、同じ長さは辞書順）。"""
        return tuple(sorted(self.forms, key=lambda f: (-len(f), f)))


def build_term_index(entries: Iterable[TermEntry], version: str = TERMS_VERSION) -> TermIndex:
    """項目を検査して索引を作る。不正な項目は ValueError。"""
    by_id: dict[str, TermEntry] = {}
    forms: dict[str, set[str]] = {}
    folded: dict[str, tuple[str, ...]] = {}
    for e in entries:
        if not isinstance(e, TermEntry) or not _ID_RE.match(e.id) or e.id in by_id:
            raise ValueError(f"invalid or duplicate term id: {getattr(e, 'id', e)!r}")
        if not e.forms_ja or not e.forms_en or not e.sources:
            raise ValueError(f"{e.id}: forms and sources are required")
        if not _DATE_RE.match(e.approved_on or ""):
            raise ValueError(f"{e.id}: approved_on must be YYYY-MM-DD")
        fs = set()
        for f in (*e.forms_ja, *e.forms_en):
            if not isinstance(f, str) or is_blank(f):
                raise ValueError(f"{e.id}: empty form")
            ff = fold_search(f, is_input=False).text
            if not ff:
                raise ValueError(f"{e.id}: form folds to empty")
            fs.add(ff)
            forms.setdefault(ff, set()).add(e.id)
        by_id[e.id] = e
        folded[e.id] = tuple(sorted(fs))
    return TermIndex(
        version=version,
        entries=dict(sorted(by_id.items())),
        forms={k: tuple(sorted(v)) for k, v in sorted(forms.items())},
        folded=folded,
    )
