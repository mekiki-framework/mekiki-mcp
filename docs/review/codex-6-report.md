検査コミット SHA：`e7b06717bce2ac9cc2d3382e384774ca01c4aeac`（`main`）

指定された `c176baedd8cab35e25d3838356577887a80767e4` 以後の変更は `SPEC.md` と `DECISIONS.md` だけで、今回の実装・試験・HTTP 規則・README・TUTORIAL・案内ページは同一。現在の HEAD にある SPEC v2.5.5 §2.12 を正本とし、HTTP-1.3.0 と照合した。検査日：2026-09-28。

## 指摘

重大度は P2＝入力・応答の契約に影響する修正対象、P3＝限定した入力の不具合または記述の不整合。指摘は5件。今回試した範囲で、HTML タグ・属性の注入、応答ヘッダへの入力混入、HTML 追加による外向き通信は再現していない。

### F1 — 生の `#` を受理した HTML の末尾リンクで、照合対象の引用が変わる

- **箇所・根拠**：`mekiki_reader/http_api.py:422` の `alternate_links` は query を URL として符号化せず連結し、`:448` で HTML エスケープだけを施す。属性からの脱出は防げるが、URL のフラグメント区切り `#` はそのまま残る。SPEC §2.12（`SPEC.md:62`）と `docs/rules/HTTP.md:65` の「同じ内容」「format だけを変える」に反する。
- **再現手順**：自分で空きポートに起動した試験サーバへ、`http.client` 等で次の要求先をそのまま送る。ヘッダは `Accept: text/html`。通常のブラウザのアドレス欄では `#` 以降を送らないため、最初の要求は生の HTTP 要求で行う。

  ```text
  /api/v1/verify?text=AI%20can%20assist%20play.%20It%20cannot%20take%20one%27s%20place%20in%20it.#extra&format=html
  ```

  応答の JSON リンクの `href` を HTML パーサーで取り出し、URL のフラグメントを除いた要求先で再要求する。
- **期待**：最初に受理した `text` の `#extra` までを保持し、同じ `quote_not_found` の JSON／Markdown を取得できる。
- **実測**：local・spaces とも最初は **200 HTML／`quote_not_found`**。生成された JSON リンクは `…it.#extra&format=json` で、リンク先の要求から `#extra&format=json` が落ちる。ブラウザ相当の Accept では **200 HTML** に戻り、同じ要求先を JSON の Accept で確認すると **`match: exact`** になる。引用の末尾と表現指定の両方が失われた。実測は「href の解析→フラグメント除去→実 HTTP 再要求」であり、GUI ブラウザのクリック試験ではない。保存済み原文は変わっていない。
- **重大度**：**P2**。生の `#` を含む要求を受理した場合に限るが、「同じ内容」のリンクで照合入力と結果が変わる。
- **差分案**：リンク用の URL 符号化と HTML 属性用のエスケープを分ける。受理済みの引数値を URL 上でも同じ値として復元できるように組み立て、その後 `esc()` を通す。少なくとも値中の生の `#` は `%23` にする。`#`／`%23`、引用符、`&`、`+`、非 ASCII を含む query について、リンクの再要求で同じツール引数・結果になることを固定する。

### F2 — 符号化された `format` の名前が末尾リンクに残り、400 になる

- **箇所・根拠**：`mekiki_reader/http_api.py:424` は未復号の名前と `b"format"` を比較して除去する。一方、問い合わせの解析は名前もパーセント復号する（`docs/rules/HTTP.md:39`）。両者で同じ名前の判定が異なる。
- **再現手順**：`GET /api/v1/papers?%66ormat=html` を送り、HTML 末尾の JSON／Markdown リンクを再要求する。`for%6Dat`、`%66%6f%72%6d%61%74` でも同じ手順。
- **期待**：元の `format` 一つが置き換わり、200 JSON／200 Markdown を取得できる。
- **実測**：local・spaces とも最初は **200 HTML**。JSON リンクは `/api/v1/papers?%66ormat=html&format=json` になり、再要求は **400 JSON／`invalid_input`**。Markdown リンクも同じ。復号後に `format` が重複するため。
- **重大度**：**P3**。受理する引数名の符号化によって表現切替が壊れる。
- **差分案**：`format` の除去は、問い合わせの検証と同じ復号済みの名前で判定する。F1 と合わせ、検証済み引数から別表現の URL を作る方法ならこの差も解消できる。上記三種類の名前について、HTML の生成だけでなくリンク先が200になることまで H02 に追加する。

### F3 — 上限内で受理した HTML から、上限超過の末尾リンクを生成する

- **箇所・根拠**：`mekiki_reader/http_api.py:427` は `format` の追加後の長さを確認しない。受信上限は `app.py:891` と `docs/rules/HTTP.md:58` の16,384バイト。「GET の末尾に同じ内容の JSON／Markdown リンク」の保証がこの境界で成立しない。
- **再現手順**：`Accept: text/html` で、次の Python 式が作る要求先に GET する。その HTML の二つのリンクを再要求する。

  ```python
  target = "/api/v1/verify?text=" + "%E3%81%82" * 1818 + "aa"
  # ASCII の要求先は16,384バイト。復号した text は1,820字。
  ```

- **期待**：200 HTML に、同じ入力を取得できるリンクを表示する。生成できない場合は、動かないリンクではなく再送方法を明示する。
- **実測**：local の実 HTTP で元の要求は **200 HTML**。JSON リンクは **16,396バイト→414**、Markdown リンクは **16,400バイト→414**。Guard の上限判定は正しい。HTML 側で自分のサーバが受けられないリンクを作っている。
- **重大度**：**P3**。要求先長が上限付近のときに表現切替が壊れる。
- **差分案**：生成先の要求先長を検査する。既定値の省略など、意味を変えずに短くできる場合だけ短くする。それでも超過する場合は JSON／Markdown の Accept を付けた再要求、または verify の POST 再送を案内する。リンクを必ず置くという SPEC／HTTP の文には、この例外の著者判断が必要。Guard の上限を引き上げて解決しない。16,384バイトと、その前後で両リンク先を検査する。

### F4 — Accept の先頭がワイルドカードでも、下位の Markdown が選ばれる

- **箇所・根拠**：`mekiki_reader/http_api.py:242` は先頭が HTML でなければ `wants_markdown()` に渡す。`SPEC.md:62` は q の降順・同順位は記載順で「`text/*` や `*/*` が先頭のときは JSON」と明記する。`docs/rules/HTTP.md:53` と `DECISIONS.md:446` は実装の Markdown フォールバックを記しており、正本との不整合がある。H02 の `tests/test_http.py:1062` はワイルドカードと下位 Markdown の組合せを試していない。
- **再現手順**：`GET /api/v1/papers` に、それぞれ `Accept: */*, text/markdown;q=0.5`、`Accept: text/*, text/markdown;q=0.5` を付ける。`format` は付けない。
- **期待**：正本と今回の検査条件に従い、両方とも **200 JSON**。
- **実測**：local・spaces とも **200 `text/markdown; charset=utf-8`**。単独の `*/*`／`text/*`、またはワイルドカードと下位 HTML の組合せは JSON になる。
- **重大度**：**P2**。正本が指定した Content-Type と本文形式を満たさない。HTML 注入の問題ではない。
- **差分案**：正本を維持する場合は、並べ替えた先頭がワイルドカードなら JSON にする分岐を Markdown フォールバックより前に置き、HTTP 規則と判断ログの対応も訂正する。下位 Markdown を優先する裁定を維持するなら SPEC の改版が必要であり、この検査では正本を読み替えない。前記二例、同順位で順序を反転した例、q の大小を反転した例、明示 `format` がそれらに優先する例を H02 に追加する。

### F5 — HTML 追加後の能力一覧・版・ETag の説明に旧記述が残る

- **箇所・根拠**：`mekiki_reader/http_api.py:279`、`README.md:327`、`docs/rules/HTTP.md:6`・`:45`、`SPEC.md:65`・`:67`。
- **再現手順**：`GET /api/v1/?format=json` の `accept` を読む。同じ一覧を HTML でも要求する。README の ETag 説明、HTTP 規則の状態・エラーの規則ID、SPEC の cache／規則文書の行を現物定数・`app.py:1015`・`:1066` と照合する。
- **期待**：経路一覧は三表現を案内し、ETag の列挙も HTML を含む。現行の規則IDは HTTP-1.3.0。SPEC v2.5.5 で確定した事項と、まだ施工判断の事項を区別できる。
- **実測**：一覧の `accept` は **`["application/json", "text/markdown"]`** の二つだけだが、同じ経路は HTML を返す。README と SPEC の cache 行も JSON／Markdown の列挙のまま。HTTP 規則の「形の誤り」は `RULES: HTTP-1.2.0` と記すが、実装は `H.HTTP_VERSION`＝HTTP-1.3.0 を使う。SPEC の規則文書行も HTTP-1.2.0 のまま。HTTP 規則の状態欄は POST 注記・Guard のエラー形式・選択の細部を施工判断と記す一方、現行 SPEC と判断ログは確定としている。
- **重大度**：**P3**。HTML の案内と契約の参照が不完全。本文の漏えいやキャッシュの混同は再現していない。
- **差分案**：経路一覧の `accept` に `text/html` を追加する。README／SPEC の ETag の列挙、現行規則ID、HTTP 規則の状態・エラー規則IDをそろえる。過去版の改版履歴は残し、現在の仕様として書く欄だけを訂正する。F4 の選択規則の不整合は単なる版表記の修正と分けて扱う。

### 指摘ゼロの項目を含む確認結果

以下の「問題なし」は、今回の HTML 範囲と実施した入力に限る。

| 検査点 | 結果・根拠 |
|---|---|
| 1. テキスト・属性のエスケープ | **見た・問題なし（タグ・属性注入の指摘0件）**。`esc()` は `html.escape(quote=True)`。出典・本文・表・候補・雛形・status・limitations・title・href を追跡した。search の q、claims の query、ID、引用文、エラー文字列相当の値にタグ閉じ、引用符、HTML 実体を入れ、HTML パーサーでも追加タグ・イベント属性を認めなかった。無効な ID 等が200 HTMLに到達しない場合は400／404 JSONとして確認した。URLとしての入力保持には F1〜F3 がある。 |
| 2. 反射入力とヘッダ | **見た・問題なし（指摘0件）**。CR／LF・タグ・引用符を含む入力のマーカーは応答ヘッダに混入しない。Content-Type は固定値、ETag はダイジェスト、Location は返さない。入力文字列は表示する場合にエスケープされる。POST の二経路は本文を含むリンクを作らず、再送注記を出す。 |
| 3. CSP・Referrer-Policy | **見た・問題なし（指摘0件）**。九経路の HTML 200 に `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'` と `Referrer-Policy: no-referrer`。GET 七経路の HTML 304 でも両ヘッダを保持し本文は空。追加の許可ディレクティブ、JS、外部資産、フォームはない。`app.py:1066` でヘッダを作った後に304を分岐する。 |
| 4. 表現の選択 | F4 を指摘。それ以外は **見た・問題なし**：三つの明示 format は Accept より優先し、通常のブラウザ Accept は HTML、q が低い HTML と先行する JSON の組合せは JSON、HTML の q=0 は HTML にしない。空・大文字違い・未知値・重複・不正符号化を含む format は400 JSON。 |
| 5. ETag・304・Vary | **見た・問題なし（表現混同の指摘0件）**。三表現のタグは異なり、JSON のタグを HTML 要求に送っても200。HTML の一致タグは304。`Vary: Accept` を200／304に保持し、Accept／If-None-Match の同名行の結合も維持する。GET は public/max-age=3600、POST は no-store。別URIで引数の符号化や既定値の明記だけが違うと、リンク文字列が違っても同じタグになる例はあるが、URIが異なる事実だけで誤ったキャッシュ再利用とは判定していない。 |
| 6. エラー形式 | **見た・問題なし（指摘0件）**。ツール外枠の400／404は HTML 要求時も JSON、no-store、ETagなし。`If-None-Match: *` があっても304にしない。Guard の早期拒否が text/plain であることは確定事項として指摘に含めない。 |
| 7. 文書との一致 | F1〜F5 に記した契約・記述の差がある。`README.md:287`、`docs/TUTORIAL.md:47`、`mekiki_reader/guide_page.py:93` の「ブラウザで HTML／format=markdown で Markdown」の案内、POST の再送注記、HTML の構成・ヘッダの説明は **見た・問題なし**。 |

### 再現・検査記録

- 既存試験は次の指定で **24 passed／43 deselected／2 warnings**。H02 と HTML 既知入力、表現追加に関係する H01 の MCP／JSON 突合および H04 のキャッシュ・同名ヘッダの回帰を含む。警告は既存 MCP クライアントの非推奨 API に関するもの。

  ```sh
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest tests/test_http.py \
    -p no:cacheprovider -q --tb=short \
    -k 'h02 or known_input_kinds_with_html or h01_http_json_is_the_mcp_json or h04_cache_headers_and_etag or h04_repeated'
  ```

- 追加の実 HTTP 検査は local・spaces の各モードで実施した。各モードで九経路×二方式（ブラウザの Accept／format=html）の **18 HTML 200**、GET 七経路×二方式の **14組の304と別表現タグの拒否**を確認した。spaces はローカルの試験起動器で再現しており、Hugging Face のエッジは検査していない。
- 各モードで追加の既知入力 **39件**を HTML 要求に適用：九経路それぞれの TE＋CL、重複 Host、16 KiB 超過の要求先（計27件）、POST 二経路それぞれの孤立サロゲート値・サロゲートの重複キー・text の重複キー・不正 UTF-8・過深 JSON（計10件）、65,537バイトの本文（計2件）。前二種類のヘッダは400、要求先超過は414、JSON の異常は400 JSON、本文超過は413。既存 HTML 試験と合わせ、重複 query・崩れた `%`・符号化されたサロゲート・3,000字入力も当てた。これらに5xxはなかった。
- メモリ内の描画検査では、全可変フィールドへの攻撃文字列に加え、実コーパス194要求の415本文／雛形区間を照合し、HTML の pre から復元した文が描画対象の文と一致した（規則上の末尾改行の処理を考慮）。
- F1・F2・F4 は local／spaces の実 HTTP で再現。F3 は local の実 HTTP で再現した。追加検査の監査には、試験器自身の接続を除いた外向き通信も、投入した識別マーカーの標準出力・標準エラーへの記録もなかった。
- CLAUDE 規則10〜12に従い、リポジトリ外の個人ファイル・シェル設定・鍵・環境変数一覧を読んでいない。監査ログは一時領域、Python の bytecode と pytest cache は無効化した。サーバは空きポートに自分で起動した PID だけを停止した。追加検査前後の `data/` 全ファイルの SHA-256 は一致。ソース・データ・既存試験は変更せず、コミットしていない。

## 差分案

各 F の差分案を実施する際は、次を同じ変更で固定する。本報告では適用していない。

| 対象 | 変更案と合格条件 |
|---|---|
| `mekiki_reader/http_api.py` の末尾リンク | F1・F2：引数名の同一性は復号後に判定し、値を URL 文脈で符号化した後に属性用 `esc()` を施す。reader の通信系 import 禁止は維持する。query が同じ値へ復元され、JSON／Markdown のリンク先で元と同じツール結果を得る。 |
| URL 長と案内 | F3：生成先にも16,384バイト上限を適用する。短縮できない場合の再送注記を SPEC／HTTP に明記する案を出し、合意後に描画へ反映する。正常な元要求を拒否したり、入力を切り詰めたりしない。 |
| `choose()` と規則の対応 | F4：ワイルドカード先頭の JSON を実装・規則・判断ログでそろえる。format の優先や既存の Markdown 単独指定は維持する。 |
| 経路一覧と説明 | F5：三表現の一覧・ETag の説明・現行 HTTP 規則ID・確定状態を同期する。 |
| H02 のリンク検査 | F1〜F3 の全入力を追加。href の文字列比較だけでなく、HTML エンティティを復元し、URLとして解釈して再要求する。期待する Content-Type、status、引用値、結果データを確認する。 `%66ormat`／`for%6Dat`／全字符号化、`#`／`%23`、16 KiB 境界を含める。 |
| H02 の構造検査 | 既存 `tests/test_http.py:946` の正規表現検査に加え、HTML パーサーでタグ・属性・本文を確認する。query を含む href、verify の language、search の k、各経路の format も入力位置の表に加える。 |
| 既知入力の回帰 | `tests/test_http.py:1098` の HTML 専用集合には重複ヘッダ・TE＋CL・64 KiB超・16 KiB超が入っていない。`:826` の集合と共通化してブラウザ Accept／format=html の両方へ適用する。今回の追加検査を永続化し、`status < 500` だけでなく400／413／414等の期待値と JSON／text/plain を固定する。 |
| CSP・キャッシュ・エラーの維持 | 九経路の200、GET七経路の304、JSONタグ→HTML200、ツール400／404→JSON、POST→リンクなし／no-store を一緒に回帰する。 |
