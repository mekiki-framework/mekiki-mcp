#!/usr/bin/env python3
"""パターン候補一覧（docs/candidates/patterns_candidates_v0.md）の「採用」行を読み、関連原文を解決する。

施工用の道具で、サーバからは使わない。同梱データ（data/）と候補一覧だけを読む。

解決の規則（PATTERNS-SRC-1.0.0）：
  1. `Tn §x.y (anchor)` / `Tn §x.y` / `Tn abstract (anchor)` → source_manifest の節。アンカーが書かれていれば
     導出したものと一致すること。`：原文 "…"` が続く行は、その文が一度だけ現れる行と文字位置に解決する。
  2. `T5-A1` などの主張ID（`・S1` のような省略を含む） → claims/t5.json の source_locator の行と節。
  3. `FR Lnn`（複数・範囲可） → FOR_AI_READERS.md の行。
  4. `THEORY_MAP Tn「見出し」`（`Tn「見出し」` の略記を含む） → THEORY_MAP.md の見出しの節。見出しが無ければ
     太字の項目行、それも無ければその文字列を含む行。番号つきの項目（`3–4` など）はその項目の行。
     `：行 "…"` が続くときは、その節の中でその文字列を含む行が一つだけであることを確かめ、その行に解決する。
  5. 上のどれにも当たらない参照は未解決とし、その行は載せない。近い見出しなどを候補として報告する。

  python scripts/build_patterns.py            # 解決の結果・未解決の行・生成する定義を出力
  python scripts/build_patterns.py --write    # mekiki_reader/patterns.py と docs/rules/PATTERNS.md を書き換える
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from mekiki_reader import corpus as C  # noqa: E402

CANDIDATES = REPO_ROOT / "docs/candidates/patterns_candidates_v0.md"
TM_PATH = "THEORY_MAP.md"
FR_PATH = "FOR_AI_READERS.md"
APPROVED_ON = "2026-09-18"
MATCH_RULE = "PATTERNS-MATCH-1.0.0"  # patterns.MATCH_RULE と同じ値（正準形に入る）
PATTERNS_VERSION = "PATTERNS-0.1.1"


class Unresolved(Exception):
    def __init__(self, ref: str, hint: str = "") -> None:
        self.ref, self.hint = ref, hint
        super().__init__(f"{ref} :: {hint}")


def headings(lines):
    out = []
    paper = None
    for no, line in enumerate(lines, 1):
        m = re.match(r"^(#{2,6}) (.+)$", line)
        if m:
            if m.group(1) == "##" and re.match(r"^T[1-5]:", m.group(2)):
                paper = m.group(2).split(":")[0]
            out.append((no, len(m.group(1)), m.group(2), paper))
    return out


def heading_range(lines, heads, idx):
    no, level, _title, _paper = heads[idx]
    end = len(lines)
    for n2, l2, _t, _p in heads:
        if n2 > no and l2 <= level:
            end = n2 - 1
            break
    return no, end


def resolve_theory_map(corpus, ref: str):
    """THEORY_MAP の参照を (path, start, end) に解決する。"""
    lines = corpus.lines[TM_PATH]
    heads = headings(lines)
    m = re.search(r"(?:THEORY_MAP\s*)?(T[1-5])?\s*「([^」]+)」(?:\s*([0-9]+)(?:[-–]([0-9]+))?)?", ref)
    if not m:
        if "日本語用語表" in ref:
            for i, (_no, _lv, title, _p) in enumerate(heads):
                if title.startswith("Japanese terms"):
                    return (TM_PATH, *heading_range(lines, heads, i))
        raise Unresolved(ref, "THEORY_MAP の参照の形が読めない")
    paper, label, num_from, num_to = m.group(1), m.group(2), m.group(3), m.group(4)
    row = re.search(r"行 \"([^\"]+)\"", ref)
    cand = [i for i, (_no, _lv, title, p) in enumerate(heads) if title == label and (paper is None or p == paper)]
    if len(cand) == 1:
        start, end = heading_range(lines, heads, cand[0])
        if row:
            hit = [n for n in range(start, end + 1) if row.group(1) in lines[n - 1]]
            if len(hit) != 1:
                raise Unresolved(ref, f"「{label}」の中で 行 \"{row.group(1)}\" に当たる行が {len(hit)} 本ある")
            return (TM_PATH, hit[0], hit[0])
        if num_from:
            items = [n for n in range(start, end + 1) if re.match(rf"^{num_from}\. ", lines[n - 1])]
            last = [n for n in range(start, end + 1) if re.match(rf"^{num_to or num_from}\. ", lines[n - 1])]
            if not items or not last:
                near = [lines[n - 1][:60] for n in range(start, end + 1) if re.match(r"^[0-9]+\. ", lines[n - 1])]
                raise Unresolved(ref, f"「{label}」に番号つきの項目 {num_from} がない。候補：" +
                                 (f"番号つきの項目を持つ節 " + "・".join(
                                     t for _n, _l, t, _p in heads if any(
                                         re.match(r"^[0-9]+\. ", lines[k - 1])
                                         for k in range(*heading_range(lines, heads, [i for i, h in enumerate(heads)
                                                                                      if h[2] == t][0]))))
                                  if not near else "この節の項目：" + "・".join(near[:3])))
            return (TM_PATH, items[0], last[-1])
        return (TM_PATH, start, end)
    if len(cand) > 1:
        raise Unresolved(ref, f"「{label}」が {len(cand)} か所にある（論文の指定が要る）")
    bold = [n for n, line in enumerate(lines, 1) if re.search(r"\*\*" + re.escape(label) + r"[.:]?\*\*", line)]
    if len(bold) == 1:
        return (TM_PATH, bold[0], bold[0])
    plain = [n for n, line in enumerate(lines, 1) if label in line]
    if len(plain) == 1:
        return (TM_PATH, plain[0], plain[0])
    similar = [t for _n, _l, t, _p in heads if label.split()[0] in t][:3]
    raise Unresolved(ref, f"「{label}」が見出し・太字・本文に一意に見つからない（{len(plain)} 行が一致）。"
                          f"近い見出し：{'・'.join(similar) or 'なし'}")


def resolve_paper(corpus, ref: str):
    out = []
    pid = re.match(r"^(T[1-5])\b", ref).group(1)
    paper = corpus.papers[pid]
    quoted = re.search(r"原文 \"([^\"]+)\"", ref)
    for m in re.finditer(r"(?:§([0-9]+(?:\.[0-9]+)*)|abstract)\s*(?:\(([a-z0-9-]+)\))?", ref):
        sec_no, anchor = m.group(1), m.group(2)
        derived = f"{pid.lower()}-" + (sec_no.replace(".", "-") if sec_no else "abstract")
        if anchor and anchor != derived:
            raise Unresolved(ref, f"アンカー {anchor} が節番号から導いた {derived} と合わない")
        sec = paper.section(derived)
        if sec is None:
            raise Unresolved(ref, f"節 {derived} が source_manifest にない")
        if quoted:
            text = corpus.texts[paper.path]
            if text.count(quoted.group(1)) == 1:
                off = text.index(quoted.group(1))
                line = text.count("\n", 0, off) + 1
                if sec.line_start <= line <= sec.line_end:
                    col = off - (text.rindex("\n", 0, off) + 1 if "\n" in text[:off] else 0)
                    out.append((paper.path, line, line, derived, col, col + len(quoted.group(1))))
                    continue
        out.append((paper.path, sec.line_start, sec.line_end, derived, None, None))
    if not out:
        raise Unresolved(ref, "節の指定が読めない")
    return out


def resolve_claims(corpus, ref: str):
    ids = re.findall(r"T5-([A-Z]+[0-9]+)|(?<=[・、])([A-Z]+[0-9]+)", ref)
    flat = [a or b for a, b in ids if a or b]
    out = []
    by_id = {c["id"]: c for c in corpus.ledger["claims"]}
    for suffix in flat:
        cid = f"T5-{suffix}"
        c = by_id.get(cid)
        if c is None:
            raise Unresolved(ref, f"主張 {cid} が台帳にない")
        loc = c["source_locator"]
        anchor = loc["section_url"].split("#")[1]
        out.append((loc["path"], loc["line_start"], loc["line_end"], anchor, None, None))
    return out


def resolve_fr(corpus, ref: str):
    out = []
    n_lines = len(corpus.lines[FR_PATH])
    for m in re.finditer(r"L([0-9]+)(?:[-–]([0-9]+))?", ref):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if not (1 <= a <= b <= n_lines):
            raise Unresolved(ref, f"FOR_AI_READERS.md に {a}-{b} 行はない")
        out.append((FR_PATH, a, b, None, None, None))
    return out


def resolve_item(corpus, item: str):
    item = item.strip()
    if not item:
        return []
    if item.startswith("THEORY_MAP") or re.match(r"^T[1-5]\s*「", item) or "日本語用語表" in item:
        return [(*resolve_theory_map(corpus, item), None, None, None)]
    if item.startswith("FR "):
        return resolve_fr(corpus, item)
    if re.match(r"^T5-[A-Z]", item):
        return resolve_claims(corpus, item)
    if re.match(r"^T[1-5]（", item):
        pid = item[:2]
        paper = corpus.papers[pid]
        key = re.match(r"^T[1-5]（([^・）]+)", item).group(1)
        keys = [key] + ([key.split("の")[0]] if "の" in key else [])
        hits = []
        for n, line in enumerate(corpus.lines[paper.path], 1):
            if any(k in line for k in keys):
                sec = paper.section_for_line(n)
                hits.append(f"{paper.path}:{n}（{sec.id if sec else '?'}）")
        raise Unresolved(item, f"節が書かれていない。{'／'.join(keys)} を含む行：" + ("・".join(hits) if hits else "0件"))
    if re.match(r"^T[1-5]\s*§|^T[1-5]\s*abstract", item):
        refs = resolve_paper(corpus, item)
        if "T5-" in item:
            refs += resolve_claims(corpus, item[item.index("T5-"):])
        return refs
    raise Unresolved(item, "参照の形が読めない")


def parse_rows():
    rows = []
    for line in CANDIDATES.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("| P") or line.count("|") != 9:
            continue
        c = [x.strip() for x in line.split("|")[1:-1]]
        rows.append({"id": c[0], "type": c[1], "forms": c[2], "refs": c[3], "note": c[4],
                     "origin": c[5], "recommend": c[6]})
    return rows


def main() -> None:
    corpus = C.load_corpus()
    rows = parse_rows()
    adopted = [r for r in rows if r["recommend"] == "採用"]
    held = [r for r in rows if r["recommend"] != "採用"]
    resolved, failed = [], []
    for r in adopted:
        refs, problems = [], []
        for item in r["refs"].split("；"):
            try:
                refs += resolve_item(corpus, item)
            except Unresolved as e:
                problems.append(f"{e.ref} → {e.hint}")
        (failed if problems else resolved).append({**r, "sources": refs, "problems": problems})
    print(f"候補 {len(rows)} 行：採用 {len(adopted)}・保留 {len(held)}（{'・'.join(x['id'] for x in held)}）")
    print(f"解決 {len(resolved)} 行・未解決 {len(failed)} 行\n")
    for r in failed:
        print(f"未解決 {r['id']}：{r['type']}")
        for p in r["problems"]:
            print(f"    {p}")
    if "--write" in sys.argv[1:]:
        write_patterns(resolved)
        write_doc(resolved, failed, held)
        print("\nwrote mekiki_reader/patterns.py, docs/rules/PATTERNS.md")
        check = subprocess.run(  # noqa: S603 - 施工用の道具。生成の直後に文書整合まで通す（Codex② 6）
            [sys.executable, "-m", "pytest", "-q", "tests/test_tools.py::test_rule_documents_match_the_tables"],
            cwd=REPO_ROOT, capture_output=True, text=True)
        print(check.stdout.strip().splitlines()[-1] if check.stdout.strip() else "(no output)")
        if check.returncode != 0:
            raise SystemExit("生成のあとの文書整合試験が通らない（規則文書を直すこと）")


def forms_of(row) -> list[str]:
    return [f.strip() for f in row["forms"].split("／") if f.strip()]


def canonical_hash(resolved) -> str:
    """これから書き出す表の正準 JSON の SHA-256（patterns.table_rows() と同じ形）。

    定数を書き換える前に値が要るので、ここで作る。書き出したあとに reload して突き合わせる。
    """
    rows = []
    for r in resolved:
        rows.append({
            "id": r["id"], "version": PATTERNS_VERSION, "match_rule": MATCH_RULE,
            "approved_on": APPROVED_ON, "surface_forms": forms_of(r),
            "related_sources": [{"path": path, "line_start": a, "line_end": b, "anchor": anchor,
                                 "char_start": c0, "char_end": c1}
                                for path, a, b, anchor, c0, c1 in r["sources"]],
        })
    raw = json.dumps({"version": PATTERNS_VERSION, "patterns": rows},
                     sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_patterns(resolved) -> None:
    p = REPO_ROOT / "mekiki_reader/patterns.py"
    t = p.read_text(encoding="utf-8")
    body = [f"# 著者承認済みのパターン（{PATTERNS_VERSION}・承認 {APPROVED_ON}・docs/rules/PATTERNS.md）。",
            "# 候補は docs/candidates/patterns_candidates_v0.md、関連原文の解決は scripts/build_patterns.py。",
            "PATTERNS: tuple[Pattern, ...] = ("]
    for r in resolved:
        body.append(f'    Pattern(')
        body.append(f'        id={r["id"]!r},')
        body.append(f'        version=PATTERNS_VERSION,')
        body.append(f'        surface_forms=(')
        for f in forms_of(r):
            body.append(f'            {f!r},')
        body.append(f'        ),')
        body.append(f'        related_sources=(')
        for path, a, b, anchor, c0, c1 in r["sources"]:
            extra = f', char_start={c0}, char_end={c1}' if c0 is not None else ""
            body.append(f'            RelatedSource({path!r}, {a}, {b}, {anchor!r}{extra}),')
        body.append(f'        ),')
        body.append(f'        approved_on=APPROVED_ON,')
        body.append(f'    ),')
    body.append(")")
    marks = ("# 著者承認済みのパターン（", "# 承認済みのパターンだけを載せる。初版は空。")  # 二度目以降は自分が書いた見出し
    mark = next((m for m in marks if m in t), None)
    if mark is None:
        raise SystemExit("patterns.py に差し込み位置の目印がない")
    start = t.index(mark)
    end = t.index("def validate_patterns(")
    t = t[:start] + "\n".join(body) + "\n\n\n" + t[end:]
    t = re.sub(r'PATTERNS_VERSION = "[^"]*"', f'PATTERNS_VERSION = "{PATTERNS_VERSION}"', t, count=1)
    t = re.sub(r'APPROVED_ON(?:: str \| None)? = (?:None|"[^"]*")', f'APPROVED_ON = "{APPROVED_ON}"', t, count=1)
    # 表とそろえて定数も書き換える（ここを忘れると、次の import で必ず落ちる）。
    new_hash = canonical_hash(resolved)
    t, n = re.subn(r'PATTERNS_TABLE_SHA256 = "[0-9a-f]{64}"', f'PATTERNS_TABLE_SHA256 = "{new_hash}"', t, count=1)
    if n != 1:
        raise SystemExit("patterns.py に PATTERNS_TABLE_SHA256 の行が無い（生成器を直すこと）")
    p.write_text(t, encoding="utf-8")


def table_hash() -> str:
    """書き出した patterns.py を読み直して表の SHA-256 を得る（定数との突き合わせも兼ねる）。"""
    import importlib

    from mekiki_reader import patterns as _patterns

    reloaded = importlib.reload(_patterns)  # 定数と食い違えば、ここで RuntimeError になる
    return reloaded.table_sha256()


def write_doc(resolved, failed, held) -> None:
    lines = [
        "# PATTERNS — check_compressions の語形",
        "",
        "| 項目 | 値 |",
        "|---|---|",
        f"| 規則ID・版 | 一覧 {PATTERNS_VERSION}（{len(resolved)}件）・照合 PATTERNS-MATCH-1.0.0 |",
        f"| 表の SHA-256 | `{table_hash()}`（`patterns.table_sha256()` が import 時に照合。Q49） |",
        f"| 状態 | 確定（著者承認 {APPROVED_ON}。起草＝検査室・SPEC §10） |",
        "| 実装 | `mekiki_reader/patterns.py`・`mekiki_reader/tools.py`（`_check_compressions`） |",
        "| 候補・解決 | `docs/candidates/patterns_candidates_v0.md`・`scripts/build_patterns.py`（PATTERNS-SRC-1.0.0） |",
        "",
        "## 照合（PATTERNS-MATCH-1.0.0）",
        "",
        "1. 入力と語形を SEARCH-1.0.0 の畳み込み（NFC-IN〔入力のみ〕・WS-ZW・WS-COLLAPSE・WIDTH・QUOTE-CURLY・ASCII 小文字化）にかける。",
        "2. ASCII だけの語形は単語境界（前後が `[a-z0-9'-]` 以外）で、それ以外は部分文字列で、重ならない出現をすべて拾う。",
        "3. 一致したパターンごとに、関連原文ごとの結果を一つ作る。並びは（入力中の最初の一致位置、パターン id、関連原文の順）。",
        "4. payload：pattern_id・pattern_version・matched（語形・入力中の文字位置。上限20件）・needs_context_review=true・"
        "source_excerpt（関連原文の行をそのまま。1000字を超えると切って `source_excerpt_truncated` を立てる）。判定を表す欄は持たない。",
        "5. limitations に契約文（CONTRACT・FORMS）と件数（PATTERNS）を必ず入れる。一致ゼロ・パターン0件でも status は ok。",
        "",
        "## 関連原文の解決（PATTERNS-SRC-1.0.0）",
        "",
        "論文の節は source_manifest の節 id と行範囲に、主張IDは claims/t5.json の source_locator に、"
        "`FR Lnn` は FOR_AI_READERS.md の行に、THEORY_MAP の「見出し」はその節（見出しが無ければ太字の項目行・本文の行）に解決する。"
        "`：原文 \"…\"` が添えられた参照は、その文が一度だけ現れる行と文字位置に解決する。",
        "",
        f"## 一覧（{PATTERNS_VERSION}・承認 {APPROVED_ON}）",
        "",
        "| ID | 型（保ちたい区別） | 登録語形 | 関連原文（解決後の locator） |",
        "|---|---|---|---|",
    ]
    for r in resolved:
        locs = []
        for path, a, b, anchor, c0, c1 in r["sources"]:
            s = f"{path}:{a}" + (f"-{b}" if b != a else "")
            if c0 is not None:
                s += f"（{c0}-{c1}字）"
            if anchor:
                s += f"（{anchor}）"
            locs.append(s)
        lines.append(f"| {r['id']} | {r['type']} | {' / '.join(forms_of(r))} | {'・'.join(locs)} |")
    lines += ["", "## 載せなかった行", ""]
    for r in failed:
        lines.append(f"- {r['id']}（{r['type']}）：関連原文を解決できない。{'／'.join(r['problems'])}")
    for r in held:
        lines.append(f"- {r['id']}（{r['type']}）：候補一覧で「保留」。")
    lines.append("")
    (REPO_ROOT / "docs/rules/PATTERNS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
