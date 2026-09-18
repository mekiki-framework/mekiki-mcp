<!-- Codex 独立検査①の報告本文。著者が配置。施工側でローカルの絶対パスをリポジトリ相対に置換した（20 箇所・2026-09-18）。本文そのものには手を入れていない。 -->

検査ブランチ：`main`
コミットSHA（`git rev-parse HEAD`）：`6b8dcaaa2f6d5ba2d7eeb4f94aa7e9d496d92b76`

## 指摘（重大度・箇所・根拠）

1. **P1：指定された検査対象と、このコミットの内容が異なる。**
   [SPEC.md (line 1)](SPEC.md:1) は **v2.1**、ルートの `README.md` は未配置。[prompts.py (line 89)](mekiki_reader/prompts.py:89) は日本語 **3件**で、指定の6件ではない。READMEの起動表示8行・Desktop橋渡し・既知の制約8項・実装より強い主張は照合不能。また、検索順位は[判断ログ:167 (line 167)](DECISIONS.md:167)の著者確定内容どおりだが、SPEC §5.3への反映が未完了。
2. **P1：要求本文の64 KiB制限を迂回できる。**
   [app.py (line 119)](app.py:119) は `Content-Length` があれば `Transfer-Encoding: chunked` を拒否しない。固定依存のh11と実際のGuardを使うメモリ内試験で、`Content-Length: 1` とchunkedの併記により **65,537バイトが下流へ渡る**ことを再現した。申告長しか検査しておらず、LIMITSの実効的な上限になっていない。
3. **P1：プロキシ環境変数で自己呼び出しが外部へ向く。**
   [app.py (line 22)](app.py:22) は `HTTP_PROXY`・`HTTPS_PROXY`・`ALL_PROXY` と小文字形を残す。固定依存のGradio／gradio_clientは自己呼び出しで環境プロキシを利用する。偽のプロキシ設定で、`127.0.0.1` 宛てにも外部プロキシが選択されることを実通信なしで確認した。HF系の無効化だけでは、この通信経路と環境依存を防げない。
4. **P2：同時実行上限4が全入口を覆わず、queueの待機件数も無制限。**
   [app.py (line 66)](app.py:66) は `/queue/join`・`/call/*` を外部からも許可する。[build_blocks:286 (line 286)](app.py:286) にqueue容量指定がなく、固定Gradioの既定値は `max_size=None`。`queue=False` でも直接HTTP経路はqueueへ投入できる。また、[resources/prompts:257 (line 257)](app.py:257) は七ツール用セマフォを取得しない。
5. **P2：反復要求によるメモリ使用量が有界でない。**
   [tools.py (line 543)](mekiki_reader/tools.py:543) の `_WORD_RE_CACHE` は利用者の検索断片を無制限に保持する。異なる100検索で、固定語形分とは別に100項目増加した。[app.py (line 99)](app.py:99) の `GUARD_LOG` も拒否要求のパスを追加し続ける。一要求の長さ制限では防げない。
6. **P2：S03が自己呼び出し以外の通信・書き込みを見逃す。**
   [server_launcher.py (line 28)](tests/_support/server_launcher.py:28) は接続先ポートを捨て、全loopbackとUnixソケットを免除する。同ファイル45行以降は `open` のflagsを捨てるため、[書き込み判定:289 (line 289)](tests/test_safety.py:289) は `os.open(..., O_WRONLY|O_CREAT)` のmode=`None`を検出できない。合成監査イベントで両方の見逃しを再現した。ファイル監査開始もlaunch完了後なので、起動中の書き込みは対象外。
7. **P2：承認済みTERMS・PATTERNSの表ハッシュがない。**
   [DECISIONS.md (line 79)](DECISIONS.md:79) と[規則一覧:3 (line 3)](docs/rules/README.md:3) は正準JSONのSHA-256を要求するが、両表には期待値・照合処理・文書の値がない。PATTERNSは47件から49件になっても版が0.1.0のままで、版番号だけでは表の内容を同定できない。
8. **P2：孤立サロゲート入力からUTF-8化できない応答を生成する。**
   [tools.py (line 648)](mekiki_reader/tools.py:648) は `"\ud800"` を受理し、QUERY注意書きへ埋め込む。[schema.py (line 66)](schema.py:66) の直列化後、`.encode("utf-8")` が `UnicodeEncodeError` になることを再現した。HTTP/MCPでの最終的なエラー形は未検証だが、通常応答として送信できない文字列を返している。
9. **P2：非通常ファイルを拒否する前に起動が待機し得る。**
   [corpus.py (line 282)](mekiki_reader/corpus.py:282) は読み取り用に開いた後で通常ファイルか検査する。最初に読む `bundle_manifest.json` がFIFOの場合、`open` が待機してBUNDLEの `not_regular` 拒否へ進めない。静的検査による指摘で、ファイル置換による再現は行っていない。
10. **P3：規則文書に旧版・旧状態が残る。**
    [規則一覧:9 (line 9)](docs/rules/README.md:9) はTERMS/PATTERNSを空、PROMPTSを承認待ちとしている。[SEARCH.md (line 7)](docs/rules/SEARCH.md:7)、[TERMS.md (line 26)](docs/rules/TERMS.md:26)にも旧版記述が残る。実物はTERMS-0.1.1＝30項目78語形、PATTERNS-0.1.0＝49件99関連原文、PROMPTS-0.1.0＝承認済み3件。

検証根拠：ツール既存試験269件通過。R01の3種類のハッシュシードで出力ハッシュ一致。パターン313語形はNFD入力を含め取りこぼしなし。bundle・NORMハッシュは一致。requirements.txtは66パッケージを固定し、SHA-256計1096件、requirements.inとの不一致なし。`.mcp.json` は既定のHTTP接続先と一致。サーバから取得スクリプトへの呼び出し、Reader内のLLM呼び出し・外部取得・data書き込みは認めなかった。ファイル変更・コミットなし。

## 差分案

- **正本・文書**：著者確定済みのSPEC v2.2とREADMEを対象コミットに揃える。検索順位は判断ログの確定内容を正本へ反映する。規則一覧の版・件数・承認状態を更新する。READMEの8行・6prompts・8制約やDesktop橋渡しは、現物と検収結果に基づいて記載する。

- **本文制限**：TEとCLの併記を拒否する。`receive()` から受け取った実バイト数にも上限を適用し、超過した本文をJSONパーサへ渡さない。CLはASCII数字として検査する。

- **環境・起動確認**：Gradio import前にプロキシ変数の大文字・小文字形を除去する。起動前後の確認へ実bind先・share・run_history・SSR・monitoring・queue設定を加える。番兵は現在最後に登録されているため、その順序を試験で固定する。

- **有限資源**：queue容量と未回収結果数を制限し、resources/promptsにも実行枠を適用する。正規表現キャッシュは容量付きLRUへ、`GUARD_LOG` は固定長dequeまたは件数集計へ変更する。

- **表・入力・ファイル検査**：TERMS/PATTERNSの語形・出典・版・承認日を正準JSON化し、期待ハッシュと照合を追加する。孤立サロゲートは入力検証で `invalid_input` にする。通常ファイル検査はFIFOで待機しない開き方にする。

- **敵対的テスト追加**：

  | 対象          | 追加する入力・期待値                                         |
  | ------------- | ------------------------------------------------------------ |
  | T09           | 数値・符号・否定・内容語を独立に改変。対象全文に生・正規化後の別一致がないことを先に確認し、`quote_not_found`・空resultsを要求する。 |
  | T10           | 実際の隣接行を結んだ引用、正規化後4/5字・9/10字、直接一致と正規化一致の20/21件を検証する。現コーパスでは `"agent-rela"` が20件、`"Externaliz"` が21件で境界を再現できる。 |
  | T11           | 全承認語形の再生、肯定・否定・引用・疑問の同形、ASCII語境界、未登録同義語・活用形、NFD入力を追加する。位置検証には仕様どおりNFC合成後の入力を使う。 |
  | S01           | 全該当ツールへパス・URL・巨大入力・異常k・孤立サロゲートを投入。Hostの欠落・重複・IPv6＋ポート、本文65,535/65,536/65,537バイト、chunked＋偽CLを検証する。 |
  | S01・同時実行 | 処理をEventで保持して4枠を確実に埋め、5件目の通信層エラーを確認する。直接queue経路でも待機上限超過を検証する。 |
  | S03           | 接続先のホスト・ポートを記録し、実際の自己接続だけを許可する。Unixソケットを一律免除しない。openのmodeとflagsを記録し、起動から停止まで監査する。監査器自身に通信・書き込みの陽性対照を追加する。 |