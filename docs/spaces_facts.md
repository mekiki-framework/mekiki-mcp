# Spaces 向けの現物確認（Codex③ 11・2026-09-19）

方針書 v2.4 の材料。**確認だけで、実装はしていない**。コードは `.venv/lib/python3.13/site-packages` に入っている
gradio 6.27.0・gradio_client 2.7.0・huggingface_hub 1.32.0・uvicorn 0.53.0 を読んだだけ。Web の参照日はすべて 2026-09-19。
使い捨ての Space での実測はしていない（費用と公開範囲は著者判断）。

根拠の区分：【文書】公式文書に書かれていること／【コード】インストール済みパッケージのソース／【実例】フォーラムや issue の
報告（HF 職員か一般利用者かを添える）／【推論】施工側の推論。施工側で主要なコードの主張（下の b・c'・a の分岐）を読み直して確かめた。
上流の挙動の詳細は、公開用に互換性の説明へ要約してある（2026-09-19・Codex④ F1）。

**要点**

- 今の `app.py` のままでは、Spaces 上で起動直後に自分で止まる（下の 1-1 b。`verify_blocks` が `pwa=True` を見て exit 5）。
- 止まらなくても、127.0.0.1 に bind しているので外から届かない（第3節）。
- Host の許可一覧が loopback だけなので、外からの要求はすべて 400 になる（第2節）。

## 1. `SYSTEM=spaces` と `SPACE_ID` があるときに動く経路

### 1-0. 前提

- `get_space()` は `SYSTEM == "spaces"` のときだけ `SPACE_ID` を返す（`gradio/utils.py:602-605`）。
  【文書】HF の組み込み環境変数の一覧にあるのは `SPACE_ID`・`SPACE_HOST`・`SPACE_AUTHOR_NAME`・`SPACE_REPO_NAME` などで、
  `SYSTEM` は載っていない。`SYSTEM=spaces` を前提にしているのは gradio 側のコード（`gradio/cli/commands/deploy_space.py:273`）。
- `app.py` の `sanitize_environ` が消すのは `GRADIO_*` とプロキシ系の10変数だけ。
  残るもの：`SYSTEM`・`SPACE_ID`・`SPACE_HOST`・`SPACE_AUTHOR_NAME`・`OAUTH_*`・`HF_TOKEN`・`SPACES_ZERO_GPU`・`FORWARDED_ALLOW_IPS`・`WEB_CONCURRENCY`。
- Spaces が入れる `GRADIO_*` は、`import gradio` の前に消える（`http_server.py:31-33` の `GRADIO_SERVER_PORT/NUM_PORTS/SERVER_NAME` は
  import 時に読まれるので、消した後の値が使われる）。【文書】Gradio の環境変数ガイドに、Spaces 上では `GRADIO_SSR_MODE` が
  この環境変数で True になるとある（Spaces が `GRADIO_*` を入れている直接の根拠）。

### 1-1. 箇所ごとの影響（app.py の現状で判定）

| # | 箇所 | Spaces で何が変わるか | app.py への影響 |
|---|---|---|---|
| a | `http_server.py:152-162`、`utils.py:229-269`（SpacesReloader）、`utils.py:319-339` | 監視用のスレッドが一本増える。起動時に `GRADIO_HOT_RELOAD: …` を標準出力に出す。`spaces` パッケージが無いとスレッド内で例外になり、traceback がログに出る（サーバは動き続ける）。`spaces` 0.43 以上があると `spaces.reloading.start_reload_server` が動く | **影響あり**。`start_reload_server` の中身（待ち受けや外向き通信の有無）は未確認。リロードで Blocks が差し替わる経路もある。S03 は Spaces 上で測り直す必要がある |
| b | `blocks.py:3007`（`pwa` 未指定なら Spaces 上で True） | `launch()` が `pwa` を渡していないので True になる | **起動が止まる**（コードから確実）。`verify_blocks` が `pwa=False` を確かめるので exit 5。`pwa=False` を明示すれば避けられる |
| c | `mcp.py:384-385`・`mcp.py:545`・`mcp.py:532` | ツール名が `<Space名>_` 付きになる（英数字以外は `_`） | Q69 のとおり |
| c' | 上流の MCP の prompts の実装 | Spaces 用の分岐では、prompts の名前に互換性の制約がある（一覧の名前と取得の照合がそろわない） | **現構成（`SYSTEM` の除去）では該当しない**（Spaces 用の分岐に入らず、接頭辞が付かない。M01・M02 の期待値どおり）。resources は影響なし |
| d | `blocks.py:1178` → `routes.py:1417` | queue=True の関数への直接 POST を拒む | 影響なし（関数は queue=False・経路はガードが塞ぐ） |
| e | `blocks.py:1180, 2566`、`routes.py:682, 837-847` | config と `/gradio_api/info` のコード例に `space_id` が入る | 公開情報で影響は小さい |
| f | `blocks.py:3343-3345` | share を強制的に False | 影響なし（もともと False） |
| g | `blocks.py:103-106`、`block_function.py:9-12, 120-124` | `spaces` が import できると、全関数を `spaces.gradio_auto_wrap` で包む | **未確認**（包むコードの中身と、`_mcp_type` などが残るか） |
| h | `oauth.py:38-41` ほか | `LoginButton` があるときだけ OAuth の経路を足す | 影響なし（UI なし） |
| i | `utils.py:608-609`、`blocks.py:2700-2701` | ZeroGPU では `max_size` 未指定なら 1 | 影響なし（72 を明示） |
| j | `external.py:88-90`、`gradio_client/client.py:113-120` ほか | `HF_TOKEN` を使うのは `gr.load` だけ。内部クライアントは送らない（`HF_HUB_DISABLE_IMPLICIT_TOKEN=1`） | 送信されない。ただし Secret に入れればプロセスの環境には残る |
| k | `uvicorn/config.py:363, 543-544` | `FORWARDED_ALLOW_IPS` から来た要求の `X-Forwarded-Proto/For` だけを信用する。Host は書き換えない | sanitize の対象外。Spaces がこの変数を入れるかは不明 |

SSL・`root_path`・`max_file_size`・show_api・heartbeat には Spaces 専用の分岐は無い。gradio 側の Spaces 分岐が新たに外向き通信を
したりファイルを書いたりすることは無い。未知なのは `spaces` パッケージだけ。

## 2. プロキシがどう転送するか

- 【文書】公開 URL は `https://<space-subdomain>.hf.space` で、Space は常にそのサブドメインの根から配信される（spaces-embed）。
  パスの前置は付かない（`root_path=""` のままで合う）。
- 【文書】独自ドメインは PRO 以上で、`hf.space` への CNAME。【コード】独自ドメインを使うと `SPACE_HOST` がカンマ区切りの複数値になる
  （`gradio/oauth.py:223-228` のコメント。HF の文書には無い）。
- 【文書】ZeroGPU の文脈で、HF 基盤がすべての要求に `X-IP-Token` を付けるとある（Gradio クライアント文書）。
- 【文書なし】アプリが受け取る Host の値と、`X-Forwarded-*` を付けるかどうかは HF の文書に無い。
- 【実例】入口は AWS の ELB（応答に `server: awselb/2.0`）で、`x-proxied-*` ヘッダがある（一般利用者の報告 2026-07-09。HF 職員が修正を確認）。
- 【実例】エッジが CORS ヘッダ（`Access-Control-Allow-Credentials`）を落とすという報告がある（2026-06〜07・一般利用者。HF 職員の回答なし）。
- 【コード】Gradio はプロキシが `X-Forwarded-Host/Proto` を付けることを前提に作られている（`route_utils.py:496-525, 557-584`、`mcp.py:451-477`）。
- 【推論】Host は `<sub>.hf.space` か独自ドメインになる見込みが高く、どちらでも loopback ではない。ガードの `ALLOWED_HOSTS` が外からの
  全要求に 400 を返す。健康検査が送る Host は分からない（使い捨ての Space で実測が要る）。
- MCP の URL：【文書】Gradio ガイドの例は `https://<owner>-<space>.hf.space/gradio_api/mcp/`。Gradio の Space に MCP を入れると
  MCP のバッジが自動で付き、利用者は HF のトークンで `hf.co/mcp` 経由で追加できる（spaces-mcp-servers）。

## 3. 0.0.0.0 への bind が必要か・ポート

- 【文書】`app_port` は Docker の Space だけで使い、既定は 7860（設定リファレンス）。【推論】Gradio SDK ではポートは 7860 固定。
- 【文書】Docker の例は `--host 0.0.0.0 --port 7860`。内部では何本でも待ち受けられるが、外に出るのは一つのポートだけ。
- 【推論】Gradio SDK の公式例は引数なしの `launch()` で動くが、Gradio の既定の bind 先は 127.0.0.1（`http_server.py:33`）。したがって
  実行環境が `GRADIO_SERVER_NAME=0.0.0.0` を入れているはず。`app.py` はこの変数を消し 127.0.0.1 を固定しているので、外から届かない。
- 【実例】健康検査はコンテナの外から 7860 番の `/` を調べ、404 以外なら Running になる。loopback に bind すると Starting のまま止まる
  （一般利用者の説明 2025-11-27。HF 職員の説明なし）。
- 0.0.0.0 に bind した場合の Gradio 側：`local_url` は `http://localhost:PORT/` になる（`http_server.py:113`）。内部クライアントの Host は
  `localhost` で許可一覧に入っている。ただし `verify_blocks` の `server_name` と `local_url` の照合は書き換えが要る。
- 127.0.0.1 のままにする案：Docker の Space に中継（nginx など）を置き、0.0.0.0:7860 から 127.0.0.1 へ渡す。外に開く面が別の部品に移り、
  構成要素が一つ増える。

## 4. ログの行き先

- 【文書】実行ログは実行中のアプリの標準出力・標準エラーで、ビルドのログとは別（`huggingface_hub/hf_api.py:8776-8779`）。画面では
  Logs の Build / Container のタブで見る。
- 【文書】誰が見られるか：Spaces の changelog（2021-08-01）に、生ログは書き込み権限のある利用者が見られるとある。現行の文書には記載が無い
  （ログアウトした状態で見えるかは著者が確かめる必要がある）。
- 【文書】保持期間の記載は無い。API は今バッファにあるログだけを返す。ディスクは永続しない（再起動で消える）。
- 【実例】レプリカが増えたときや再起動のときにログが消えることがある（2026-01・一般利用者）。標準出力のバッファは
  `PYTHONUNBUFFERED=1` で解決した例がある（`app.py` 自身の出力は `flush=True`）。
- 【コード】この構成で Gradio がディスクに書くものは無い（flagging・examples のキャッシュ・run history・share 用の証明書・vibe は不使用。
  アップロードと deep_link は塞いでいる。uvicorn は `log_level="warning"` でアクセスログを出さない）。
- ログに出うるもの（Codex③ 7 の反映後）：遮断の記録（状態コードと理由だけ）、例外の型と場所、ログの水準・名前・書式、起動時の要約と
  消した環境変数の名前（Spaces では Spaces が入れた `GRADIO_*` の名前も並ぶ）、1-1 a の reloader の行。

## 方針書 v2.4 に向けた論点（著者判断）

1. **bind 先**：SPEC §2.4・Q67（loopback・環境変数では変えない）を Spaces でどう書き換えるか。0.0.0.0 を認める条件。
2. **Host の許可一覧**：`SPACE_HOST`（カンマ区切り）を実行時に読むか、固定値を SPEC に書くか。独自ドメインを使うか。
3. **実測用の使い捨て Space**：Host・ヘッダ・健康検査・ログの見え方・エッジの CORS を測る。費用と公開範囲（private で足りるか）。
4. **SDK**：Gradio SDK は事前に入るパッケージがあり、ハッシュ付きの固定（Q77）と両立するか分からない。Docker なら依存を完全に固定できる。
5. **`spaces` パッケージと SpacesReloader**：未検査のコードがツール関数を包み、リロードの経路を持つことを許すか。`SYSTEM` を消せば
   分岐ごと止まるが、接頭辞と pwa の既定も変わるので Q69 を見直すことになる。
6. **`pwa=False` の明示**：施工の範囲で直せるが、SPEC の固定値の一覧に加えるか。
7. **prompts と接頭辞**：Spaces 用の分岐では prompts の名前に互換性の制約がある。**現構成（`SYSTEM` の除去）では該当しない**（SPEC v2.4 で除去を採用し、接頭辞が付かない）。
8. **MCP バッジ**：自動で付くバッジと `hf.co/mcp` 経由の呼び出しを、公開範囲と開示文でどう扱うか。
9. **ログの開示文**：閲覧は書き込み権限者のみ（2021 年の記載）、保持期間は記載なし＝「保証しない」とするか。
10. **CORS の検査**：エッジでの CORS の操作は `check_cors`（loopback で自分に当てる検査）では見つけられない。Spaces 上で外から当てる検査を検収に入れるか。
11. **sanitize の範囲**：`FORWARDED_ALLOW_IPS`・`WEB_CONCURRENCY`・`SPACES_ZERO_GPU`・`HF_TOKEN` など、`GRADIO_*` 以外で挙動に効く変数を対象に加えるか。
    Space に Secret を置かない方針も明記するか。
12. **費用と版**：Gradio / Docker の Space の作成には有料プランが要る。無料枠は ZeroGPU だけで、ZeroGPU は Gradio SDK 専用・対応 Python は
    3.12.12 と 3.10.13。3.13 の方針と合わないので、PRO と CPU Basic の前提を再確認する。

## 出典（いずれも 2026-09-19 参照）

- https://huggingface.co/docs/hub/spaces-overview
- https://huggingface.co/docs/hub/spaces-config-reference
- https://huggingface.co/docs/hub/spaces-sdks-docker
- https://huggingface.co/docs/hub/spaces-sdks-docker-first-demo
- https://huggingface.co/docs/hub/spaces-sdks-gradio
- https://huggingface.co/docs/hub/spaces-dependencies
- https://huggingface.co/docs/hub/spaces-embed
- https://huggingface.co/docs/hub/spaces-custom-domain
- https://huggingface.co/docs/hub/spaces-dev-mode
- https://huggingface.co/docs/hub/spaces-zerogpu
- https://huggingface.co/docs/hub/spaces-mcp-servers
- https://huggingface.co/docs/hub/spaces-changelog
- https://huggingface.co/docs/huggingface_hub/main/en/guides/manage-spaces
- https://www.gradio.app/guides/environment-variables
- https://www.gradio.app/guides/building-mcp-server-with-gradio
- https://www.gradio.app/guides/deploying-gradio-with-docker
- https://gradio.app/docs/python-client/using-zero-gpu-spaces
- https://github.com/gradio-app/gradio/pull/11821
- https://pypi.org/pypi/spaces/0.51.3/json
- https://discuss.huggingface.co/t/space-to-space-requests-to-hf-space-return-503-from-awselb-since-jul-8/177607
- https://discuss.huggingface.co/t/hugging-face-spaces-proxy-suddenly-stripping-access-control-allow-credentials-header-on-options-preflight/177064
- https://discuss.huggingface.co/t/hf-space-stuck-at-starting/170911/2
- https://discuss.huggingface.co/t/space-stuck-at-starting-health-checker-not-responding-june-20-2026/177005
- https://discuss.huggingface.co/t/error-debug-logs-in-spaces/172682
- https://discuss.huggingface.co/t/spaces-runtime-logging/139383
- ローカルのコード：`app.py` と、`.venv/lib/python3.13/site-packages/` の gradio・gradio_client・huggingface_hub・uvicorn（行番号は本文のとおり）
