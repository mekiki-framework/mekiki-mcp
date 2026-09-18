# Codex 独立検査①（対象コミット `6b8dcaa`）

| 項目 | 値 |
|---|---|
| 検査 | Codex（独立検査。指摘と差分案のみ。SPEC §10） |
| 対象 | コミット `6b8dcaa`（施工段階3の merge 時点）・corpus v3.5.0・Gradio 6.27.0・Python 3.13.15 |
| 受領 | 2026-09-18（著者経由） |
| 反映 | ブランチ `codex1` → `f88effc`・`4548eac`。**Codex② の検算では ④・⑥ が一部残存、⑤ に退行**と判定され、`codex3` で追って直した（下の「Codex② の検算」） |
| 試験 | `.venv/bin/python -m pytest -q` → 392 passed（反映後の自己点検で2件足した） |

> **この記録について**：**報告の本文は [codex-1-report.md](codex-1-report.md)**（著者が配置。ローカルの絶対パスは
> 施工側でリポジトリ相対に置換した。本文には手を入れていない）。本書はそれに対する施工側の反映記録で、
> 指摘ごとの採否・直した箇所・確かめ方をまとめたものである。参照はすべてリポジトリ相対で書く。
> 本文の番号（P1〜P10）と本書の見出し（P1-2〜P3-10）は、著者が転記した並びに合わせてある。

## 指摘と反映

**Codex② による検算の結果（対象 `41fa3f9`）**：①②③⑦⑧⑨ は修正済み、④（queue の待機・未回収結果）と
⑥（S03 の書き換え先・停止処理・自己接続判定）は**一部残存**、⑤（キャッシュ）は制限は入ったが**並行での退行あり**、
⑩ は SEARCH・PROMPTS の旧記述が**残存**。いずれも `codex3`（Codex② の反映）で直した。

### P1-1 検査対象と内容の食い違い（Codex② の表の①）

- **指摘**：指定の対象（6件の prompts・README・SPEC v2.2）とコミットの内容が違う。検索順位は確定どおりだが SPEC 未反映。
- **反映**：SPEC v2.2 は著者が改版済み、README と英語 prompts 6件は施工段階4で搭載済み。本表にこの行が無かったのを、
  Codex② の指摘を受けて足した。

### P1-2 通信層：本文の長さの表明を信じている

- **指摘**：`Content-Length` と `Transfer-Encoding` の併記を許し、表明された長さだけで 64 KiB を判定していた。
  `Content-Length` の検査が `str.isdigit()` で、全角数字などの ASCII 以外も通っていた。
- **差分案**：TE と CL の併記を拒否／`receive()` の実バイト数で 64 KiB を打ち切る／CL は ASCII 数字のみ。
- **反映**：`app.py` の Guard で、①TE と CL の併記・CL の重複・CL の非 ASCII を 400、②本文は実際に届いたバイト数で
  数えて 64 KiB 超を 413、③表明と実測の食い違いを 400 にした。読み終えた本文は後段へ一度だけ渡し、
  二度目以降は本物の `receive` に戻す（即 `http.disconnect` にすると SSE の応答が切れる。実測）。
- **試験**：`tests/test_safety.py::test_s01_framing_is_checked`・`test_s01_host_variants`・`test_s01_body_size_boundary`。

### P1-3 起動時の環境と確認が足りない

- **指摘**：プロキシの環境変数が残っていると、自分自身への loopback 接続が外へ迂回しうる。
  起動前後の確認が vibe/dev/allowed_paths に限られていた。番兵が最後に登録される保証が試験に無い。
- **差分案**：`HTTP_PROXY`・`HTTPS_PROXY`・`ALL_PROXY` と小文字形を import 前に除去し `NO_PROXY` を設定／
  起動前後の確認に bind 先・share・run_history・SSR・monitoring・queue 設定を追加／番兵の順序を試験で固定。
- **反映**：`app.py` の `PROXY_ENV_NAMES` を消してから `NO_PROXY=127.0.0.1,localhost,::1` を入れ直す。
  `verify_blocks(demo, launched=True, port=…)` が share・ssr_mode・enable_monitoring・run_history・pwa・
  mcp_server・server_name・server_port・max_threads・root_path・allowed_paths・blocked_paths・
  queue の max_size と同時実行数・`local_url` の前置きを確かめ、違えば起動しない（起動後なら停止する）。
- **試験**：`tests/_support/server_launcher.py` が `get_api_info()` の endpoint 一覧を記録し、
  `tests/test_safety.py::test_s03_no_outbound_traffic` が最後の endpoint が番兵であることを確かめる。

### P2-4 自己呼び出しの経路が外にも開いている

- **指摘**：`/gradio_api/queue/join`・`/gradio_api/call/*` は外からも叩ける。待ち行列の長さと未回収の結果に上限が無い。
  resources・prompts には実行枠が無い。
- **差分案**：queue の max_size と未回収結果数を制限／resources・prompts にも実行枠／
  `/queue/join`・`/call/*` を外部から閉じられるか実測し、閉じられなければ容量制限で受けて README に明記。
- **実測**：`/gradio_api/call/*` は**閉じられる**（塞いでも `resources/read`・`prompts/get` は通る）。
  `/gradio_api/queue/join` は**閉じられない**（塞ぐと `resources/read` が `McpError` になる）。
- **反映**：`/call/*` を許可一覧から外した。`queue(max_size=16, default_concurrency_limit=4)`。
  `/queue/join` は同時8件までを**順番待ち**で受ける（20秒を超えたときだけ 503。初版は即 503 にして退行を起こし、下の自己点検で直した）。resources・prompts も七ツールと同じ実行枠（同時4）を使う。
  README §4・§8 と `docs/rules/LIMITS.md` に明記した。

### P2-5 無制限に伸びる入れ物

- **指摘**：語形ごとの正規表現キャッシュ（`_WORD_RE_CACHE`）と遮断の記録（`GUARD_LOG`）が無制限。
- **差分案**：容量付き LRU／固定長 deque か件数集計。
- **反映**：`mekiki_reader/tools.py` の `_word_pattern()` が容量 512 の LRU。
  `app.py` の `GUARD_LOG` は `deque(maxlen=256)` にし、応答コードごとの総数を `GUARD_COUNTS` に残す。

### P2-6 S03 の監査が甘い

- **指摘**：宛先をホストだけで見ており、ポートが違う自分以外の loopback 先を見逃す。Unix ソケットを免除している。
  `open` の flags を見ていない。配信中しか記録していない。フック自体が効いていることを示していない。
- **差分案**：宛先 host:port 記録・実際の自己接続だけ免除・Unix ソケット非免除・open の flags/mode 記録・
  起動から停止まで・陽性対照。
- **反映**：`tests/_support/server_launcher.py` を差分案どおりに書き直した。陽性対照では
  `getaddrinfo("mekiki-control.invalid")` と `connect(203.0.113.1:80)` が止まること、自己接続は通ることを確かめる
  （どちらもフックが syscall の前に例外にするので、外へは一歩も出ない）。

### P2-7 表の同一性が担保されていない

- **指摘**：`terms.py`・`patterns.py` の表は、規則文書と食い違っても起動できてしまう。
- **差分案**：正準 JSON 化して SHA-256 を規則文書に記し、import 時に照合。PATTERNS は 0.1.1（49件）に上げ、
  0.1.0＝47件は撤回として記録。
- **反映**：`terms.table_sha256()`＝`790e124094aeca1ccd3cf72823e9acbd70a897057b12d357eece26486e467be0`、
  `patterns.table_sha256()`＝`92666827a79b31b55c0fa1b424f7be9e4891b97fab044d316b2622ec1a3a304b`（`match_rule` を含めた形。下の自己点検⑦）。
  どちらも import 時に定数と照合し、違えば起動しない。`docs/rules/TERMS.md`・`PATTERNS.md` に値を載せた。
  PATTERNS は 0.1.1（49件）。0.1.0（47件）は撤回（`DECISIONS.md`）。

### P2-8 孤立サロゲート

- **指摘**：JSON 経由で孤立サロゲートが入ると、応答の直列化で落ちうる。
- **差分案**：入力検証で `invalid_input`。
- **反映**：`tools.has_lone_surrogate()` を足し、ID・query・text の検証で弾く（6ツールで確認）。

### P2-9 FIFO で待ち続ける

- **指摘**：通常ファイルかどうかを `open` の後に見ているので、`data/` に FIFO があると起動が止まる。
- **差分案**：`lstat` で先に種別を見る／FIFO で待機しない。
- **反映**：`corpus._read_regular()` が `lstat` → 種別確認 → `O_NONBLOCK|O_NOFOLLOW` で open →
  `fstat` の inode/デバイス一致まで確かめる。実測：`data/llms.txt` を FIFO に差し替えると、止まらずに
  `BundleError(not_regular)` になる。

### P3-10 文書と現物の食い違い

- **指摘**：`docs/rules/README.md`・`SEARCH.md`・`TERMS.md` に旧い記述が残っている。
- **反映**：規則一覧の版・件数・表ハッシュ、TERMS の語形数（79→78）と表題の版、SCHEMA の注記、
  LIMITS の通信層の表を現物に合わせた。

## 敵対的テスト（差分案の表どおり追加）

| 種別 | 内容 | 場所 |
|---|---|---|
| T09 | 否定・内容語・所有格・記号・数値を変えた6件が一致しないこと。空白だけ増やした版は `normalized` で一致すること | `test_t09_adversarial_mutations` |
| T10 | 一致数の境界：`"agent-rela"` 20件＝ok、`"Externaliz"` 21件＝`invalid_input`＋TOTAL。長さの境界（2000／2001字・仮名漢字5/4字・英語10/9字） | `test_t10_result_limit_boundary`・`test_t10_length_boundaries` |
| T11 | 同じ語形30回（matched 20件＋総数）・全角・ゼロ幅・BOM・大文字小文字・肯定否定引用疑問・行またぎ・部分一致 | `test_t11_adversarial_forms` |
| S01 | Host の欠落・重複・IPv6（`[::1]` とポート付き）・空・紛らわしい名前／CL と TE の併記・CL の重複・全角の CL・符号つきの CL／本文 65,535・65,536・65,537 バイト | `test_s01_host_variants`・`test_s01_framing_is_checked`・`test_s01_body_size_boundary` |
| 同時実行 | `Event` で4枠を占有し、5件目と resources/prompts の枠が通信層のエラーになること。解放後に戻ること | `test_s01_concurrency_slots_are_held` |
| S03 | 宛先 host:port・自己接続だけ免除・Unix ソケット非免除・open の flags・起動から停止まで・陽性対照 | `test_s03_no_outbound_traffic` |

### 反映後の自己点検（2026-09-18・施工側）

Codex① の反映（`f88effc`）を、下位エージェント3体（通信層・監査・表と文書）＋検算1体で点検した。
**反映そのものが持ち込んだ退行が2件**見つかったので、merge の前に直した。

| # | 見つかったこと | 直し方 | 確かめ方 |
|---|---|---|---|
| 退行① | `/gradio_api/queue/join` を即 503 にしたため、**正規の `resources/read`・`prompts/get` が同時9本以上で壊れる**（上流の実装が未定義参照になり `code:0` の内部エラー文を返す）。`6b8dcaa` では24本まで通っていた | 断らずに順番待ちにした（`asyncio.Semaphore` と20秒の上限。超えたときだけ 503） | 同時 9・14・24本の `resources/read` が 24/24 `ok`、`blocked 503` は0件（実測） |
| 退行② | `scripts/build_patterns.py --write` が表だけ書き換えて `PATTERNS_TABLE_SHA256` を置き換えないため、**再生成するとリポジトリが起動不能**になる | 生成器が定数も書き換え、そのあと reload で突き合わせる。死んでいた 0.0.0 用の置換も直した | 複製で候補に語形を足して `--write` → import 成功・定数と文書が新しい値に（実測） |
| ③ | 遮断の記録に制御文字がそのまま載る（`%0a` で偽の記録行を立てられる） | `unicode_escape` で逃がして200字で切る | `GET /%0aFAKE` が一行に収まること |
| ④ | 本文を送り切らない要求で接続が残り続ける（先読みを入れたことで生じた待ち面） | 本文を読むのは MCP と自己呼び出しの経路だけにし、10秒で 408 | `POST /config` に長さだけ宣言して送らない要求が即 405（先読みに入らない） |
| ⑤ | `Content-Length` の重複・非 ASCII は実際には HTTP の層（h11）が拒んでおり、規則文書の書き方と食い違う。死んだ条件も残っていた | `LIMITS.md` を実物に合わせ、条件を削った | 生ソケットで各形を実測し、どの層が拒むかを記録 |
| ⑥ | 監査フックが子プロセス・`socket.sendmsg`・`os.rename` などを見ていない。`OPEN_MAX` に達すると黙って空振りする | `PROCESS_EVENTS`（子プロセスは遮断）・`sendmsg`・`MUTATE_EVENTS`・`socket.bind`・取りこぼし件数を追加し、S03 で検査 | `audit["process"]==[]`・リポジトリ配下の書き換え0件・`open_dropped==0`・`bind` が `127.0.0.1` |
| ⑦ | `match_rule` だけ表の正準形に入っていなかった | `table_rows()` を `asdict` にして全欄を入れた（欄を足せば必ずハッシュが変わる）。PATTERNS-0.1.1 の表ハッシュは `92666827a79b31b55c0fa1b424f7be9e4891b97fab044d316b2622ec1a3a304b` | `pytest` と生成器の reload |
| ⑧ | `docs/rules/SEARCH.md`（TERMS-0.0.0＝空）・`terms.py` の注釈・`README.md` の「prompts 3件」・検収記録が古い | 現物に合わせた。SDK の検収記録は**取り直した**（prompts 6件・PATTERNS-0.1.1・同時24本の結果を追加） | `test_rule_documents_match_the_tables`（規則文書の64桁と件数を実装と突き合わせる新しい試験） |
| ⑨ | Host のポートを検査していない。監査の自己接続の免除が名前（`localhost`・`0.0.0.0`）でも通る | ポートは省略か十進1〜65535のときだけ認める。免除は数値の loopback＋自ポートに限る | `Host: localhost:0 / :99999 / :abc / :` が 400（実測） |

**著者の判断が要るもの（実装していない）**：
1. `SPEC.md` §5.6・§12 の「PATTERNS-0.1.0（49件・語形293）」は、現物が `PATTERNS-0.1.1`・語形313（P22・P39 を載せた後）。SPEC の改版は著者判断。
2. ~~Gradio の CORS が loopback の Origin に許可を返す~~ → **2026-09-18 に著者の指示で塞いだ**（`codex2`）。
   上流の `CustomCORSMiddleware` を通しに差し替え、`Origin` 付きの要求には CORS の許可ヘッダを一切返さない。
   起動後に自分自身へ `Origin: http://localhost:1` を当てて、許可ヘッダが無いことを確かめてから配信に入る
   （無ければ起動しない）。README の既知の制約8に一行。M01〜M03・resources 同時24本・SDK 検収は壊れていない（実測）。
