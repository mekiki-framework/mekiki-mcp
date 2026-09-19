# 検収記録：Hugging Face Space（private）＋ Claude Code / 2026-09-19

配置段階二の private での検収（SPEC §7 S04・P01・P02）。**今回の記録は著者の実測（S04・P01・起動表示）と、
施工セッションからの `list_papers` 一回（P02）**。ほかの項目は未実施。続きは同じファイルに書き足す。

## 1. 条件

| 項目 | 値 |
|---|---|
| 実施日時 | 2026-09-19（P02 の呼び出しは 19:38 JST ごろ。S04・P01 の時刻は未記録） |
| 実施者 | S04・P01・起動表示：著者（Kengo Tomita）の実測を施工が転記。P02：施工（Claude Code）が著者の指示で本セッションから呼んだ |
| Space | `KennGoTm/mekiki-reader`（Docker・CPU basic・private） |
| クライアント | Claude Code（Desktop アプリの Code タブ）。版は未確認 |
| モデル | Opus 5（`claude-opus-5`） |
| 接続方式 | Streamable HTTP 直結（MCP サーバ名 `mekiki-reader-space`。接続設定はトークンを含みうるので施工は中身を読んでいない） |
| 接続 URL | `https://kenngotm-mekiki-reader.hf.space/gradio_api/mcp/` |
| サーバの起動表示 | モード `spaces`・待ち受け `0.0.0.0:7860`・許可 Host `kenngotm-mekiki-reader.hf.space`（著者の転記。`corpus …・bundle …` と `tools …・resources …・prompts …` の行は未記録） |
| サーバの版 | Space のコミット `b8c4b38`（元は mekiki-mcp `main` `d6ae3ed` 相当）。Space 上での `pytest` は対象外。応答の `limitations`：SECTION-1.0.0 LANG-1.0.0 JSON-1.0.0 |
| 消した環境変数 | `SPACE_AUTHOR_NAME`・`SPACE_ID`・`SPACE_REPO_NAME`（起動表示） |

## 2. 発見と呼び出し（P02）

| 項目 | 期待 | 実測 | 備考 |
|---|---|---|---|
| `tools/list` | 7件（接頭辞なし） | 7件：`list_papers` `get_section` `search_passages` `get_claim_record` `verify_quote` `check_compressions` `get_reading_guide` | Claude Code が出した名前（`mcp__mekiki-reader-space__<ツール名>`）から読んだ。接頭辞はクライアント側の名前空間。生の `tools/list` は見ていない |
| `list_papers` | `ok`・5本 | `ok`・results 5（T1〜T5）・candidates 0 | `bundle_hash` `40a09c5ba422582c951928f873f5729a420514a46409359559d7e6123c1224d5`＝手元の `shasum -a 256 data/bundle_manifest.json` と一致。`corpus_version` 3.5.0・`source_commit` `67480613108cf72c29d5691e3d7a6c7e6553eb9b`・`schema_version` 1.0.0。生の応答は会話に全文を貼ったが、このファイルには写していない |
| `get_section`（ja） | `ok` | 未実施 | |
| `get_section`（`language="en"`） | `ok`・`source_kind=translation` | 未実施 | |
| `search_passages` | `ok`・順位つき | 未実施 | |
| `get_claim_record`（T5） | `ok`・`status` を逐語 | 未実施 | |
| `get_claim_record`（T1〜T4） | `ledger_not_available` | 未実施 | |
| `verify_quote`（一致） | `ok`・`match` は exact か normalized | 未実施 | |
| `check_compressions` | `ok`（該当ゼロでも ok） | 未実施 | |
| `get_reading_guide` | `ok` | 未実施 | |
| `resources/list` | 12件・テンプレート0件 | 未実施 | |
| `resources/read` | 本文の SHA-256 が bundle と一致 | 未実施 | |
| `prompts/list` | 6件（日本語3・英語3） | 未実施 | |
| `prompts/get`（既知） | 文面が `mekiki_reader/prompts.py` と一致 | 未実施 | |
| `prompts/get`（未知の名前） | 雛形を返さずエラー | 未実施 | |

P02 は SPEC §7 では「M01〜M03 と E01 二問（R01・R14）」。今回は `list_papers` だけで、**P02 は一部実施**。

## 3. 不正な入力とゼロ件

未実施。

## 4. E01（スモーク・五問）

未実施（P02 の R01・R14 を含む）。

## 5. E02（事例と命令文）

未実施。

## 6. P01（代替：Pause→Restart）

| 項目 | 値 |
|---|---|
| 実施の別 | 休止からの復帰（Space の Pause→Restart。SPEC の「再起動・休止復帰」の代替として著者が実施） |
| 操作した時刻 | 未記録 |
| 最初の呼び出しが返った時刻 | 未記録 |
| 復帰までの時間（実測） | 著者の報告は「<17>」のまま転記（単位・測り方の記載なし。要確認） |
| 復帰後に `tools/list` が7件か | 未確認 |
| 復帰後に `list_papers` が `ok` か | 未確認（本記録の P02 の呼び出しが復帰の前か後かは未記録） |
| 起動表示（3行）が同じか | 未確認 |

## 7. S04（Spaces 上・外からの検査。様式外の追加）

| 項目 | SPEC §7 の期待 | 実測（著者） | 判定・備考 |
|---|---|---|---|
| `GET /` | 健康検査が通る | 200 | 健康検査の Running 表示は記録なし（P02 の呼び出しが通ったので稼働はしていた） |
| 旧 SSE 経路（`/gradio_api/mcp/sse`） | 404（README §6 の表） | 404 | 一致 |
| `/config` | 404 | 404 | 一致 |
| ツールの schema | 接頭辞なし | 接頭辞なし | 一致 |
| `Origin` 付きの要求 | 許可ヘッダが返らない（エッジの改変も含めて外から測る） | `access-control-allow-origin` が返る。付与しているのは HF のエッジで、サーバは付与しない | **期待と不一致**。著者の判断で開示の対象とした（README §8 既知の制約 8）。SPEC §7 S04 の文言は変えていない |
| `Host` 不一致 | 400 | 未確認 | |
| stdout／stderr に受信した値が出ない | 出ない | 未確認 | |
| S03 相当の監査（起動時の外向き通信・書き込み）を Space のログで確認 | 宣言範囲内 | 未確認 | |

## 8. 未対応・備考

- 未対応の機能：なし（今回使ったのは `list_papers` だけ）。
- 次にやること：S04 の残り（Host 不一致・ログに値が出ないこと・監査）、P01 の単位と時刻の確認、P02 の残り（M01〜M03・R01・R14）。
  README §8 の「費用と休止」と「Spaces 側のログ」の実測の記入も残っている。
