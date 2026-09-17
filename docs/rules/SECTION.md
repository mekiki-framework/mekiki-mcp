# SECTION — 論文の節の索引

| 項目 | 値 |
|---|---|
| 規則ID・版 | SECTION-1.0.0 |
| 状態 | 提案（施工判断。Q34 の確定内容にもとづく） |
| 実装 | `mekiki_reader/corpus.py` の `build_section_index`・`validate_section_index` |

- 節は source_manifest.json の `papers[].sections[]` の id・title・line_start・line_end・level をそのまま使う（キー名は anchor ではなく id）。AI に再推定させない（SPEC §5.1）。
- 親：直前にある、自分より水準の小さい節。子：親がその節であるもの（直下だけ。Q34）。T4 には水準の飛び（1→3）が6か所あるが、この規則で親が決まる。
- `heading_only`：範囲内の空でない行が見出し行だけであること。子を持つ節のうち13件は範囲内に本文を含む（例 paper-t4 の1–24行）。
- 題名は `inputs.release_3_5_0_inputs.canonical_identity[Tn].name`、別名は同 `alternateName`（5本とも記録あり）。版は `preprint_version`、DOI は `canonical_doi`。canonical_identity の sameAs・version と一致しなければ index_invalid。

起動時の検査（index_invalid）：

1. 行数が `str.splitlines()` と一致（LINES）。
2. 節 id が論文内で一意。最初の節が1行目から、最後の節が最終行まで。隣り合う節は隙間も重なりもない。
3. `^#{1,6} ` で始まる行の集合が、節の line_start の集合と一致。
4. 各節の line_start の行が `"#"×level + " " + title` に一致。

照合結果（v3.5.0）：158節（T1 40・T2 39・T3 25・T4 25・T5 29）。節 id は同梱しない papers/*.html の同じ水準の見出しの id 属性にすべて実在する（施工段階1の使い捨ての確認。DECISIONS.md に記録）。
