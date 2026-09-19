"""引用照合と語句検索のための正規化（NORM-1.2.0・docs/rules/NORM.md）。

明示の対応表だけを使い、NFKC は使わない。`unicodedata.normalize` は入力側の NFC 合成（NFC-IN）だけに使う
（明示の例外。正準等価の合成で互換変換ではなく、同梱データは全ファイル NFC 済み）。
文脈の判定（CJK に挟まれた空白、数字に接する句読点）は、写像する前の元の文字で行う。
正規化後の各文字は、元の文字列上の区間 [start, end) を持つ。
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass

NORM_VERSION = "NORM-1.2.0"
SEARCH_FOLD_VERSION = "SEARCH-1.1.0"  # 検索用の畳み込み（SEARCH 規則の一部。畳み込み自体は 1.0.0 と同じ）

WHITESPACE = frozenset(map(chr, (0x09, 0x0A, 0x0D, 0x20, 0xA0, 0x202F, 0x205F, 0x3000, *range(0x2000, 0x200B))))
ZERO_WIDTH = frozenset(map(chr, (0x200B, 0x2060, 0xFEFF)))
CJK_RANGES = (
    (0x3001, 0x303F),
    (0x3040, 0x309F),
    (0x30A0, 0x30FF),
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xFF01, 0xFF60),
)
HIRAGANA_RANGE = (0x3040, 0x309F)
DIGITS = frozenset(map(chr, (*range(0x30, 0x3A), *range(0xFF10, 0xFF1A))))
WIDTH_ASCII_RANGE = (0xFF01, 0xFF5E)
WIDTH_EXCLUDED = frozenset(map(chr, (0xFF0C, 0xFF0E, 0xFF0D, 0xFF0B, 0xFF1C, 0xFF1D, 0xFF1E, 0xFF5E)))  # ，．－＋＜＝＞～
COMMA_CLASS = frozenset(map(chr, (0x3001, 0xFF0C, 0xFF64, 0x2C)))  # 、，､,
COMMA_REP = chr(0x3001)  # 、
PERIOD_CLASS = frozenset(map(chr, (0x3002, 0xFF0E, 0xFF61, 0x2E)))  # 。．｡.
PERIOD_REP = chr(0x3002)  # 。
PERIOD_LEADING_DIGIT_PROTECTED = frozenset(map(chr, (0x2E, 0xFF0E)))  # 直後が数字なら写像しない
QUOTE_MAP = {chr(0x2018): "'", chr(0x2019): "'", chr(0x201C): '"', chr(0x201D): '"'}  # ‘’“”
MIDDOT_MAP = {chr(0xFF65): chr(0x30FB)}  # ･→・
# 強調記号（Markdown の **…**・*…*・_…_）。引用照合（NORM）でだけ取り除く（NORM-1.1.0・検収の観察 c）。
# 全角の＊・＿も同じ記号として扱う。検索の畳み込み（SEARCH）には使わない。
EMPHASIS_MARKS = frozenset(map(chr, (0x2A, 0x5F, 0xFF0A, 0xFF3F)))  # * _ ＊ ＿
_HALF = "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ｢｣"
_FULL = "ヲァィゥェォャュョッーアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン゛゜「」"
assert len(_HALF) == len(_FULL) == 60
KANA_MAP = dict(zip(_HALF, _FULL))
VOICED_MARK = "ﾞ"
SEMI_VOICED_MARK = "ﾟ"
VOICED = {**{c: chr(ord(c) + 1) for c in "カキクケコサシスセソタチツテトハヒフヘホ"}, "ウ": "ヴ"}
SEMI_VOICED = {c: chr(ord(c) + 2) for c in "ハヒフヘホ"}

RULE_IDS = ("NFC-IN", "WS-ZW", "WS-CJK", "WS-COLLAPSE", "WIDTH-ASCII", "WIDTH-KANA",
            "PUNCT-COMMA", "PUNCT-PERIOD", "PUNCT-MIDDOT", "QUOTE-CURLY", "ASCII-LOWER", "MARK-EMPH")


def _table() -> dict:
    return {
        "version": NORM_VERSION,
        "whitespace": sorted(ord(c) for c in WHITESPACE),
        "zero_width": sorted(ord(c) for c in ZERO_WIDTH),
        "cjk_ranges": [list(r) for r in CJK_RANGES],
        "hiragana_range": list(HIRAGANA_RANGE),
        "digits": sorted(ord(c) for c in DIGITS),
        "width_ascii_range": list(WIDTH_ASCII_RANGE),
        "width_excluded": sorted(ord(c) for c in WIDTH_EXCLUDED),
        "comma_class": sorted(ord(c) for c in COMMA_CLASS),
        "comma_rep": ord(COMMA_REP),
        "period_class": sorted(ord(c) for c in PERIOD_CLASS),
        "period_rep": ord(PERIOD_REP),
        "period_leading_digit_protected": sorted(ord(c) for c in PERIOD_LEADING_DIGIT_PROTECTED),
        "quote_map": sorted([ord(k), ord(v)] for k, v in QUOTE_MAP.items()),
        "middot_map": sorted([ord(k), ord(v)] for k, v in MIDDOT_MAP.items()),
        "emphasis_marks": sorted(ord(c) for c in EMPHASIS_MARKS),
        "kana_map": sorted([ord(k), ord(v)] for k, v in KANA_MAP.items()),
        "voiced": sorted([ord(k), ord(v)] for k, v in VOICED.items()),
        "semi_voiced": sorted([ord(k), ord(v)] for k, v in SEMI_VOICED.items()),
    }


def table_sha256() -> str:
    raw = json.dumps(_table(), sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


# 表の正準 JSON の SHA-256（Q49）。表を変えたら版を上げ、この値と docs/rules/NORM.md を更新する。
NORM_TABLE_SHA256 = "19f90a79f945e17050264999caf4cd06dbe1056af0272ebfe079a9e10b16f6f0"
if table_sha256() != NORM_TABLE_SHA256:  # pragma: no cover - 表と定数の食い違いは import 時に止める
    raise RuntimeError(f"NORM table hash mismatch: {table_sha256()}")


def is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in CJK_RANGES)


KANA_KANJI_RANGES = ((0x3040, 0x30FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF))


def has_kana_kanji(s: str) -> bool:
    """仮名・漢字を一字でも含むか（引用の最小長の判定に使う。句読点や全角英数は含めない）。"""
    return any(lo <= ord(c) <= hi for c in s for lo, hi in KANA_KANJI_RANGES)


def is_hiragana_only(s: str) -> bool:
    lo, hi = HIRAGANA_RANGE
    return bool(s) and all(lo <= ord(c) <= hi for c in s)


def is_ascii(s: str) -> bool:
    return all(ord(c) < 128 for c in s)


@dataclass(frozen=True)
class Normalized:
    """正規化の結果。spans[i] は text[i] の元の区間、tags[i] はその文字を変えた規則（無ければ ""。複数は "+" でつなぐ）。

    drops は落とした元の区間 (直後の正規化位置, start, end, 規則)。source は正規化した元の文字列
    （入力側では NFC 合成後）。
    """

    text: str
    spans: tuple[tuple[int, int], ...]
    tags: tuple[str, ...]
    drops: tuple[tuple[int, int, int, str], ...]
    source: str
    nfc_applied: bool


def _normalize(s: str, *, nfc: bool, ws_cjk: bool, punct: bool, lower: bool, emph: bool = False) -> Normalized:
    src = unicodedata.normalize("NFC", s) if nfc else s
    nfc_applied = nfc and src != s
    n = len(src)
    out: list[str] = []
    spans: list[tuple[int, int]] = []
    tags: list[str] = []
    drops: list[tuple[int, int, int, str]] = []

    def significant(k: int) -> bool:
        return (src[k] not in WHITESPACE and src[k] not in ZERO_WIDTH
                and not (emph and src[k] in EMPHASIS_MARKS))

    def is_digit_at(k: int) -> bool:
        return 0 <= k < n and src[k] in DIGITS

    i = 0
    last_space_end = -1  # 直前に空白一つとして出した並びの終わり（強調記号だけを挟んだ次の並びはそこへ畳む）
    while i < n:
        ch = src[i]
        if ch in WHITESPACE:
            j = i
            while j < n and (src[j] in WHITESPACE or src[j] in ZERO_WIDTH):
                j += 1
            if (emph and out and out[-1] == " " and last_space_end >= 0
                    and all(src[k] in EMPHASIS_MARKS or src[k] in ZERO_WIDTH for k in range(last_space_end, i))):
                # 「空白 記号 空白」：記号を落とすと空白が二つ並ぶので、後ろの並びを前の空白へ畳む（規則9）。
                # 並びの中のゼロ幅文字は WS-ZW として記録する（規則7）
                has_zw = any(c in ZERO_WIDTH for c in src[i:j])
                drops.append((len(out), i, j, "WS-COLLAPSE" + ("+WS-ZW" if has_zw else "")))
                last_space_end = j
                i = j
                continue
            # 左右とも「意味のある文字」まで探す（強調記号は空白の文脈判定に数えない。規則8・Codex③ 10）
            prev = next((src[k] for k in range(i - 1, -1, -1) if significant(k)), None)
            nxt = next((src[k] for k in range(j, n) if significant(k)), None)
            run = src[i:j]
            ws_only = "".join(c for c in run if c not in ZERO_WIDTH)
            has_zw = len(ws_only) != len(run)
            if prev is None or nxt is None or (ws_cjk and is_cjk(prev) and is_cjk(nxt)):
                rule = "WS-COLLAPSE" if prev is None or nxt is None else "WS-CJK"
                drops.append((len(out), i, j, rule + ("+WS-ZW" if has_zw else "")))
            else:
                out.append(" ")
                spans.append((i, j))
                parts = ([] if ws_only == " " else ["WS-COLLAPSE"]) + (["WS-ZW"] if has_zw else [])
                tags.append("+".join(parts))
                last_space_end = j
            i = j
            continue
        if ch in ZERO_WIDTH:
            drops.append((len(out), i, i + 1, "WS-ZW"))
            i += 1
            continue
        if emph and ch in EMPHASIS_MARKS:  # MARK-EMPH：強調記号を落とす（差分として記録される）
            drops.append((len(out), i, i + 1, "MARK-EMPH"))
            i += 1
            continue
        if ch in KANA_MAP and i + 1 < n and src[i + 1] in (VOICED_MARK, SEMI_VOICED_MARK):
            base = KANA_MAP[ch]
            table = VOICED if src[i + 1] == VOICED_MARK else SEMI_VOICED
            if base in table:
                out.append(table[base])
                spans.append((i, i + 2))
                tags.append("WIDTH-KANA")
                i += 2
                continue
        mapped, tag = ch, ""
        cp = ord(ch)
        if punct and ch in COMMA_CLASS:
            if not (is_digit_at(i - 1) and is_digit_at(i + 1)):
                mapped = COMMA_REP
                tag = "PUNCT-COMMA" if ch != COMMA_REP else ""
        elif punct and ch in PERIOD_CLASS:
            protected = (is_digit_at(i - 1) and is_digit_at(i + 1)) or (
                ch in PERIOD_LEADING_DIGIT_PROTECTED and is_digit_at(i + 1))
            if not protected:
                mapped = PERIOD_REP
                tag = "PUNCT-PERIOD" if ch != PERIOD_REP else ""
        elif ch in MIDDOT_MAP:
            mapped, tag = MIDDOT_MAP[ch], "PUNCT-MIDDOT"
        elif ch in QUOTE_MAP:
            mapped, tag = QUOTE_MAP[ch], "QUOTE-CURLY"
        elif WIDTH_ASCII_RANGE[0] <= cp <= WIDTH_ASCII_RANGE[1] and ch not in WIDTH_EXCLUDED:
            mapped, tag = chr(cp - 0xFEE0), "WIDTH-ASCII"
        elif ch in KANA_MAP:
            mapped, tag = KANA_MAP[ch], "WIDTH-KANA"
        if lower and "A" <= mapped <= "Z":
            mapped = mapped.lower()
            tag = tag or "ASCII-LOWER"
        out.append(mapped)
        spans.append((i, i + 1))
        tags.append(tag)
        i += 1
    return Normalized("".join(out), tuple(spans), tuple(tags), tuple(drops), src, nfc_applied)


def normalize_quote(s: str, *, is_input: bool) -> Normalized:
    """NORM-1.2.0（verify_quote）。入力側だけ NFC-IN を先にかける。強調記号は両側で落とす（MARK-EMPH）。"""
    return _normalize(s, nfc=is_input, ws_cjk=True, punct=True, lower=False, emph=True)


def fold_search(s: str, *, is_input: bool) -> Normalized:
    """SEARCH の畳み込み（1.0.0 から不変・現行 SEARCH-1.1.0）：WS-ZW・WS-COLLAPSE・WIDTH・QUOTE-CURLY・ASCII 小文字化（WS-CJK と PUNCT は使わない）。"""
    return _normalize(s, nfc=is_input, ws_cjk=False, punct=False, lower=True)


def find_all(hay: str, needle: str) -> list[int]:
    """重なりを許して needle の全出現位置を返す。"""
    if not needle:
        return []
    out, start = [], 0
    while True:
        k = hay.find(needle, start)
        if k < 0:
            return out
        out.append(k)
        start = k + 1


def source_span(norm: Normalized, j0: int, j1: int) -> tuple[int, int]:
    """正規化位置 [j0, j1) に対応する元の区間。"""
    return norm.spans[j0][0], norm.spans[j1 - 1][1]


def _drops_between(norm: Normalized, j: int) -> list[tuple[int, int, int, str]]:
    return [d for d in norm.drops if d[0] == j]


def _split_tags(*tags: str) -> set[str]:
    return {r for tag in tags for r in tag.split("+") if r}


def compare(inp: Normalized, src: Normalized, j0: int, diff_limit: int) -> tuple[list[str], list[dict], int]:
    """入力全体と原文の正規化位置 j0 からの一致について、適用した規則と差分を返す。

    返り値：(規則IDの整列済み一覧, 差分（上限 diff_limit 件）, 差分の総数)。
    """
    rules: set[str] = set()
    diffs: list[dict] = []
    total = 0
    if inp.nfc_applied:
        rules.add("NFC-IN")
    length = len(inp.text)

    def add(i_seg: tuple[int, int], s_seg: tuple[int, int], extra_rules: set[str]) -> None:
        nonlocal total
        a = inp.source[i_seg[0]:i_seg[1]]
        b = src.source[s_seg[0]:s_seg[1]]
        if a == b:
            return
        rules.update(extra_rules)
        total += 1
        if len(diffs) < diff_limit:
            diffs.append({
                "input": a, "input_char_start": i_seg[0],
                "source": b, "source_char_start": s_seg[0],
                "rules": sorted(r for r in extra_rules if r),
            })

    def edge(position: int) -> None:
        """先頭・末尾で入力側が落とした部分（前後の空白など）。強調記号を含むときは差分にも残す（MARK-EMPH の記述）。"""
        nonlocal total
        dropped = [d for d in inp.drops if d[0] == position]
        if not dropped:
            return
        edge_rules = _split_tags(*(d[3] for d in dropped))
        rules.update(edge_rules)
        if "MARK-EMPH" not in edge_rules or not length:
            return
        start, end = min(d[1] for d in dropped), max(d[2] for d in dropped)
        source_at = src.spans[j0][0] if position == 0 else src.spans[j0 + length - 1][1]
        total += 1
        if len(diffs) < diff_limit:
            diffs.append({"input": inp.source[start:end], "input_char_start": start,
                          "source": "", "source_char_start": source_at, "rules": sorted(edge_rules)})

    edge(0)
    for k in range(length):
        isp, ssp = inp.spans[k], src.spans[j0 + k]
        add(isp, ssp, _split_tags(inp.tags[k], src.tags[j0 + k]))
        if k + 1 < length:
            i_gap = (isp[1], inp.spans[k + 1][0])
            s_gap = (ssp[1], src.spans[j0 + k + 1][0])
            gap_rules = _split_tags(*(d[3] for d in _drops_between(inp, k + 1)),
                                    *(d[3] for d in _drops_between(src, j0 + k + 1)))
            add(i_gap, s_gap, gap_rules)
    edge(length)
    return sorted(rules), diffs, total
