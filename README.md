---
sdk: gradio
sdk_version: "6.27.0"
python_version: "3.13"
app_file: app.py
license: mit
---

# Mekiki Reader（mekiki-mcp）

Mekiki Framework の論文 T1〜T5 を、**固定した版から・出典つきで・決定的に**読むための MCP サーバ。
サーバの中に言語モデルは無い。取得・語句照合・記録の返却だけを行い、意味の判断はしない。

> **In short.** A read-only MCP server over a pinned snapshot (v3.5.0) of the Mekiki Framework corpus
> (papers T1–T5). It fetches sections, matches strings, and returns what the author recorded — with a
> citation, version and locator on every result. No model runs inside the server; after start-up, every
> source it returns comes from the bundled data. Seven tools, twelve resources, six prompt templates
> (three in Japanese, three in English).

## 1. 設計上の対応

| ツール | 設計上保ちたい区別 | 根拠・参照先 |
|---|---|---|
| `list_papers` / `get_section` / `search_passages` | 読むことの外化（取得・検索）は渡し、何を良しとするかは渡さない | T1（仕様と外化の分離） |
| `get_claim_record` | 主張の位置づけは**著者が記録した通り**返し、道具は真偽を判定しない | T2（能力と正統性の分離）・`claims/t5.json` |
| `verify_quote`・版と位置の記録 | 返答を原文と**照合できる**ようにし、出典・版・位置を残す。ツールは照合結果を返すが、判断について答える立場を著者や利用者から引き受けない | T3（answerability は関係的な立場・§4.1・§4.3–4.4） |
| `check_compressions` | 要確認箇所に対して関連する原文を返す（禁止でなく根拠の提示） | T4（理由を返す経路）・FOR_AI_READERS |
| `get_reading_guide`・サーバ内LLMなし・四モードは任意の設定 | 道具が届けるのは該当原文で、理解は届けない | T5・FOR_AI_READERS（四モードは任意の応用ヒューリスティクス） |

**設計の整合は理論の妥当性の証明ではない。静的な方針の検証は動作の保証でもない。**

### 保証は三層に分ける

| 層 | 保証・確認すること | 保証しないこと |
|---|---|---|
| サーバ | 固定データからの取得、文字列照合、記録済み情報の返却、入力制限、結果ごとの出典 | 自然言語の意図分類、文脈での意味判断、最終回答の妥当性 |
| MCP接続 | 七ツールの発見・呼出し、応答スキーマ、resources/prompts の提供 | 取得した prompt を接続先 AI が常に採用すること |
| 対話 | 選んだガイドに沿ったツール利用、原文と解説の分離、適用判断の支援 | 任意のモデル・任意の会話での無条件の遵守 |

## 2. しないこと

- コーパス・利用者のファイル・外部サービスの変更（読み取り専用。取得は許可済みの ID からだけ）。
- 意味検索・埋め込み・外部モデルの呼び出し（サーバ内に LLM を置かない）。全ツールは決定的で、同じ入力・同じデータ・同じ規則なら同じ結果データを返す。
- 判断の採点、読解の正誤判定、利用者の分類。
- 非公開資料の同梱、版どうしの比較（`compare_versions` は作らない）、理論の妥当性の主張。
- 概念レベルの用語対応（用語表はコーパス自身が示す対訳と表記揺れに限る）、形態素解析。
- 利用者が指定した任意のパス・URL・シェル命令の実行。
- チャット UI の提供（このサーバに画面は無い）。

## 3. 同梱データと版

| 項目 | 値 |
|---|---|
| コーパス版 | `3.5.0`（タグ `v3.5.0`） |
| 固定コミット | `67480613108cf72c29d5691e3d7a6c7e6553eb9b` |
| tree | `7c50a4fc2bf20f1529aebe8a8b7898e26332f1a1` |
| bundle ハッシュ | `40a09c5ba422582c951928f873f5729a420514a46409359559d7e6123c1224d5` |
| 同梱ファイル | コーパス由来 18本（`data/` 配下。下記）＋照合用の `data/bundle_manifest.json` |

同梱：`source_manifest.json`・`papers/T1〜T5.md`・`THEORY_MAP.md`・`FOR_AI_READERS.md`・`SOURCE_INDEX.md`・
`claims/t5.json`・`T5_CLAIM_STATUS.md`・`tests/reading_cases.json`・`AI_READING_TESTS.md`・
`translations/T4.en.md`・`translations/T4.en.manifest.json`・`llms.txt`・`LICENSE`・`CITATION.md`。

起動時に `data/bundle_manifest.json` で、①manifest 自体のハッシュ → ②形式と許可一覧 → ③欠落・余剰・種別 →
④各ファイルのバイト列と SHA-256 → ⑤コーパス内部の記録（`source_manifest.json` の行数など）→ ⑥索引、の順に検査する。
一つでも合わなければ**起動しない**。`main` は読みに行かない。固定の参照先は各結果の `snapshot_url`（固定コミットの raw URL）。

この照合が想定しているのは**事故の検出**（改行変換・誤コピー・部分更新）であって、改竄への耐性ではない。

## 4. ツール・resources・prompts

### 七ツール

| ツール | 返すもの | status | 主な上限 |
|---|---|---|---|
| `list_papers()` | 五本の題名・版・DOI・原文の言語・英訳の有無・節一覧（`source_manifest.json` の記録） | `ok` | — |
| `get_section(paper_id, anchor, language="")` | 記録された行範囲の原文（行を改変しない）。`language="en"` は T4 英訳のみ。訳注は別結果 | `ok` / `unknown_id`（近傍候補5件）/ `invalid_input` | ID は1〜128字。パス・URL の形は `invalid_input` |
| `search_passages(query, paper_id="", k=5)` | 語句検索（モデルなし・行単位）。全語一致を `results`、一部一致を `candidates`。一致位置・±100字の抜粋・`match_via`・節への経路 | `ok` / `no_lexical_match` / `unknown_id` / `invalid_input` | query は生1000字・畳み込み後200字・断片8個、`k` は1〜20（既定5） |
| `get_claim_record(claim_id="", query="")` | `claims/t5.json` の記録を逐語（台帳の `status`〔位置づけのラベル〕・`source_quote`・`not_claimed` ほか）。未記録欄は `null` | （応答の状態）`ok` / `unknown_id` / `ledger_not_available`（T1〜T4）/ `no_lexical_match` / `invalid_input` | `query` 経路の候補は5件。`unknown_id` では台帳の全項目、`ledger_not_available` ではその論文の全節を候補に出す |
| `verify_quote(text, paper_id="", language="")` | 引用が原文にあるかの照合（`exact` / `normalized` / `none`）と、位置・差分・近接候補 | `ok` / `quote_not_found` / `unknown_id` / `invalid_input` | text 2000字、最小長は仮名・漢字を含めば5字・それ以外10字、一致20件 |
| `check_compressions(text)` | 著者が承認した語形に当たった箇所と、その関連原文の抜粋 | `ok`（該当ゼロでも ok）/ `invalid_input` | text 2000字、抜粋1000字、一致20件 |
| `get_reading_guide(part="all")` | `FOR_AI_READERS.md` の該当部分と、読み方の雛形（`templates`） | `ok` / `invalid_input` | `part` は11個の固定列挙 |

`status` は六値（`ok` / `unknown_id` / `quote_not_found` / `no_lexical_match` / `invalid_input` / `ledger_not_available`）で、混ぜない。
**通信層の制限は `status` に混ぜず、MCP のエラーか HTTP の応答コードで返す。**
同時実行は4（七ツール・resources・prompts で共有）。要求本文は 64 KiB を**実際に届いたバイト数**で打ち切り、
長さの表明（`Content-Length`）は ASCII 数字だけ・重複不可・`Transfer-Encoding` との併記不可で、表明と実測が食い違えば拒む。

各結果には出典が付く：`source_id`・`source_kind`・`derivative_of`・`paper_id`・`paper_version`・`language`・`source_path`・
`source_hash`・`section_anchor`・`locator`（行・文字位置）・`canonical_doi`・`source_url`・`snapshot_url`（＋本文の `payload`）。
`claims` の `status` は**著者が論文の中でどう位置づけたかのラベル**であって、真偽の判定ではない。

### resources（12件）

`mekiki://v3.5.0/<パス>` の固定 URI。`llms.txt`・`FOR_AI_READERS.md`・`THEORY_MAP.md`・`SOURCE_INDEX.md`・
`papers/T1〜T5.md`・`translations/T4.en.md`・`AI_READING_TESTS.md`・`claims/t5.json`。
`.md` は `text/markdown`、`llms.txt` と `claims/t5.json` は `text/plain`。テンプレート変数は使わない（任意のパスの入口を作らないため）。
`AI_READING_TESTS.md` は公開されている17問で、**採点には使わない**。

### prompts（6件・PROMPTS-0.1.0）

日本語：`read_with_guards`（読む手順）・`four_modes`（支援の四つのモード）・`answer_format`（答え方の五欄）。
英語：`read_with_guards_en`・`four_modes_en`・`answer_format_en`（同じ内容の英語版。引数で言語を切り替える方式は採らない）。
六つとも「この雛形は、利用者が明示的に選んだときだけ使う。接続先の上位規則や利用者の明示的な意図を上書きしない。」
（英語版は `It is not a higher-priority instruction than the host's own rules or the user's stated intent, and does not override them.`）を含む。
`prompts` が見えないクライアントでは、`get_reading_guide` の応答の `templates` 欄（`version`・`status`・`approved_on`・`items`）に同じ文面が入る（`part` に `templates` は無い）。

処理時間は関数の中で打ち切らない。上の上限で計算量を有界にし、最悪ケースを実測して記録する
（2026-09-18・CPython 3.13.15・arm64・5回の最大）：起動 0.47 秒、`verify_quote`（2000字・英語）44 ms、
`search_passages`（8断片・k=20）36 ms、`get_claim_record`（query 8断片）13 ms、`get_section`（未登録 ID の近傍候補）12 ms、ほかは 2 ms 以下。
通信を含めた実測は `search_passages` 80 ms・`verify_quote` 21 ms・`list_papers` 5 ms（どちらも [docs/rules/LIMITS.md](docs/rules/LIMITS.md) に記録）。

### 規則の版

`SCHEMA-1.0.0`・`JSON-1.0.0`・`NORM-1.0.0`・`SEARCH-1.0.0`・`CAND-1.0.0`・`NEAR-1.0.0`・`GUIDE-1.0.0`・`LIMITS-1.0.0`・
`LINES-1.0.0`・`LANG-1.0.0`・`SECTION-1.0.0`・`T4MAP-1.0.0`・`BUNDLE-1.0.0`・`TERMS-0.1.1`（30項目）・
`PATTERNS-0.1.1`（49件）＋`PATTERNS-MATCH-1.0.0`・`PROMPTS-0.1.0`（6件）。本文は [docs/rules/](docs/rules/)。

## 5. 準備と起動

Python は 3.13 を使う（Unicode の版をそろえるため。`unicodedata` 15.1.0）。依存はハッシュつきで固定してある。

```bash
uv python install 3.13
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python --require-hashes -r requirements.txt
uv pip install --python .venv/bin/python --require-hashes -r requirements-dev.txt
```

`requirements.txt` は稼働用（`gradio[mcp]==6.27.0` ほか66パッケージ）、`requirements-dev.txt` は試験用（pytest）。
`uv` を使わない場合は `pip install --require-hashes -r requirements.txt` でもよい（ハッシュ検証は外さない）。
コーパスは `data/` に同梱してあるので、取得は要らない。

```bash
.venv/bin/python app.py
```

インタプリタは明示する（システムの `python3` は要件を満たさないことがある）。ポートは環境変数
`MEKIKI_READER_PORT`（1024〜65535・既定 7860。塞がっているときは `起動しない：ポート … で待ち受けられない` と出て終了する）。
起動すると次の8行が出る。

```
* Running on local URL:  http://127.0.0.1:7860
* To create a public link, set `share=True` in `launch()`.

🔨 Launching MCP server:
* Streamable HTTP URL: http://127.0.0.1:7860/gradio_api/mcp/
corpus 3.5.0 (6748061)・bundle 40a09c5ba422…
tools 7・resources 12・prompts 6（PROMPTS-0.1.0）
消した環境変数：なし
```

最後の3行がこのサーバ自身の表示で、検収記録にはこの3行をそのまま写す。

待ち受けは `127.0.0.1` だけで、環境変数では変わらない。`GRADIO_*` は読み込み前に消す。
データ根は `data/` に固定で、環境変数でも引数でも変えられない。不要な環境変数（API キーなど）は子プロセスに渡さないこと。

### Claude Code

リポジトリ直下に `.mcp.json` を置いてある（`"type": "http"`）。このリポジトリを開いて作業するときは、
接続先として出てくるので許可すればよい（許可は利用者が行う）。

リポジトリの外から使いたいときは CLI で登録する。こちらは `.mcp.json` ではなく利用者ごとの設定に入る。

```bash
claude mcp add --transport http mekiki-reader http://127.0.0.1:7860/gradio_api/mcp/
```

ポートを変えるときは `MEKIKI_READER_PORT` と `.mcp.json`（または上の登録）の両方を直す。

### Claude Desktop

Claude Desktop の設定ファイルは stdio（`command` / `args`）だけを受け付け、HTTP を直接指定する書き方は公式手順に無い。
UI の Custom Connectors はリモートの URL を Anthropic 側から取りに行く仕組みなので、`127.0.0.1` で待ち受けるこのサーバには届かない。
そこで橋渡しに `mcp-remote`（版を固定・Node.js 18 以上が必要）を使う。**この設定は利用者自身が書き込むこと。**

```json
{
  "mcpServers": {
    "mekiki-reader": {
      "command": "npx",
      "args": ["-y", "mcp-remote@0.14.2", "http://127.0.0.1:7860/gradio_api/mcp/",
               "--allow-http", "--transport", "http-only"]
    }
  }
}
```

ファイルは macOS で `~/Library/Application Support/Claude/claude_desktop_config.json`。書き換えたら Claude Desktop を再起動する。
`--allow-http` は暗号化されない loopback 接続を許すための指定で、外に出る経路では使わない。

橋渡し自体の動作は確認済み：`mcp-remote@0.14.2`（Node v24.13.1）を stdio で起動して MCP クライアントからつなぐと、
ツール7件・resources 12件・prompts 6件が見え、`list_papers` は `ok` を返した。Claude Desktop 本体での確認は
利用者が行い、`docs/acceptance/` に記録する。

### 接続時に知っておくこと

- **未知の prompt 名**は雛形を返さず、MCP のエラー（`McpError: 'data'`）として返る。引数を付けて呼んだときは、上流 Gradio の `Parameter … is not a valid key-word argument` という英文が返る。要求された名前は上流の実装からサーバ側の関数に渡らないため、エラー文に名前を入れられない。登録してある名前は `read_with_guards`・`four_modes`・`answer_format` と、その英語版 `…_en` の六つだけ。
- Hugging Face Spaces に置いた場合、ツール名に Space 名の接頭辞が付く（`<Space名>_list_papers`）。
- `http://127.0.0.1:7860/` をブラウザで開くと Gradio 標準のフロント HTML が返る（UI は無く、静的資産は遮断してあるので画面は組み上がらない）。
- 旧 SSE の経路 `/gradio_api/mcp/sse` は予備。通常は Streamable HTTP を使う。
- ChatGPT の開発者モードからの接続は、公開（Spaces）の段階で確かめる。ローカルの loopback には外から届かない。
- 接続先ごとの確認の記録は [docs/acceptance/](docs/acceptance/) に置く。

## 6. 試験と検収

```bash
.venv/bin/python -m pytest -q
```

D01〜D04（同梱データ）・T01〜T12 と R01（七ツールと再現性）・S01〜S03（安全）・M01〜M03（MCP 接続）。
`-m server` を付けるとサーバを起動する試験だけを走らせる。接続先ごとの検収記録は [docs/acceptance/](docs/acceptance/) に置く。

## 7. ライセンス

このリポジトリには条件の異なる二つの素材がある（[NOTICE](NOTICE) を参照）。

- **コード（`data/` 以外のすべて）**：MIT License（[LICENSE](LICENSE)）。MIT は `data/` には及ばない。
- **`data/`**：Mekiki Framework T1–T5 AI-Readable Corpus v3.5.0 の公開ファイル。CC BY 4.0（[data/LICENSE](data/LICENSE)・<https://creativecommons.org/licenses/by/4.0/>）。
  ただし `data/bundle_manifest.json` は本リポジトリで作成した照合用の一覧で、コーパス由来ではなくコード側（MIT）に属する（[NOTICE](NOTICE)）。

帰属表示は `data/CITATION.md` の書式に従う（引用文の「listed above」が指す DOI の一覧は `data/CITATION.md` の表）：

> Kengo Tomita, *Mekiki Framework T1–T5 AI-Readable Corpus*, <https://mekiki-framework.github.io/>, licensed under CC BY 4.0. Canonical scholarly sources: the T1 through T5 DOIs listed above.

改変の有無：**原文の行は改変しない。行単位で抜粋し JSON に構造化して返す。**
同梱物は `data/LICENSE`（CC BY 4.0）に従う。論文本文中に別の表記があっても同梱物には及ばない。

学術的な引用先は各論文の DOI（`data/CITATION.md` の表）。リポジトリの Markdown・HTML は派生の読解ビューであって、
正典の学術出典ではない。ガイド類と訳注の `canonical_doi` は `null`。

## 8. 開示（下書き・著者の承認待ち）

> この節は施工側の下書きで、文面は著者の承認と署名を待っている。

| 項目 | 記入欄 |
|---|---|
| 承認（この節の文面） | 承認者：＿＿＿＿＿＿／承認日：＿＿＿＿-＿＿-＿＿ |
| 署名 | ＿＿＿＿＿＿＿＿＿＿＿＿ |
| 公開の版 | 対象コミット：＿＿＿＿＿＿＿ |

- **制作工程と使用モデル**：方針（`SPEC.md`）→施工（Claude Code / Claude Opus 5）→独立検査（Codex。指摘と差分案のみ）→最終検査（Claude）→接続確認と公開判断（著者）。生成 AI を使って作った。<!-- 著者確認：独立検査・最終検査に使ったモデルの具体名 -->
- **参照した型**：Paper2Agent（Miao et al., Nature 2026）から借りたのは型（資源・プロンプト・ツール・検証テスト・Spaces での公開）であって工程ではない。読解の対象は T1〜T5（題名・版・DOI は `data/CITATION.md`）。
- **費用と休止**：ローカルで動かす分には追加の API 料金・ホスティング料金は要らない。公開（Spaces）での費用と休止からの復帰時間は、公開時に実測して記す。<!-- 配置段階二で記入 -->
- **利用者入力の送信先と保存方針**：`verify_quote` と `check_compressions` の入力には未公開の情報が入りうる。実測では、起動から全ツール・全 resource・全 prompt の呼び出しまで loopback 以外への接続は0件、書き込みで開いたファイルも0件だった。サーバは入力をファイルに保存しない方針で、実測した範囲（外への接続と、書き込みで開いたファイル）では保存は確認されなかった。**標準出力・標準エラー、およびホスティング側のログに何が残るかは未実測**で、公開の前に実測して記す。
- **外向きの資料取得**：起動後に取得する資料は同梱データだけ。
- **既知の制約**：
  1. T4 の英訳は ChatGPT で作成された派生の言語版で、著者レビューの認証はない。英訳由来の結果には作成経緯（`preparation`・`authority`）を必ず添える。
  2. 英訳の manifest の `source.corpusVersion`（英訳が底本にした T4 の収録版）は `3.2.1` で、manifest 自身の `corpusVersion`（3.5.0）とは別。記録どおり `payload.source_corpus_version` に載せ、版どうしの比較はしない。
  3. 同梱物は `data/LICENSE`（CC BY 4.0）に従う。論文本文中に別の表記（T1 の figshare 寄託データについての `CC BY-NC 4.0`）があっても、同梱物には及ばない。原文は改変しない。
  4. 日本語の問いは英語の論文に当たりにくい（語句の照合であるため）。該当ゼロは記述が無いことを意味しない。
  5. 未知の prompt 名は MCP のエラーとして返る（上流の実装の挙動。本文は §5 参照）。Spaces ではツール名に接頭辞が付く。
  6. `/` に Gradio 標準のフロント HTML が返る。`resources/read` と `prompts/get` はサーバが自分自身に出す HTTP 要求で実行されるため、その経路（`/gradio_api/queue/join`・`/gradio_api/queue/data`）だけは通してある。外から同じ経路を叩くこともできるので、**同時数を8件に、待ち行列を16件に絞って受ける**（超えると HTTP 503）。実行されるのは登録済みの七ツール・resources・prompts だけで、どれも同じ実行枠（同時4）を使う。`/gradio_api/call/*` は塞いである（実測で、自己呼び出しには要らないことを確かめた）。
  7. 起動時に `HF_HUB_DISABLE_TELEMETRY=1`・`HF_HUB_DISABLE_IMPLICIT_TOKEN=1`・`HF_HUB_OFFLINE=1`・`HF_TOKEN_PATH=/dev/null` を設定している（依存ライブラリの利用状況送信を止め、利用者のトークンファイルを開かせないため）。
  8. ブラウザからは応答を読めない。`Origin` ヘッダの付いた要求には CORS の許可（`Access-Control-Allow-Origin` ほか）を一切返さない（`http://localhost:<ポート>` など同じ機械からの Origin も含む）。上流の既定では loopback の Origin に許可が出るため、差し替えてある。MCP のクライアントは `Origin` を送らないので接続には影響しない。
  9. 同梱データの照合は事故の検出までで、改竄への耐性は主張しない。
