# TERMS — 用語対応表

| 項目 | 値 |
|---|---|
| 規則ID・版 | TERMS-0.0.0（空） |
| 状態 | 確定（Q52・Q53）。中身は著者承認待ち（候補は `docs/candidates/terms_candidates_v0.md`） |
| 実装 | `mekiki_reader/terms.py`（`TERMS`・`build_term_index`）・`mekiki_reader/tools.py`（`_term_prepass`・`_expansions`） |

- 載せるのは著者が承認した項目だけ。範囲はコーパスが自ら示す対訳と表記揺れに限る（概念レベルの対応は入れない。SPEC §11）。
- 項目の形：id（`M` と数字）・forms_ja・forms_en・sources（コーパス内の出所）・approved_on。起動時に形を確かめ、不正なら起動しない。
- 索引：各語形を SEARCH-1.0.0 の畳み込みにかけ、語形 → 項目 id の表を作る。
- 検索での使い方（SEARCH-1.0.0）：
  1. 前処理：畳み込んだクエリの中から、語形（空白や記号を含むものも）を長い順・左から拾い、一つの断片として取り出す。
  2. 断片が語形と一致すれば、その項目の他の語形でも照合する。一致の経路は `match_via` に `term_map:<id>` として記録する（直接の一致は `query`）。
  3. 順位では直接一致を優先する（SEARCH）。
- 候補の出所の機械的な検索は `scripts/find_term_sources.py`（TERMS-SRC-1.0.0）で行う。
