# T4MAP — T4 英訳の位置対応

| 項目 | 値 |
|---|---|
| 規則ID・版 | T4MAP-1.0.0 |
| 状態 | 提案（施工判断。Q26〜Q28 の確定内容にもとづく） |
| 実装 | `mekiki_reader/corpus.py` の `build_translation_index`・`validate_translation_index`・`verify_internal_hashes` |

## 対応づけ

- 位置対応は `translations/T4.en.manifest.json` の sourceUnits（137件）だけを使う。
- 各 unit の節は、sourceLine を papers/T4.md の節範囲に当てて決める（`derived_anchor`）。記録の `unit.section` は保持するが、節の決定には使わない（注と参考文献の範囲の37単位で '6'、前付けの3単位で null のため。Q27）。
- 英訳側の位置は translationLineStart・translationLineEnd（126件。1 始まり・終端を含む）。wrapper（6件、description あり）と separator（5件、description なし）は英訳側の位置を持たない。
- 訳注：`<details class="translation-note" id="tn-NN">` の行から次の `</details>` の行まで（16件、各6行）。それぞれ1つの translated unit の範囲の内側にある（Q26）。

## ハッシュの算出（⑤で照合。internal_mismatch）

- sourceSha256 ＝ `sha256("\n".join(T4.md の行[s-1:e]))`（末尾に改行を付けない。コーパスの検証器が掛ける strip の有無で結果は変わらない：137件とも一致）。
- translationSegmentSha256 ＝ `sha256("\n".join(T4.en.md の行[s-1:e]) + "\n")`（末尾に LF を1個付ける。付けないと0件一致、付けると126件一致）。

## 構造の検査（index_invalid）

1. manifest の見出し：format・translationId（T4.en）・corpusVersion（3.5.0）・originalLanguage（ja）・inLanguage（en）・source.path・translation.markdown・source.doi と source.preprintVersion が T4 の値と一致。
2. unit は sourceLine の昇順で、原文の範囲が重ならない。T4.md の空でない行はすべていずれかの unit に覆われる。unit の範囲は1つの節に収まる。
3. translation* の3キーと targetId は、そろって有るか、そろって無い。位置を持たない unit は wrapper か separator。
4. 位置を持つ unit の英訳範囲は隙間なく続き、先頭行が `<!-- t4-source-unit:N -->`（N＝sourceLine）。targetId が範囲内に `id="…"` か `{#…}` として現れる。マーカーの総数は位置を持つ unit の数と一致。
5. 訳注の id は一意で、閉じており、translated の unit の中にある。訳注・原著者注（author-note-N）・参考文献（ref-N）の数が manifest の translatorNotes（16）・originalAuthorNotes（5）・referenceRecords（28）と一致。

英訳にしかない1〜22行と1098〜1105行は、どの unit にも属さない（Q27：明示要求時だけ別 ID で返す。施工段階2）。
