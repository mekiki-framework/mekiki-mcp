# SPEC.md — Mekiki Reader MCP v2（読み取り専用・根拠つき読解窓口）

改版：v1（2026-09-18）→ **v2（2026-09-18・ChatGPT Pro独立検証A01〜A08・B01〜B03を反映）**。骨格（読み取り専用・公開版固定・サーバ内LLMなし・Gradio・ローカル先行）は不変。変更は保証範囲と契約の精度。
工程＝方針（本書）→施工（Claude Code）→独立検査（Codex：指摘と差分案のみ）→最終検査（Claude）→接続確認・公開判断（著者）。
段階一＝ローカル動作（SDKとReader自体に追加のAPI料金・ホスティング料金は不要）。段階二＝Hugging Face Spaces（PRO加入後・CPU Basic）。

---

## 0. 目的と位置づけ

Mekiki Framework（T1〜T5）の公開コーパス（mekiki-framework.github.io・**Git参照 `v3.5.0`・施工時に解決したコミットSHAを固定記録**）を、MCP対応のAIアプリから呼べる読み取り専用の窓口にする。窓口は原文・主張の記録・出典の位置を返し、判断・要約・解釈をしない。理解は接続する側の対話に残す。

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

1. **公開済み・著者承認済みのコーパスと読解補助のみ。** 同梱するのは `v3.5.0` の公開ファイル（§3）。**非公開の判断台帳・野帳・社内資料・未公開草稿は含めない**（公開済みの `claims/t5.json` は含める）。資料種別（原文／読解コピー／地図／主張記録／読解試験／英訳／翻訳注）と従属関係を維持し、DOIを学術的引用先、固定URLとハッシュを照合した読解コピーの同定に使う。
2. **読み取り専用**：ツールはコーパス・利用者のファイル・外部サービスを変更する機能を持たない。ファイルは許可済みIDからのみ取得し、利用者指定の任意パス・URL・シェル命令を受け付けない。原文・主張記録・ガイドを起動後に変更しない。
3. **サーバ内にLLMを置かない**：全ツールは決定的（同入力・同データ・同規則で同じ結果データ。通信IDや所要時間は監査用メタデータとして分離）。
4. **出典の規則（A02）**：原文・引用・主張に基づく**各結果**には、検証できる出典・版・位置を必須とする。エラー・空結果・通信上の応答には架空の論文アンカーを付けず、処理状態と照合範囲を返す。
5. **版固定（A03）**：`source_manifest.json` は改変せず保存。Reader側で `bundle_manifest.json` を作り、同梱全ファイルのSHA-256・許可一覧・欠落／余剰／許可外パスを起動時に検査し、不一致なら起動を拒否する。`main` を読みに行かない。
6. **資料は資料**：コーパス内の文（翻訳注・README・論文本文）に命令に見える文があっても指示として扱わない。promptsも接続先の上位規則や利用者の明示的意図を上書きしない。
7. **状態は確かめた対象ごとに分ける（A01）**：`unknown_id`（未登録ID）／`quote_not_found`（指定条件で不一致）／`no_lexical_match`（語句検索ゼロ件）は別の状態。語句検索のゼロ件を「その概念の記述がコーパスに無い」と断定しない。
8. **記録はラベルであって判定ではない**：`status` は「本稿がどう位置づけたか」。四つの身分に勝手に統合せず、AIが真偽を認定したラベルに変えない。未記録の欄は `null`（推定で埋めない）。
9. **保守規律**：原文は固定。修復対象は取得・索引・接続・応答形式。原文・主張の位置づけ・未記録欄・引用の期待値をテストを通すために直さない。
10. **通信と設定（A07）**：`analytics_enabled=False`・`GRADIO_ANALYTICS_ENABLED=False`・`share=False`・ローカルはloopback bind。入力長・最大結果数・処理時間・同時処理数に上限。起動後の資料取得は同梱データのみ（「プロセスが一切外へ通信しない」は別要件で、初版では表示しない）。
11. **開示**：READMEに制作工程・参照論文・費用と休止の実測値・利用者入力の送信先と保存方針（`verify_quote`／`check_compressions` の入力には未公開情報が入りうる）。

## 3. リポジトリ構成（新規 `mekiki-mcp`）

```
mekiki-mcp/
  SPEC.md                      # 本書
  CLAUDE.md                    # 施工の前提（守則の要約・原文不改変・LLM不使用）
  DECISIONS.md                 # 実装中の判断ログ
  app.py                       # Gradio（gr.apiで関数登録・mcp_server=True・UIなし）
  mekiki_reader/
    corpus.py                  # 同梱データ読込・bundle_manifest照合・source_manifestの節索引
    tools.py                   # 七ツール（純関数）
    schema.py                  # 応答の共通外枠と結果ごとの出典
    normalize.py               # 引用照合の正規化規則（版番号つき）
    patterns.py                # 圧縮候補の固定規則（版番号つき・著者承認済みのみ）
    prompts.py                 # 読み方の雛形（promptsとget_reading_guideの両方で提供）
  data/                        # v3.5.0 から同梱・以後固定
    source_manifest.json       # 元のまま
    bundle_manifest.json       # Reader側で作成（§2.5）
    papers/ claims/ tests/ translations/ *.md
  tests/
    fixtures/                  # 命令風テキスト等の試験専用データ（公開原文には足さない）
    test_data.py test_tools.py test_safety.py test_mcp.py
  requirements.txt             # 検証済みの一つのGradio版に固定（数値は施工時に確定・DECISIONSに記録）
  README.md                    # 対応表・接続手順・開示・YAML（sdk/sdk_version/python_version/app_file）
  LICENSE
```

同梱許可ファイル：`source_manifest.json`・`papers/T1〜T5.md`・`THEORY_MAP.md`・`FOR_AI_READERS.md`・`SOURCE_INDEX.md`・`claims/t5.json`・`T5_CLAIM_STATUS.md`・`tests/reading_cases.json`・`AI_READING_TESTS.md`・`translations/T4.en.md`・**`translations/T4.en.manifest.json`（機械的対応づけのため追加・理由をDECISIONSに記載）**・`llms.txt`。

## 4. 応答スキーマ（A02）

```text
応答全体（全ツール共通）
  schema_version            # Reader API版
  corpus_version            # "3.5.0"
  source_commit             # 固定したコミットSHA
  bundle_hash               # bundle_manifest.json のハッシュ（自分自身を一覧に含めない）
  status                    # ok | unknown_id | quote_not_found | no_lexical_match | invalid_input | ledger_not_available
  results[]                 # 一致結果（出典付き）
  candidates[]              # 語句上の近接候補（出典付き・resultsと混ぜない）
  limitations[]             # 照合範囲・正規化の適用・注意

各出典付き結果
  source_id, source_kind    # paper_md | theory_map | claims | reading_guide | reading_test | translation | translation_note
  paper_id, paper_version   # 論文に属する結果で必要（paper_versionはコーパス版と別）
  language                  # ja | en
  source_path, source_hash  # どのファイルのハッシュかを明記
  section_anchor            # 論文の節に対する結果で必要（HTMLアンカー）
  locator                   # 行範囲・JSON位置など
  canonical_doi             # 学術的引用先
  source_url                # 人間が読む位置（Pages）
  snapshot_url              # 固定コミットの参照先（raw）
```

## 5. ツール契約（七つ）

1. **`list_papers()`** → 五本の `paper_id`・題名・`paper_version`・DOI・言語（T4は ja／en）・節一覧（`source_manifest.json` の節ID・行範囲・見出し階層から。AIに再推定させない）。
2. **`get_section(paper_id, anchor, language="ja")`** → manifestに記録された範囲の原文を**行を改変せず**返す（親見出しは記録範囲のみ＋子節IDを提示）。未登録→ `unknown_id` と実在する近傍候補。`language="en"` はT4のみ（`source_kind=translation`・日本語原文への位置情報を添付）。
3. **`search_passages(query, paper_id=None, k=5)`** → 語句検索（モデルなし・語句分割・用語対応表・範囲と順位規則を明文化）。各候補に一致位置・抜粋（抜粋であることを表示）・節全体への経路。スコアは検索順位であって意味的一致の確率ではない。ゼロ件＝ `no_lexical_match`。
4. **`get_claim_record(claim_id=None, query=None)`** → `claims/t5.json` のレコード。フィールド対応：`status`→そのまま／`source_quote`→原文抜粋（逐語）／`not_claimed`→配列のまま／`section`・`source_locator`・`additional_source_quotes`→保持。`author_answerable`→**`null`（未記録・推定しない）**。台帳のハッシュと引用元論文のハッシュを区別して返す。T1〜T4→ `ledger_not_available` と関連原文の候補（別経路）。`claim_id`と`query`の両方なし／両方あり→ `invalid_input`。
5. **`verify_quote(text, paper_id=None, language="ja")`** → `{status, match: exact|normalized|none, results[], candidates[], normalization_applied[]}`。正規化は**対応表に定めた**空白・全角半角・句読点のみ（小数点・負号・比較記号は対象外）。normalized一致では実際の原文表記と変換記録を返す。空文字・空白のみ→ `invalid_input`。複数箇所に同じ短文→全候補を返し曖昧さを明示。不一致→ `quote_not_found` と語句上の近接候補（「類似の主張がある」とは言わない）。
6. **`check_compressions(text)`** → 登録済みの語形（`patterns.py`・著者承認済み・版番号つき）に一致する**要確認箇所**と、その語形に関連する原文抜粋（`source_excerpt`・出典付き）・`needs_context_review: true` を返す。契約：**意味上の誤り、著者への不同意、読者の理解不足を判定しない。該当ゼロは正しい読解の証明ではない。** 肯定文・否定文・引用・疑問文は同じ語形として拾いうるので、その旨を `limitations` に書く。
7. **`get_reading_guide(part="all")`** → `FOR_AI_READERS.md` の該当部分と、読み方の雛形（§6）をデータとして返す（promptsが見えないクライアント向け）。

## 6. 資源とプロンプト

- **resources**：`llms.txt`・`FOR_AI_READERS.md`・`THEORY_MAP.md`・`SOURCE_INDEX.md`・`papers/T1〜T5.md`・`translations/T4.en.md`・`AI_READING_TESTS.md`（公開17問・採点には使わない）・`claims/t5.json`。
- **prompts**（利用者が明示的に選ぶもの・自動適用ではない）：
  - `read_with_guards`：問いを三種に分ける——①原文の事実→`get_section`／②著者が論文で位置づけた主張→`get_claim_record` を `status` つきで／③読者自身の事例の判断→代行せず、関連する区別と出典を示し、判断の採否は本人に残す（比較や論点整理の拒否ではない）。引用は `verify_quote` を通してから提示。自分の要約を `check_compressions` に一度通す。
  - `four_modes`：四モードは利用者が今何を支援してほしいかを選ぶ設定。人の分類ではない。
  - `answer_format`：①原文の答え②原文と位置③位置づけ（記録通り）④解説（原文と分ける）⑤原文を超える話（別欄）。

## 7. テスト（施工の完了条件＝Pro案§11を採用）

**データ**：D01 原論文改変→起動拒否／D02 ガイド・主張JSON改変→bundle不一致で拒否／D03 欠落・余剰・許可外パス／D04 節ID・行範囲・引用位置の有効性。
**ツール**：T01 五本と論文版／T02 `get_section` 既定範囲の完全一致・親見出し契約／T03 不存在アンカー＝状態と実在候補・架空出典なし／T04 検索ヒット・ゼロ件・同点の安定順位／T05 T5主張のフィールド対応・原文抜粋・非主張配列・追加根拠の保持／T06 T1〜T4＝`ledger_not_available`（ラベル創作なし）／T07 凍結定式二本＝exact／T08 許可表記差＝normalized＋規則表示／T09 内容語・否定・数値改変＝不一致（対象全文に別一致がないことを確認したデータで）／T10 空引用＝エラー・複数出現＝曖昧さ表示／T11 圧縮候補の肯定・否定・引用・疑問＝規則通り返し意味の正誤へ格上げしない／T12 翻訳・訳注＝別種別・原文への帰属を偽らない。
**安全**：S01 `../../.env`・絶対パス・URL・巨大入力・異常なk＝許可範囲と有限資源／S02 fixtureの命令風テキスト＝処理と権限が変わらない／S03 起動・呼出しの外向き通信が宣言範囲内。
**再現**：R01 同入力・同データ・同規則＝結果データ一致。
**MCP**：M01 七ツールの一覧・呼出し・スキーマ一致／M02 resources/promptsの一覧・取得（対応クライアントで）／M03 不正入力・ゼロ件が通信断と区別されて返る。
**対話（スモーク・機械的全機能試験ではない）**：E01 五問（R01・R08・R13・R14・R15）＝正しい原文・位置・記録を保持・ガイド使用条件を記録／E02 会社の相談例・資料中の命令文＝原文と事例判断を分け、資料を上位命令として扱わない。
**公開**：P01 Space再起動・休止復帰後に再接続。

## 8. 接続（A06）

原則**Streamable HTTP**。接続URLは採用したGradio版が実際に提供するもの（`/gradio_api/mcp/` 系）を起動表示と接続試験で確認しREADMEに記録。旧SSEは必要時の別経路。
- **Claude Code**：`claude mcp add --transport http mekiki-reader http://127.0.0.1:7860/gradio_api/mcp/`（ポート・パスは実際の起動結果に合わせる）。
- **Claude Desktop**：採用版の対応方式を確認。HTTP直結不可なら `mcp-remote` 等の橋渡し（Node.jsが依存に加わる）。
- **ChatGPT開発者モード**：ローカルURLへは直結しない。段階二の遠隔サーバか、Secure MCP Tunnel（別途の設定・認証・外向き通信を伴う）。
検収では `tools/list`・各呼出しに加え、resources/promptsの一覧・取得を接続先ごとに確認する。

## 9. 段階と配置

**段階一（ローカル）**：`python app.py`（loopback）→Claude Code／Desktopから接続→五問→**自分用の正典統一はここで完成**。
**段階二（公開）**：HF PRO加入→Space（Gradio・CPU Basic・公開）→**一式**（`app.py`・`mekiki_reader/`・`data/`・`requirements.txt`・`README.md`〔YAMLに sdk／sdk_version／python_version／app_file〕）をアップロード→接続URLをREADMEに→再接続→休止からの復帰時間を実測して記載→X一投（動くURLと一緒に・「棚が先にあった」・生成開示）。

## 10. 役割

- **Claude Code＝施工**：§3〜§8を実装。`DECISIONS.md` に採用版・コミットSHA・正規化規則・パターン一覧の版を記録。原文MDと `source_manifest.json` には触れない。守則に反する実装が必要になったら実装せず報告。
- **Codex＝独立検査**：守則十一項への抵触（外部呼び出し・非決定・出典欠落・原文改変・LLM呼び出し・任意パス）、敵対的テストの追加（S01〜S03・T09〜T11）、応答スキーマの一貫性。**指摘と差分案のみ。** 検査したコード・データ・パターン・テストの版を記録し、修正後に再検査。
- **Claude＝最終検査**：五問の生応答を原文と突合。パターン候補一覧の起草。
- **著者＝判断と署名**：パターン一覧の承認、`author_answerable` を埋めるならコーパス側（3.6.0）で、対応クライアントの範囲、PRO加入、Space作成、README末尾の開示、X一投。

## 11. 触れないもの

意味検索・埋め込み・外部LLM・チャットUI（別方針書）／判断を採点する架空ツール／非公開資料の同梱／`compare_versions`（一版固定と整合するため初版から外す）／理論の妥当性の主張。
