# NEAR — 未登録 ID の近傍候補

| 項目 | 値 |
|---|---|
| 規則ID・版 | NEAR-1.0.0 |
| 状態 | 提案（施工判断。Q35 の確定内容にもとづく） |
| 実装 | `mekiki_reader/tools.py`（`_near`・`_levenshtein`） |

- 未登録の anchor：同じ論文の節 id（language=en のときは T4 の節 id と英訳の枠部分の id `translation-guide`・`edition-integrity`）を、（先頭からの共通部分の長さ↓、編集距離〔Levenshtein〕↑、manifest の並び順↑）で並べ、上位5件を candidates に出す。候補は本文を含まない（題名・水準・親子・経路だけ）。
- 未登録の paper_id（形式違反を含む）：五本すべてを候補に出す。
- 未登録の claim_id（T5）：台帳の11件すべてを候補に出す。
- パスや URL の形の ID は近傍候補を出さず invalid_input（LIMITS）。
- 候補の anchor は必ず索引に実在する（`schema.validate_result` が確かめる）。
