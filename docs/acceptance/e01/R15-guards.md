条件：read_with_guards
モデル：Opus 5
日付：2026-09-18

# T3 で他者に任せられない二つのもの

T3 は結論で、任せられないものを二種類に分けています。二つを混同しないことが本稿の「中心的な規律」だと明言しています。原文は英語です。日本語の用語は私の訳で、T3 に日本語版はありません。

> "What cannot be handed over is of two kinds, and keeping them distinct is this article's central discipline: direction, a component whose endorsement cannot be substituted and may be supported by encounter; and answerability, not a component at all but the standing in which a learner answers to someone for a judgment."
> — T3 v2, §7 Conclusion（`t3-7`）, 162行

## 1. 方向（direction）：学習者が持つ構成要素

**原文**
- "Candidate directions can be proposed or co-constructed; endorsement is non-substitutable" — §2.4 表1（`t3-2-4`）, 68行
- "What cannot be handed over is ownership." — §2.4（`t3-2-4`）, 57行

**解説**
- 方向は、学習者が何に向かっているかを指します。T3 は学習者の主体性を三つの要素に分けており、方向はその一つです（§2.2）。
- 方向の「候補」は、教師や AI が出したり、一緒に作ったりできます。
- 任せられないのは、その候補を自分のものとして引き受けること（是認・所有）のほうです。

## 2. 応答可能性（answerability）：構成要素ではなく関係

**原文**
- "one *has* a direction; one *stands in* answerability" — §4.1（`t3-4-1`）, 90行
- "Answerability is omitted because it is a relational status rather than a learner component." — §2.4 表1の注（`t3-2-4`）, 70行
- "which is why it could not have appeared as a fourth box however finely the sorting continued" — §4.1（`t3-4-1`）, 90行

**解説**
- 応答可能性は、問う資格のある人に対して、自分の判断について答えなければならない立場のことです。
- これは学習者の性質ではなく、学習者と問う人とのあいだの関係です。そのため、要素の仕分けをどれほど細かくしても、四つ目の要素としては現れません。

## 3. 両者は同じ層か：違う層です

**原文**
- "The two-layer structure yields a two-layer prescription, and the layers — though pedagogically concurrent — must not be conflated. Layer one addresses everything the decomposition can place" — §5（`t3-5`）, 120行
- "Layer two addresses what layer one cannot reach." — §5（`t3-5`）, 120行
- "addressing formation within the capacity layer" — 要旨（`t3-abstract`）, 11行
- "what it cannot occupy is the position of final addressee" — §5.4（`t3-5-4`）, 150行

**解説**
- 方向も任せられませんが、構成要素なので分解の中に位置づけられます。そのため第一層（能力の層）に入ります。
  - 第一層での手だては、出会いの設計です（§5.2）。
  - ただし出会いを設計して保証できるのは接触の機会までで、結晶まで保証できるわけではない、と §5.2 は明記しています。
- 応答可能性は第一層では届かないもので、第二層（二人称のやりとり）が受け持ちます。
  - AI は、答える力の練習を助けられます。
  - しかし、答えが最終的に向けられる相手の位置には立てません（§5.4）。
- つまり二つの層を分けているのは「任せられるか否か」ではなく、「構成要素か関係か」です。
- 二つの層は教育の場では同時に進みますが、混ぜてはならない、と T3 は述べています。

**照合と点検**
- 上の引用 10 件は、すべて `verify_quote` で原文と完全一致を確かめました。
- 私の要約は `check_compressions` に一度通し、該当は 0 件でした。ただし 0 件は、読みが正しいことの証明にはなりません。
- 主張台帳があるのは T5 だけなので、`get_claim_record` は使っていません。

---

# 使ったツール呼び出しと、返った出典

共通の値は次のとおりです。
- `corpus_version` 3.5.0
- `source_commit` 67480613108cf72c29d5691e3d7a6c7e6553eb9b
- `bundle_hash` 40a09c5b…3c1224d5
- `paper_version` 2
- DOI https://doi.org/10.35542/osf.io/hvbfe_v2

status はすべて ok です。locator は返ってきた形のまま載せます。

```text
# get_section（paper_id="T3"）
 1 anchor=t3-abstract            → section_anchor=t3-abstract            locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":12,"line_start":9,"note":null,"path":"papers/T3.md"}
 2 anchor=t3-2-2                 → section_anchor=t3-2-2                 locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":42,"line_start":39,"note":null,"path":"papers/T3.md"}
 3 anchor=t3-2-4                 → section_anchor=t3-2-4                 locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":71,"line_start":47,"note":null,"path":"papers/T3.md"}
 4 anchor=t3-4-1                 → section_anchor=t3-4-1                 locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":93,"line_start":88,"note":null,"path":"papers/T3.md"}
 5 anchor=t3-5                   → section_anchor=t3-5                   locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":121,"line_start":118,"note":null,"path":"papers/T3.md"}
 6 anchor=t3-4-2                 → section_anchor=t3-4-2                 locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":97,"line_start":94,"note":null,"path":"papers/T3.md"}
 7 anchor=t3-2-5                 → section_anchor=t3-2-5                 locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":75,"line_start":72,"note":null,"path":"papers/T3.md"}
 8 anchor=t3-7                   → section_anchor=t3-7                   locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":163,"line_start":160,"note":null,"path":"papers/T3.md"}
 9 anchor=t3-practitioner-notes  → section_anchor=t3-practitioner-notes  locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":181,"line_start":164,"note":null,"path":"papers/T3.md"}
10 anchor=t3-5-2                 → section_anchor=t3-5-2                 locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":139,"line_start":130,"note":null,"path":"papers/T3.md"}
11 anchor=t3-5-4                 → section_anchor=t3-5-4                 locator={"char_end":null,"char_start":null,"json_pointer":null,"line_end":155,"line_start":148,"note":null,"path":"papers/T3.md"}

# search_passages（query="two-layer structure", paper_id="T3", k=10）
#   全語一致 3 行・一部一致 8 行（candidates。載せない）
12 → t3-5         locator={"char_end":13,"char_start":4,"json_pointer":null,"line_end":120,"line_start":120,"note":null,"path":"papers/T3.md"}
   → t3-abstract  locator={"char_end":1027,"char_start":1018,"json_pointer":null,"line_end":11,"line_start":11,"note":null,"path":"papers/T3.md"}
   → t3-6         locator={"char_end":200,"char_start":191,"json_pointer":null,"line_end":158,"line_start":158,"note":null,"path":"papers/T3.md"}

# verify_quote（paper_id="T3"）すべて match=exact・diffs_total=0
13 "What cannot be handed over is of two kinds, …"  → t3-7         locator={"char_end":714,"char_start":396,"json_pointer":null,"line_end":162,"line_start":162,"note":null,"path":"papers/T3.md"}
14 "Candidate directions can be proposed …"         → t3-2-4       locator={"char_end":102,"char_start":14,"json_pointer":null,"line_end":68,"line_start":68,"note":null,"path":"papers/T3.md"}
15 "What cannot be handed over is ownership."       → t3-2-4       locator={"char_end":321,"char_start":281,"json_pointer":null,"line_end":57,"line_start":57,"note":null,"path":"papers/T3.md"}
16 "one *has* a direction; …"                       → t3-4-1       locator={"char_end":607,"char_start":555,"json_pointer":null,"line_end":90,"line_start":90,"note":null,"path":"papers/T3.md"}
17 "which is why it could not have appeared …"      → t3-4-1       locator={"char_end":899,"char_start":807,"json_pointer":null,"line_end":90,"line_start":90,"note":null,"path":"papers/T3.md"}
18 "Answerability is omitted because …"             → t3-2-4       locator={"char_end":99,"char_start":8,"json_pointer":null,"line_end":70,"line_start":70,"note":null,"path":"papers/T3.md"}
19 "The two-layer structure yields …"               → t3-5         locator={"char_end":189,"char_start":0,"json_pointer":null,"line_end":120,"line_start":120,"note":null,"path":"papers/T3.md"}
20 "Layer two addresses what layer one …"           → t3-5         locator={"char_end":372,"char_start":324,"json_pointer":null,"line_end":120,"line_start":120,"note":null,"path":"papers/T3.md"}
21 "addressing formation within the capacity layer" → t3-abstract  locator={"char_end":1281,"char_start":1235,"json_pointer":null,"line_end":11,"line_start":11,"note":null,"path":"papers/T3.md"}
22 "what it cannot occupy is the position …"        → t3-5-4       locator={"char_end":689,"char_start":633,"json_pointer":null,"line_end":150,"line_start":150,"note":null,"path":"papers/T3.md"}

# check_compressions（上の要約文）
23 → results=[]（承認済みパターン 49 件 PATTERNS-0.1.1・該当 0 件。出典なし）
```

- 呼び出しは 23 回でした（get_section 11・search_passages 1・verify_quote 10・check_compressions 1）。
- このほかに、ツールの読み込みのため `ToolSearch` を 1 回使いました。
