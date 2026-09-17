# Codex 独立検査①（対象コミット `6b8dcaa`）

| 項目 | 値 |
|---|---|
| 検査 | Codex（独立検査。指摘と差分案のみ。SPEC §10） |
| 対象 | コミット `6b8dcaa`（施工段階3の merge 時点）・corpus v3.5.0・Gradio 6.27.0・Python 3.13.15 |
| 受領 | 2026-09-18（著者経由） |
| 反映 | ブランチ `codex1` → コミット `f88effc`（10件すべて差分案どおり反映） |
| 試験 | `.venv/bin/python -m pytest -q` → 390 passed |

> **この記録について**：ここに載せているのは、著者から渡された指摘の一覧（P1-2〜P3-10）と、施工側での反映結果である。
> Codex の報告本文そのもの（前文・行番号つきの分析・差分の全文）は施工側に届いていないため、本書はその要約にあたる。
> 本文を受け取ったら、本書をそれに差し替える（そのとき、ローカルの絶対パスはリポジトリ相対に置き換える）。
> 施工側でローカルの絶対パスを書かない方針のため、以下の参照はすべてリポジトリ相対である。

## 指摘と反映

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
  `/queue/join` は同時8件まで（超過は 503）。resources・prompts も七ツールと同じ実行枠（同時4）を使う。
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
  `patterns.table_sha256()`＝`b38299528fe444babb2fb343d8877dcd284a8021f0621e91c6c4a0439c8dd70d`。
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
