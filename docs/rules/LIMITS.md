# LIMITS — 入力と結果の上限

| 項目 | 値 |
|---|---|
| 規則ID・版 | LIMITS-1.0.0 |
| 状態 | 提案（施工判断。Q56・Q60・Q84・Q85 の確定内容にもとづき、値は施工段階2で実測。source_excerpt の上限は 2026-09-18 に追記） |
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

## 通信層の上限（施工段階3・Q65・Q66。status には混ぜない）

| 対象 | 上限 | 超えたとき |
|---|---|---|
| 同時に実行する呼び出し | 4（`tools.py` ではなく `app.py` のセマフォ） | 通信層のエラー（MCP の isError）。結果データは返さない |
| 要求本文 | 64 KiB | HTTP 413。長さ不明の chunked は 411 |
| Host ヘッダ | 127.0.0.1・localhost・::1 | HTTP 400 |
| アップロードの大きさ | `max_file_size="1kb"`（経路自体は 403 で遮断） | HTTP 403 |
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

## 処理時間（Q85・案A）

関数の内部では時間で打ち切らない。上の上限で計算量を有界にし、最悪ケースを実測して記録する。
実測（2026-09-18、CPython 3.13.15・arm64・5回の最大値）：起動（load_corpus と索引）0.47 秒。verify_quote（2000字・英語）44 ms、同（日本語）4 ms、同（language=en）13 ms、search_passages（8断片・k=20）36 ms、同（200字）15 ms、get_claim_record（query 8断片）13 ms、get_section（未登録・128字の NEAR）12 ms、check_compressions（2000字・試験パターン2件）1.1 ms、list_papers 1.9 ms。通信層の時間制限は施工段階3の実測後に判断する。

通信を含めた実測（2026-09-18・MCP の Streamable HTTP・同一機・5回の最大）：search_passages（8断片・k=20）80 ms、verify_quote（1990字・英語）21 ms、同（日本語2000字）14 ms、check_compressions（1200字）19 ms、list_papers 5 ms、get_reading_guide（all）3 ms。
