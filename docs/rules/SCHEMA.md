# SCHEMA — 応答の共通外枠と出典

| 項目 | 値 |
|---|---|
| 規則ID・版 | SCHEMA 1.0.0（応答の `schema_version`） |
| 状態 | 提案（施工判断。SPEC v2.1 §4 に従う。下の「資料種別の表」は Q38⑦ の起草で著者承認待ち） |
| 実装 | `mekiki_reader/schema.py`（`envelope`・`result`・`validate_result`・`validate_envelope`） |

## 外枠（全ツール共通）

`schema_version`・`corpus_version`（3.5.0）・`source_commit`・`bundle_hash`・`status`・`results`・`candidates`・`limitations`。ツールごとの追加欄：verify_quote は `match`（exact・normalized・none）と `normalization_applied`（規則IDの和集合・整列済み。不正入力や不一致では空）、get_reading_guide は `templates`。
status が ok でなければ results は空。limitations は `"CODE: 本文"` の形で、Reader 自身の注意書きだけを置き、辞書順・重複なしに並べる。

主な CODE：RULES（使った規則と版）・SCOPE・INPUT・TOTAL・AMBIGUOUS・NEARBY・NORMALIZED・NOT_FOUND・CAND・NEAR・ZERO・LANG・SCORE・QUERY・TERMS・LEDGER・LABEL・ROUTE・PARENT・TRANSLATION・UNIT・FRAME・HTML・NFC・CONTRACT・FORMS・PATTERNS・TEMPLATES・GUIDE。

## 出典付きの結果

欄：`source_id`・`source_kind`・`derivative_of`・`paper_id`・`paper_version`・`language`・`source_path`・`source_hash`・`section_anchor`・`locator`（path・line_start・line_end・char_start・char_end・json_pointer・note）・`canonical_doi`・`source_url`・`snapshot_url`・`payload`。

- `source_id` ＝ `<source_path>#<fragment>`。fragment は、節の結果なら節 id、行の結果なら `L<n>` か `L<a>-L<b>`、台帳なら主張 id、訳注なら訳注 id、manifest の記録なら `sourceUnits/<i>`、ガイドなら part 名。
- `source_hash` はそのファイルの bundle 上の SHA-256。`snapshot_url` は固定コミットの raw URL。
- `locator` は行範囲か JSON 位置の少なくとも一方を持つ。char は元の行の中の文字位置（0 始まり・終端を含まない）。
- 論文に属する種別（paper_md・claims・translation・translation_note）は paper_id・paper_version・section_anchor が必須。section_anchor は、paper_md と claims では論文の節 id、translation と translation_note では T4.en.md に実在する id（unit の targetId・訳注の id・枠部分の id）。位置を持たない unit（wrapper・separator）は、同じ節の最初の位置つき unit の targetId を使う。
- `canonical_doi`：paper_md・translation・claims は論文の DOI、translation_note とガイド類は null（Q88）。
- `source_url`：Pages の URL。フラグメントは実在する id だけ（論文は `papers/Tn.html#節id`、英訳は `papers/T4.en.html#id`、台帳は記録の section_url、ガイドはフラグメントなし）。
- `derivative_of`：paper_md は null。translation は `papers/T4.md#<節id>`、translation_note は `translations/T4.en.md#<unit の targetId>`、claims は `papers/T5.md#<節id>`、ガイド類は論文五本のパス。
- payload には本文と付随情報を置く（text・excerpt・is_excerpt・matched_text・diffs・match_via・original_locator・preparation・authority など）。コーパス由来の文（manifest の preparation・authority・description、台帳の editorial_status・source_role）は、記録の位置（record_path・json_pointer）を付けて payload に置く。

## 資料種別の表（Q38⑦・起草・著者承認待ち）

| 同梱ファイル | source_kind | ツールの結果に出るか |
|---|---|---|
| papers/T1〜T5.md | paper_md | 出る |
| translations/T4.en.md | translation（訳注の区間は translation_note） | 出る |
| translations/T4.en.manifest.json | translation（位置を持たない unit の記録） | 出る |
| claims/t5.json | claims | 出る |
| T5_CLAIM_STATUS.md | claims（台帳から生成された表示） | 出ない |
| THEORY_MAP.md | theory_map | check_compressions の関連原文としてだけ |
| FOR_AI_READERS.md | reading_guide | 出る |
| SOURCE_INDEX.md・llms.txt | reading_guide | 出ない |
| AI_READING_TESTS.md・tests/reading_cases.json | reading_test | 出ない |
| source_manifest.json・LICENSE・CITATION.md | （種別なし。記録・表示の資料） | 出ない（list_papers は payload.record で source_manifest.json の位置を示す） |
