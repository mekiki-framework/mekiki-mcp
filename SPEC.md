# SPEC.md — Mekiki Reader MCP v2.1（読み取り専用・根拠つき読解窓口）

改版：v1（2026-09-18）→ v2（2026-09-18・ChatGPT Pro独立検証A01〜A08・B01〜B03を反映）→ **v2.1（2026-09-18・段階0の現物確認 Q01〜Q95 と回答票 `docs/stage0_answers.md` を反映）**。骨格（読み取り専用・公開版固定・サーバ内LLMなし・Gradio・ローカル先行）は不変。v2.1 の変更は §12 に列挙。
工程＝方針（本書）→施工（Claude Code）→独立検査（Codex：指摘と差分案のみ）→最終検査（Claude）→接続確認・公開判断（著者）。
段階一＝ローカル動作（SDKとReader自体に追加のAPI料金・ホスティング料金は不要）。段階二＝Hugging Face Spaces（PRO加入後・CPU Basic）。

---

## 0. 目的と位置づけ

Mekiki Framework（T1〜T5）の公開コーパス（mekiki-framework.github.io・**Git参照 `v3.5.0`・段階0で解決したコミット `67480613108cf72c29d5691e3d7a6c7e6553eb9b`（tree `7c50a4fc…`）を固定**。以後タグ名ではなくこのSHAで取得する）を、MCP対応のAIアプリから呼べる読み取り専用の窓口にする。窓口は原文・主張の記録・出典の位置を返し、判断・要約・解釈をしない。理解は接続する側の対話に残す。

Paper2Agent（Miao et al., Nature 2026）から借りるのは型（資源・プロンプト・ツール・検証テスト・Spacesでの公開）であって工程ではない。

**保証は三層に分ける（A01）。**

| 層 | 保証・確認すること | 保証しないこと |
|---|---|---|
| サーバ | 固定データからの取得、文字列照合、記録済み情報の返却、入力制限、結果ごとの出典 | 自然言語の意図分類、文脈での意味判断、最終回答の妥当性 |
| MCP接続 | 七ツールの発見・呼出し、応答スキーマ、resources/promptsの提供 | 取得したpromptを接続先AIが常に採用すること |
| 対話 | 選んだガイドに沿ったツール利用、原文と解説の分離、適用判断の支援 | 任意のモデル・任意の会話での無条件の遵守 |

## 1. 設計上の対応（READMEの冒頭に置く。列名は「保ちたい区別／根拠・参照先」——実装が論文の直接の主張だとは書かない）

| ツール | 設計上保ちたい区別 | 根拠・参照先 |
|---|---|---|
| `list_papers` / `get_section` / `search_passages` | 読むことの外化（取得・検索）は渡し、何を良しとするかは渡さない | T1（仕様と外化の分離） |
| `get_claim_record` | 主張の位置づけは**著者が記録した通り**返し、道具は真偽を判定しない | T2（能力と正統性の分離）・`claims/t5.json` |
| `verify_quote`・版と位置の記録 | 返答を原文と**照合できる**ようにし、出典・版・位置を残す。ツールは照合結果を返すが、判断について答える立場を著者や利用者から引き受けない | T3（answerabilityは関係的な立場・§4.1・§4.3–4.4） |
| `check_compressions` | 要確認箇所に対して関連する原文を返す（禁止でなく根拠の提示） | T4（理由を返す経路）・FOR_AI_READERS |
| `get_reading_guide`・サーバ内LLMなし・四モードは任意の設定 | 道具が届けるのは該当原文で、理解は届けない | T5・FOR_AI_READERS（四モードは任意の応用ヒューリスティクス） |

末尾に必ず：**設計の整合は理論の妥当性の証明ではない。静的な方針の検証は動作の保証でもない。**

## 2. 守則

1. **公開済み・著者承認済みのコーパスと読解補助のみ。** 同梱するのは固定コミットの公開ファイル（§3）。**非公開の判断台帳・野帳・社内資料・未公開草稿は含めない**（公開済みの `claims/t5.json` は含める）。資料種別（原文／読解コピー／地図／主張記録／読解試験／英訳／翻訳注）と従属関係を維持し、DOIを学術的引用先、固定URLとハッシュを照合した読解コピーの同定に使う。**T4英訳**はコーパスが同梱する著者管理の翻訳版（edition 1.0.0）で、`T4.en.manifest.json` の preparation・authority の記述（別途の著者レビュー認証は主張しない）を英訳由来の各結果に添える。Reader はこの身分を格上げも格下げもしない。
2. **読み取り専用**：ツールはコーパス・利用者のファイル・外部サービスを変更する機能を持たない。ファイルは許可済みIDからのみ取得し、利用者指定の任意パス・URL・シェル命令を受け付けない。原文・主張記録・ガイドを起動後に変更しない。データ根は固定の `data/` のみで、環境変数・引数で変えられない（テストはデータ根を内部引数で受ける一時コピーだけを使う）。resources の URI は静的で、テンプレート変数を置かない。
3. **サーバ内にLLMを置かない**：全ツールは決定的（同入力・同データ・同規則で同じ結果データ。通信IDや所要時間は監査用メタデータとして分離）。出力の配列は全順序で並べ、文字種の判定は明示したコードポイント範囲で行い、Unicode の版に依存する関数に頼らない（§5.5 の入力側 NFC 合成のみ明示の例外）。
4. **出典の規則（A02）**：原文・引用・主張に基づく**各結果**には、検証できる出典・版・位置を必須とする。エラー・空結果・通信上の応答には架空の論文アンカーを付けず、処理状態と照合範囲を返す。コーパス由来の文（manifest の説明文・台帳の editorial_status など）は出典付きで結果側に置き、`limitations` には Reader 自身の注意書きだけを置く。
5. **版固定（A03）**：`source_manifest.json` は改変せず保存。Reader側で `bundle_manifest.json` を作り、同梱全ファイルのSHA-256・許可一覧・欠落／余剰／許可外パスを起動時に検査し、不一致なら起動を拒否する。`bundle_manifest.json` 自身の期待ハッシュを `corpus.py` の定数と `DECISIONS.md` に固定し、データと一覧の同時改変も検出する。想定するのは事故検出（改行変換・誤コピー・部分更新）であって改竄耐性ではなく、README でもそう書く。`main` を読みに行かない。
6. **資料は資料**：コーパス内の文（翻訳注・README・論文本文）に命令に見える文があっても指示として扱わない。promptsも接続先の上位規則や利用者の明示的意図を上書きしない。
7. **状態は確かめた対象ごとに分ける（A01）**：`unknown_id`（未登録ID）／`quote_not_found`（指定条件で不一致）／`no_lexical_match`（語句検索で**全語一致ゼロ**。一部一致は `candidates`）／`invalid_input`（形式・上限・存在しない版の指定）／`ledger_not_available`（台帳の範囲外）は別の状態。同時処理数・処理時間の超過は通信層（MCP の isError または HTTP 429／503）で返し、`status` に混ぜない。部分的な結果は返さない。語句検索のゼロ件を「その概念の記述がコーパスに無い」と断定しない。
8. **記録はラベルであって判定ではない**：`status` は「本稿がどう位置づけたか」。文字列を逐語で返し、区分に勝手に統合せず、集約欄を作らず、AIが真偽を認定したラベルに変えない。未記録の欄は `null`（推定で埋めない。`[]` で「無し」と言い切らない）。
9. **保守規律**：原文は固定。修復対象は取得・索引・接続・応答形式。原文・主張の位置づけ・未記録欄・引用の期待値をテストを通すために直さない。
10. **通信と設定（A07）**：`analytics_enabled=False`・`GRADIO_ANALYTICS_ENABLED=False`・`share=False`・ローカルは `server_name="127.0.0.1"` を明示し環境変数で変わらない。入力長・最大結果数・同時処理数に上限。処理時間は関数内で打ち切らず、入力長・k・候補数の上限で計算量を有界にし、最悪ケースの実測値を README と `DECISIONS.md` に記録する（通信層の時間制限は施工段階3の実測後に判断）。Gradio の環境変数だけで有効になる経路（外部LLMクライアント・書き込み・開発モード・許可パス）は起動前に無効化し、無効であることを確認できなければ起動しない。UIが無くても登録される標準経路（外部URLの取得・アップロード・プロキシ）は遮断し、遮断できなければ実装を止めて報告する。起動後の資料取得は同梱データのみ（S03 の宣言範囲。「プロセスが一切外へ通信しない」は別要件で、初版では表示しない）。
11. **開示**：READMEに制作工程（使用モデル・段階）・参照論文（型を借りた Paper2Agent と読解対象の T1〜T5 の両方）・費用と休止の実測値・利用者入力の送信先と保存方針（`verify_quote`／`check_compressions` の入力には未公開情報が入りうる。Reader は入力を保存しない方針とし、Gradio や Spaces のログに残るかは施工段階3で実測してから文面を起草）。ライセンス節：コード＝MIT（著作権者はコーパスの著作者表示と同じ個人名）、`data/`＝CC BY 4.0（`data/LICENSE`・帰属は `data/CITATION.md` の書式・「原文の行は改変しない。行単位で抜粋し JSON に構造化して返す」）。論文本文中に別のライセンス表記があっても同梱物には及ばないことを一行。

## 3. リポジトリ構成（`mekiki-mcp`）

```
mekiki-mcp/
  SPEC.md                      # 本書
  CLAUDE.md                    # 施工の前提（v1.1：判断の級・リポジトリ外読取禁止）
  DECISIONS.md                 # 実装中の判断ログ（ログ表のみ）
  NOTICE                       # コード＝MIT／data/＝CC BY 4.0（固定コミット・帰属は data/CITATION.md）
  LICENSE                      # MIT（著作権者＝個人名）
  .gitattributes               # data/** -text（改行の自動変換を防ぐ）
  app.py                       # Gradio（gr.apiで関数登録・mcp_server=True・UIなし）
  mekiki_reader/               # 標準ライブラリのみ・gradio を import しない
    corpus.py                  # 同梱データ読込・bundle_manifest照合・期待ハッシュ定数・source_manifestの節索引・言語表 LANG
    tools.py                   # 七ツール（純関数）
    schema.py                  # 応答の共通外枠と結果ごとの出典・JSON直列化規則
    normalize.py               # 引用照合の正規化規則（版番号つき）
    terms.py                   # 用語対応表（著者承認済みのみ・初版は空・版番号つき）
    patterns.py                # 圧縮候補の固定規則（版番号つき・著者承認済みのみ・空で起動可）
    prompts.py                 # 読み方の雛形（promptsとget_reading_guideの両方で提供）
  scripts/
    build_bundle.py            # data/ の取得（SHA指定）と bundle_manifest.json の生成。サーバは使わない
  data/                        # 固定コミットから同梱・以後固定
    source_manifest.json       # 元のまま
    bundle_manifest.json       # Reader側で作成（§2.5）
    LICENSE CITATION.md        # コーパスの原本をバイト一致で
    papers/ claims/ tests/ translations/ *.md
  tests/
    conftest.py                # 実物 data/ の前後ハッシュ比較・server マーク
    _support/                  # テスト補助
    fixtures/                  # 命令風テキスト・T11用の試験パターン等（公開原文には足さない・本番 patterns.py からは入れない）
    test_data.py test_tools.py test_safety.py test_mcp.py
  docs/
    PLAN.md                    # 施工計画（段階0付録A）
    rules/                     # 版つき規則表（NORM・SEARCH・CAND・NEAR・GUIDE・LANG・LIMITS・JSON 等）
    stage0_facts.md            # 段階0で確認した現物
    stage0_answers.md          # 段階0の回答票（確定）
    acceptance/                # 接続先ごとの検収記録 <日付>-<クライアント>.md
  requirements.txt             # 検証済みの一つのGradio版に固定（推移依存までハッシュ付き・施工段階4で確定）
  requirements-dev.txt         # pytest 等
  README.md                    # 対応表・接続手順・開示・ライセンス節・YAML（sdk/sdk_version/python_version/app_file/license）
```

同梱許可ファイル（18本）：`source_manifest.json`・`papers/T1〜T5.md`・`THEORY_MAP.md`・`FOR_AI_READERS.md`・`SOURCE_INDEX.md`・`claims/t5.json`・`T5_CLAIM_STATUS.md`・`tests/reading_cases.json`・`AI_READING_TESTS.md`・`translations/T4.en.md`・`translations/T4.en.manifest.json`・`llms.txt`・**`LICENSE`（CC BY 4.0 本文・バイト一致）**・**`CITATION.md`（帰属文の書式）**。`translations/T4.en.meta.json`・`metadata.json`・`papers/*.html`・統合MD・`tools/*.py` は同梱しない（名前で参照される場合は `not_bundled_references` に列挙するだけ）。

## 4. 応答スキーマ（A02）

```text
応答全体（全ツール共通）
  schema_version            # Reader API版
  corpus_version            # "3.5.0"
  source_commit             # 固定したコミットSHA
  bundle_hash               # bundle_manifest.json のハッシュ（自分自身を一覧に含めない）
  status                    # ok | unknown_id | quote_not_found | no_lexical_match | invalid_input | ledger_not_available
  results[]                 # 一致結果（出典付き）。status が ok でなければ空
  candidates[]              # 語句上の近接候補（出典付き・resultsと混ぜない）
  limitations[]             # Reader 自身の注意書き（"CODE: 本文"。照合範囲・適用規則の版 RULES:・曖昧さ AMBIGUOUS: total=n など）
  templates                 # get_reading_guide のみ：読み方の雛形（results の外）

各出典付き結果
  source_id, source_kind    # <path>#<fragment>／paper_md | theory_map | claims | reading_guide | reading_test | translation | translation_note
  derivative_of             # 派生物が従属する原文の参照（原文そのものは null）
  paper_id, paper_version   # 論文に属する結果で必要（paper_versionはコーパス版と別。英訳は "1"＋payload.translation_version）
  language                  # 結果の言語 ja | en（原文の言語は固定表 LANG：T1〜T3・T5＝en、T4＝ja。ガイド類は en）
  source_path, source_hash  # どのファイルのハッシュかを明記
  section_anchor            # 論文の節に対する結果で必要（HTMLアンカー。英訳は T4.en.html の実在id・原文の節は payload.original_locator）
  locator                   # 行範囲・JSON位置など
  canonical_doi             # 学術的引用先（paper_md・translation・claims＝論文のDOI／translation_note・ガイド類＝null）
  source_url                # 人間が読む位置（Pages。フラグメントは実在するidに限る）
  snapshot_url              # 固定コミットの参照先（raw）
  payload                   # 本文と付随情報（text・excerpt・match_via・original_locator・diffs・preparation 等）
```

## 5. ツール契約（七つ）

`language` は**版の選択**：`None`＝原文、`"en"`＝英訳（T4 のみ存在）。存在しない版の指定（T1〜T3・T5 に `ja`／`en`、T4 に `ja` は原文なので可）→ `invalid_input`。

1. **`list_papers()`** → 五本の `paper_id`・題名・`paper_version`・DOI・原文の言語（固定表 LANG）・英訳の有無（T4＝en）・節一覧（`source_manifest.json` の節ID・行範囲・見出し階層から。AIに再推定させない）。
2. **`get_section(paper_id, anchor, language=None)`** → manifestに記録された範囲の原文を**行を改変せず**返す。親見出しは記録範囲のみ＋**直下の**子節IDを提示（親＝直前にある自分より水準の小さい節。`heading_only`＝範囲内の空でない行が見出し行だけ）。未登録→ `unknown_id` と実在する近傍候補（規則 NEAR・上位5件）。パス・URLの形の入力→ `invalid_input`。`language="en"` はT4のみ（`source_kind=translation`・日本語原文への位置は sourceLine で決め `original_locator` に添付・manifest の preparation を添える）。訳注は `translation_note` の別結果に分け、マーカー行は改変せず含める。英訳にしかない枠部分（告知・方針・用語一覧）は別IDで明示的に要求されたときだけ返す。
3. **`search_passages(query, paper_id=None, k=5)`** → 語句検索（モデルなし）。範囲＝論文五本の原文（参考文献を含む）。単位＝行。クエリを空白・区切りで断片に分け、日本語は部分文字列、英語は単語境界での完全一致（表記揺れは用語対応表 `terms.py`・著者承認済み・初版は空）。**全語一致**を `results`、一部一致を `candidates`、全語一致ゼロ＝ `no_lexical_match`。各結果に一致位置・抜粋（±100字・抜粋であることを表示）・`match_via`（`query` か `term_map:<id>`）・節全体への経路。順位＝語の種類数↓→総出現数↓→直接一致優先→論文順↑→行番号↑（同点処理を明文化）。`k` は1〜20（既定5・範囲外は `invalid_input`）。query は正規化後200字・断片8個まで、超過は切り詰めず `invalid_input`。日本語を含むクエリで英語の論文が範囲に入るとき、および `no_lexical_match` のとき、言語差の注意を `limitations` に出す。スコアは検索順位であって意味的一致の確率ではない。
4. **`get_claim_record(claim_id=None, query=None)`** → `claims/t5.json` のレコード。フィールド対応：`status`→逐語／`source_quote`→原文抜粋（逐語）／`not_claimed`→配列のまま／`section`・`source_locator`（中身ごと）・`additional_source_quotes`→保持。欠けた欄は `null`（`[]` にしない）。SPEC外のキー（`id`・`claim`・`footnote`）は保持し、`claim` は「台帳の要約であって逐語の引用ではない」と表示。台帳全体の `editorial_status`・`source_role` は出典（JSON位置）付きで返す。`author_answerable`→**`null`（未記録・推定しない）**。台帳のハッシュと引用元論文のハッシュを区別して返す。`claim_id` の形式は `^T[1-5]-[A-Z]+[0-9]+$`。T1〜T4→ `ledger_not_available` と関連原文の候補（出典付きの節のみ。別経路の案内文は `limitations`）。`query` の照合は規則 CAND（claim・status・source_quote・not_claimed を単位）、ゼロ件＝ `no_lexical_match`、`limitations` に「台帳は T5 のみ」を常に入れる。`claim_id`と`query`の両方なし／両方あり→ `invalid_input`。
5. **`verify_quote(text, paper_id=None, language=None)`** → `{status, match: exact|normalized|none, results[], candidates[], normalization_applied[]}`。照合範囲＝論文原文（`paper_id=None` で五本）。`language="en"` は T4 英訳のみ。単位＝行（行をまたぐ引用は `quote_not_found` とし `limitations` に明記）。正規化は**対応表に定めた**空白（畳み込み・CJK に挟まれた空白の削除）・全角半角（除外集合 ， ． － ＋ ＜ ＝ ＞ ～ を除く）・句読点（日本語と ASCII の同一視。両隣が数字なら写像しない。「.」「．」は直後が数字でも写像しない）・曲線引用符のみ。数字に挟まれた小数点・負号・比較記号は全角形も含め変換しない。NFKC は使わない。入力側の NFC 合成のみ規則 `NFC-IN` として明示の例外。normalized一致では実際の原文表記と変換記録（`payload.diffs`）を返し、`normalization_applied` は適用した規則IDの和集合。空文字・空白のみ・最小長未満→ `invalid_input`。複数箇所に同じ短文→全候補を返し曖昧さを明示（`AMBIGUOUS: total=n`）、上限を超えたら `invalid_input` と `total`（部分結果は返さない。最小長と上限の値は施工段階2で実測して `docs/rules/` に固定）。不一致→ `quote_not_found` と語句上の近接候補（規則 CAND・上限5件。「類似の主張がある」とは言わない。句読点だけが違う箇所は `candidates`）。HTML からコピーした引用（強調記号なし・脚注が番号）は初版では扱わず、`limitations` に明記。
6. **`check_compressions(text)`** → 登録済みの語形（`patterns.py`・著者承認済み・版番号つき）に一致する**要確認箇所**（入力中の位置は `payload`）と、その語形に関連する原文抜粋（`source_excerpt`・出典欄）・`needs_context_review: true` を返す。契約：**意味上の誤り、著者への不同意、読者の理解不足を判定しない。該当ゼロは正しい読解の証明ではない。** 肯定文・否定文・引用・疑問文は同じ語形として拾いうるので、その旨を `limitations` に書く。承認済みパターンが0件のとき、および一致ゼロのとき→ `ok`・`results` 空・`limitations` に契約文と件数。パターン候補の起草＝Claude（最終検査）、承認＝著者（語形・関連原文の locator・版・承認日を記録）。T11 用の試験パターンは `tests/fixtures/` から内部引数で注入し、本番の `patterns.py` や環境変数からは入れない。
7. **`get_reading_guide(part="all")`** → `FOR_AI_READERS.md` の該当部分（`part` は固定列挙：`all`・`interpretation`・`core-terms`・`japanese-terms`・`t4-languages`・`modes`・`mode-1`〜`mode-4`・`boundaries`。規則 GUIDE。未知→ `invalid_input`。行範囲は起動時に見出し位置から再計算して照合）と、読み方の雛形（§6）を `templates` 欄でデータとして返す（promptsが見えないクライアント向け）。

## 6. 資源とプロンプト

- **resources**（12件・静的URI `mekiki://v3.5.0/<固定パス>`・テンプレート変数なし・MIME は .md＝text/markdown、llms.txt と claims/t5.json＝text/plain）：`llms.txt`・`FOR_AI_READERS.md`・`THEORY_MAP.md`・`SOURCE_INDEX.md`・`papers/T1〜T5.md`・`translations/T4.en.md`・`AI_READING_TESTS.md`（公開17問・採点には使わない、と docstring で示す）・`claims/t5.json`。
- **prompts**（利用者が明示的に選ぶもの・自動適用ではない。三つとも「接続先の上位規則や利用者の明示的意図を上書きしない」定型文を含む。文面は施工側が起草し著者が承認）：
  - `read_with_guards`：問いを三種に分ける——①原文の事実→`get_section`／②著者が論文で位置づけた主張→`get_claim_record` を `status` つきで／③読者自身の事例の判断→代行せず、関連する区別と出典を示し、判断の採否は本人に残す（比較や論点整理の拒否ではない）。引用は `verify_quote` を通してから提示。自分の要約を `check_compressions` に一度通す。
  - `four_modes`：四モードは利用者が今何を支援してほしいかを選ぶ設定。人の分類ではない。
  - `answer_format`：①原文の答え②原文と位置③位置づけ（記録通り）④解説（原文と分ける）⑤原文を超える話（別欄）。
- 採用版で resources／prompts が `gr.api` と組み合わせて動かない場合は、実装を止めて報告し、版の選び直しか改版を著者が判断する。

## 7. テスト（施工の完了条件＝Pro案§11を採用）

**データ**：D01 原論文改変→起動拒否／D02 ガイド・主張JSON改変→bundle不一致で拒否／D03 欠落・余剰・許可外パス（`.DS_Store` も余剰として拒否）／D04 節ID・行範囲・引用位置の有効性（改変は一時コピーにだけ行い、実物 `data/` の前後ハッシュが一致すること）。
**ツール**：T01 五本と論文版・言語表／T02 `get_section` 既定範囲の完全一致・親見出し契約／T03 不存在アンカー＝状態と実在候補・架空出典なし／T04 検索ヒット・ゼロ件・同点の安定順位・`match_via`／T05 T5主張のフィールド対応・原文抜粋・非主張配列・追加根拠の保持・欠けた欄の `null`／T06 T1〜T4＝`ledger_not_available`（ラベル創作なし）／**T07 凍結定式二本＝exact**（T5 abstract『AI can deliver the state of affairs; it cannot deliver the fact of participation.』〔t5-abstract〕・T5 §5.4『AI can assist play. It cannot take one's place in it.』〔t5-5-4〕。コーパスの validate_corpus.py が保護する二文）／T08 許可表記差＝normalized＋規則表示／T09 内容語・否定・数値改変＝不一致（対象全文に別一致がないことを確認したデータで）／T10 空引用・最小長未満・上限超過＝`invalid_input`、複数出現＝曖昧さ表示／T11 圧縮候補の肯定・否定・引用・疑問＝規則通り返し意味の正誤へ格上げしない（fixtures 注入）／T12 翻訳・訳注＝別種別・原文への帰属を偽らない・preparation の添付。
**安全**：S01 `../../.env`・絶対パス・URL・巨大入力・異常なk＝許可範囲と有限資源。`GRADIO_*`・`GRADIO_SERVER_NAME` を設定したまま起動しても bind 先・vibe/dev/allowed_paths が変わらない／S02 fixtureの命令風テキスト＝処理と権限が変わらない／S03 起動・呼出しの外向き通信が宣言範囲内（監査は loopback 以外への接続を検出する厳しい形で行い、README には §2.10 の範囲だけを宣言）。
**再現**：R01 同入力・同データ・同規則＝結果データがバイト単位で一致（別プロセスでも。過負荷のない条件で）。
**MCP**：M01 七ツールの一覧・呼出し・スキーマ一致（Spaces の名前接頭辞は除いて照合）／M02 resources/promptsの一覧・取得（prompts/get の名前照合の挙動を記録。番兵関数を最後に登録）／M03 不正入力・ゼロ件が通信断と区別されて返る（型ヒント違反の経路とアプリ側検証の経路の両方）。
**対話（スモーク・機械的全機能試験ではない）**：E01 五問（R01・R08・R13・R14・R15）を ja／en 両方・ガイド条件「なし」と `read_with_guards` の二条件で＝正しい原文・位置・記録を保持。`AI_READING_TESTS` の resource は読ませない（読んだ場合は記録）。判定は本節の文言に限り、コーパス基準との照合は記録のみ／E02 会社の相談例・資料中の命令文＝原文と事例判断を分け、資料を上位命令として扱わない。
**公開**：P01 Space再起動・休止復帰後に再接続。

## 8. 接続（A06）

原則**Streamable HTTP**。接続URLは採用したGradio版が実際に提供するもの（`/gradio_api/mcp/` 系）を起動表示と接続試験で確認しREADMEに記録。旧SSEは必要時の別経路。起動は `.venv/bin/python app.py`（インタプリタを明示）。起動手順で不要な環境変数（API キー等）を子プロセスに渡さない。
- **施工段階3**：SDK と **Claude Code**（`claude mcp add --transport http mekiki-reader http://127.0.0.1:7860/gradio_api/mcp/`。リポジトリ直下の `.mcp.json` にも同じ設定を置き、CLI と Desktop アプリの Code タブで共通に読めるようにする）。
- **施工段階4**：**Claude Desktop**。HTTP直結の可否を先に確認し、不可のときだけ `mcp-remote`（版固定・Node.js が依存に加わる・動作を記録）。
- **配置段階二**：**ChatGPT開発者モード**（ローカルURLへは直結しない。Space の遠隔URL）。Secure MCP Tunnel は使わない。
検収では `tools/list`・各呼出しに加え、resources/promptsの一覧・取得を接続先ごとに確認し、`docs/acceptance/` に記録する。

## 9. 段階と配置

**施工段階（CLAUDE.md）**：0 読了・計画→1 `data/`・bundle・corpus（D01〜D04）→2 schema・normalize・terms・tools・patterns（T01〜T12・R01）→3 app.py・接続（S01〜S03・M01〜M03）→4 README・requirements 固定・検収記録。実行環境は Python **3.13**（uv で導入・minor をローカルと Spaces でそろえる）、Gradio は **6.27.0** を暫定（`run_history=False` 必須・施工段階3の着手時に再比較して確定）。
**配置段階一（ローカル）**：`app.py`（loopback）→Claude Code／Desktopから接続→五問→**自分用の正典統一はここで完成**。
**配置段階二（公開）**：HF PRO加入→Space（Gradio・CPU Basic・公開）→**一式**（`app.py`・`mekiki_reader/`・`data/`〔LICENSE・CITATION.md を含む〕・`requirements.txt`・`README.md`〔YAMLに sdk／sdk_version／`python_version: "3.13"`／app_file／`license: mit`〕・`LICENSE`・`NOTICE`）をアップロード→接続URLをREADMEに→再接続→休止からの復帰時間を実測して記載→X一投（動くURLと一緒に・「棚が先にあった」・生成開示）。公開前に `DECISIONS.md` の非公開資料への参照を置換し、未報告の上流不具合の詳細を要約化する。

## 10. 役割

- **Claude Code＝施工**：§3〜§8を実装。判断は CLAUDE.md v1.1 の級に従う（著者判断だけ停止・施工判断は提案して続行）。`DECISIONS.md` に採用版・コミットSHA・規則の版・使用モデルを記録。原文MDと `source_manifest.json` には触れない。守則に反する実装が必要になったら実装せず報告。リポジトリの外を読まない。
- **Codex＝独立検査**：守則十一項への抵触（外部呼び出し・非決定・出典欠落・原文改変・LLM呼び出し・任意パス）、敵対的テストの追加（S01〜S03・T09〜T11・同義語再生）、応答スキーマの一貫性。**指摘と差分案のみ。** 検査したコード・データ・パターン・テストの版を記録し、修正後に再検査。
- **Claude＝最終検査**：五問の生応答を原文と突合。パターン候補一覧と用語対応表の候補の起草。本書の改版の起草。
- **著者＝判断と署名**：パターン一覧・用語対応表・prompts 文面・試験用テキストの承認、`author_answerable` を埋めるならコーパス側（3.6.0）で、対応クライアントの範囲、PRO加入、Space作成、README末尾の開示とライセンス節、上流への報告の要否、X一投。

## 11. 触れないもの

意味検索・埋め込み・外部LLM・チャットUI（別方針書）／判断を採点する架空ツール／非公開資料の同梱／`compare_versions`（一版固定と整合するため初版から外す。英訳 manifest の `source.corpusVersion=3.2.1` は記録のまま返し、版どうしの比較は応答に出さない）／理論の妥当性の主張／概念レベルの用語対応（対訳と表記揺れに限る）／形態素解析器。

## 12. 改版履歴 v2 → v2.1

1. §0 固定コミットSHAを明記（Q01）。
2. §2.1 T4英訳の身分（preparation を添える・格上げしない）（Q25）。
3. §2.2 データ根固定・静的URI（Q12・Q70）。§2.3 決定性の実装規則と NFC-IN の例外（Q47・付録A-0）。
4. §2.5 期待ハッシュ定数と脅威想定（Q03）。
5. §2.7 `no_lexical_match`＝全語一致ゼロ、超過は通信層、部分結果なし（Q55・Q65・Q84・Q85）。
6. §2.8 「四つの身分」→「区分に統合しない」（誤記の訂正・Q31）。
7. §2.10 環境変数の無効化・標準経路の遮断・処理時間の扱い・S03 の宣言範囲（Q66・Q67・Q85・Q86・Q93）。
8. §2.11 開示に使用モデル・参照論文の両方・ライセンス節（Q13〜Q18・Q20・Q89・Q90）。
9. §3 許可一覧に `LICENSE`・`CITATION.md` を追加（16→18本）。構成に `NOTICE`・`.gitattributes`・`scripts/build_bundle.py`・`terms.py`・`tests/conftest.py`・`tests/_support/`・`docs/`・`requirements-dev.txt` を追加（Q04〜Q09・Q12・Q52・Q76・Q81）。
10. §4 `payload`・`derivative_of`・`templates`、`limitations` の書式、canonical_doi の表、言語表 LANG（Q22・Q33・Q38・Q88）。
11. §5 `language` を版の選択（既定 None＝原文）に変更（Q21・Q24）。各ツールの状態・上限・規則名を明記（Q26〜Q37・Q41〜Q61・Q84・Q92）。
12. §6 静的URI・MIME・prompts の定型文・動かない場合の停止（Q39・Q70・Q87）。
13. §7 T07 の二文を同定（Q23）。T10・T12・S01・S03・M01〜M03・E01 の条件を追記（Q12・Q64・Q68・Q69・Q82・Q86）。
14. §8 接続先を施工段階で分け、`.mcp.json` を併置（Q71〜Q73・Q79・Q80・Q91）。
15. §9 実行環境（Python 3.13・Gradio 6.27.0 暫定）と一式の内訳（Q19・Q62・Q74〜Q78）。公開前の置換（Q95）。
16. §10 判断の級・Claude の起草範囲・著者の承認事項を追記（Q37・Q94）。§11 に用語対応の範囲と形態素解析器を追加（Q28・Q50・Q53）。
