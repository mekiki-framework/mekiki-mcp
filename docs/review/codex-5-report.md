検査コミット：`b072d88a2bb9f2f9d14672265fca3b29f1018fa2`

ブランチ：`main`／正本：`SPEC.md` v2.5.1・`CLAUDE.md` v1.2／検査日：2026-09-27

## 指摘（重大度・箇所・根拠）

HTTP併設に限定して検査した。指摘は **P2が2件、P3が3件**。既存のH01〜H04は両モードで通るが、追加した入力で500と表現選択の不一致を再現した。確認した範囲では、HTTP追加による任意ファイル取得・外向き通信・原文書込みの入口、受付枠の漏れは見つからなかった。

### F1 — P2：重複JSONキーの孤立サロゲートで400ではなく500になる

- 箇所：`mekiki_reader/http_api.py:126`〜137、`app.py:822`〜823、`app.py:1038`。
- 根拠：SPEC §2.12の不正・重複引数400、`docs/rules/HTTP.md:44`〜45の本文・入力エラー契約。
- `object_pairs_hook` が、許可名の検査より先に未検証のキーをエラー理由へ埋め込む。孤立サロゲートを含む理由もJSON文字列までは作れるが、応答本文のUTF-8化で `UnicodeEncodeError` になる。

最小の本文：

```json
{"\ud800":1,"\ud800":2}
```

入れ子でも再現する：

```json
{"text":{"\ud800":1,"\ud800":2}}
```

実HTTPで **local／spaces × verify／check × JSON／Markdown × 直下／入れ子の16条件がすべて500**。現物関数のメモリ試験では応答開始前の例外と確認した。本文中の通常の `text` 値に対する既存サロゲート検査では、このキー側の経路を覆えない。受付枠は戻り、後続のpapersは200だったため、永続的な枠枯渇・サーバ停止までは再現していない。

### F2 — P2：複数行のAcceptを最後の一行に潰し、同じ意味のヘッダで表現が変わる

- 箇所：`app.py:804`〜805、`app.py:836`〜837。
- 根拠：SPEC §2.12のMarkdown選択・表現別ETag・Vary、`docs/rules/HTTP.md:53`、同69〜70行。
- ヘッダを辞書にすると、同名ヘッダの最後の値だけが残る。実HTTPの `GET /api/v1/papers` で、両モードとも次の差を確認した。

| Acceptの送り方 | 実際の応答 |
|---|---|
| 一行：`text/markdown, application/json` | Markdown・1,181バイト |
| 二行：`text/markdown`、次に `application/json` | JSON・33,380バイト |

どちらも200・`public, max-age=3600`・`Vary: Accept` で、ETagは異なる。二行の要求へJSON側のETagを付けると304も返る。

同名のリスト型ヘッダは順序を保ったカンマ結合で意味が決まり、キャッシュのVary照合でも行の結合による一致を認める。このため、**originには二行のまま転送し、Vary照合では結合するキャッシュ**では、二行の要求で保存したJSONを、一行のMarkdown要求へ再利用する条件がある。これはoriginの実測と規格からの条件付き推論であり、HFエッジや実キャッシュでの誤再利用は今回測定していない。[RFC 9110 §5.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-5.2)、[RFC 9111 §4.1](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.1)

同じ辞書化で `If-None-Match` も失われる。現物式のメモリ試験では、現在のETagが最初の行、別タグが最後の行にあると不一致になり、カンマ結合した一行では一致した。こちらは主に304を返し損ねる問題で、F2と同じ箇所で直せる。

### F3 — P3：Guardの拒否応答に、文書で約束したcacheヘッダが付かない

- 箇所：`app.py:761`〜773。
- 根拠：`README.md:324`〜326、`docs/rules/LIMITS.md:39`、`docs/rules/HTTP.md:69`〜72。
- `_send_api` の応答には共通ヘッダが付くが、その前の `_reply` には `Cache-Control: no-store`・`Vary: Accept`・`X-Content-Type-Options: nosniff` がない。
- 実HTTPで、不許可Hostの `/api/v1/papers`（400）、`/api/v1/nope`・`/api/v1/papers/`・パス形anchor（404）、未知経路へのPOST（404）の三ヘッダ欠落を両モードで確認した。対照のツール由来400には三つとも付く。
- したがって「POSTと400・404はno-store」「400・404にも必ずVary」は実装より強い。既存H04は既知経路での `unknown_id` 404を確認するため、Guard由来404の欠落を検出しない。今回、キャッシュによる保存や情報漏れ自体は実証していない。

### F4 — P3：メソッドを大文字化し、九経路にないget／Postも受ける

- 箇所：`app.py:895`〜903。
- 根拠：SPEC §2.12の「上記以外のメソッドは405」、`docs/rules/HTTP.md:29`。
- `scope["method"]` を `.upper()` してから許可表と照合する。実HTTPで両モードとも `get /api/v1/papers` と `Post /api/v1/check` が200になった。HTTPのメソッド名は大小文字を区別するので、契約上のGET／POST以外も実行できる。[RFC 9110 §9.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.1)
- 既存H03は大文字のメソッドだけを試している。読み取り専用の処理・引数検査・受付枠を迂回するものではないが、メソッドの許可契約に余分な入口がある。

### F5 — P3：引数と本文の説明に過剰な一般化・旧範囲が残る

| 箇所 | 記述と現物の差 |
|---|---|
| `docs/rules/HTTP.md:37`、`app.py:993` | 「空文字は省略と同じ」は全引数には当てはまらない。`guide?part=` はinvalid_inputだが省略はallでok。`search?q=answerability&k=` はinvalid_inputだが省略は5でok。現物の引数変換・ツールで確認。MCP側も同じなので、実装を一律に省略扱いへ変えると互換性を崩す |
| `docs/rules/LIMITS.md:29` | 「MCPと自己呼び出し以外は本文に触れない」という旧説明が残る。現物 `app.py:251` のPRE_READには `/api/v1/` が加わり、本文付きのHTTP要求も先読みする。同文書39行のHTTP追加説明は実装どおり |

### 範囲ごとの検算結果

以下は上の指摘を除いた確認結果。実測とメモリ試験を分けて記す。

| 九経路 | 確認結果 |
|---|---|
| GET `/api/v1/` | 一覧を固定表と照合。ツール応答との同一JSONの対象ではない。JSON／Markdownとも確認 |
| GET `/api/v1/papers` | MCPのlist_papersとJSONバイト一致 |
| GET `/api/v1/papers/{paper_id}/sections/{anchor}` | 原文・T4英訳・不存在ID・不存在anchorをMCPと突合。パス形の値は404 |
| GET `/api/v1/search` | q・paper_id・k、空結果・候補・範囲外kをMCPと突合 |
| GET `/api/v1/claims` | claim_id／query、未記録範囲・不存在ID・省略時エラーをMCPと突合 |
| GET `/api/v1/guide` | 全体・指定part・不存在partをMCPと突合 |
| GET `/api/v1/verify` | 原文・言語指定・不一致・短すぎる入力をMCPと突合 |
| POST `/api/v1/verify` | GETと同じJSON。language=enの英訳照合、POSTへのquery付加拒否を確認。キー側の例外はF1 |
| POST `/api/v1/check` | MCPのcheck_compressionsとJSONバイト一致。GETは405／Allow: POST。キー側の例外はF1 |

| 検査対象 | 結果・確認方法 |
|---|---|
| 通常の同一JSON | H01の38入力を両モードで実MCPと実HTTPのバイト比較。七ツール・八つのツール経路を含む。R01の固定呼び出しもHTTP反復と別プロセスの結果データが一致 |
| Markdownの出典・原文 | H02の実HTTP試験に加え、現物Readerと描画関数のメモリ試験で194要求・327本文区間を原文の行と照合。末尾改行・表セルの処理はHTTP規則の明示範囲。本文の改変を確認せず |
| 404／405・転送 | 末尾slash・余分な区切り・大小の異なる経路・未知経路・パス形ID、HEAD／OPTIONS等を実HTTP確認。Locationなし。304は条件付きGETであり転送とは区別。メソッドの大小差はF4。既存の明示遮断が先に働く `/api/v1/file=app.py` は403で、遮断は弱まっていない |
| 受付枠 | 既存H03は実サーバで枠を縮めて超過503・切断後の復帰を確認。追加の現物Guardメモリ試験では、未完POST50本がactive16・waiting32・503×2、切断後0／0。枠は本文の前に取り、送信完了まで持つ |
| 実行枠 | HTTPもAPI_TOOLS→MCPと同じ入口→共有 `_SLOTS` を通る。枠を0にした実サーバ試験・メモリ試験で503。独自の無制限なツール実行入口は確認せず |
| 本文・受信期限 | 実HTTPで65,536バイトは本文層を通りツール検査の400、65,537バイトは413、未完本文は約10秒で408。追加メモリ試験ではTE＋CL、表明と実測の差、継続的な小分け受信も確認 |
| 送信期限 | 現物Guardのメモリ試験でsendを停止させ、期限後のabort呼出し1回・受付枠解放を確認。実TCPの送信停止試験は今回再実施していない |
| Host・Origin | 両モードの実HTTPで許可／不許可Host・Origin付き応答・OPTIONSを確認。追加メモリ試験で欠落／重複Host、長いポート、IPv6括弧の不正接尾辞も400。HTTP応答にCORS許可ヘッダなし。spacesのroot健康検査例外はHTTP APIに及ばない |
| 引数解析 | 不正な%列・不正UTF-8・サロゲートの百分率表現・未知名・重複引数・異常kは既存実HTTP試験で400。追加メモリ試験で%00〜%FF、深いJSON・長大数値・NaN／Infinityを確認。F1以外の未捕捉例外は再現せず |
| 長いquery・URL | ローカルの実HTTPで1,001／16,000／18,000／65,000／260,000字のqがツール由来400。空項目だけのquery（&の反復）は18,000／65,000／260,000バイトでも200で、空項目を数えない規則どおり。500なし。**260 KB級もHTTP層を通ったため、16 KiB等をURLの固定上限とは見なせない**。この測定は最大受理長の確定ではなく、HFエッジの長さ制限も未測定 |
| cache・ETag | 単一Acceptの通常要求では、経路・引数・表現の差、既定引数の同値性、弱いタグ・*・リスト、304の空本文、400／404に304を返さないことを実HTTP確認。F2・F3が残存 |
| 情報・副作用 | 入力マーカーが標準出力・標準エラーに出ない既存H04が両モードで通過。HTTP層の固定API表・既存Reader入口・任意パスやURL取得処理の不在をコード確認。追加実サーバ試験の監査は外向き通信0件（陽性対照を除く）、dataの前後SHA-256一覧は一致。検査範囲外も含めた安全保証はしていない |

実行した既存試験：

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest tests/test_http.py -p no:cacheprovider -q --tb=short
39 passed, 2 warnings in 45.34s

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest tests/test_safety.py -p no:cacheprovider -q --tb=short -k 'reader_has_no_network_imports or allowlist_is_pinned'
2 passed, 64 deselected in 2.30s
```

最初のHTTP試行はサンドボックスのloopback bind拒否で起動できず、許可された実行で再試験した。39件通過は後者の結果。警告2件はMCPクライアントの非推奨APIに関するもの。spacesの試験は配置設定・Hostをspacesにし、待受だけ試験用loopback／空きポートにしたもので、公開Spaceそのものへの負荷試験ではない。試験用プロセスは自分で起動したものだけを停止した。リポジトリの変更は本報告書だけで、コミットしていない。

## 差分案

| 対応 | 変更案 | 追加する試験 |
|---|---|---|
| F1 | 重複キーのエラーを入力キーを含まない固定文にする。許可名を示す場合も未検証キーを埋め込まない | verify／check、JSON／Markdown、直下／入れ子、上位／下位サロゲートの重複キーが400・invalid_input・有効UTF-8になり、500を出さない。通常の重複textも400を維持 |
| F2 | AcceptとIf-None-Matchは、全同名ヘッダを順序維持でカンマ結合してから解釈する。HostやContent-Lengthの既存重複拒否は変更しない | 一行と複数行でContent-Type・本文・ETagが一致。MDが最初／最後、q=0、大小の異なるヘッダ名も検査。現在のETagを最初のIf-None-Match行に置いても304。Vary照合で結合する小さなキャッシュ試験も置く |
| F3 | HTTP名前空間の早期拒否にもno-store・Vary・nosniffを付け、_send_apiと共通化する | 不許可Host400、未知経路404、パス形ID404、405、413、408、503、POSTの早期拒否でヘッダとETag不在を確認。h11がGuardより前に返す応答は別と文書化 |
| F4 | HTTP経路の許可判定では、ASGIの元のmethod文字列をそのまま表と照合する | 九経路すべてでget／Get／post／Post等は405・正しいAllow、GET／POSTは従来どおり。既存MCP側の振り分けには影響させない |
| F5 | 空文字の説明を引数ごとに限定する。partとkは省略時だけ既定値、空文字はinvalid_inputと明記。LIMITSの本文対象にHTTP併設を含める | H01でpart／kの省略と空文字をそれぞれMCPと突合し、HTTPだけの既定値補完を追加しない |

F1の最小変更例（未適用）：

```diff
--- a/mekiki_reader/http_api.py
+++ b/mekiki_reader/http_api.py
@@
         for key, value in items:
             if key in seen:
-                raise HttpInputError(f"引数 {key} が重複している")
+                raise HttpInputError("本文のJSONキーが重複している")
             seen[key] = value
```

長いqueryは今回例外を起こさなかったが、次のH03ではサイズだけでなく送信を一括／分割した場合も固定する。アプリ独自のURL上限を導入する場合は、現在の「HTTP層とエッジに従う」契約を変更するため、SPEC・HTTP・LIMITSの改版と合わせて扱う。
