# LIMITS — 入力と結果の上限

| 項目 | 値 |
|---|---|
| 規則ID・版 | LIMITS-1.0.0 |
| 状態 | 提案（施工判断。Q56・Q60・Q84・Q85 の確定内容にもとづき、値は施工段階2で実測。source_excerpt の上限と通信層の表は 2026-09-18 に追記・Codex① P1-2・P2-4 を反映） |
| 実装 | `mekiki_reader/tools.py` の定数 |

| 対象 | 上限 | 超えたとき |
|---|---|---|
| ID（paper_id・anchor・claim_id） | 1〜128字。制御文字・`/`・`\`・`:`・`..`・先頭の `.` `~` は不可 | invalid_input（パスや URL の形）。それ以外の形式違反は unknown_id と近傍候補（NEAR。claim_id は invalid_input） |
| query（search_passages・get_claim_record） | 生で1000字、畳み込み後1〜200字、断片8個 | invalid_input（切り詰めない） |
| text（verify_quote・check_compressions） | 2000字 | invalid_input |
| k | 1〜20の整数（既定5。真偽値・文字列・小数は不可） | invalid_input |
| 引用の最小長（verify_quote） | 正規化後、仮名・漢字を含む入力は5字、それ以外は10字 | invalid_input |
| 引用の一致数（verify_quote） | 20件 | invalid_input。limitations に `TOTAL: total=n`（部分結果は返さない） |
| 近接候補（verify_quote の不一致・get_claim_record の query） | 5件 | 上位5件だけ返す |
| 一致位置（match_positions・matched） | 1結果につき20件 | 先頭20件と総数（`*_total`） |
| 差分（payload.diffs） | 1結果につき20件 | 先頭20件と総数（`diffs_total`） |
| 抜粋 | 最初の一致の前後100字 | 切った側に「…」 |
| 関連原文の抜粋（check_compressions の source_excerpt） | 1000字 | 末尾に「…」を付け `source_excerpt_truncated: true` |
| check_compressions の結果数 | 上限を置かない（一致したパターンの関連原文の数だけ出る）。**実測の最悪ケース：310字の入力で 100 結果・応答 184 KiB**（PATTERNS-0.2.1 の関連原文が100件のため、これが上限。0.2.1 で再計測しても同じ値。0.1.1 では 99 結果・183 KiB） | — |

## 通信層の上限（施工段階3・Q65・Q66。status には混ぜない）

| 対象 | 上限 | 超えたとき |
|---|---|---|
| 同時に実行する呼び出し | 4（`tools.py` ではなく `app.py` のセマフォ。七ツール・resources・prompts で共有） | 通信層のエラー（MCP の isError）。結果データは返さない |
| 要求本文 | 64 KiB。MCP と自己呼び出しの経路では**実際に届いたバイト数**で打ち切る（ほかの経路では本文に触れない） | HTTP 413 |
| 本文の到着 | 10 秒（表明した長さが届かないまま待たない） | HTTP 408 |
| 本文の長さの表明 | `Transfer-Encoding` と `Content-Length` の併記は不可（この検査はサーバ側）。`Content-Length` が ASCII 数字でない場合・値の違う重複・表明と実測の食い違いは HTTP の層（h11）が先に拒む。同じ値の重複は h11 が畳むので通る | HTTP 400 |
| Host ヘッダ | 127.0.0.1・localhost・::1（欠落・重複は不可。ポートは省略か十進1〜65535のときだけ認める） | HTTP 400 |
| 自己呼び出しの経路（`/gradio_api/queue/join`） | 受付 8（＝同時実行4＋4）。順番待ちに並べるのは 64 まで・待ち時間は20秒まで。Gradio の待ち行列は 72（＝8＋64。断るのはこちらの層にする） | 待機が 64 を超える／20秒を超える＝HTTP 503 |
| 回収されない結果 | 同じセッションにつき 64 件・4 MiB・120 秒。5秒ごとに掃除する | 期限や上限を超えた分は捨てる（`/queue/data` で取りに来なかった結果） |
| アップロードの大きさ | `max_file_size="1kb"`（経路自体は 403 で遮断） | HTTP 403 |
| CORS | `Origin` 付きの要求には許可ヘッダを一切返さない（上流の CORS 中間層を通しに差し替え、起動後に自分自身へ当てて確認） | 許可を返さない（要求自体は通る） |
| 待ち受け | 127.0.0.1 のみ・`max_threads=8` | — |

## 最小長の実測（2026-09-18・data/ のコミット 6748061）

規則：同梱した論文原文の空でない行（NORM-1.0.0 で正規化）から、長さ L の部分文字列を決まった間隔（日本語 31 字ごと・英語 97 字ごと）で取り出し、原文全体での出現回数を数える。出現回数の中央値が 1 になる最小の L を最小長とする。

| 範囲 | L | 標本 | 一意の割合 | 20回超の割合 | 中央値 |
|---|---|---|---|---|---|
| T4（日本語） | 4 | 905 | 0.481 | 0.151 | 2 |
| T4（日本語） | 5 | 901 | 0.609 | 0.084 | 1 |
| T1〜T3・T5（英語） | 9 | 3452 | 0.479 | 0.073 | 2 |
| T1〜T3・T5（英語） | 10 | 3441 | 0.563 | 0.048 | 1 |

「仮名・漢字を含む」の判定は、元の入力（NFC 合成後）に U+3040–U+30FF・U+3400–U+4DBF・U+4E00–U+9FFF の文字が一つでもあるかで行う（正規化で「.」が「。」に写っても日本語とはみなさない）。

### 実測（2026-09-18・Codex② の反映後）

`resources/read` を同時 24・32・64・80 本送っても全て `ok`（順番待ちの最大は 26・拒否は0件）。
結果を回収しない `/queue/join` を12本投げて放置すると、掃除が1セッションを捨てた。

## 処理時間（Q85・案A）

関数の内部では時間で打ち切らない。上の上限で計算量を有界にし、最悪ケースを実測して記録する。
実測（2026-09-18、CPython 3.13.15・arm64・5回の最大値）：起動（load_corpus と索引）0.47 秒。verify_quote（2000字・英語）44 ms、同（日本語）4 ms、同（language=en）13 ms、search_passages（8断片・k=20）36 ms、同（200字）15 ms、get_claim_record（query 8断片）13 ms、get_section（未登録・128字の NEAR）12 ms、check_compressions（2000字・試験パターン2件）1.1 ms、list_papers 1.9 ms。通信層の時間制限は施工段階3の実測後に判断する。

通信を含めた実測（2026-09-18・MCP の Streamable HTTP・同一機・5回の最大）：search_passages（8断片・k=20）80 ms、verify_quote（1990字・英語）21 ms、同（日本語2000字）14 ms、check_compressions（1200字）19 ms、list_papers 5 ms、get_reading_guide（all）3 ms。
