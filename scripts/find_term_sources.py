#!/usr/bin/env python3
"""用語対応表の候補（docs/candidates/terms_candidates_v0.md）の「要確認」行 M23〜M31 の出所を機械的に探す。

施工用の道具で、サーバからは使わない。同梱データ（data/）だけを読み、表には何も載せない。

探し方（TERMS-SRC-1.0.0）：
  A. T4 本文の対訳表記：papers/T4.md で「日本語（…英語…）」の形（日本語の直後の全角括弧に英語の語形）。
  B. 英訳 manifest の対応：位置を持つ unit ごとに、原文の範囲（papers/T4.md）に日本語の語形があり、
     英訳の範囲（translations/T4.en.md、訳注を除く）に英語の語形があるもの（共起）。
  C. 訳注：訳注（TN）の本文に日本語と英語の語形が両方あるもの。
  D. ガイド：THEORY_MAP.md・FOR_AI_READERS.md・SOURCE_INDEX.md・llms.txt の同じ行に両方あるもの。
英語の語形は大文字小文字を区別せず単語境界で、日本語は部分文字列で照合する。

  python scripts/find_term_sources.py            # Markdown の表を出力
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from mekiki_reader import corpus as C  # noqa: E402

ROWS = (
    ("M23", ("委任",), ("delegation",)),
    ("M24", ("正統性",), ("legitimacy",)),
    ("M25", ("立場",), ("standing",)),
    ("M26", ("能力",), ("competence", "capability")),
    ("M27", ("逆方向経路", "逆方向の経路"), ("reverse pathway",)),
    ("M28", ("承認",), ("recognition",)),
    ("M29", ("是認",), ("endorsement",)),
    ("M30", ("相互性",), ("reciprocity", "reciprocal")),
    ("M31", ("主体性",), ("agency",)),
)
GUIDES = ("THEORY_MAP.md", "FOR_AI_READERS.md", "SOURCE_INDEX.md", "llms.txt")
# 補足：候補表の語形では見つからない、または別の対応が目立つ行について、近い語形での同じ検索（判定には使わない）
SUPPLEMENT = (
    ("M26", ("能力",), ("ability", "capacities", "capacity")),
    ("M27", ("逆方向",), ("reverse pathway", "reverse")),
    ("M28", ("承認",), ("endorse", "endorsed", "endorsing", "endorses", "endorsement", "approval")),
)


def en_re(form: str) -> re.Pattern:
    return re.compile(r"(?<![A-Za-z0-9-])" + re.escape(form) + r"(?![A-Za-z0-9-])", re.I)


def main() -> None:
    corpus = C.load_corpus()
    print("## 判定（候補表の語形）\n")
    report(corpus, ROWS)
    print("\n## 補足（近い語形・判定には使わない）\n")
    report(corpus, SUPPLEMENT)


def report(corpus, rows) -> None:
    t4 = corpus.lines[C.T4_PATH]
    en = corpus.lines[C.T4EN_PATH]
    idx = corpus.t4en
    note_lines = {n for t in idx.notes for n in range(t.line_start, t.line_end + 1)}
    print("| ID | 日本語 | 英語 | A 対訳表記（T4.md） | B manifest 共起（unit） | C 訳注 | D ガイド | 判定 |")
    print("|---|---|---|---|---|---|---|---|")
    for mid, jas, ens in rows:
        ens_re = [en_re(f) for f in ens]
        a_hits = []
        for no, line in enumerate(t4, 1):
            for ja in jas:
                for m in re.finditer(re.escape(ja) + r"（([^）]*)）", line):
                    if any(r.search(m.group(1)) for r in ens_re):
                        a_hits.append(f"T4.md:{no}「{ja}（{m.group(1)}）」")
        b_both, b_ja = [], 0
        for u in idx.units:
            if u.t_line_start is None:
                continue
            src = "\n".join(t4[u.source_line - 1:u.source_end_line])
            if not any(ja in src for ja in jas):
                continue
            b_ja += 1
            tr = "\n".join(en[n - 1] for n in range(u.t_line_start, u.t_line_end + 1) if n not in note_lines)
            if any(r.search(tr) for r in ens_re):
                b_both.append(f"T4.md:{u.source_line}↔T4.en.md:{u.t_line_start}")
        c_hits = []
        for t in idx.notes:
            body = "\n".join(en[t.line_start - 1:t.line_end])
            if any(ja in body for ja in jas) and any(r.search(body) for r in ens_re):
                c_hits.append(f"{t.id}（T4.en.md:{t.line_start}）")
        d_hits = []
        for g in GUIDES:
            for no, line in enumerate(corpus.lines[g], 1):
                if any(ja in line for ja in jas) and any(r.search(line) for r in ens_re):
                    d_hits.append(f"{g}:{no}")
        found = bool(a_hits or b_both or c_hits or d_hits)
        b_text = f"{len(b_both)}/{b_ja}" + (("：" + "・".join(b_both[:4]) + ("…" if len(b_both) > 4 else "")) if b_both else "")
        print(f"| {mid} | {'／'.join(jas)} | {' / '.join(ens)} | {'・'.join(a_hits) or '—'} | {b_text} | "
              f"{'・'.join(c_hits) or '—'} | {'・'.join(d_hits) or '—'} | {'出所あり' if found else '出所なし'} |")


if __name__ == "__main__":
    main()
