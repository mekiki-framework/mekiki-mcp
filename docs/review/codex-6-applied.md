# Codex 独立検査⑥ の反映記録（対象コミット `e7b0671`）

| 項目 | 値 |
|---|---|
| 検査 | Codex（独立検査。指摘と差分案のみ）。範囲は HTML 表現（SPEC v2.5.5 §2.12・HTTP-1.3.0） |
| 対象 | `e7b06717bce2ac9cc2d3382e384774ca01c4aeac`（main） |
| 報告 | [codex-6-report.md](codex-6-report.md)（著者が配置。本文には手を入れていない） |
| 正本 | SPEC v2.5.6（F1〜F5 の裁定）・CLAUDE.md v1.3（規則10〜12） |
| 反映 | ブランチ `http6`（コミットの SHA は施工報告） |
| 規則の版 | HTTP-1.3.0（未配置）→ **HTTP-2.0.0**（F4 が配置版 1.2.0 の値を変えるため。判定は DECISIONS の「Codex⑥」の節） |

否定対照は、修正前（`e7b0671`）の `app.py` と `mekiki_reader/http_api.py` に戻して local モードで走らせ、落ちることを確かめてから修正版に戻した。

## 指摘ごとの反映

| 指摘 | 重大度 | 変更箇所 | 否定対照の試験 | 修正前で落ちた確認 |
|---|---|---|---|---|
| F1 生の `#` で末尾 link の引用が変わる | P2 | `mekiki_reader/http_api.py`：`quote`（自前の百分率符号化）を新設し、`alternate_links(route, path_values, values)` を検証済みの引数からの組み立て直しに変更。`app.py`：`_serve_api` が復号後の引数を渡す（POST は link なし） | `test_h02_links_rebuild_the_same_arguments[生の #]`・`[%23]`・`[引用符・&・+・非 ASCII（search）]`・`[…（claims）]`・`[+ は空白・%2B は +（verify・T4 英訳）]`・`[経路の値と language]`。link を HTML パーサーで取り出し、エンティティを復元し、`urllib.parse.urlsplit` で URL として解釈して（フラグメントは送らない）実際に要求する。元の要求が意味する引数で同じ入口を呼んだ結果と、JSON はバイト一致、Markdown は同じ外枠の描画と一致 | **「生の #」は落ちた**（link が `…it.#extra&format=json` になり `#` を含む）。`%23`・引用符／`&`／`+`／非 ASCII・language の5件は修正前でも通った（継ぎ足しでも符号化が保たれる入力。回帰の検出用として残す） |
| F2 符号化した `format` の名前が link に残り 400 | P3 | 同上（`format` は復号後の名前で除く） | `test_h02_links_rebuild_the_same_arguments[%66ormat]`・`[for%6Dat]`・`[全字符号化の名前]` | **3件とも落ちた**（link 先で `format` が重複して 400） |
| F3 上限内の要求から上限超えの link を作る | P3 | `alternate_links` が表現ごとに組み立てた要求行の長さを見て、超えれば URL を `None` に。`_html_page` が link の代わりに注記（`Accept` を付けて要求するか、verify は POST）を出す。短縮しない | `test_h02_links_respect_the_request_target_limit`：GET verify の要求先 16,367〜16,373・16,384 バイト（JSON の link が 16,383／16,384／16,385、Markdown の link が 16,383／16,384／16,385 になる点を含む）。置いた link は 200 で辿れ、超える表現は link なし＋注記。16,385 バイトの元の要求は従来どおり 414 | **落ちた**（16,369 バイトの要求で、Markdown の link が 16,385 バイトになるのに置かれた。修正前は長さを見ずに継ぎ足していた） |
| F4 ワイルドカード先頭でも下位の Markdown | P2 | `http_api.choose`：q の降順（同順位は記載順）の先頭一項目だけで決める。`wants_markdown` を削除。HTTP.md の「表現の選択」と DECISIONS の該当行を訂正 | `test_h02_accept_is_decided_by_the_first_item`：`*/*, text/markdown;q=0.5`・`text/*, text/markdown;q=0.5`→JSON、同順位の順序反転・q の大小反転、`application/json, text/markdown;q=0.5`→JSON、`text/markdown` 単独→Markdown、明示の `format` が三表現とも優先 | **落ちた**（`*/*, text/markdown;q=0.5` が Markdown） |
| F5 一覧・版・ETag の旧記述 | P3 | `http_api.index` の `accept` に `text/html`。README の ETag の説明（三表現）、HTTP.md の状態欄・形の誤りの規則 ID（`HTTP-2.0.0`）・ETag の行、規則一覧 | `test_h04_index_lists_three_representations` | **落ちた**（`accept` が二表現） |

## 試験の整備（差分案の表）

| 対象 | 反映 |
|---|---|
| H02 の構造検査 | `_assert_safe_html` に HTML パーサー（`html.parser.HTMLParser`）を足した：タグの許可表・属性の許可表（`html lang`・`meta charset/name/content`・`p class`・`a href` だけ）・href は `/api/v1/` の相対 URL でフラグメントと別のスキームを含まない。正規表現の検査も残した |
| 入力位置の表 | verify の `language`・search の `k`・各経路の `format`（GET 五経路と POST 二経路の問い合わせ）を足した。link の href（query を含む）は全ページでパーサーが検査する |
| 既知の入力の集合 | `_known_input_cases` の一つにまとめ、表現の指定なし・ブラウザの Accept・`format=html` の三通りで九経路に当てる（`test_h03_known_input_kinds_on_every_route[plain/accept/format]`）。期待値を固定：問い合わせ・本文の異常は 400 と JSON（invalid_input）、本文 64 KiB 超は 413・要求行 16 KiB 超は 414、Host の重複・Content-Length の値違いの重複・TE と CL の併記・生の非 ASCII は 400、これらは text/plain。深すぎる JSON（`[` ×60,000）を足した。旧 HTML 専用の集合（`test_h03_known_input_kinds_with_html`）は削除 |
| 回帰の束 | `test_h04_html_regression_bundle`：九経路の HTML 200（CSP・Referrer-Policy・両 link／POST は link なし・no-store・注記）、GET 七経路の HTML 304（CSP を保持・本文なし）、JSON のタグ→HTML 200、ツールの 400／404→JSON（`If-None-Match: *` でも 304 にしない・no-store・ETag なし・CSP なし）。ブラウザの Accept と `format=html` の両方で |

## 規則12の当て込み

`test_h03_known_input_kinds_on_every_route` を三通り（plain・accept・format）× local・spaces で通した。九経路とも
GET は 400・414、POST verify／check は 400・413・414 で、5xx はなく、Content-Type は期待どおり（JSON か text/plain）。

## SPEC との食い違い（直さず報告）

- SPEC v2.5.6 §2.12 の「規則文書」の行は `HTTP-1.3.0` と書く。F4 の版の判定（同じ節が施工に委ねた基準）で HTTP-2.0.0 にしたので、SPEC の版の表記と現物がずれる。
- SPEC v2.5.6 の「表現の選び方（v2.5.4）」の見出しと「HTTP-1.3.0（MINOR）」の記述も同様。
