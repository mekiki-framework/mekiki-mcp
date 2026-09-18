条件：なし
モデル：Opus 5
日付：2026-09-18

# Mekiki Framework における Spec.cost

Spec.cost（specification cost）は、**課題の性質**です。何を作るべきかを決めるのに、その課題がドメイン専門性をどの程度必要とするか、を指します。実務者が持っている専門性そのものとは別の概念です。専門性を課題に使った結果として出てくる判断の中身（Spec.）とも別です。T1 §2.1 と T2 §2.1 は、この三つを区別しています。

## 三つの違い

| | 何か | 何に属するか | 根拠 |
|---|---|---|---|
| 実務者のドメイン専門性 | 訓練・実践、分野の資料や規範に触れることで蓄積された資源 | 実務者（人） | T2 L37、T1 L54 |
| Spec.cost | その資源を課題が必要とする度合い。専門性が足りなければ障壁になる | 課題 | T1 L54、T2 L37 |
| Spec. | 専門性を特定の課題に使った結果として出てくる具体的な判断。何を作るか、何を除くか、どの基準で質を評価するか。T1 図1 では「substrate」（基盤）と呼ばれる | 課題に専門性を使った結果 | T2 L37、T1 L423 |

## 原文（verify_quote で exact 一致を確認した引用のみ）

1. **T1 v1 §2.1（`t1-2-1`）L54：Spec.cost の定義**（照合 #11）
   Specification cost は "denotes the barrier arising from the domain expertise required to determine what should be built."
   私訳：何を作るべきかを決めるのに必要なドメイン専門性から生じる障壁。

2. **T1 v1 §2.1 L54：専門性との区別**（照合 #7）
   "Specification cost should be distinguished from domain expertise itself: domain expertise is a resource that the practitioner possesses; specification cost is the degree to which a task demands domain expertise."
   私訳：専門性は実務者が持つ資源であり、Spec.cost は課題が専門性を必要とする度合いである。

3. **T2 v2 §2.1（`t2-2-1`）L37：三つの概念**（照合 #12・#13・#14・#10）
   - Domain expertise は "is a resource that a practitioner possesses — accumulated through training, practice, and exposure to a field's materials and norms."
   - Specification cost は "is a property of the task: the degree to which the task demands that resource."
   - specification は "the term used on Figure 1 of the original article as "substrate"" で、"is what results when domain expertise is invested in a particular task: the concrete judgments about what should be built, what should be excluded, and by what criteria quality should be assessed."

4. **T1 v1 Figure 1（`t1-figure-1`）L423：substrate としての specification**（照合 #15）
   specification は "the domain expertise invested in deciding what should be built, how quality should be judged, and what should be excluded."

5. **T1 v1 §2.1 L54：Spec.cost の範囲**（照合 #8）
   "Specification cost is not reducible to requirements elicitation in the software engineering sense; it includes judgements that the domain expert may not be able to articulate as formal requirements but can recognise and evaluate when presented with candidate implementations."

## 解説（私の説明で、原文とは別）

以下の文は check_compressions（#16）に一度通しました。

> 実務者のドメイン専門性は実務者が持っている資源で、Spec.cost は課題の側の性質、Spec. は専門性を課題に使った結果として出てくる判断の中身です。Spec.cost は仕様書を書く手間のことではありません。実務者がすでに持っている判断の量のことでもありません。評価基準は別の成分として立てず、Spec.cost に含めます（T1 L54）。

- **該当 2 件の確認:** check_compressions の該当は P01「仕様書」と P02「判断の量」の 2 件でした。どちらも上の否定文の語に当たったものです。返ってきた THEORY_MAP.md L37–43 の抜粋は「Spec.cost は specification の別名ではなく、すでにある判断の量として記述しない」という趣旨です。見比べたところ、私の否定は同じ向きでした。
- **否定文の出典:** この二つの否定は論文本文の言い方ではありません。派生物である FOR_AI_READERS.md（L7–29）と THEORY_MAP.md の言い方です。論文本文でいちばん近いのは、上の引用 5「要件定義に還元されない」です。
- **略記の出典:** 「Spec.」「Spec.cost」という略記は、上の二つの派生物で確認しました。論文本文でこの略記を使っているかどうかは調べていません。
- **位置づけ（status）:** 主張台帳があるのは T5 だけです。今回の出典は T1 と T2 なので、get_claim_record は呼んでいません。

## ツール呼び出しと、返ってきた出典（返り値のまま）

16 回の呼び出しすべてで、`corpus_version` は 3.5.0、`source_commit` は `67480613108cf72c29d5691e3d7a6c7e6553eb9b`、`bundle_hash` は `40a09c5ba422582c951928f873f5729a420514a46409359559d7e6123c1224d5` でした。

```text
#1 get_reading_guide(part="core-terms") → status: ok
   paper_id: null / section_anchor: null
   {"char_end":null,"char_start":null,"json_pointer":null,"line_end":29,"line_start":7,"note":null,"path":"FOR_AI_READERS.md"}

#2 search_passages(query="specification cost", k=20) → status: ok（全語一致 52 行・上位 20 件）
   1  T1 t1-2-1      {"char_end":20,"char_start":2,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}
   2  T1 t1-5-6      {"char_end":193,"char_start":175,"json_pointer":null,"line_end":295,"line_start":295,"note":null,"path":"papers/T1.md"}
   3  T1 t1-5-1      {"char_end":243,"char_start":225,"json_pointer":null,"line_end":225,"line_start":225,"note":null,"path":"papers/T1.md"}
   4  T1 t1-abstract {"char_end":699,"char_start":681,"json_pointer":null,"line_end":14,"line_start":14,"note":null,"path":"papers/T1.md"}
   5  T1 t1-1        {"char_end":430,"char_start":412,"json_pointer":null,"line_end":40,"line_start":40,"note":null,"path":"papers/T1.md"}
   6  T1 t1-2-3      {"char_end":240,"char_start":222,"json_pointer":null,"line_end":85,"line_start":85,"note":null,"path":"papers/T1.md"}
   7  T1 t1-3-3      {"char_end":109,"char_start":91,"json_pointer":null,"line_end":135,"line_start":135,"note":null,"path":"papers/T1.md"}
   8  T1 t1-5-1      {"char_end":512,"char_start":494,"json_pointer":null,"line_end":217,"line_start":217,"note":null,"path":"papers/T1.md"}
   9  T1 t1-5-5      {"char_end":159,"char_start":141,"json_pointer":null,"line_end":267,"line_start":267,"note":null,"path":"papers/T1.md"}
   10 T1 t1-urgency  {"char_end":154,"char_start":136,"json_pointer":null,"line_end":319,"line_start":319,"note":null,"path":"papers/T1.md"}
   11 T1 t1-figure-1 {"char_end":697,"char_start":679,"json_pointer":null,"line_end":423,"line_start":423,"note":null,"path":"papers/T1.md"}
   12 T1 t1-keywords {"char_end":80,"char_start":62,"json_pointer":null,"line_end":20,"line_start":20,"note":null,"path":"papers/T1.md"}
   13 T1 t1-2-1      {"char_end":220,"char_start":202,"json_pointer":null,"line_end":50,"line_start":50,"note":null,"path":"papers/T1.md"}
   14 T1 t1-2-1      {"char_end":1010,"char_start":992,"json_pointer":null,"line_end":62,"line_start":62,"note":null,"path":"papers/T1.md"}
   15 T1 t1-2-2      {"char_end":749,"char_start":731,"json_pointer":null,"line_end":66,"line_start":66,"note":null,"path":"papers/T1.md"}
   16 T1 t1-2-3      {"char_end":45,"char_start":27,"json_pointer":null,"line_end":74,"line_start":74,"note":null,"path":"papers/T1.md"}
   17 T1 t1-2-3      {"char_end":200,"char_start":182,"json_pointer":null,"line_end":81,"line_start":81,"note":null,"path":"papers/T1.md"}
   18 T1 t1-2-3      {"char_end":287,"char_start":269,"json_pointer":null,"line_end":82,"line_start":82,"note":null,"path":"papers/T1.md"}
   19 T1 t1-2-3      {"char_end":94,"char_start":76,"json_pointer":null,"line_end":87,"line_start":87,"note":null,"path":"papers/T1.md"}
   20 T1 t1-3-1      {"char_end":26,"char_start":8,"json_pointer":null,"line_end":105,"line_start":105,"note":null,"path":"papers/T1.md"}

#3 get_section(paper_id="T1", anchor="t1-2-1") → status: ok
   T1 / t1-2-1 / {"char_end":null,"char_start":null,"json_pointer":null,"line_end":63,"line_start":48,"note":null,"path":"papers/T1.md"}

#4 get_section(paper_id="T2", anchor="t2-2-1") → status: ok
   T2 / t2-2-1 / {"char_end":null,"char_start":null,"json_pointer":null,"line_end":38,"line_start":35,"note":null,"path":"papers/T2.md"}

#5 get_section(paper_id="T1", anchor="t1-figure-1") → status: ok
   T1 / t1-figure-1 / {"char_end":null,"char_start":null,"json_pointer":null,"line_end":424,"line_start":419,"note":null,"path":"papers/T1.md"}

#6 verify_quote(paper_id="T1", text="Specification cost denotes the barrier …") → status: quote_not_found, match: none, results: []
   candidates（一致ではない・5件すべて match: none）: T1 t1-2-1 L54 / T1 t1-1 L40 / T1 t1-abstract L14 / T1 t1-figure-1 L423 / T1 t1-6 L301

#7 verify_quote(paper_id="T1", text="Specification cost should be distinguished …") → status: ok, match: exact
   T1 / t1-2-1 / {"char_end":1227,"char_start":1016,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}

#8 verify_quote(paper_id="T1", text="Specification cost is not reducible …") → status: ok, match: exact
   T1 / t1-2-1 / {"char_end":1015,"char_start":740,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}

#9 verify_quote(paper_id="T2", text="Domain expertise is a resource … Specification cost is a property …") → status: quote_not_found, match: none, results: []
   candidates（一致ではない・5件すべて match: none）: T2 t2-2-1 L37 / T2 t2-2-3 L63 / T2 t2-4-4 L143 / T2 t2-abstract L13 / T2 t2-1 L21

#10 verify_quote(paper_id="T2", text="is what results when domain expertise …") → status: ok, match: exact
   T2 / t2-2-1 / {"char_end":676,"char_start":480,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}

#11 verify_quote(paper_id="T1", text="denotes the barrier arising …") → status: ok, match: exact
   T1 / t1-2-1 / {"char_end":120,"char_start":23,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}

#12 verify_quote(paper_id="T2", text="is a resource that a practitioner possesses …") → status: ok, match: exact
   T2 / t2-2-1 / {"char_end":290,"char_start":158,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}

#13 verify_quote(paper_id="T2", text="is a property of the task …") → status: ok, match: exact
   T2 / t2-2-1 / {"char_end":390,"char_start":312,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}

#14 verify_quote(paper_id="T2", text="the term used on Figure 1 of the original article as \"substrate\"") → status: ok, match: exact
   T2 / t2-2-1 / {"char_end":477,"char_start":413,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}

#15 verify_quote(paper_id="T1", text="the domain expertise invested in deciding …") → status: ok, match: exact
   T1 / t1-figure-1 / {"char_end":523,"char_start":401,"json_pointer":null,"line_end":423,"line_start":423,"note":null,"path":"papers/T1.md"}

#16 check_compressions(text=<解説の文>) → status: ok（承認済みパターン 49 件・該当 2 件・結果 3 件）
   P01「仕様書」   T1 / t1-2-1 / {"char_end":null,"char_start":null,"json_pointer":null,"line_end":63,"line_start":48,"note":null,"path":"papers/T1.md"}
   P01「仕様書」   null / null / {"char_end":null,"char_start":null,"json_pointer":null,"line_end":43,"line_start":37,"note":null,"path":"THEORY_MAP.md"}
   P02「判断の量」 T1 / t1-2-1 / {"char_end":null,"char_start":null,"json_pointer":null,"line_end":63,"line_start":48,"note":null,"path":"papers/T1.md"}
```

## 気づいた点

- **検索の上位 20 件はすべて T1 でした。** 全 52 行のうち、T2 の行は上位 20 件に入りませんでした。T2 §2.1 は、ガイド（#1）が示していた場所をもとに読みました。
- **照合で 2 件が `quote_not_found` になりました**（#6 と #9）。原文の強調記号（`**…**`、`*…*`）を外して渡したことが原因です。返り値の limitations にも、強調記号のない引用は正規化の対象外だと書かれています。この 2 件は引用として使っていません。強調語を含まない断片で照合し直し、#11〜#15 で exact 一致を確認しました。

今回は結果を表示しただけで、ファイルには何も書いていません。`docs/acceptance/e01/` に検収記録として残す場合は指示をください。
