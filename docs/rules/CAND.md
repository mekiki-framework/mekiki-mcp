# CAND — 語句上の近接候補

| 項目 | 値 |
|---|---|
| 規則ID・版 | CAND-1.0.0 |
| 状態 | 提案（施工判断。Q92 の確定内容にもとづく） |
| 実装 | `mekiki_reader/tools.py`（`_parse_query`・`_match_lines`） |

候補は語句上の一部一致であって、類似の主張があることを意味しない（SPEC §5.5）。

## verify_quote が quote_not_found のとき

1. 入力を SEARCH-1.0.0 と同じ手順で断片に分ける（ひらがなだけ・記号だけの断片は捨てる）。入力は2000字まで許すので、**先頭から8断片**だけを使う（limitations に明記）。
2. 照合範囲は verify_quote と同じ（論文原文、または language=en なら T4 英訳の unit 範囲）。単位は行。
3. 断片が一つ以上一致した行を、SEARCH-1.0.0 の順位（語の種類数↓→直接一致↓→総出現数↓→論文順↑→行番号↑）で並べ、上位5件を candidates に出す。payload に `match: "none"`・`partial`・抜粋・一致位置を付ける。

## verify_quote で exact 一致があるとき（Q48）

同じ引用が別の箇所で正規化によってだけ一致する場合、その箇所を candidates に出す（上位5件・位置の順）。payload に `match: "normalized"`・`diffs`・`candidate_reason` を付け、limitations に `NEARBY:` を入れる。

## get_claim_record(query=…)

1. query を SEARCH-1.0.0 で断片に分ける（上限は LIMITS）。
2. 照合の単位は、各主張の claim・status・source_quote・not_claimed の各項目（not_claimed は一項目ずつ）。
3. 一つの単位に全断片が一致した主張を results（全語一致の多い順→直接一致→総出現数→台帳の順）、一部だけ一致した主張を candidates（上位5件）に出す。payload.match に一致した項目名・断片・経路・順位を付ける。
4. 全語一致がなければ no_lexical_match。limitations に「主張台帳は T5 のみ」を必ず入れる。
