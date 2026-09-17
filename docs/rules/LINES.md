# LINES — 行の分割

| 項目 | 値 |
|---|---|
| 規則ID・版 | LINES-1.0.0 |
| 状態 | 提案（施工判断） |
| 実装 | `mekiki_reader/corpus.py` の `split_lines` |

- 同梱テキストを UTF-8（BOM なし）として読み、`"\n"` で分ける。末尾が `"\n"` なら、最後の空要素を1個だけ除く。
- 行番号は 1 始まり。範囲は終端を含む。
- 起動時に、この件数が `str.splitlines()` の件数と一致することを確かめる（U+2028・CR などの別の改行文字が混じれば index_invalid）。
- source_manifest の papers[].lines（442・376・251・261・325）と一致する（⑤で照合）。
