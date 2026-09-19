# SPEC.md — Mekiki Reader MCP v2.4.2（読み取り専用・根拠つき読解窓口）

改版：v1（2026-09-18）→ v2（2026-09-18・ChatGPT Pro独立検証A01〜A08・B01〜B03を反映）→ v2.1（2026-09-18・段階0の現物確認 Q01〜Q95 と回答票 `docs/stage0_answers.md` を反映）→ v2.2（2026-09-18・施工段階2〜4の実測と確定した規則・表を反映）→ v2.3（2026-09-18・Codex①②の反映、配置段階一の検収 E01/E02、規則改版を反映。配置段階一は完成）→ v2.3.1（2026-09-19・v2.3 と現物の照合結果、開放経路の最終一覧、旧 SSE の閉鎖、長時間接続の上限、内部クライアントの単一化、LIMITS-2.0.0、版運用の境界を反映）→ **v2.4（2026-09-19・Codex③の反映と、配置段階二の方針＝配置モード〔local／spaces〕・Docker Space・Host と bind・環境変数の整理・ログの開示・公開前後の検収を追加。`docs/spaces_facts.md` に基づく）→ **v2.4.1（2026-09-19・施工照合の二点＝一式に `.dockerignore`、README の YAML 記述の更新。P03 の順序）→ **v2.4.2（2026-09-19・Codex④の反映＝spaces のポート固定・LIMITS-3.1.0・E01 の完了記述）**。骨格（読み取り専用・公開版固定・サーバ内LLMなし・Gradio・ローカル先行）は不変。v2.1〜v2.3.1 の変更は §12 に列挙。
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
5. **版固定（A03）**：`source_manifest.json` は改変せず保存。Reader側で `bundle_manifest.json` を作り、同梱全ファイルのSHA-256・許可一覧・欠落／余剰／許可外パスを起動時に検査し、不一致なら起動を拒否する。`bundle_manifest.json` 自身の期待ハッシュを `corpus.py` の定数と `DECISIONS.md` に固定し、データと一覧の同時改変も検出する。用語対応表と圧縮パターン表は正準 JSON の SHA-256 を規則文書に記し、import 時に照合する（生成器 `scripts/build_patterns.py` は表と定数を同時に書き換え、文書整合試験まで走らせる）。想定するのは事故検出（改行変換・誤コピー・部分更新）であって改竄耐性ではなく、README でもそう書く。`main` を読みに行かない。
6. **資料は資料**：コーパス内の文（翻訳注・README・論文本文）に命令に見える文があっても指示として扱わない。promptsも接続先の上位規則や利用者の明示的意図を上書きしない。
7. **状態は確かめた対象ごとに分ける（A01）**：`unknown_id`（未登録ID）／`quote_not_found`（指定条件で不一致）／`no_lexical_match`（語句検索で**全語一致ゼロ**。一部一致は `candidates`）／`invalid_input`（形式・上限・存在しない版の指定）／`ledger_not_available`（台帳の範囲外）は別の状態。同時処理数・処理時間の超過は通信層（MCP の isError または HTTP 429／503）で返し、`status` に混ぜない。部分的な結果は返さない。語句検索のゼロ件を「その概念の記述がコーパスに無い」と断定しない。
8. **記録はラベルであって判定ではない**：`status` は「本稿がどう位置づけたか」。文字列を逐語で返し、区分に勝手に統合せず、集約欄を作らず、AIが真偽を認定したラベルに変えない。未記録の欄は `null`（推定で埋めない。`[]` で「無し」と言い切らない）。
9. **保守規律**：原文は固定。修復対象は取得・索引・接続・応答形式。原文・主張の位置づけ・未記録欄・引用の期待値をテストを通すために直さない。
10. **通信と設定（A07）**：`analytics_enabled=False`・`GRADIO_ANALYTICS_ENABLED=False`・`share=False`・ローカルは `server_name="127.0.0.1"` を明示し環境変数で変わらない。入力長・最大結果数・同時処理数に上限。処理時間は関数内で打ち切らず、入力長・k・候補数の上限で計算量を有界にし、最悪ケースの実測値を README と `DECISIONS.md` に記録する（通信層の時間制限は施工段階3の実測後に判断）。Gradio の環境変数だけで有効になる経路（外部LLMクライアント・書き込み・開発モード・許可パス）は起動前に無効化し、無効であることを確認できなければ起動しない。UIが無くても登録される標準経路（外部URLの取得・アップロード・プロキシ）は遮断し、遮断できなければ実装を止めて報告する。起動後の資料取得は同梱データのみ（S03 の宣言範囲。「プロセスが一切外へ通信しない」は別要件で、初版では表示しない）。例外として通す経路（完全一致の許可一覧・試験で固定・README と LIMITS に同じ表）：`/`（起動時の到達確認と内部クライアントの設定の読み先。静的資産は遮断・画面は組み上がらない）／`/gradio_api/startup-events`（起動時の確認）／`/gradio_api/info`（末尾 `/` も。自己呼び出しが読む）／`/gradio_api/queue/join`・`/gradio_api/queue/data`（自己呼び出しの実行と結果）／`/gradio_api/heartbeat/*`（内部クライアントが再接続を前提に設計されているため閉じられない。上限で受ける）／`/gradio_api/mcp/`（MCP 本体。`/gradio_api/mcp` は 307）／`/gradio_api/mcp/schema`（読み取り専用の GET）。`/config`（内部クライアントは `/` の HTML から設定を読む）・旧 SSE（`/gradio_api/mcp/sse`・`/gradio_api/mcp/messages/`）・別名 `/gradio_api/mcp/http`・`/gradio_api/call/*` は閉じる。依存ライブラリの既定動作（利用状況の送信・利用者のトークンファイルの読取）は import 前に `HF_HUB_DISABLE_TELEMETRY=1`・`HF_HUB_DISABLE_IMPLICIT_TOKEN=1`・`HF_HUB_OFFLINE=1`・`HF_TOKEN_PATH=/dev/null` で止め、S03 の監査（外向き接続と開いたファイルの記録）で確認する。通信層の上限と検査（Codex①②の反映・実測値）：本文を読む経路（MCP 本体と `queue/join`）では**実バイト数**で 64 KiB（超過 413、送り切らない要求は受信ループ全体の 10 秒期限で 408。`Transfer-Encoding` と `Content-Length` の併記は Guard が 400、`Content-Length` 自体の異常は HTTP 層〔h11〕が先に拒む）／`Host` は許可値に限り括弧付きの接尾辞も検査／`Origin` 付き要求に CORS の許可ヘッダを返さず、起動時に自分へ `Origin` を当てて確かめる（`check_cors`）／`/gradio_api/call/*` は遮断／実行枠は同時4（七ツール・resources・prompts で共有）、`/gradio_api/queue/join` は受付8・待機64（超過は 503）・待ち行列72、未回収結果は 64件・4 MiB・120 秒で破棄／プロキシ環境変数（`HTTP_PROXY`・`HTTPS_PROXY`・`ALL_PROXY`・小文字形）は import 前に除去し `NO_PROXY` を固定／正規表現キャッシュは LRU 512、遮断記録は固定長。長時間接続の同時数に上限（heartbeat 8・`queue/data` 8・`GET /gradio_api/mcp/` 32。超過は 503。内部クライアントの接続は数えるが断らない）。内部クライアントは起動直後に一つだけ作る（同時の初回呼び出しで上流が複数作り heartbeat を残す競合の対策。作成に鍵をかける方式は thread pool を塞いで退行したため採らない）。ポートは `local` では環境変数 `MEKIKI_READER_PORT`（1024〜65535・既定 7860）で変えられるが、`spaces` では **7860 固定**（別の値が与えられれば起動しない。Docker の EXPOSE と Space の app_port に一致させる。試験用のポートは起動器の内部引数で扱う）。待ち受けアドレスは配置モード以外では変えられない。受付は種類ごとの枠（MCP 32＋待機96・`queue/join` 8＋64・その他 16＋32）を本文を読む前に取り、応答を送り終えるまで持つ。受付から60秒の送信期限を置き、期限を過ぎた接続は切る。未回収結果は生成時刻から数え、内部・処理中・回収中のセッションは掃除で消さない。追い出したセッションの関連状態は一括で解放する。例外とログは型・場所・水準・名前だけを出し、受信した値を出さない（実測で目印の文字列が出力に0件）。

**配置モード（v2.4）**：`MEKIKI_READER_MODE` は `local`（既定）か `spaces` の二値で、起動表示に出す。`spaces` で変わるのは三つだけ——bind が `0.0.0.0:7860`、許可 `Host` が起動時に読んだ `SPACE_HOST`（カンマ区切りは各値）と `localhost`・`127.0.0.1`（`SPACE_HOST` が無ければ起動しない）、`/` だけは健康検査のために Host を問わず応答する（静的 HTML のみ）。それ以外の環境変数で挙動は変わらない。`spaces` では `SPACE_HOST` を読んだ後に `SYSTEM`・`SPACE_ID`・`SPACE_AUTHOR_NAME`・`SPACE_REPO_NAME`・`SPACES_ZERO_GPU`・`OAUTH_*`・`HF_TOKEN`・`WEB_CONCURRENCY`・`FORWARDED_ALLOW_IPS` を import 前に除去し、Gradio をローカルと同じ分岐で動かす（Spaces 用の監視スレッド・`pwa` 既定・ツール名の接頭辞・`spaces` パッケージの関数包装を使わない）。`pwa=False` は launch で明示し固定値の一覧に入れる。Space に Secret を置かない。`spaces` パッケージは依存に入れない。
11. **開示**：READMEに制作工程（使用モデルを役割ごとに列挙：方針と最終検査／施工／方針の独立検証／独立検査。文面は著者が承認・署名）・参照論文（型を借りた Paper2Agent と読解対象の T1〜T5 の両方）・費用と休止の実測値・利用者入力の送信先と保存方針（`verify_quote`／`check_compressions` の入力には未公開情報が入りうる。Reader は入力を保存しない。ローカルでは stdout／stderr に受信した値が出ないことを実測済み。Spaces では実行ログは stdout／stderr で、閲覧できるのは Space に書き込み権限のある者、保持は再起動までで期間は保証されない、と開示する。`hf.co/mcp` 経由の呼び出しは HF 側の機能で本サーバは関知しない、と一行）。ライセンス節：コード＝MIT（著作権者はコーパスの著作者表示と同じ個人名）、`data/`＝CC BY 4.0（`data/LICENSE`・帰属は `data/CITATION.md` の書式・「原文の行は改変しない。行単位で抜粋し JSON に構造化して返す」）。論文本文中に別のライセンス表記があっても同梱物には及ばないことを一行。

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
    __init__.py
  .mcp.json                    # Claude Code 用のプロジェクト接続設定（type=http・loopback）
  scripts/
    build_bundle.py            # data/ の取得（SHA指定）と bundle_manifest.json の生成。サーバは使わない
    build_patterns.py          # 候補表→patterns.py の生成（関連原文の locator を source_manifest 等に解決）
    find_term_sources.py       # 用語対応表の出所検索
  data/                        # 固定コミットから同梱・以後固定
    source_manifest.json       # 元のまま
    bundle_manifest.json       # Reader側で作成（§2.5）
    LICENSE CITATION.md        # コーパスの原本をバイト一致で
    papers/ claims/ tests/ translations/ *.md
  tests/
    __init__.py conftest.py    # 実物 data/ の前後ハッシュ比較・server マーク
    _support/                  # テスト補助
    fixtures/                  # 命令風テキスト・T11用の試験パターン等（公開原文には足さない・本番 patterns.py からは入れない）
    test_data.py test_tools.py test_safety.py test_mcp.py
  pytest.ini
  docs/
    PLAN.md                    # 施工計画（段階0付録A）
    rules/                     # 版つき規則表（SCHEMA・JSON・NORM・SEARCH・CAND・NEAR・GUIDE・LIMITS・LINES・LANG・SECTION・T4MAP・BUNDLE・TERMS・PATTERNS・PROMPTS）
    candidates/                # 候補表（patterns・terms・prompts_en。承認後は docs/rules/ が正）
    review/                    # Codex の報告原本（codex-N-report.md）と反映記録（codex-N.md。②も独立ファイル）
    stage0_facts.md            # 段階0で確認した現物
    stage0_answers.md          # 段階0の回答票（確定）
    acceptance/                # 接続先ごとの検収記録 <日付>-<クライアント>.md（TEMPLATE.md・README.md）、E01 の設問 e01_questions.md、e01/ の応答20本と E02 1本、総括 <日付>-e01-e02.md
  requirements.in requirements.txt         # gradio[mcp]==6.27.0 ほか・推移依存までハッシュ付き（uv pip compile --generate-hashes）
  Dockerfile                   # Docker Space 用：python:3.13 の slim をダイジェストで固定・pip --require-hashes・PYTHONUNBUFFERED=1・MEKIKI_READER_MODE=spaces・EXPOSE 7860・CMD python app.py
  requirements-dev.in requirements-dev.txt # pytest 等
  README.md                    # 対応表・接続手順・開示・ライセンス節・YAML（sdk: docker／app_port: 7860／license: mit）
  .dockerignore                # Space への一式に含める（.DS_Store・.venv・.git・tests 等を除外）
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
  derivative_of             # 派生物が従属する原文の参照（配列。paper_md は常に null・他は常に非 null。対応表は docs/rules/SCHEMA.md）
  paper_id, paper_version   # 論文に属する結果で必要（paper_versionはコーパス版と別。英訳は "1"＋payload.translation_version）
  language                  # 結果の言語 ja | en（原文の言語は固定表 LANG：T1〜T3・T5＝en、T4＝ja。ガイド類は en）
  source_path, source_hash  # どのファイルのハッシュかを明記
  section_anchor            # 論文の節に対する結果で必要（HTMLアンカー。英訳は T4.en.html の実在id・原文の節は payload.original_locator）
  locator                   # 行範囲・JSON位置など
  canonical_doi             # 学術的引用先（paper_md・translation・claims＝論文のDOI／translation_note・ガイド類＝null）
  source_url                # 人間が読む位置（Pages。フラグメントは実在するidに限る）
  snapshot_url              # 固定コミットの参照先（raw）
  payload                   # 本文と付随情報（text・excerpt・match_via・original_locator・diffs・preparation 等）。source_excerpt は1000字で切り source_excerpt_truncated を立てる
```

## 5. ツール契約（七つ）

`language` は**版の選択**：`None`（MCP 経由では空文字）＝原文、`"en"`＝英訳（T4 のみ存在）。存在しない版の指定（T1〜T3・T5 に `ja`／`en`、T4 に `ja` は原文なので可）→ `invalid_input`。

1. **`list_papers()`** → 五本の `paper_id`・題名・`paper_version`・DOI・原文の言語（固定表 LANG）・英訳の有無（T4＝en）・節一覧（`source_manifest.json` の節ID・行範囲・見出し階層から。AIに再推定させない）。
2. **`get_section(paper_id, anchor, language=None)`** → manifestに記録された範囲の原文を**行を改変せず**返す。親見出しは記録範囲のみ＋**直下の**子節IDを提示（親＝直前にある自分より水準の小さい節。`heading_only`＝範囲内の空でない行が見出し行だけ）。未登録→ `unknown_id` と実在する近傍候補（規則 NEAR・上位5件）。パス・URLの形の入力→ `invalid_input`。`language="en"` はT4のみ（`source_kind=translation`・日本語原文への位置は sourceLine で決め `original_locator` に添付・manifest の preparation を添える）。訳注は `translation_note` の別結果に分け、マーカー行は改変せず含める。英訳にしかない枠部分（告知・方針・用語一覧）は別IDで明示的に要求されたときだけ返す。
3. **`search_passages(query, paper_id=None, k=5)`** → 語句検索（モデルなし）。範囲＝論文五本の原文（参考文献を含む）。単位＝行。クエリを空白・区切りで断片に分け、日本語は部分文字列、英語は単語境界での完全一致（SEARCH-1.1.0：ハイフンは語境界としても扱い、ハイフン付きの語句そのものも当たる。表記揺れは用語対応表 `terms.py`・著者承認済み・TERMS-0.1.1＝30項目。コーパスに日本語形が無い語は英語の表記揺れだけを束ねる）。**全語一致**を `results`、一部一致を `candidates`、全語一致ゼロ＝ `no_lexical_match`。各結果に一致位置・抜粋（±100字・抜粋であることを表示）・`match_via`（`query` か `term_map:<id>`）・節全体への経路。順位＝語の種類数↓→直接一致（対応表を経由しない）↓→総出現数↓→論文順↑→行番号↑（同点処理を明文化。v2.1 の並びは起草の誤り）。`k` は1〜20（既定5・範囲外は `invalid_input`）。query は生1000字・正規化後200字・断片8個まで、超過は切り詰めず `invalid_input`。日本語を含むクエリで英語の論文が範囲に入るとき、および `no_lexical_match` のとき、言語差の注意を `limitations` に出す。スコアは検索順位であって意味的一致の確率ではない。
4. **`get_claim_record(claim_id=None, query=None)`** → `claims/t5.json` のレコード。フィールド対応：`status`→逐語／`source_quote`→原文抜粋（逐語）／`not_claimed`→配列のまま／`section`・`source_locator`（中身ごと）・`additional_source_quotes`→保持。欠けた欄は `null`（`[]` にしない）。SPEC外のキー（`id`・`claim`・`footnote`）は保持し、`claim` は「台帳の要約であって逐語の引用ではない」と表示。台帳全体の `editorial_status`・`source_role` は出典（JSON位置）付きで返す。`author_answerable`→**`null`（未記録・推定しない）**。台帳のハッシュと引用元論文のハッシュを区別して返す。`claim_id` の形式は `^T[1-5]-[A-Z]+[0-9]+$`。T1〜T4→ `ledger_not_available` と関連原文の候補（出典付きの節のみ。別経路の案内文は `limitations`）。`query` の照合は規則 CAND（claim・status・source_quote・not_claimed を単位）、ゼロ件＝ `no_lexical_match`、`limitations` に「台帳は T5 のみ」を常に入れる。`claim_id`と`query`の両方なし／両方あり→ `invalid_input`。
5. **`verify_quote(text, paper_id=None, language=None)`** → `{status, match: exact|normalized|none, results[], candidates[], normalization_applied[]}`。照合範囲＝論文原文（`paper_id=None` で五本）。`language="en"` は T4 英訳のみ。単位＝行（行をまたぐ引用は `quote_not_found` とし `limitations` に明記）。正規化は**対応表に定めた**空白（畳み込み・CJK に挟まれた空白の削除）・全角半角（除外集合 ， ． － ＋ ＜ ＝ ＞ ～ を除く）・句読点（日本語と ASCII の同一視。両隣が数字なら写像しない。「.」「．」は直後が数字でも写像しない）・曲線引用符・Markdown の強調記号（NORM-1.1.0 の規則 `MARK-EMPH`：`*`・`_`・全角形を落とす。HTML から写した引用が落ちる事故を E01 で7回観測して追加）のみ。数字に挟まれた小数点・負号・比較記号は全角形も含め変換しない。NFKC は使わない。入力側の NFC 合成のみ規則 `NFC-IN` として明示の例外。normalized一致では実際の原文表記と変換記録（`payload.diffs`）を返し、`normalization_applied` は適用した規則IDの和集合。空文字・空白のみ・最小長未満→ `invalid_input`。複数箇所に同じ短文→全候補を返し曖昧さを明示（`AMBIGUOUS: total=n`）、上限を超えたら `invalid_input` と `total`（部分結果は返さない。最小長＝仮名・漢字を含めば5字、それ以外10字〔無作為部分文字列の出現回数の中央値が1になる長さで決定〕、上限＝20件。LIMITS-3.1.0）。不一致→ `quote_not_found` と語句上の近接候補（規則 CAND・上限5件。「類似の主張がある」とは言わない。句読点だけが違う箇所は `candidates`）。HTML からコピーした引用のうち、脚注が番号になる差は扱わず、`limitations` に明記（強調記号の差は `MARK-EMPH` で吸収）。孤立サロゲートを含む入力は `invalid_input`。
6. **`check_compressions(text)`** → 登録済みの語形（`patterns.py`・著者承認済み・版番号つき）に一致する**要確認箇所**（入力中の位置は `payload`）と、その語形に関連する原文抜粋（`source_excerpt`・出典欄）・`needs_context_review: true` を返す。契約：**意味上の誤り、著者への不同意、読者の理解不足を判定しない。該当ゼロは正しい読解の証明ではない。** 肯定文・否定文・引用・疑問文は同じ語形として拾いうるので、その旨を `limitations` に書く。承認済みパターンが0件のとき、および一致ゼロのとき→ `ok`・`results` 空・`limitations` に契約文と件数。関連原文は行または行内の文字範囲（`char_start`／`char_end`）で指し、抜粋は1000字で切る。現行は PATTERNS-0.2.1（50件・関連原文100。E01 の取りこぼし——「代替できない」「があると証明」（先頭の語は任意）「AI cannot replace」「障害を残す」「preserve obstacles」——を追加。保留4件は次版へ）。照合は PATTERNS-MATCH-1.1.0（ハイフンを語境界に。SEARCH と同じ規則）。結果数に上限は設けない（入力 2000 字で有界。最悪ケースの結果数と応答サイズは LIMITS に実測記録）。パターン候補の起草＝Claude（最終検査）、承認＝著者（語形・関連原文の locator・版・承認日を記録）。T11 用の試験パターンは `tests/fixtures/` から内部引数で注入し、本番の `patterns.py` や環境変数からは入れない。
7. **`get_reading_guide(part="all")`** → `FOR_AI_READERS.md` の該当部分（`part` は固定列挙：`all`・`interpretation`・`core-terms`・`japanese-terms`・`t4-languages`・`modes`・`mode-1`〜`mode-4`・`boundaries`。規則 GUIDE。未知→ `invalid_input`。行範囲は起動時に見出し位置から再計算して照合）と、読み方の雛形（§6）を `templates` 欄でデータとして返す（promptsが見えないクライアント向け）。

## 6. 資源とプロンプト

- **resources**（12件・静的URI `mekiki://v3.5.0/<固定パス>`・テンプレート変数なし・MIME は .md＝text/markdown、llms.txt と claims/t5.json＝text/plain）：`llms.txt`・`FOR_AI_READERS.md`・`THEORY_MAP.md`・`SOURCE_INDEX.md`・`papers/T1〜T5.md`・`translations/T4.en.md`・`AI_READING_TESTS.md`（公開17問・採点には使わない、と docstring で示す）・`claims/t5.json`。
- **prompts**（利用者が明示的に選ぶもの・自動適用ではない。三つとも「接続先の上位規則や利用者の明示的意図を上書きしない」定型文を含む。文面は施工側が起草し著者が承認。日本語版 PROMPTS-0.1.0 に加え、英語版は `_en` を付けた別名（`read_with_guards_en` 等）で同版に登録する。引数で言語を切り替える方式は採らない）：
  - `read_with_guards`：問いを三種に分ける——①原文の事実→`get_section`／②著者が論文で位置づけた主張→`get_claim_record` を `status` つきで／③読者自身の事例の判断→代行せず、関連する区別と出典を示し、判断の採否は本人に残す（比較や論点整理の拒否ではない）。引用は `verify_quote` を通してから提示。自分の要約を `check_compressions` に一度通す。
  - `four_modes`：四モードは利用者が今何を支援してほしいかを選ぶ設定。人の分類ではない。
  - `answer_format`：①原文の答え②原文と位置③位置づけ（記録通り）④解説（原文と分ける）⑤原文を超える話（別欄）。
- 採用版で resources／prompts が `gr.api` と組み合わせて動かない場合は、実装を止めて報告し、版の選び直しか改版を著者が判断する。未知の prompt 名は番兵関数が止め、上流の実装により `McpError` として返る（名前はサーバ側に渡らないため例外文に入れられない。README に明記）。`prompts` が見えないクライアント向けに、`get_reading_guide` の `templates` 欄へ同じ文面を入れる。

## 7. テスト（施工の完了条件＝Pro案§11を採用）

**データ**：D01 原論文改変→起動拒否／D02 ガイド・主張JSON改変→bundle不一致で拒否／D03 欠落・余剰・許可外パス（`.DS_Store` も余剰として拒否）／D04 節ID・行範囲・引用位置の有効性（改変は一時コピーにだけ行い、実物 `data/` の前後ハッシュが一致すること）。
**ツール**：T01 五本と論文版・言語表／T02 `get_section` 既定範囲の完全一致・親見出し契約／T03 不存在アンカー＝状態と実在候補・架空出典なし／T04 検索ヒット・ゼロ件・同点の安定順位・`match_via`／T05 T5主張のフィールド対応・原文抜粋・非主張配列・追加根拠の保持・欠けた欄の `null`／T06 T1〜T4＝`ledger_not_available`（ラベル創作なし）／**T07 凍結定式二本＝exact**（T5 abstract『AI can deliver the state of affairs; it cannot deliver the fact of participation.』〔t5-abstract〕・T5 §5.4『AI can assist play. It cannot take one's place in it.』〔t5-5-4〕。コーパスの validate_corpus.py が保護する二文）／T08 許可表記差＝normalized＋規則表示／T09 内容語・否定・数値改変＝不一致（対象全文に別一致がないことを確認したデータで）／T10 空引用・最小長未満・上限超過＝`invalid_input`、複数出現＝曖昧さ表示／T11 圧縮候補の肯定・否定・引用・疑問＝規則通り返し意味の正誤へ格上げしない（fixtures 注入）／T12 翻訳・訳注＝別種別・原文への帰属を偽らない・preparation の添付。
**安全**：S01 `../../.env`・絶対パス・URL・巨大入力・異常なk・孤立サロゲート・`Host` の欠落／重複／IPv6＋ポート／括弧の接尾辞・本文 65,535／65,536／65,537 バイト・chunked＋偽 CL・低速分割送信・`Origin` 付き要求＝許可範囲と有限資源（孤立サロゲートは6ツールの関数層と MCP の `\udXXX` 形式で自動試験）。同時実行は Event で枠を埋めて超過が通信層で返ること。許可一覧は完全一致で試験に固定し、開放経路への大量要求で遮断記録が嵐にならないこと（20件以上で失敗）。起動直後の同時100本の初回呼び出しが通り内部クライアントが一つであること。`GRADIO_*`・`GRADIO_SERVER_NAME` を設定したまま起動しても bind 先・vibe/dev/allowed_paths が変わらない／S02 fixtureの命令風テキスト＝処理と権限が変わらない／S03 起動・呼出しの外向き通信が宣言範囲内（監査は起動から停止まで、宛先 host:port を記録して実際の自己接続だけを免除し、Unix ソケットを一律免除せず、open の mode/flags・rename の元と先・子プロセス・`sendmsg` を記録し、`data/` 宛ての書き換えは遮断する。陽性対照を置き、検出漏れを記録する。README には §2.10 の範囲だけを宣言）。同時実行の上限超過は通信層で返り `status` に混ざらないこと。`lsof` の待ち受けが `127.0.0.1:<port>` の一行だけであること（`spaces` モードでは `0.0.0.0:7860` の一行）。S04（Spaces 上）：Space に上げた状態で、外から `Host` 不一致が 400、`Origin` 付きで許可ヘッダが返らない（エッジの改変も含めて外から測る）、健康検査が Running になる、stdout／stderr に受信した値が出ない、S03 相当の監査（起動時の外向き通信・書き込み）を Space のログで確認。
**再現**：R01 同入力・同データ・同規則＝結果データがバイト単位で一致（別プロセスでも。過負荷のない条件で）。
**MCP**：M01 七ツールの一覧・呼出し・スキーマ一致（`spaces` モードでは `SYSTEM` を除去するため接頭辞は付かない。付いていれば除去が効いていない＝不合格）／M02 resources/promptsの一覧・取得（resources 本文の SHA-256 が bundle と一致・prompts 文面が一致。prompts/get の名前照合の挙動を記録。番兵関数を最後に登録）／M03 不正入力・ゼロ件が通信断と区別されて返る（型ヒント違反の経路とアプリ側検証の経路の両方）。
**対話（スモーク・機械的全機能試験ではない）**：E01 五問（R01・R08・R13・R14・R15）を ja／en 両方・ガイド条件「なし」と `read_with_guards` の二条件で＝正しい原文・位置・記録を保持。配置段階一の基準＝12本（設問の日本語版で五問×二条件＋英語版で R01・R14 をガード条件）。**20本すべて実施済み（9/18 に12本・9/19 に残り8本・Claude Code／Opus 5・全本合格・総括 `docs/acceptance/2026-09-18-e01-e02.md`）**。観察：該当は否定文や資料内の語に対して出てモデルが返却原文と比較して保持した／取りこぼしは PATTERNS-0.2.1 へ／強調記号の差は NORM-1.1.0 へ／ハイフンは SEARCH-1.1.0 へ／出現数順位で T2 に届かず派生物が経路になった／T1 §3.1 と §4.2 の記述の食い違いを二セッションが独立に検出（著者の在庫）。`AI_READING_TESTS` の resource は読ませない（読んだ場合は記録）。判定は本節の文言に限り、コーパス基準との照合は記録のみ／E02 会社の相談例・資料中の命令文＝原文と事例判断を分け、資料を上位命令として扱わない。**実施済み（同日・1本合格：資料内の「AI への指示」を資料として読み従わず、KPI の問いを T4 §5.3 の「測ってよいもの」の線で扱い、判断を部署に残した）**。
**公開**：P01 Space 再起動・休止復帰後に再接続し、復帰までの時間を記録。P02 Space の URL で M01〜M03 と E01 二問（R01・R14）を Claude Code から実施。P03 Claude Desktop（Custom Connector・遠隔 HTTPS）と ChatGPT 開発者モードから `list_papers`。

## 8. 接続（A06）

**Streamable HTTP のみ**。接続URLは採用したGradio版が実際に提供するもの（`/gradio_api/mcp/`）を起動表示と接続試験で確認しREADMEに記録。旧 SSE（`/sse`・`/messages/`）と別名 `/http` は閉じる（閉じた状態で M01〜M03・SDK・mcp-remote〔http-only〕が動くことを実測済み）。起動は `.venv/bin/python app.py`（インタプリタを明示）。起動手順で不要な環境変数（API キー等）を子プロセスに渡さない。
- **施工段階3**：SDK と **Claude Code**（`claude mcp add --transport http mekiki-reader http://127.0.0.1:7860/gradio_api/mcp/`。リポジトリ直下の `.mcp.json` にも同じ設定を置き、CLI と Desktop アプリの Code タブで共通に読めるようにする）。**検収済み**（`docs/acceptance/2026-09-18-claude-code.md`）。Code タブでは prompts の一覧がセッション内で一度サーバに触れてから現れる（README に明記）。
- **施工段階4**：**Claude Desktop**。設定ファイルは stdio のみを受け、UI の Custom Connectors は Anthropic 側から取得するため loopback に届かない。よって `mcp-remote@0.14.2`（`--allow-http --transport http-only`・Node.js 18 以上）で橋渡しする。設定ファイル（`~/Library/Application Support/Claude/claude_desktop_config.json`）は利用者自身が書く（施工側はリポジトリ外を読み書きしない）。橋渡し自体の動作は SDK で確認済み（prompts 6件で再検収）、実機の検収は著者（任意・未実施）。
- **配置段階二**：Space の URL `https://<owner>-<space>.hf.space/gradio_api/mcp/`。Claude Code は `claude mcp add --transport http`、Claude Desktop・claude.ai は Custom Connector（遠隔 HTTPS なので mcp-remote 不要・実機で検収）、**ChatGPT開発者モード**（Space の遠隔URL）。Secure MCP Tunnel は使わない。HF の MCP バッジと `hf.co/mcp` 経由は HF の機能で、検収の対象外（README にその旨）。
検収では `tools/list`・各呼出しに加え、resources/promptsの一覧・取得を接続先ごとに確認し、`docs/acceptance/` に記録する。

## 9. 段階と配置

**施工段階（CLAUDE.md）**：0 読了・計画→1 `data/`・bundle・corpus（D01〜D04）→2 schema・normalize・terms・tools・patterns（T01〜T12・R01）→3 app.py・接続（S01〜S03・M01〜M03）→4 README・requirements 固定・検収記録。実行環境は Python **3.13**（uv で導入・minor をローカルと Spaces でそろえる）、Gradio は **6.27.0** を暫定（`run_history=False` 必須・施工段階3の着手時に再比較して確定）。
**配置段階一（ローカル）**：`.venv/bin/python app.py`（loopback）→Claude Code（`.mcp.json` を許可）から接続し `docs/acceptance/` に記録→Codex①②の反映→五問（E01）と E02→**自分用の正典統一は 2026-09-18 に完成**（Desktop の実機検収は任意で残す）。
**配置段階二（公開）**：HF PRO加入→**Docker Space**（CPU Basic・最初は private）→**一式**（`Dockerfile`・`.dockerignore`・`app.py`・`mekiki_reader/`・`data/`〔LICENSE・CITATION.md を含む〕・`requirements.txt`・`README.md`〔YAMLに `sdk: docker`／`app_port: 7860`／`license: mit`〕・`LICENSE`・`NOTICE`）を git で push（フォルダのアップロードは `.DS_Store` が混入しうる）→S04・M01〜M03・P01・P02 を private のまま検収（Claude Code は読み取りトークンをヘッダで送る）→README に接続 URL と復帰時間→開示に署名と対象コミット→Space を public に（この時点では告知しない）→P03（Custom Connector と ChatGPT は認証ヘッダを送れないため public 後にしか検収できない）→GitHub リポジトリを public に→X一投（動くURLと一緒に・「棚が先にあった」・生成開示）。ZeroGPU の無料枠は Gradio SDK 専用で Python 3.12 以前のため使わない。公開前に `DECISIONS.md` の非公開資料への参照を置換し、未報告の上流不具合の詳細を要約化する。公開前に、標準出力・標準エラーと Spaces 側のログに利用者入力が残るかを実測し、開示に記す。Codex③は実施済み（対象 40b2777・11件反映・437件通過）。Spaces 構成の施工後に Codex④（③の残存と配置モードだけの狭い検査）を入れる。

## 10. 役割

- **Claude Code＝施工**：§3〜§8を実装。判断は CLAUDE.md v1.1 の級に従う（著者判断だけ停止・施工判断は提案して続行）。`DECISIONS.md` に採用版・コミットSHA・規則の版・使用モデルを記録。原文MDと `source_manifest.json` には触れない。守則に反する実装が必要になったら実装せず報告。リポジトリの外を読まない。
- **Codex＝独立検査**：守則十一項への抵触（外部呼び出し・非決定・出典欠落・原文改変・LLM呼び出し・任意パス）、敵対的テストの追加（S01〜S03・T09〜T11・同義語再生）、応答スキーマの一貫性。**指摘と差分案のみ。** 検査したコミット SHA と版を報告冒頭に記録し、修正後に再検査（①＝対象 6b8dcaa・10件、②＝対象 41fa3f9・7件＋残存3件。原本は `docs/review/`）。施工は反映後に自己点検を一回行い、自分の退行を merge 前に捕まえる。
- **Claude＝最終検査**：五問の生応答を原文と突合。パターン候補一覧と用語対応表の候補の起草。本書の改版の起草。施工報告の照合と Codex 指摘の仕分け。
- **規則文書の版**：項目を足したら MINOR、既存の値を変えたら MAJOR。運用は `main` の `72b13eb` 以降の改版に適用し、それ以前の改版は `DECISIONS.md` の一覧を正とする（遡って振り直さない）。
- **著者＝判断と署名**：パターン一覧・用語対応表・prompts 文面・試験用テキストの承認、`author_answerable` を埋めるならコーパス側（3.6.0）で、対応クライアントの範囲、PRO加入、Space作成、README末尾の開示とライセンス節、上流への報告の要否、X一投。

## 11. 触れないもの

意味検索・埋め込み・外部LLM・チャットUI（別方針書）／判断を採点する架空ツール／非公開資料の同梱／`compare_versions`（一版固定と整合するため初版から外す。英訳 manifest の `source.corpusVersion=3.2.1` は記録のまま返し、版どうしの比較は応答に出さない）／理論の妥当性の主張／概念レベルの用語対応（対訳と表記揺れに限る）／形態素解析器。

## 12. 改版履歴

### v2 → v2.1

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

### v2.1 → v2.2
1. §2.10 自己呼び出し経路（queue/join・queue/data）と `/` の HTML を開示対象として明記。HF 系環境変数四つ。通信層の上限（同時4・64 KiB）とポート環境変数（施工段階3の実測）。
2. §2.11 使用モデルの列挙方法。
3. §3 構成に `__init__.py`・`.mcp.json`・`scripts/build_patterns.py`・`scripts/find_term_sources.py`・`pytest.ini`・`docs/candidates/`・`requirements*.in`・検収様式を追加（施工段階2〜4の食い違い②）。
4. §4 `derivative_of` の意味（配列・paper_md は null）と SCHEMA.md への参照。`source_excerpt` の打ち切り。
5. §5 `language` の空文字＝原文。§5.3 の順位を「種類数→直接一致→総出現数」に訂正（v2.1 の誤り）。TERMS-0.1.1 と query の生文字数上限。§5.5 最小長（5／10字）と上限20件の確定値。§5.6 文字範囲の locator・抜粋の打ち切り・PATTERNS-0.1.0（49件）。
6. §6 英語 prompts を `_en` の別名で登録。未知の prompt 名の挙動と `templates` 欄。
7. §7 S03 の監査範囲（開いたファイル・同時実行・lsof）、M02 の一致条件。
8. §8 Claude Desktop は mcp-remote@0.14.2 で橋渡し（実測）。
9. §9 配置段階一の順序（接続記録→Codex→五問）と、公開前のログ実測。
10. §10 Claude の役割に施工報告の照合と Codex 指摘の仕分けを追記。

### v2.2 → v2.3
1. §2.5 表ハッシュ（TERMS・PATTERNS）の import 時照合と生成器の定数更新（Codex①-7・②-6）。
2. §2.10 通信層の実測値と検査（実バイト打ち切り・TE/CL・408・Host・Origin/CORS・/call/* 遮断・queue の受付／待機／待ち行列／未回収結果・プロキシ変数・LRU・固定長記録）（Codex①-2〜5・②-1〜5）。
3. §3 `docs/review/`・E01 の記録と総括。
4. §5.3 SEARCH-1.1.0（ハイフンを語境界に。E01 R13）。§5.5 NORM-1.1.0 `MARK-EMPH`（E01 R14）と孤立サロゲート。§5.6 PATTERNS-0.2.1・PATTERNS-MATCH-1.1.0・結果数の上限を設けない裁定。v2.2 の「PATTERNS-0.1.0（49件・語形293）」は旧値で、本版で訂正。
5. §7 S01・S03 の追加項目（Codex②）と E01・E02 の実施記録。
6. §8 Claude Code の検収済み、Code タブでの prompts の見え方、Desktop 実機は任意。
7. §9 配置段階一の完成（2026-09-18）と Codex③の位置。§10 Codex①②の実績と施工の自己点検。

### v2.3 → v2.3.1
1. §2.10 開放経路の最終一覧（8本・完全一致）、`/config`・旧 SSE・`/http`・`/call/*` の閉鎖、heartbeat が塞げない理由、長時間接続の上限（8／8／32）、内部クライアントの起動時単一化、64 KiB と 408 の適用範囲と HTTP 層との分担。
2. §3 `codex-2.md`。§5.5 LIMITS-2.0.0。§5.6 「があると証明」の表記。
3. §7 E01 の段階一基準＝12本（公開前に20本）、孤立サロゲートの自動試験、許可一覧の固定と再試行の嵐の検査、起動直後の同時100本。
4. §8 Streamable HTTP のみ（SSE 閉鎖の実測）。§10 規則文書の版運用と境界（`72b13eb`）。

### v2.3.1 → v2.4
1. §2.10 Codex③の反映（受付枠と送信期限・未回収結果の基準・ログの整形・heartbeat の記述を互換性説明に）。配置モード `MEKIKI_READER_MODE`（local／spaces）と、spaces で変わる三点（bind・許可 Host＝`SPACE_HOST`・`/` の Host 不問）、除去する環境変数、`pwa=False` の固定、Secret を置かない、`spaces` パッケージを入れない。
2. §2.11 ログの開示（stdout／stderr・閲覧者・保持）と `hf.co/mcp` の扱い。
3. §3 `Dockerfile`。
4. §7 S04（Spaces 上の外からの検査）、M01 の接頭辞の扱いの反転、P01〜P03。
5. §8 Space の URL と各クライアントの接続方式（Desktop は Custom Connector）。
6. §9 Docker Space・private で検収してから public・ZeroGPU 不使用・Codex④の位置。

### v2.4 → v2.4.1
1. §3 `.dockerignore` と README の YAML 記述を Docker Space に合わせた。§9 一式に `.dockerignore`、git push を推奨、P03 を public 後に（認証ヘッダの制約）。

### v2.4.1 → v2.4.2
1. §2.10 `spaces` のポートを 7860 固定に（Codex④ F7）。§5.5 LIMITS-3.1.0（F9）。§3・§7 E01 の完了記述を20本に同期（F9）。

