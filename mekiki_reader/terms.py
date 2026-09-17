"""用語対応表（TERMS・docs/rules/TERMS.md）。

著者が承認した項目だけを載せる（Q52）。範囲はコーパスが自ら示す対訳と表記揺れに限り、概念レベルの
対応は入れない（SPEC §11・Q53）。
候補は docs/candidates/terms_candidates_v0.md、確定した表と出所は docs/rules/TERMS.md。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

from .corpus import is_blank
from .normalize import fold_search

TERMS_VERSION = "TERMS-0.1.0"
APPROVED_ON = "2026-09-18"

# 項目ごとの出所（scripts/find_term_sources.py --terms の出力。TERMS-SRC-1.0.0）
SOURCES: dict[str, tuple[str, ...]] = {
    'M01': (
        'T4 本文の対訳表記 papers/T4.md:61',
        'T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:61↔T4.en.md:220）',
        '訳注 translations/T4.en.md:227（tn-05）',
    ),
    'M02': (
        '対訳の出所なし（日本語形の出現 0件）',
        '英語形の出現 papers/T1.md:14・papers/T1.md:20・papers/T1.md:40 ほか',
    ),
    'M03': (
        'T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:19↔T4.en.md:30・T4.md:41↔T4.en.md:126 ほか）',
    ),
    'M04': (
        'T4 本文の対訳表記 papers/T4.md:61・papers/T4.md:104・papers/T4.md:116 ほか',
        'T4↔T4.en の manifest 対応で共起 4/7 unit（T4.md:61↔T4.en.md:220・T4.md:104↔T4.en.md:386 ほか）',
    ),
    'M05': (
        'T4 本文の対訳表記 papers/T4.md:61・papers/T4.md:69・papers/T4.md:116 ほか',
        'T4↔T4.en の manifest 対応で共起 4/8 unit（T4.md:61↔T4.en.md:220・T4.md:69↔T4.en.md:258 ほか）',
    ),
    'M06': (
        'T4 本文の対訳表記 papers/T4.md:19・papers/T4.md:21・papers/T4.md:45 ほか',
        'T4↔T4.en の manifest 対応で共起 17/20 unit（T4.md:19↔T4.en.md:30・T4.md:21↔T4.en.md:45 ほか）',
        'ガイドの同じ行 SOURCE_INDEX.md:182',
        '読解試験の日英設問 R06',
    ),
    'M07': (
        'T4 本文の対訳表記 papers/T4.md:77',
        'T4↔T4.en の manifest 対応で共起 8/9 unit（T4.md:19↔T4.en.md:30・T4.md:45↔T4.en.md:150 ほか）',
    ),
    'M08': (
        'T4↔T4.en の manifest 対応で共起 33/36 unit（T4.md:19↔T4.en.md:30・T4.md:29↔T4.en.md:70 ほか）',
        'ガイドの同じ行 THEORY_MAP.md:134',
    ),
    'M09': (
        'T4↔T4.en の manifest 対応で共起 22/22 unit（T4.md:19↔T4.en.md:30・T4.md:21↔T4.en.md:45 ほか）',
        '訳注 translations/T4.en.md:37（tn-01）',
        'ガイドの同じ行 THEORY_MAP.md:12・THEORY_MAP.md:133',
    ),
    'M10': (
        'T4 本文の対訳表記 papers/T4.md:228',
        'T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:228↔T4.en.md:907）',
    ),
    'M11': (
        'T4 本文の対訳表記 papers/T4.md:144',
        'T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:144↔T4.en.md:558）',
    ),
    'M12': (
        'T4 本文の対訳表記 papers/T4.md:144',
        'T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:144↔T4.en.md:558）',
    ),
    'M13': (
        'T4 本文の対訳表記 papers/T4.md:164',
        'T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:85↔T4.en.md:340・T4.md:138↔T4.en.md:529 ほか）',
    ),
    'M14': (
        'T4 本文の対訳表記 papers/T4.md:53',
        'T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:53↔T4.en.md:182）',
    ),
    'M15': (
        'T4↔T4.en の manifest 対応で共起 4/6 unit（T4.md:19↔T4.en.md:30・T4.md:29↔T4.en.md:70 ほか）',
        '読解試験の日英設問 R06・R07・R08',
        'THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13・THEORY_MAP.md:253↔256',
    ),
    'M16': (
        '読解試験の日英設問 R01',
        'THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13',
    ),
    'M17': (
        'ガイドの同じ行 THEORY_MAP.md:238・SOURCE_INDEX.md:33',
        '読解試験の日英設問 R01・R03・R05・R16',
        'THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13',
    ),
    'M18': (
        'THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13',
    ),
    'M19': (
        'ガイドの同じ行 THEORY_MAP.md:238',
    ),
    'M20': (
        'ガイドの同じ行 THEORY_MAP.md:240・FOR_AI_READERS.md:36・llms.txt:13',
        '読解試験の日英設問 R03',
    ),
    'M21': (
        '訳注 translations/T4.en.md:826（tn-16）',
        'ガイドの同じ行 THEORY_MAP.md:239・FOR_AI_READERS.md:35・SOURCE_INDEX.md:36 ほか',
        '読解試験の日英設問 R17',
    ),
    'M22': (
        'ガイドの同じ行 FOR_AI_READERS.md:34',
        '読解試験の日英設問 R16',
    ),
    'M24': (
        'T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:49↔T4.en.md:166・T4.md:51↔T4.en.md:175 ほか）',
    ),
    'M25': (
        'T4↔T4.en の manifest 対応で共起 10/12 unit（T4.md:29↔T4.en.md:70・T4.md:45↔T4.en.md:150 ほか）',
    ),
    'M26': (
        'T4↔T4.en の manifest 対応で共起 3/3 unit（T4.md:75↔T4.en.md:289・T4.md:150↔T4.en.md:581 ほか）',
        '読解試験の日英設問 R01',
    ),
    'M27': (
        'T4↔T4.en の manifest 対応で共起 2/2 unit（T4.md:19↔T4.en.md:30・T4.md:132↔T4.en.md:508）',
        '読解試験の日英設問 R11',
    ),
    'M28': (
        'T4↔T4.en の manifest 対応で共起 2/5 unit（T4.md:69↔T4.en.md:258・T4.md:192↔T4.en.md:760）',
        '訳注 translations/T4.en.md:303（tn-07）',
    ),
    'M30': (
        'T4↔T4.en の manifest 対応で共起 8/8 unit（T4.md:19↔T4.en.md:30・T4.md:45↔T4.en.md:150 ほか）',
        '読解試験の日英設問 R10',
    ),
    'M31': (
        'ガイドの同じ行 SOURCE_INDEX.md:27',
    ),
    'M32': (
        'THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:253↔256',
    ),
}

_ID_RE = re.compile(r"^M[0-9]{2,3}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


@dataclass(frozen=True)
class TermEntry:
    id: str
    forms_ja: tuple[str, ...]
    forms_en: tuple[str, ...]
    sources: tuple[str, ...]  # コーパス内の出所（例 "papers/T4.md:41"）
    approved_on: str


# 著者承認済みの項目（TERMS-0.1.0・承認 2026-09-18・docs/rules/TERMS.md）。
# 出所（sources）は scripts/find_term_sources.py --terms の機械的な検索結果（TERMS-SRC-1.0.0）。
TERMS: tuple[TermEntry, ...] = (
    TermEntry("M01", ('仕様', '専門性の基質'), ('specification', 'Spec.'), SOURCES["M01"], APPROVED_ON),
    TermEntry("M02", ('仕様化費用',), ('specification cost', 'Spec.cost', 'Spec. cost'), SOURCES["M02"], APPROVED_ON),
    TermEntry("M03", ('外化', '外化費用'), ('externalization', 'externalisation', 'Ext.cost', 'externalization cost'), SOURCES["M03"], APPROVED_ON),
    TermEntry("M04", ('事実', '事実認識'), ('Sein', 'Sein-type'), SOURCES["M04"], APPROVED_ON),
    TermEntry("M05", ('価値判断',), ('Sollen', 'Sollen-type'), SOURCES["M05"], APPROVED_ON),
    TermEntry("M06", ('応答可能性', '答える立場'), ('answerability',), SOURCES["M06"], APPROVED_ON),
    TermEntry("M07", ('説明責任',), ('accountability',), SOURCES["M07"], APPROVED_ON),
    TermEntry("M08", ('引き受け',), ('undertaking',), SOURCES["M08"], APPROVED_ON),
    TermEntry("M09", ('自分ごと化',), ('jibungoto-ka',), SOURCES["M09"], APPROVED_ON),
    TermEntry("M10", ('心理的所有',), ('psychological ownership',), SOURCES["M10"], APPROVED_ON),
    TermEntry("M11", ('責任の空隙',), ('responsibility gap',), SOURCES["M11"], APPROVED_ON),
    TermEntry("M12", ('多くの手の問題',), ('the problem of many hands', 'many hands'), SOURCES["M12"], APPROVED_ON),
    TermEntry("M13", ('自惚れ',), ('self-conceit',), SOURCES["M13"], APPROVED_ON),
    TermEntry("M14", ('直接服薬確認療法',), ('DOTS',), SOURCES["M14"], APPROVED_ON),
    TermEntry("M15", ('参加',), ('participation',), SOURCES["M15"], APPROVED_ON),
    TermEntry("M16", ('非移転性',), ('non-transferability', 'non-transferable'), SOURCES["M16"], APPROVED_ON),
    TermEntry("M17", ('尊厳',), ('dignity',), SOURCES["M17"], APPROVED_ON),
    TermEntry("M18", ('可視性',), ('visibility',), SOURCES["M18"], APPROVED_ON),
    TermEntry("M19", ('明晰な没入',), ('lucid absorption',), SOURCES["M19"], APPROVED_ON),
    TermEntry("M20", ('遊び',), ('play',), SOURCES["M20"], APPROVED_ON),
    TermEntry("M21", ('趣味',), ('shumi',), SOURCES["M21"], APPROVED_ON),
    TermEntry("M22", ('知好楽の「楽」',), ('delight',), SOURCES["M22"], APPROVED_ON),
    TermEntry("M24", ('正統性',), ('legitimacy',), SOURCES["M24"], APPROVED_ON),
    TermEntry("M25", ('立場',), ('standing',), SOURCES["M25"], APPROVED_ON),
    TermEntry("M26", ('能力',), ('ability', 'capacities'), SOURCES["M26"], APPROVED_ON),
    TermEntry("M27", ('逆方向',), ('reverse pathway', 'reverse'), SOURCES["M27"], APPROVED_ON),
    TermEntry("M28", ('承認',), ('endorsement', 'endorse', 'approval'), SOURCES["M28"], APPROVED_ON),
    TermEntry("M30", ('相互性',), ('reciprocity', 'reciprocal'), SOURCES["M30"], APPROVED_ON),
    TermEntry("M31", ('主体性',), ('agency',), SOURCES["M31"], APPROVED_ON),
    TermEntry("M32", ('事態',), ('state of affairs',), SOURCES["M32"], APPROVED_ON),
)


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
