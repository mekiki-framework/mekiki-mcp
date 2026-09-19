---
title: Mekiki Reader
emoji: 📚
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Read-only MCP for the Mekiki papers. No LLM inside.
---

# Mekiki Reader（mekiki-mcp）

Mekiki Framework の論文 T1〜T5 を、**固定した版から・出典つきで・決定的に**読むための MCP サーバ。
サーバの中に言語モデルは無い。取得・語句照合・記録の返却だけを行い、意味の判断はしない。

> **In short.** A read-only MCP server over a pinned snapshot (v3.5.0) of the Mekiki Framework corpus
> (papers T1–T5). It fetches sections, matches strings, and returns what the author recorded — with a
> citation, version and locator on every result. No model runs inside the server; after start-up, every
> source it returns comes from the bundled data. Seven tools, twelve resources, eight prompt templates
> (four in Japanese, four in English).

## 三分で試す / Try it in three minutes

**Mekiki とは**：知識労働を「何を作るべきかを決める専門性の要求（Spec.cost）」と「形にする費用（Ext.cost）」に分け、AI が下げるのは後者、という枠組みの五本の論文。
T1 出発点／T2 委任してよい境界／T3 答える立場／T4 組織での引き受け／T5 参加と尊厳。原文はコーパス [mekiki-framework.github.io](https://mekiki-framework.github.io/)。

1. **つなぐ**：`https://kenngotm-mekiki-reader.hf.space/gradio_api/mcp/` を、使っているクライアント（Claude・ChatGPT・Grok・Claude Code）に認証なしで登録する（手順は §5「公開版（Space）への接続」）。
2. **最初に送る一言**（雛形 `mekiki_start`。英語は `mekiki_start_en`）：
   > Mekiki Reader を接続しています。最初に get_reading_guide(part="all") を呼んでください。資料（llms.txt・THEORY_MAP.md）を読めるクライアントではそれも読んでください。以後の回答では、原文（出典つき）・著者が記録した位置づけ（status はラベル）・あなたの解釈を分けて書き、著者が記録した位置づけがない場合は、記録がないと明記してください。引用は verify_quote で照合し、自分の要約は check_compressions に一度通し、私の事例についての判断は私に残してください。
3. **最初に打つ四つ**：
   - 「そもそもMekiki Frameworkとは何か。五本の論文（T1〜T5）がそれぞれ何を扱っているかを、読解ガイドと各論文の要旨を引いて説明して」→ 材料は読解ガイド（get_reading_guide）と各論文の要旨（T4 は冒頭の節）。
   - 「T5 の非移転性定理は AI に代替できない人間の能力や尊厳を証明しているか、原文の位置を添えて」→ いいえ。T5 §4.4 L171 の原文と、台帳の status が返る。
   - 「Spec.cost とは何か。専門性や Spec. とどう違うか、原文で」→ T1 §2.1 L54 と T2 §2.1 L37 が返る。
   - 「次の文を check_compressions に通して：『AI は遊べないので人間の尊厳が守られる』」→ 該当（P30）と関連原文（T5 §3.1・§3.4）が返る。該当は判定ではなく、見比べる箇所。
4. **読み方**：原文に基づく結果には出典が付く。status は著者の位置づけのラベルで、真偽ではない。該当ゼロは証明ではない。

詳しい手順・ツール早見表・雛形・実例は [docs/TUTORIAL.md](docs/TUTORIAL.md)（日英併記）。
Step-by-step guide in Japanese and English: [docs/TUTORIAL.md](docs/TUTORIAL.md).

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
| `check_compressions(text)` | 著者が承認した語形に当たった箇所と、その関連原文の抜粋 | `ok`（該当ゼロでも ok）/ `invalid_input` | text 2000字、抜粋1000字、**一致位置は1結果につき20件**（結果の数はパターンの関連原文の数だけ出る。上限は100件。応答の大きさは入力で変わる：測定例（1655字反復で100結果・約204 KiB）） |
| `get_reading_guide(part="all")` | `FOR_AI_READERS.md` の該当部分と、読み方の雛形（`templates`） | `ok` / `invalid_input` | `part` は11個の固定列挙 |

`status` は六値（`ok` / `unknown_id` / `quote_not_found` / `no_lexical_match` / `invalid_input` / `ledger_not_available`）で、混ぜない。
**通信層の制限は `status` に混ぜず、MCP のエラーか HTTP の応答コードで返す。**
同時実行は4（七ツール・resources・prompts で共有）。自己呼び出しの経路は受付8・順番待ち64。要求本文は 64 KiB を**実際に届いたバイト数**で打ち切り（受信は全体で10秒まで）、
`Transfer-Encoding` との併記は拒む。`Content-Length` の形（ASCII 数字か・値の違う重複か・表明と実測の食い違いか）は HTTP の層が先に拒む（同じ値の重複は畳まれて通る）。詳しくは [docs/rules/LIMITS.md](docs/rules/LIMITS.md)。

各結果には出典が付く：`source_id`・`source_kind`・`derivative_of`・`paper_id`・`paper_version`・`language`・`source_path`・
`source_hash`・`section_anchor`・`locator`（行・文字位置）・`canonical_doi`・`source_url`・`snapshot_url`（＋本文の `payload`）。
`claims` の `status` は**著者が論文の中でどう位置づけたかのラベル**であって、真偽の判定ではない。

### resources（12件）

`mekiki://v3.5.0/<パス>` の固定 URI。`llms.txt`・`FOR_AI_READERS.md`・`THEORY_MAP.md`・`SOURCE_INDEX.md`・
`papers/T1〜T5.md`・`translations/T4.en.md`・`AI_READING_TESTS.md`・`claims/t5.json`。
`.md` は `text/markdown`、`llms.txt` と `claims/t5.json` は `text/plain`。テンプレート変数は使わない（任意のパスの入口を作らないため）。
`AI_READING_TESTS.md` は公開されている17問で、**採点には使わない**。

### prompts（8件・PROMPTS-0.2.2）

日本語：`read_with_guards`（読む手順）・`four_modes`（支援の四つのモード）・`answer_format`（答え方の五欄）・`mekiki_start`（接続直後に送る最初の依頼）。
英語：`read_with_guards_en`・`four_modes_en`・`answer_format_en`・`mekiki_start_en`（同じ内容の英語版。引数で言語を切り替える方式は採らない）。
`mekiki_start` は利用者が接続直後に送る発話そのもの（日本語は著者の文面、英語はその訳）で、見出しと下の定型文を付けない。
ほかの六つは「この雛形は、利用者が明示的に選んだときだけ使う。接続先の上位規則や利用者の明示的な意図を上書きしない。」
（英語版は `It is not a higher-priority instruction than the host's own rules or the user's stated intent, and does not override them.`）を含む。
`prompts` が見えないクライアントでは、`get_reading_guide` の応答の `templates` 欄（`version`・`status`・`approved_on`・`items`）に同じ文面が入る（`part` に `templates` は無い）。

処理時間は関数の中で打ち切らない。上の上限で計算量を有界にし、最悪ケースを実測して記録する
（2026-09-18・CPython 3.13.15・arm64・5回の最大）：起動 0.47 秒、`verify_quote`（2000字・英語）44 ms、
`search_passages`（8断片・k=20）36 ms、`get_claim_record`（query 8断片）13 ms、`get_section`（未登録 ID の近傍候補）12 ms、ほかは 2 ms 以下。
通信を含めた実測は `search_passages` 80 ms・`verify_quote` 21 ms・`list_papers` 5 ms（どちらも [docs/rules/LIMITS.md](docs/rules/LIMITS.md) に記録）。

### 規則の版

`SCHEMA-1.0.0`・`JSON-1.0.0`・`NORM-1.2.0`・`SEARCH-1.1.0`・`CAND-1.0.0`・`NEAR-1.0.0`・`GUIDE-1.0.0`・`LIMITS-3.1.0`・
`LINES-1.0.0`・`LANG-1.0.0`・`SECTION-1.0.0`・`T4MAP-1.0.0`・`BUNDLE-1.0.0`・`TERMS-0.1.1`（30項目）・
`PATTERNS-0.2.1`（50件）＋`PATTERNS-MATCH-2.0.0`・`PROMPTS-0.2.2`（8件）。本文は [docs/rules/](docs/rules/)。

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
`MEKIKI_READER_PORT`（1024〜65535・既定 7860。塞がっているときは `起動しない：ポート … で待ち受けられない` と出て終了する。spaces モードでは 7860 に固定で、別の値があれば起動しない）。
起動すると次の9行が出る。

```
* Running on local URL:  http://127.0.0.1:7860
* To create a public link, set `share=True` in `launch()`.

🔨 Launching MCP server:
* Streamable HTTP URL: http://127.0.0.1:7860/gradio_api/mcp/
corpus 3.5.0 (6748061)・bundle 40a09c5ba422…
tools 7・resources 12・prompts 8（PROMPTS-0.2.2）
消した環境変数：なし
モード local・待ち受け 127.0.0.1:7860・許可 Host：127.0.0.1・localhost・::1・[::1]
```

最後の4行がこのサーバ自身の表示で、検収記録にはこの4行をそのまま写す（消した環境変数は名前だけで、値は出さない）。

待ち受けは `127.0.0.1` だけで、変えられるのは配置モード（下）だけ。`GRADIO_*` は読み込み前に消す。
データ根は `data/` に固定で、環境変数でも引数でも変えられない。不要な環境変数（API キーなど）は子プロセスに渡さないこと。

### 配置モード（local と spaces）

環境変数 `MEKIKI_READER_MODE` は `local`（既定）か `spaces` のどちらか（それ以外なら起動しない）。
`spaces` は Hugging Face の Docker Space で動かすためのもので、変わるのは次の四つだけ。

| 項目 | local | spaces |
|---|---|---|
| 待ち受け | `127.0.0.1`（ポートは `MEKIKI_READER_PORT`・既定 7860） | `0.0.0.0:7860`（ポートは固定。`MEKIKI_READER_PORT` に 7860 以外があれば起動しない） |
| 許可する `Host` | `127.0.0.1`・`localhost`・`::1` | 起動時に読んだ `SPACE_HOST`（Space の公開ホスト名。カンマ区切りは各値）と `localhost`・`127.0.0.1`。`SPACE_HOST` が無ければ起動しない |
| `/` の `Host` | 検査する | 許可していない `Host` にも 200 で答える（Space の健康検査のため。`GET`・`HEAD` だけ）。そのときは Gradio の画面ではなく、要求の中身を写さない固定の短い HTML を返す |
| `/` の中身 | Gradio の HTML | 外部の許可 Host（`SPACE_HOST`）宛ての `GET`・`HEAD /` には**案内ページ**（自前の静的 HTML。JS・外部資産なし・英日併記。MCP の URL は起動時の `SPACE_HOST` から作る）。loopback（`localhost`・`127.0.0.1`。内部クライアントと起動時の確認）には従来どおり Gradio の HTML |

どちらのモードでも、Spaces が入れる変数のうち Gradio と依存の動きを変えるもの（`SYSTEM`・`SPACE_ID`・`SPACE_AUTHOR_NAME`・
`SPACE_REPO_NAME`・`SPACES_ZERO_GPU`・`OAUTH_*`・`HF_TOKEN`・`WEB_CONCURRENCY`・`FORWARDED_ALLOW_IPS`）は、`SPACE_HOST` を読んだ後に
Gradio を読み込む前に消す。そのため Space の上でも Gradio はローカルと同じ分岐で動く（Spaces 用の監視スレッド・PWA・
ツール名の接頭辞・`spaces` パッケージによる関数の包み直しは使わない）。`pwa=False` は明示している。Space に Secret は置かない。

### Docker（Hugging Face の Docker Space）

`Dockerfile` は Space 用。基底は `python:3.13.15-slim-trixie` をダイジェストで固定し（2026-09-19 に Docker Hub で確認）、
依存は `pip install --require-hashes --only-binary=:all: -r requirements.txt`（ソースからの組み立てをしない）で入れる。
`PYTHONUNBUFFERED=1`・`MEKIKI_READER_MODE=spaces`・`EXPOSE 7860`、実行は ID 1000 の利用者（コードと `data/` は root の持ち物で読むだけ）。

施工側の確認（2026-09-19）：この機械には Docker が無いので、**イメージの組み立てと起動は未確認**（Docker を入れるのはローカル環境の
変更で、著者の判断）。代わりに、`requirements.txt` の全項目が Linux（x86_64・CPython 3.13）の wheel としてハッシュつきで取得できる
ことを `pip download --require-hashes --only-binary=:all: --platform manylinux…` で確かめた（63項目。Windows か emscripten でだけ入る3項目〔colorama・pywin32・tzdata〕を除く全部）。
`spaces` モードの設定（待ち受け・許可 Host・変数の除去・`pwa`・接頭辞なし）は試験で確かめている（試験では手元の網に出さないため
待ち受けだけ loopback にする）。実際の `0.0.0.0:7860` の待ち受けは Space の上で確かめる（SPEC §7 S04）。

### Claude Code

リポジトリ直下に `.mcp.json` を置いてある（`"type": "http"`）。このリポジトリを開いて作業するときは、
接続先として出てくるので許可すればよい（許可は利用者が行う）。

リポジトリの外から使いたいときは CLI で登録する。こちらは `.mcp.json` ではなく利用者ごとの設定に入る。

```bash
claude mcp add --transport http mekiki-reader http://127.0.0.1:7860/gradio_api/mcp/
```

ポートを変えるときは `MEKIKI_READER_PORT` と `.mcp.json`（または上の登録）の両方を直す。
URL の末尾スラッシュは有無どちらでも可（`/gradio_api/mcp` も転送なしで同じ本体として扱う）。

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
ツール7件・resources 12件・**prompts 6件**（英語版を載せた後に取り直した）が見え、`list_papers` は `ok`、
`four_modes_en` の文面も届いた。Claude Desktop 本体での確認は利用者が行い、`docs/acceptance/` に記録する。

### 公開版（Space）への接続

Space の MCP の URL は `https://<owner>-<space>.hf.space/gradio_api/mcp/`（`<owner>`・`<space>` は Space の持ち主と名前。
英数字以外はハイフンになる）。この Space の URL は `https://kenngotm-mekiki-reader.hf.space/gradio_api/mcp/`。末尾スラッシュの有無どちらでも可（`…/gradio_api/mcp` も転送なしで同じ本体に届く。Claude の Custom Connector は末尾の `/` を落として送る）。遠隔の HTTPS なので `mcp-remote` は要らない。Space が公開（public）のときは、どのクライアントでも
認証は「なし」で登録する。ツール名に接頭辞は付かない（`list_papers` など、ローカルと同じ名前）。

Space が非公開（private）の間は、Hugging Face が要求ごとに持ち主の認証を求める。Claude Code なら持ち主のアクセストークンを
要求のヘッダで送れる（`claude mcp add --transport http --header "Authorization: Bearer <HF のトークン>" mekiki-reader <URL>`。
トークンは Space には置かない）。任意のヘッダを送れないクライアント（Claude の Custom Connector・ChatGPT）は非公開の間はつながらない見込みだったので、
これらと Grok での確認（SPEC §7 P03）は公開の後に行った。

対応クライアントは次の四系統（2026-09-19 に公開版で実測。どれも認証なしで登録し、`list_papers` が `ok`・`bundle_hash` 一致。
記録は [docs/acceptance/2026-09-19-space-private.md](docs/acceptance/2026-09-19-space-private.md) §9・§10）。画面の名前は執筆時点のもの。

| 系統 | 登録の仕方（実測どおり） |
|---|---|
| Claude Code | `claude mcp add --transport http mekiki-reader https://kenngotm-mekiki-reader.hf.space/gradio_api/mcp/`（公開後はヘッダ不要） |
| Claude（Web／Desktop） | Custom Connector に上の URL を登録（認証なし）。実測は Web で、サインインなしでつながった |
| ChatGPT | **Web** で Developer mode →Plugins →MCP URL を登録 →Personal plugin をインストール。Web で入れればデスクトップ版のチャットにも出る（デスクトップ版の設定にある「MCP サーバー」は Codex 系統で、通常のチャットには出ない） |
| Grok | `grok.com/connectors` →新しいコネクタ →Custom・認証なし。チャットでは `@Mekiki Reader` で呼ぶ |

Gemini（個人向け）は Spark（ベータ）のアプリ連携→カスタムアプリで MCP を登録でき、七ツールが操作一覧に出る。`list_papers` ok（2026-09-19）。`bundle_hash` は未照合のまま。通常チャットでは未確認。

Hugging Face の MCP バッジと `hf.co/mcp` 経由の呼び出しは Hugging Face 側の機能で、このサーバは関知しない（検収の対象外）。
各クライアントでの確認は `docs/acceptance/` に記録する（SPEC §7 P02・P03）。

### 遮断している経路（Gradio が UI 無しでも登録するもの）

| 経路 | 応答 |
|---|---|
| `…file=`・`…proxy=`（外部 URL の取得・プロキシ） | 403 |
| `/gradio_api/upload` | 403 |
| `/gradio_api/run-history/*` | 403 |
| `/vibe*`（外部 LLM・書き込み） | 403 |
| `/gradio_api/dev/reload` | 403 |
| `/gradio_api/monitoring`・`/profiling` | 403 |
| `/gradio_api/component_server` | 403 |
| `/gradio_api/reset`・`/cancel` | 403 |
| `/gradio_api/login`・`/logout` | 403 |
| `/gradio_api/deep_link`・`/process_recording` | 403 |
| `/gradio_api/mcp/sse`・`/gradio_api/mcp/messages/`（上流が MCP 本体と同じ下に置く旧 SSE の予備経路。閉じても Streamable HTTP の三機能・SDK 検収・`mcp-remote --transport http-only` が動くことを実測して閉じた）と、上流の Streamable HTTP の別名 `/gradio_api/mcp/http`（末尾 `/` 付きも。許可を前方一致から完全一致に改めたので一緒に閉じた） | 404 |
| 上の一覧にも下の許可にも無い経路（`/config`・`/gradio_api/call/*`・`/queue/status`・`/openapi.json`・`/assets/*`・`/static/*`・`/theme.css`・`/manifest.json` など） | 404 |

通しているのは次の経路だけ（`/gradio_api/mcp/schema` を除き、どれも実測で要ると分かったもの。`/config` は要らないことを確かめて塞いだ）。
一覧は `app.py` の `ALLOWED_EXACT`・`ALLOWED_PREFIXES` と一致させてあり、試験が固定している（2026-09-19 時点で次の9経路と heartbeat の前方一致）。

| 経路 | 通す理由 |
|---|---|
| `/` | Gradio が起動時に到達を確かめる（`HEAD /`。塞ぐと起動しない）。また自己呼び出しの内部クライアントは、`/config` が 404 のとき `GET /` の HTML に埋め込まれた設定（`window.gradio_config`）を読む（塞ぐと `resources/read`・`prompts/get` が失敗する）。つまり**設定は `/` から出ている**：Gradio の画面と設定を返すのは loopback 宛てだけ。spaces では、外部の許可 Host（`SPACE_HOST`）宛ての `GET`・`HEAD /` に設定を含まない案内ページを、許可していない Host 宛てには固定の短い HTML（健康検査用）を返す（2026-09-19 まで、許可した Host には Gradio の画面と設定が返っていた）。静的資産は塞いであるので画面は組み上がらない |
| `/gradio_api/startup-events` | 起動時の確認（塞ぐと起動しない） |
| `/gradio_api/info`（末尾 `/` 付きも） | `resources/read`・`prompts/get` の自己呼び出しが読む（塞ぐと McpError） |
| `/gradio_api/queue/join` | 同じく自己呼び出しの実行（受付8・待機64） |
| `/gradio_api/queue/data` | 同じく自己呼び出しの結果の受け取り |
| `/gradio_api/heartbeat/*` | 自己呼び出しの内部クライアントが使う。上流のクライアントは断られると間を置かずに再試行するので、塞がずに同時数で絞る（上流との互換のため） |
| `/gradio_api/mcp/`（末尾 `/` なしも） | MCP 本体（Streamable HTTP）。`/gradio_api/mcp`（末尾 `/` なし）も転送せず、サーバの中で `/gradio_api/mcp/` と同じ本体として扱う（許可一覧は両方を完全一致。2026-09-19 まで上流の 307 で転送していたが、プロキシの裏では `Location` が `http://` になり、末尾の `/` を落とす Custom Connector がつながらなかった） |
| `/gradio_api/mcp/schema` | ツールの JSON スキーマ（上流が MCP 本体と同じ下に置く）。三機能には要らないが、著者の指示で開けてある |

つながったままになる GET の流れ（塞げないもの）は、種類ごとに同時数を絞る。超えた分は通信層で 503。

| 種類 | 同時数 | 実測（2026-09-19） |
|---|---|---|
| `/gradio_api/heartbeat/*` | 8 | 内部クライアントが1本（resources/read 同時80本でも同じ） |
| `/gradio_api/queue/data` | 8 | 内部クライアントが最大1本 |
| `GET /gradio_api/mcp/`（Streamable HTTP の待ち受け） | 32 | mcp SDK（Python）は0本。`mcp-remote@0.14.2` は1クライアントあたり最大4本（落ち着くと2本）。断られても呼び出しは続けられる（上限0でも40回の呼び出しがすべて通った） |

内部クライアント（`resources/read`・`prompts/get` の自己呼び出し）の分も数えるが、断らない（上流のクライアントは断られると
間を置かずに再試行するため）。内部かどうかは要求が名乗るセッションで見分ける。内部クライアントは起動の直後に一つだけ作り、
それと起動後の確認が済むまで、外からの MCP は HTTP 503（`starting`）で断る（上流の遅延作成は、同時の初回呼び出しで重複しうる
ため。上流との互換の措置）。起動直後の同時100本の初回呼び出しがすべて通り、内部クライアントは一つ（`tests/test_safety.py`）。

そのほかの要求は、種類ごとの受付枠で受ける。枠は本文を読む前に取り、応答を送り終えるまで持つ（受付から60秒の期限つき。
受け取りを止めた相手は期限で接続ごと切る）。枠も順番待ちも埋まっていれば HTTP 503（`busy`）で、断った接続は閉じる。
接続の数とヘッダを送り切らない接続には、こちらでは上限を置いていない（HTTP の層の既定に従う。`docs/rules/LIMITS.md`）。

| 種類 | 同時に受け付ける数 | 順番待ち（20秒まで） |
|---|---|---|
| MCP の要求（`/gradio_api/mcp/` への POST など） | 32 | 96 |
| 自己呼び出しの登録（`/gradio_api/queue/join`） | 8 | 64 |
| そのほか（`/`・`/gradio_api/info`・`/gradio_api/mcp/schema` など） | 16 | 32 |

### 接続時に知っておくこと

- **未知の prompt 名**は雛形を返さず、MCP のエラー（`McpError: 'data'`）として返る。引数を付けて呼んだときは、上流 Gradio の `Parameter … is not a valid key-word argument` という英文が返る。要求された名前は上流の実装からサーバ側の関数に渡らないため、エラー文に名前を入れられない。登録してある名前は `read_with_guards`・`four_modes`・`answer_format`・`mekiki_start` と、その英語版 `…_en` の八つだけ。
- Hugging Face Spaces に置いても、ツール名・prompt 名に接頭辞は付かない（spaces モードは `SYSTEM`・`SPACE_ID` を読み込み前に消すので、ローカルと同じ `list_papers` などになる）。
- `http://127.0.0.1:7860/` をブラウザで開くと Gradio 標準のフロント HTML が返る（UI は無く、静的資産は遮断してあるので画面は組み上がらない）。
- Claude Code の Code タブでは、**prompts の一覧は一度サーバに触れてから現れる**（最初のツール呼び出しの前は空に見える）。
- 原文の強調記号（`**…**`・`*…*`・`_…_`）を外して引用しても、NORM-1.1.0 からは `normalized` で一致する（それより前の版では `quote_not_found` になっていた。検収で観察）。
- 旧 SSE の経路（`/gradio_api/mcp/sse`・`/gradio_api/mcp/messages/`）と別名 `/gradio_api/mcp/http` は閉じてある。接続先は `/gradio_api/mcp/`（末尾 `/` なしも可。Streamable HTTP）だけで、`mcp-remote` は `--transport http-only` で使う。
- Claude（Web）・ChatGPT・Grok からの接続は公開版（Space）で確かめた（2026-09-19・上の対応表）。ローカルの loopback には外から届かない。
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

## 8. 開示

> この節は施工側が下書きし、文面を著者が承認・署名した（2026-09-19）。

| 項目 | 記入欄 |
|---|---|
| 承認（この節の文面） | 承認者：Kengo Tomita／承認日：2026-09-19 |
| 署名 | Kengo Tomita（2026-09-19） |
| 公開の版 | 対象コミット：Space `KennGoTm/mekiki-reader` の `b8c4b38`（mekiki-mcp `main` `d6ae3ed` 相当） |

- **制作工程と使用モデル**：方針（`SPEC.md`。Claude〔claude.ai・Fable 5.1〕）→方針の独立検証（ChatGPT〔Pro〕）→施工（Claude Code〔Opus 5〕）→独立検査（Codex〔GPT-6 Astra〕。指摘と差分案のみ）→最終検査（Claude〔claude.ai・Fable 5.1〕）→接続確認と公開判断（著者）。生成 AI を使って作った。
- **参照した型**：Paper2Agent（Miao et al., Nature 2026）から借りたのは型（資源・プロンプト・ツール・検証テスト・Spaces での公開）であって工程ではない。読解の対象は T1〜T5（題名・版・DOI は `data/CITATION.md`）。
- **費用と休止**：ローカルで動かす分には追加の API 料金・ホスティング料金は要らない。公開（Spaces）は HF PRO（月9ドル）・CPU basic。再起動からの復帰は17秒（Space 画面の Restarting→Running を目視計測・2026-09-19）。休止からの復帰は未実測。
- **利用者入力の送信先と保存方針**：`verify_quote` と `check_compressions` の入力には未公開の情報が入りうる。実測では、起動から全ツール・全 resource・全 prompt の呼び出しまで loopback 以外への接続は0件。**配信中**は書き込みで開いたファイルも0件で、`data/` には一切触れない。起動の途中では、依存ライブラリ（filelock）が一時ディレクトリの中に `probe-source`・`probe-link` を作って消し、Gradio が一時領域に書く（どちらも利用者の入力とは関係がない）。サーバは入力をファイルに保存しない方針で、実測した範囲（外への接続と、書き込みで開いたファイル）では保存は確認されなかった。**標準出力・標準エラー**に出るのは、起動時の表示・遮断の記録（状態コードと理由だけ。経路は出さない）・例外の型と場所（ファイル名と行。例外の文は出さない）・ログの水準と名前と出した場所（文は出さない。文に値が埋め込まれることがあるため）だけにしてある。実測（2026-09-19・ローカル）では、正常・不正・例外の各要求（ツールの引数・未知のツール名・未知のメソッドと通知・応答やエラーの形の要求・URL でない URI・壊れた `_meta`・JSON でない本文・壊れた JSON・queue の入力検証のエラー・遮断した経路・ヘッダ・問い合わせ・待ち受け直後の例外）に入れた目印の文字列は、標準出力・標準エラーのどこにも出なかった（試した範囲。`tests/test_safety.py::test_s01_inputs_do_not_reach_the_logs`・`test_s01_logs_are_redacted_from_the_start`）。対策の前は、queue の入力検証のエラー・未知のツール名・JSON-RPC の中身がログに出ていた。**Spaces 側のログ**は、実行中の標準出力・標準エラーがそのまま出るもので、中身は上と同じ（2026-09-19 に private の Space で、目印の文字列を `verify_quote` に送り、Container ログに値も呼び出しの痕跡も出ないことを目視で確かめた。SPEC §7 S04）。閲覧できるのは Space に書き込み権限のある者で、保持は Space の再起動までで期間は保証されない。`hf.co/mcp` 経由の呼び出しは Hugging Face 側の機能で、このサーバは関知しない。
- **外向きの資料取得**：起動後に取得する資料は同梱データだけ。
- **既知の制約**：
  1. T4 の英訳は ChatGPT で作成された派生の言語版で、著者レビューの認証はない。英訳由来の結果には作成経緯（`preparation`・`authority`）を必ず添える。
  2. 英訳の manifest の `source.corpusVersion`（英訳が底本にした T4 の収録版）は `3.2.1` で、manifest 自身の `corpusVersion`（3.5.0）とは別。記録どおり `payload.source_corpus_version` に載せ、版どうしの比較はしない。
  3. 同梱物は `data/LICENSE`（CC BY 4.0）に従う。論文本文中に別の表記（T1 の figshare 寄託データについての `CC BY-NC 4.0`）があっても、同梱物には及ばない。原文は改変しない。
  4. 日本語の問いは英語の論文に当たりにくい（語句の照合であるため）。該当ゼロは記述が無いことを意味しない。
  5. 未知の prompt 名は MCP のエラーとして返る（上流の実装の挙動。本文は §5 参照）。Space でもツール名に接頭辞は付かない（`SYSTEM` を消して、Gradio をローカルと同じ分岐で動かすため）。
  6. `/` には、loopback 宛てでは Gradio 標準のフロント HTML が返る（spaces の外部の許可 Host 宛てには案内ページ）。`resources/read` と `prompts/get` はサーバが自分自身に出す HTTP 要求で実行されるため、その経路（`/gradio_api/queue/join`・`/gradio_api/queue/data`）だけは通してある。外から同じ経路を叩くこともできるので、**受付8件・順番待ち64件まで**で受ける（本文を読む前に取る枠。超えると HTTP 503）。回収されない結果は、できてから120秒・同じセッションで64件・4 MiB（UTF-8 の JSON で数える）を超えた分を古いものから捨てる（取りに来ているセッションは期限では捨てない。内部クライアントのセッションには手を付けない）。実行されるのは登録済みの七ツール・resources・prompts だけで、どれも同じ実行枠（同時4）を使う。`/gradio_api/call/*` は塞いである（実測で、自己呼び出しには要らないことを確かめた）。
  7. 起動時に `HF_HUB_DISABLE_TELEMETRY=1`・`HF_HUB_DISABLE_IMPLICIT_TOKEN=1`・`HF_HUB_OFFLINE=1`・`HF_TOKEN_PATH=/dev/null` を設定している（依存ライブラリの利用状況送信を止め、利用者のトークンファイルを開かせないため）。
  8. **CORS の許可ヘッダ**：サーバは許可ヘッダを返さないが、Spaces のエッジが付与する（2026-09-19 実測）。サーバは利用者の状態を持たず公開データのみ。
  9. 同梱データの照合は事故の検出までで、改竄への耐性は主張しない。
  10. **上流の差し替え**：Gradio 6.27.0・uvicorn 0.53.0 との互換と、守則を満たすために、上流の次の部分を差し替えている（どれも起動後の確認で差し替えが効いていることを確かめ、外れていれば起動しない）。①CORS の中間層（許可ヘッダを返さない）／②待ち行列の例外の印字（型と場所だけ）／③ログの出口（水準・名前・出した場所だけ。uvicorn がログを設定した直後にも差し替える）／④待ち行列のセッションの表（追い出すときに関連する記録も消す・内部と処理中と回収中は追い出さない）／⑤結果の送り出し（できた時刻を記録する）／⑥uvicorn の要求ごとの処理（送信期限を過ぎた接続をすぐ切る手段をガードへ渡す）／⑦MCP の `tools/list` の処理（七ツールに注釈 `readOnlyHint=true`・`destructiveHint=false`・`idempotentHint=true`・`openWorldHint=false` を足す。Gradio 6.27.0 には注釈を渡す経路が無い。注釈はクライアントへの手がかりで、保証ではない）。あわせて、内部クライアントは上流の遅延作成を使わず起動の直後に一つ作る。上流を別の版にするときは、この一覧をすべて見直す。
  11. **転送は返さない**：サーバは 3xx の転送を一切返さない（プロキシの裏では上流が組み立てる `Location` が `http://` になり、HTTPS の接続先に戻れないため）。`/gradio_api/mcp` は転送せず `/gradio_api/mcp/` と同じ本体として扱い、上流がほかに返す転送（末尾 `/` の付け外し。実測では `/gradio_api/heartbeat/<id>/`）は 404 に置き換える（`Location` を出さない）。
