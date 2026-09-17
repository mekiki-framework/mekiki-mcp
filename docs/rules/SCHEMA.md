# SCHEMA — 応答の共通外枠と出典

| 項目 | 値 |
|---|---|
| 規則ID・版 | SCHEMA 1.0.0（応答の `schema_version`） |
| 状態 | 提案（施工判断。SPEC v2.1 §4 に従う。「資料種別の表」は 2026-09-18 に著者承認・derivative_of 欄を実測で追記） |
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
- `derivative_of`：**常に文字列の配列か null**（整列・重複なし。1件でも配列）。paper_md は null、それ以外の種別は必ず非 null（`schema.py` が `(kind == "paper_md") != (derivative_of is None)` で検査する）。translation は `["papers/T4.md#<節id>"]`、translation_note は `["translations/T4.en.md#<unit の targetId>"]`、claims は `["papers/T5.md#<節id>"]`、ガイド類（theory_map・reading_guide）は論文五本のパス。**例外**：英訳の枠部分（translation-guide・edition-integrity）だけは `["papers/T4.md"]`（T4 の特定の節から訳したものではないため、フラグメントを付けない）。
- payload には本文と付随情報を置く（text・excerpt・is_excerpt・matched_text・diffs・match_via・original_locator・preparation・authority など）。コーパス由来の文（manifest の preparation・authority・description、台帳の editorial_status・source_role）は、記録の位置（record_path・json_pointer）を付けて payload に置く。

## 資料種別の表（Q38⑦・著者承認 2026-09-18）

`derivative_of` の欄は実装を呼び出して確かめた実測値（2026-09-18・PATTERNS-0.1.0・49件を載せた状態）。

| 同梱ファイル | source_kind | derivative_of（実測） | ツールの結果に出るか |
|---|---|---|---|
| papers/T1〜T5.md | paper_md | `null`（paper_md は常に null） | 出る |
| translations/T4.en.md | translation（訳注の区間は translation_note） | 本体：`["papers/T4.md#<T4の節id>"]`／訳注：`["translations/T4.en.md#<unitのtargetId>"]`／枠部分：`["papers/T4.md"]` | 出る |
| translations/T4.en.manifest.json | translation（位置を持たない unit の記録） | `["papers/T4.md#<T4の節id>"]`（section_anchor は T4.en 側の id なので別物） | 出る |
| claims/t5.json | claims | `["papers/T5.md#<T5の節id>"]` | 出る |
| T5_CLAIM_STATUS.md | claims（台帳から生成された表示） | （結果に出ないので値なし。関連原文にもできない） | 出ない |
| THEORY_MAP.md | theory_map | 論文五本 `["papers/T1.md",…,"papers/T5.md"]` | check_compressions の関連原文としてだけ |
| FOR_AI_READERS.md | reading_guide | 論文五本 | 出る（get_reading_guide と関連原文） |
| SOURCE_INDEX.md・llms.txt | reading_guide | （PATTERNS-0.1.0 が引いていないので現状は出ない。種別としては reading_guide なので、将来の承認パターンが引けば論文五本で出る） | 出ない |
| AI_READING_TESTS.md・tests/reading_cases.json | reading_test | （関連原文にできない種別。結果に出ない） | 出ない |
| source_manifest.json・LICENSE・CITATION.md | （種別なし。記録・表示の資料） | （種別が無く結果にならない） | 出ない（list_papers は payload.record で source_manifest.json の位置を示す） |
