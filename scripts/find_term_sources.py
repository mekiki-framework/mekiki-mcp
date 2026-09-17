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

  python scripts/find_term_sources.py            # 候補 M23〜M31（v0）の判定表を出力
  python scripts/find_term_sources.py --terms    # terms.py の全項目の出所を検索し、表と SOURCES の案を出力

--terms では、上の A〜D に加えて次も探す。
  E. 読解試験：tests/reading_cases.json の同じ設問で、question_ja に日本語、question_en に英語の語形があるもの。
  F. THEORY_MAP.md の「Japanese public wording」節（<a id="t5-japanese-expressions">）：「literal translation」と
     明記された行に日本語の語形があり、その英語側に英語の語形があるもの。英語側は、題の直訳の行なら
     THEORY_MAP.md 冒頭の T5 の英題の行、文の直訳の行なら同節の「English source sentence」の行。
  どれにも当たらない項目は、日本語・英語それぞれの語形が同梱ファイルのどこに出るかだけを記録する（対訳の出所なし）。
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
    if "--terms" in sys.argv[1:]:
        terms_report(corpus)
        return
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


def evidence(corpus, jas, ens) -> dict:
    t4 = corpus.lines[C.T4_PATH]
    en = corpus.lines[C.T4EN_PATH]
    idx = corpus.t4en
    note_lines = {n for t in idx.notes for n in range(t.line_start, t.line_end + 1)}
    ens_re = [en_re(f) for f in ens]
    ev = {"A": [], "B": [], "B_ja": 0, "C": [], "D": [], "E": [], "F": [], "ja_only": [], "en_only": []}
    for no, line in enumerate(t4, 1):
        for ja in jas:
            for m in re.finditer(re.escape(ja) + r"（([^）]*)）", line):
                if any(r.search(m.group(1)) for r in ens_re):
                    ev["A"].append(f"papers/T4.md:{no}")
    for u in idx.units:
        if u.t_line_start is None:
            continue
        src = "\n".join(t4[u.source_line - 1:u.source_end_line])
        if not any(ja in src for ja in jas):
            continue
        ev["B_ja"] += 1
        tr = "\n".join(en[n - 1] for n in range(u.t_line_start, u.t_line_end + 1) if n not in note_lines)
        if any(r.search(tr) for r in ens_re):
            ev["B"].append(f"T4.md:{u.source_line}↔T4.en.md:{u.t_line_start}")
    for t in idx.notes:
        body = "\n".join(en[t.line_start - 1:t.line_end])
        if any(ja in body for ja in jas) and any(r.search(body) for r in ens_re):
            ev["C"].append(f"translations/T4.en.md:{t.line_start}（{t.id}）")
    for g in GUIDES:
        for no, line in enumerate(corpus.lines[g], 1):
            if any(ja in line for ja in jas) and any(r.search(line) for r in ens_re):
                ev["D"].append(f"{g}:{no}")
    for case in corpus.reading_cases["cases"]:
        if any(ja in case["question_ja"] for ja in jas) and any(r.search(case["question_en"]) for r in ens_re):
            ev["E"].append(f"tests/reading_cases.json {case['id']}")
    tm = corpus.lines["THEORY_MAP.md"]
    start = next(n for n, line in enumerate(tm, 1) if 'id="t5-japanese-expressions"' in line)
    end = next((n - 1 for n, line in enumerate(tm, 1) if n > start + 1 and line.startswith(("## ", "<a id="))), len(tm))
    sentence_rows = [n for n in range(start, end + 1) if "English source sentence" in tm[n - 1]]
    title_rows = [n for n, line in enumerate(tm, 1) if line.startswith("- **T5 — ")]
    for a in range(start, end + 1):
        row = tm[a - 1]
        if "literal translation" not in row.lower() or not any(ja in row for ja in jas):
            continue
        partners = title_rows if "title" in row.lower() else sentence_rows if "sentence" in row.lower() else []
        for b in partners:
            if any(r.search(tm[b - 1]) for r in ens_re):
                ev["F"].append(f"THEORY_MAP.md:{a}↔{b}")
    ev["A"] = sorted(set(ev["A"]), key=lambda x: int(x.rsplit(":", 1)[1]))
    if not any(ev[k] for k in "ABCDEF"):
        for path in sorted(C.ALLOWED_PATHS, key=lambda p: (not p.startswith("papers/"), p)):
            if not path.endswith((".md", ".txt")):
                continue
            for n, line in enumerate(corpus.lines[path], 1):
                if any(ja in line for ja in jas):
                    ev["ja_only"].append(f"{path}:{n}")
                if any(r.search(line) for r in ens_re):
                    ev["en_only"].append(f"{path}:{n}")
    return ev


def summarize(ev) -> tuple[str, ...]:
    out = []
    if ev["A"]:
        out.append("T4 本文の対訳表記 " + "・".join(ev["A"][:3]) + (" ほか" if len(ev["A"]) > 3 else ""))
    if ev["B"]:
        out.append(f"T4↔T4.en の manifest 対応で共起 {len(ev['B'])}/{ev['B_ja']} unit（" + "・".join(ev["B"][:2])
                   + (" ほか" if len(ev["B"]) > 2 else "") + "）")
    if ev["C"]:
        out.append("訳注 " + "・".join(ev["C"][:2]))
    if ev["D"]:
        out.append("ガイドの同じ行 " + "・".join(ev["D"][:3]) + (" ほか" if len(ev["D"]) > 3 else ""))
    if ev["E"]:
        out.append("読解試験の日英設問 " + "・".join(x.split(" ")[1] for x in ev["E"][:4]))
    if ev["F"]:
        out.append("THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） " + "・".join(ev["F"][:2]))
    if not out:
        out.append("対訳の出所なし（日本語形の出現 " + ("・".join(ev["ja_only"][:3]) or "0件") + "）")
        out.append("英語形の出現 " + ("・".join(ev["en_only"][:3]) + (" ほか" if len(ev["en_only"]) > 3 else "") or "0件"))
    return tuple(out)


def terms_report(corpus) -> None:
    from mekiki_reader import terms as TM
    print("| ID | 日本語 | 英語 | 出所（機械的な検索） |")
    print("|---|---|---|---|")
    sources = {}
    for e in TM.TERMS:
        ev = evidence(corpus, e.forms_ja, e.forms_en)
        s = summarize(ev)
        sources[e.id] = s
        print(f"| {e.id} | {'／'.join(e.forms_ja)} | {' / '.join(e.forms_en)} | {'；'.join(s) or '出所なし'} |")
    print()
    print("SOURCES = {")
    for k, v in sources.items():
        print(f"    {k!r}: {v!r},")
    print("}")


if __name__ == "__main__":
    main()
