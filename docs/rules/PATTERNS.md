# PATTERNS — check_compressions の語形

| 項目 | 値 |
|---|---|
| 規則ID・版 | 一覧 PATTERNS-0.0.0（空）・照合 PATTERNS-MATCH-1.0.0 |
| 状態 | 一覧は著者承認待ち（候補は `docs/candidates/patterns_candidates_v0.md`）。照合規則は提案（施工判断） |
| 実装 | `mekiki_reader/patterns.py`・`mekiki_reader/tools.py`（`_check_compressions`） |

## 一覧（PATTERNS）

- 載せるのは著者が承認した項目だけ（CLAUDE.md 絶対規則9）。承認前は空で起動する。
- 項目の形：id（`P` で始まる）・version・surface_forms・related_sources（同梱ファイル・行範囲・論文なら節 id）・approved_on・match_rule。
- related_sources の種別は paper_md・theory_map・reading_guide に限る。起動時に、行範囲の実在と、論文なら節がその行を含むことを確かめる（不正なら起動しない）。
- 試験用のパターンは `tests/fixtures/patterns_fixture.py` にあり、テストが Reader の内部引数でだけ注入する。

## 照合（PATTERNS-MATCH-1.0.0）

1. 入力と語形を SEARCH-1.0.0 の畳み込み（NFC-IN〔入力のみ〕・WS-ZW・WS-COLLAPSE・WIDTH・QUOTE-CURLY・ASCII 小文字化）にかける。
2. ASCII だけの語形は単語境界（前後が `[a-z0-9'-]` 以外）で、それ以外は部分文字列で、重ならない出現をすべて拾う。
3. 一致したパターンごとに、関連原文ごとの結果を一つ作る。並びは（入力中の最初の一致位置、パターン id、関連原文の順）。
4. payload：pattern_id・pattern_version・matched（語形・入力中の文字位置。上限20件）・needs_context_review=true・source_excerpt（関連原文の行をそのまま）。判定を表す欄は持たない。
5. limitations に契約文（CONTRACT・FORMS）と件数（PATTERNS）を必ず入れる。一致ゼロ・パターン0件でも status は ok。
