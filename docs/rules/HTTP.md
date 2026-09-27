# HTTP — 素の HTTP の口（経路・引数・応答の契約）

| 項目 | 値 |
|---|---|
| 規則ID・版 | HTTP-1.1.0（2026-09-27・SPEC v2.5.1。1.0.0 に verify の `language` を足した〔MINOR〕。あわせて、崩れた `%` を 400 にし〔1.0.0 はそのまま残していた〕、生の非 ASCII のバイト列が HTTP の層で断られる実測を記した）。HTTP-1.0.0（2026-09-27・SPEC v2.5 §2.12 の施工） |
| 状態 | 確定（経路・応答・上限・`HEAD`／`OPTIONS` の 405・パス形の値の 404・未知／重複引数の 400・304 は SPEC v2.5.1 が採用）。Markdown の形と ETag の算式の細部は施工判断（提案） |
| 実装 | `mekiki_reader/http_api.py`（経路の表・引数の読み取り・Markdown・ETag。通信に触れない）と `app.py` の Guard（受付枠・本文・送信・ツールの呼び出し） |
| 試験 | `tests/test_http.py`（H01〜H04。local と spaces の両モード）・`tests/test_safety.py::test_s01_allowlist_is_pinned` |

MCP の置き換えではなく追加。七ツールは MCP に登録したのと同じ入口の関数（`app.py` の `list_papers` など）を
そのまま呼ぶので、同じ入力なら**MCP の応答（`text`）と同じ JSON 文字列**を返す。サーバ内に LLM を置かない・
判断しない・データを書き換えない、は MCP と同じ。

## 1. 経路（九本。完全一致・型で固定）

| # | メソッド | 経路 | ツール | 引数 | 置き場 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/` | （経路の一覧） | なし | — |
| 2 | GET | `/api/v1/papers` | `list_papers` | なし | — |
| 3 | GET | `/api/v1/papers/{paper_id}/sections/{anchor}` | `get_section` | `language`（`en` は T4 のみ） | 経路＋問い合わせ |
| 4 | GET | `/api/v1/search` | `search_passages` | `q`・`paper_id`・`k` | 問い合わせ |
| 5 | GET | `/api/v1/claims` | `get_claim_record` | `claim_id` か `query` | 問い合わせ |
| 6 | GET | `/api/v1/guide` | `get_reading_guide` | `part` | 問い合わせ |
| 7 | GET | `/api/v1/verify` | `verify_quote` | `text`・`paper_id`・`language`（`en` は T4 のみ・1.1.0） | 問い合わせ |
| 8 | POST | `/api/v1/verify` | `verify_quote` | `text`・`paper_id`・`language`（同） | 本文の JSON |
| 9 | POST | `/api/v1/check` | `check_compressions` | `text` | 本文の JSON（**POST のみ**） |

- 経路は完全一致。末尾の `/` の付け外し（`/api/v1`・`/api/v1/papers/`）・大文字・余分な区切りは別の経路で、404。**転送（3xx）は返さない**。
- 経路が当たってメソッドが違えば 405（`Allow` に受けるメソッド）。`HEAD`・`OPTIONS` も 405（SPEC の九経路に無いため。ブラウザの事前確認も通らない）。
- `{paper_id}`・`{anchor}` は登録済みの値だけを通す：パスや URL の形（`_classify_id` が invalid。`..`・`\`・`:`・制御文字など）は 404（素の文）。それ以外の未登録の値はツールを呼び、`unknown_id`（実在の候補つき）を 404 で返す。`%2F` は経路の区切りになるので、値に `/` は入らない。
- `check` を POST に限るのは、入力が利用者自身の文章で、URL に載せるとエッジ（Hugging Face の前段）のログに残りうるため。`verify` の GET は、引用が公開の原文なので許す（照合結果を URL で共有できる）。ただし引用文は URL に載り、エッジのログに残りうる（サーバ自身は記録しない）。URL の長さには上限があるので、短い引用は GET、長い引用（日本語で数百字以上）は POST を案内する。

## 2. 引数の読み方

| 規則 | 内容 |
|---|---|
| 意味 | MCP の入口と同じ：空文字は省略と同じ（`paper_id=` は範囲の指定なし）。省略時の既定も同じ（`k`＝5・`part`＝`all`・`language`＝原文）。`verify` の `language`（1.1.0）も MCP と同じ検証：`en` は T4 英訳（`paper_id` 省略時も英訳だけが範囲）、T1〜T3・T5 に `en`、存在しない値は `invalid_input` |
| 検査 | 値の中身（長さ・形・範囲・孤立サロゲート）は**ツールと同じ関数**が検査し、`invalid_input` を返す。HTTP の層が見るのは形だけ（下の行） |
| 問い合わせ（GET） | `&` で区切り、`=` の前が名前。`+` は空白、`%XX` はそのバイト（リテラルの `+` は `%2B`）。`%` の後に16進2桁が続かない列（`%`・`%G1`・末尾の `%`）は 400（1.1.0。`urllib.parse` はそのまま残すが、ここでは誤りにする）。復号した列を UTF-8 として厳格に読み、UTF-8 でない列（`%FF`・途中で切れた多バイト・`%ED%A0%80` のサロゲート・過長符号）は 400。空の項目（`&&`）は飛ばす。項目は8つまで。名前は経路の引数だけ・重複は不可 |
| 生のバイト列 | 百分率符号化していない非 ASCII のバイトを要求行に入れると、UTF-8 でも HTTP の層（uvicorn の h11）が先に 400（素の文）で断る（実測・2026-09-27）。百分率符号化して送る（curl なら `-G --data-urlencode`） |
| 経路の中の符号化 | 経路（`{paper_id}`・`{anchor}`）の `%XX` は HTTP の層（uvicorn）が復号する。崩れた符号化・UTF-8 でない列は 404 か 400 で、500 にはならない（H03 で固定） |
| 自前の復号の理由 | `mekiki_reader` は通信系の module を import しない静的検査（`test_s03_reader_has_no_network_imports`）の下にあり、`urllib` は `urllib.request` を含むパッケージなので名前ごと禁じている。復号は `http_api._unquote`（正規表現で `%XX` を置き換えるだけ）で、規則はこの表 |
| `k` | 5桁以内の十進数字だけを整数にする。ほかの形（`-1`・`abc`・長い数字）はそのままツールへ渡し、ツールが `invalid_input` にする |
| 本文（POST） | UTF-8 の JSON オブジェクト。名前は経路の引数だけ・重複は不可・値は文字列か `null`（`null` は省略と同じ）。`Content-Type` は見ない（`curl -d` の既定でも通る）。POST に問い合わせを付けたら 400（引数は本文だけ） |
| 形の誤り | `invalid_input` の外枠（ツールと同じ形）を 400 で返す。`limitations` は `INPUT: …` と `RULES: HTTP-1.1.0` |

## 3. 応答

| 項目 | 内容 |
|---|---|
| 既定の表現 | JSON。本文は MCP のツールの応答と同じ文字列（JSON-1.0.0 の直列化・同じ schema・`status`・`results`・`candidates`・`limitations`・`corpus_version`・`source_commit`・`bundle_hash`・`schema_version`）。`Content-Type: application/json; charset=utf-8` |
| 状態コード | `invalid_input` → 400、`unknown_id` → 404、ほか（`ok`・`quote_not_found`・`no_lexical_match`・`ledger_not_available`）→ 200。本文は同じ JSON |
| 表現の選択 | `Accept` のどれかの項目が `text/markdown`（大小は区別しない・`q` が 0 でない）なら Markdown、ほか（省略・`*/*`・`application/json` など）は JSON。`Vary: Accept` |
| 経路の一覧（`/api/v1/`） | `api_version`・`schema_version`・`corpus_version`・`source_commit`・`bundle_hash`・`accept`・`routes`（上の九本。メソッド・経路・ツール・引数・置き場）。JSON-1.0.0 で直列化 |
| 通信層の誤り | 素の文（`text/plain`）：404 `not found`・405 `method not allowed`・413・408・503 `busy`／`request timeout`・400（Host・長さの表明）。`status` には混ぜない |

### Markdown（`Accept: text/markdown`）

- **節とガイド**（`get_section`・`get_reading_guide` の `ok`）：結果ごとに、先頭に出典行、空行、`payload.text` を**行を変えずに**（末尾の改行だけ除く）。結果が複数（英訳の節と訳注）なら `---` で区切る。本文の無い結果（英訳側に位置の無い unit）は括弧書きで記載を示す。ガイドは続けて `templates`（雛形）の本文を行のまま。
- **表**（検索・照合・検出・台帳・論文一覧と、`ok` 以外のすべて）：先頭に外枠の出典行、続けて結果の表。列は `#`・`paper_id`・`paper_version`・`section_anchor`・`lines`・`path`・`text`。`text` は `pattern_id`・`id`・`status`・`match`・`matched`（語形）と、本文系の値（`matched_text`・`excerpt`・`source_quote`・`source_excerpt`・`title`・`text`・`description` の最初のもの）。表のセルに限り、改行を空白に、`|` を `\|` にする。候補は別の表（`candidates:`）。
- **最後**に `status: …` と `limitations:`（箇条書き・外枠の順のまま）。
- 出典行の形（結果）：`Source: paper_id=… · paper_version=… · section_anchor=… · lines=<開始>-<終了> · path=… · corpus_version=… · source_commit=…`（行の無い結果は `lines` に JSON 位置。値の無い欄は `-`）。外枠：`Source: tool=… · status=… · corpus_version=… · source_commit=… · bundle_hash=…`。

## 4. cache・ETag

| 項目 | 内容 |
|---|---|
| GET の 200 | `Cache-Control: public, max-age=3600` と `ETag`（強い ETag） |
| ETag | `sha256(JSON[規則の版, bundle_hash, 経路の名前, ツールに渡す引数（既定を埋めた後）, 表現])` の先頭32桁を `"` で囲む。**表現（JSON／Markdown）ごとに別の ETag**で、応答には必ず `Vary: Accept`（304・400・404 も）。同じ URL でも `Accept` が違えば ETag が違い、別の表現の ETag では 304 にならない。同じ意味の要求（`k` の省略と `k=5`・空の `paper_id` と省略）は同じ ETag |
| 条件付き GET | `If-None-Match` に同じ ETag（`W/` を外した弱い比較・`*` を含む）があれば 304（本文なし・同じ `ETag`・`Cache-Control`）。応答を作ってから比べる（400・404 になる要求には 304 を返さない）。304 は転送ではない |
| POST・400・404 | `Cache-Control: no-store`・ETag なし |
| そのほか | `X-Content-Type-Options: nosniff`。CORS の許可ヘッダは返さない（`Origin` 付きでも。Guard の既存の扱い） |

## 5. 上限と遮断（既存の Guard のまま）

- 受付枠は「その他」（同時16・順番待ち32。本文を読む前に取り、応答を送り終えるまで持つ）。送信期限60秒。
- 本文は実際に届いたバイト数で 64 KiB（超過 413）、受信ループ全体で10秒（超過 408）。`Transfer-Encoding` と `Content-Length` の併記は 400。
- 実行枠（同時4）は MCP と共有。埋まっていれば 503 `busy`（ツールの呼び出しは上流と同じ worker thread の枠で動かす）。
- Host の検査・`Origin` の扱い・許可外 Host の応答は従来どおり（spaces の `/` 以外は許可外 Host に 400）。
- 引数の値・経路の値は標準出力・標準エラーに出さない（遮断の記録は状態コードと理由だけ）。
- URL の長さは HTTP の層（uvicorn・h11）とエッジの上限に従う。ローカルでは日本語2,000字（百分率符号化で約18 KB）の `verify` の GET が通った（2026-09-27）が、エッジの上限は測っていない。短い引用は GET、長い引用（日本語で数百字以上）は POST を案内する。
