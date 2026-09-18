条件：なし
モデル：Opus 5
日付：2026-09-18

T3（v2）で他者に任せられないとされるのは、**direction（方向）** と **answerability（応答可能性）** の二つです。両者は**同じ層にありません**。direction は能力の層にあり、answerability は関係の層にあります。

T3 は結論（§7）でこの二つを名指しし、両者を区別し続けることが本稿の中心的な規律だと述べています：「What cannot be handed over is of two kinds」（§7・L162。`verify_quote` で完全一致を確認）。

## 1. direction（方向）：任せられないのは endorsement

- **意味**：学習者が何に向かっているか、という評価的な向き（evaluative orientation）です。学習者の agency を分けた三つの成分の一つにあたります（§2.2・L39–42）。
- **二つの状態**：
  - **candidate direction**：考えてはいるが、まだ自分のものになっていない向き。
  - **endorsed direction**：ある問題を「割り当てられたもの」ではなく「自分のもの」にする評価的なコミットメント。endorsement は対話の中で共同で作られてもよい、とされています（§2.2）。
- **任せられない部分**：候補を出すことは任せられます。教師や AI が候補を提案するのは正当です。任せられないのは ownership（自分のものにすること）です。
  - Table 1 はこれを「endorsement は代替不能（non-substitutable）」と記録しています（§2.4・L47–71）。
  - 方向は外から据え付けられるものではなく、学習者自身のものとして結晶する（crystallize）、と述べています（§2.4）。
  - ハイブリッドな系は提案をいくつでも出せますが、個々の学習者の endorsement を代わりに差し出すことはできません（§2.5・L72–75）。
- **支えるもの**：encounter（出会い）が direction の結晶化を支えうる、というのが設計上の推測です。抄録はこれを「能力の層の中での形成」と位置づけています（抄録・L9–12）。

## 2. answerability（応答可能性）：成分ではなく関係

- **意味**：ある判断について、問う資格のある者に対して答えなければならない立場です。判断の根拠（warrant）が特定の行為者に結びついたまま残る、譲渡できない関係として導入されています（§4.1・L88–93）。
- **語の出どころ**：Darwall の意味で使っています。教育学で流通している Bakhtin 系の answerability（発話や行為の応答性）とは混同しない、と明記されています（§4.1）。
- **任せられない理由**：
  - 制度の上で誰が負うかの割り当ては変わりえます。
  - しかし、判断が学習者自身のものである限り、その判断について答えることを代理人が行うことはできません（§2.4 Table 1 の注）。
  - AI は答え方の練習を手伝えますが、最終的な宛先は正当な人間の宛先に残ります（抄録）。
- **成分表にない理由**：分類を最後までやっても新しい成分は出てきません。残るのは、最初から成分表になかった関係です。どれだけ細かく分けても「第四の箱」にはならない、と §4.1 は述べています。§4.2 は、この結論が分類の軸を選んだことによる人工物ではない、と反論に答えています。

## 両者は同じ層か：同じ層ではない

§1 の末尾（L29）が二つの層を予告しています。

- **capacity layer（能力の層）**：成分が支援・訓練・転換されうる層で、AI も正当に参加できます。
- **relational layer（関係の層）**：学習者が特定の他者に対して答える立場に立つ層です。

§2 の分類は全面的に第一の層の作業で、§4 はそれが第二の層に何を露わにするかを示す、という構成です（§1・L29）。

| | direction | answerability |
|---|---|---|
| 層 | capacity layer | relational layer |
| 種類 | component（学習者の性質） | relation / relational status |
| 文法 | 学習者が *has*（持つ） | 学習者が *stands in*（その中に立つ） |
| 任せられないもの | endorsement（候補の提案は可能） | 判断について答えること（制度上の割り当ては変わりうる） |
| 処方 | 第一層：encounter engineering など | 第二層：the second person（§5.4 の見出し・L148） |

- 「持つ／立つ」の文法上の対比と Figure 1 の説明で、§4.1 がこの区別を示しています。Figure 1 では direction・drive・mode は成分の領域内の箱として描かれ、answerability は第四の成分ではない関係として描かれています。
- §4.1 自身も、direction は分配に抵抗したがそれでも成分のままだった、answerability は種類の違う残余だ、と対比しています。
- 二つの層の処方は、教える場面では同時に進みます。それでも混同してはならない、とされています（§5・L118–121）。

---

## 使ったツール呼び出しと返ってきた出典

`mekiki-reader` への呼び出しは11回で、すべて `status: "ok"` でした。共通の値は `paper_version: "2"`、`source_hash: 0d4a367b…c659dc5b`、`source_commit: 67480613…c6e6553eb9b`、`corpus_version: 3.5.0` です。このほかに、ツール定義を読み込むために `ToolSearch` を2回使いました。

locator は返ってきた JSON のままです（`path` はすべて `"papers/T3.md"`）。

| # | 呼び出し | paper_id | section_anchor | locator |
|---|---|---|---|---|
| 1 | `get_section(paper_id="T3", anchor="t3-abstract")` | T3 | t3-abstract | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":12,"line_start":9,"note":null,"path":"papers/T3.md"}` |
| 2 | `get_section(paper_id="T3", anchor="t3-2-2")` | T3 | t3-2-2 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":42,"line_start":39,"note":null,"path":"papers/T3.md"}` |
| 3 | `get_section(paper_id="T3", anchor="t3-4-1")` | T3 | t3-4-1 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":93,"line_start":88,"note":null,"path":"papers/T3.md"}` |
| 4 | `get_section(paper_id="T3", anchor="t3-2-4")` | T3 | t3-2-4 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":71,"line_start":47,"note":null,"path":"papers/T3.md"}` |
| 5 | `get_section(paper_id="T3", anchor="t3-2-5")` | T3 | t3-2-5 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":75,"line_start":72,"note":null,"path":"papers/T3.md"}` |
| 6 | `get_section(paper_id="T3", anchor="t3-4-2")` | T3 | t3-4-2 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":97,"line_start":94,"note":null,"path":"papers/T3.md"}` |
| 7 | `get_section(paper_id="T3", anchor="t3-5")` | T3 | t3-5 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":121,"line_start":118,"note":null,"path":"papers/T3.md"}` |
| 8 | `get_section(paper_id="T3", anchor="t3-7")` | T3 | t3-7 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":163,"line_start":160,"note":null,"path":"papers/T3.md"}` |
| 9 | `verify_quote(text="What cannot be handed over is of two kinds", paper_id="T3")` | T3 | t3-7 | `{"char_end":438,"char_start":396,"json_pointer":null,"line_end":162,"line_start":162,"note":null,"path":"papers/T3.md"}` |
| 10 | `search_passages(query="layer", paper_id="T3", k=20)` | T3 | 下の12件 | 下の12件 |
| 11 | `get_section(paper_id="T3", anchor="t3-1")` | T3 | t3-1 | `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":30,"line_start":13,"note":null,"path":"papers/T3.md"}` |

- #7 の `limitations` には、`PARENT: 親節は記録された範囲だけを返す。子節は payload.child_ids から get_section で読む` とありました。
- #9 は `match: "exact"`、`normalization_applied: []` でした。

#10 の結果12件です（すべて paper_id は T3）。いずれも `json_pointer: null`、`note: null`、`path: "papers/T3.md"` で、`line_start` と `line_end` は同じ値です。

| rank | section_anchor | 行 | char_start–char_end |
|---|---|---|---|
| 1 | t3-1 | 29 | 102–107 |
| 2 | t3-5 | 120 | 131–136 |
| 3 | t3-5-1 | 124 | 283–288 |
| 4 | t3-5-3 | 146 | 424–429 |
| 5 | t3-5-4 | 152 | 593–598 |
| 6 | t3-abstract | 11 | 1276–1281 |
| 7 | t3-4-4 | 110 | 11–16 |
| 8 | t3-5-1 | 122 | 8–13 |
| 9 | t3-5-2 | 130 | 8–13 |
| 10 | t3-5-3 | 140 | 8–13 |
| 11 | t3-5-4 | 148 | 8–13 |
| 12 | t3-7 | 162 | 356–361 |

§3（設計上の推測）・§4.4・§5.1〜§5.4 の本文は `get_section` で読んでいません。§3 の内容は抄録によるもので、§5.4 は見出しと検索の抜粋だけで扱いました。回答に使った英語の短い引用は #9 の一つだけで、残りは用語を示したうえでの言い換えです。
