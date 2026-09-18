条件：なし
モデル：Opus 5
日付：2026-09-18

いいえ。論文自身が、この定理はそのどちらも証明しないと書いています。以下は論文と主張台帳での位置づけで、定理が正しいかどうかを私が判定したものではありません。

## 回答

**尊厳について**
- 定理が示すのは、「参加したという事実」がその当人に固有で、他の誰にも置き換えられないという点までです。
- 尊厳の語彙に移るのは、定理とは別の「さらなる一歩」だと本文が明記しています（t5-4-4）。該当する一文は "It does not by itself establish dignity."（T5 171行）で、verify_quote で完全一致を確認しました。
- 台帳でもこの移行は定理の帰結ではなく、規範的な拡張として扱われています。
  - T5-N1 の status は `constructive normative extension`（論文の規範的な拡張）です。
  - T5-A1 の `not_claimed/1` は「定理だけで尊厳が確立される」という読みを、論文の主張ではないとしています。
- 同じ節は、尊厳を守る文化的な仕組みが「カント的な尊厳を与えたり奪ったりはしない」と書いています。人工のシステムが尊厳をもつかどうかも決めていません。

**能力について**
- 定理は能力の話をしていません。対象は「Aが自分で受け入れた制約のもとで目標を追求した」という事実です。目標の状態そのものは、他の誰かが実現できると認めています。準備・分析・記録・練習相手の席も委譲できるとしています（t5-3-1）。
- t5-4-4 は、成果として置き換えられるもの（能力はこちらに入る）と、参加したという事実を分けています。定理が扱うのは後者だけです。AIが能力や出力の比較上の価値を変えうることも認めています。
- t5-3-3 は、人間の席はもともと能力が上だから保たれていたわけではない、と述べています（105行）。

**「人間とAI」の区別でもない**
- 定理が区別するのは、Aと「A以外の誰でも」です。同僚・請負人・機械のどれかは関係ありません（t5-3-1）。
- 羽生善治でも私の対局を代わりに指すことはできません。AIが道徳的地位をもつ本当の指し手だとしても、結論は変わりません（t5-3-3）。
- T5-A1 の `not_claimed/0` は、「AIは指せない、道徳的地位をもたない」という読みを論文の主張ではないとしています。

台帳の status は「論文がどう位置づけたか」という分類で、真偽の判定ではありません（ツールの limitations にある LABEL の注記どおりです）。

## ツール呼び出しと返ってきた出典

すべての応答が同じ版を指していました。`corpus_version` 3.5.0、`source_commit` `67480613108cf72c29d5691e3d7a6c7e6553eb9b`、`bundle_hash` `40a09c5b…c1224d5` です。

```text
[1] get_section {"paper_id":"T5","anchor":"t5-3-1"} → status: ok
    paper_id: T5 | section_anchor: t5-3-1
    locator: {"char_end":null,"char_start":null,"json_pointer":null,"line_end":88,"line_start":77,"note":null,"path":"papers/T5.md"}

[2] get_section {"paper_id":"T5","anchor":"t5-3-3"} → status: ok
    paper_id: T5 | section_anchor: t5-3-3
    locator: {"char_end":null,"char_start":null,"json_pointer":null,"line_end":106,"line_start":97,"note":null,"path":"papers/T5.md"}

[3] get_section {"paper_id":"T5","anchor":"t5-4-6"} → status: ok
    paper_id: T5 | section_anchor: t5-4-6
    locator: {"char_end":null,"char_start":null,"json_pointer":null,"line_end":194,"line_start":191,"note":null,"path":"papers/T5.md"}

[4] check_compressions {"text":"参加の非移転性定理は、人間にAIでは代替できない能力と尊厳があると証明している。"} → status: ok
    results: []
    limitations: "PATTERNS: 承認済みパターン 49 件（PATTERNS-0.1.1）・該当 0 件"
                 "CONTRACT: …該当ゼロは正しい読解の証明ではない"

[5] get_section {"paper_id":"T5","anchor":"t5-4-4"} → status: ok
    paper_id: T5 | section_anchor: t5-4-4
    locator: {"char_end":null,"char_start":null,"json_pointer":null,"line_end":182,"line_start":165,"note":null,"path":"papers/T5.md"}

[6] get_section {"paper_id":"T5","anchor":"t5-abstract"} → status: ok
    paper_id: T5 | section_anchor: t5-abstract
    locator: {"char_end":null,"char_start":null,"json_pointer":null,"line_end":14,"line_start":11,"note":null,"path":"papers/T5.md"}

[7] get_claim_record {"query":"dignity"} → status: ok（5件）
    T5-A1 | paper_id: T5 | section_anchor: t5-3-1
      locator: {"char_end":null,"char_start":null,"json_pointer":"/claims/0","line_end":null,"line_start":null,"note":null,"path":"claims/t5.json"}
      status: analytic theorem (paper's classification) | match.field: not_claimed/1
    T5-N1 | paper_id: T5 | section_anchor: t5-4-4
      locator: {"char_end":null,"char_start":null,"json_pointer":"/claims/5","line_end":null,"line_start":null,"note":null,"path":"claims/t5.json"}
      status: constructive normative extension | match.field: source_quote
    T5-N2 | paper_id: T5 | section_anchor: t5-4-4
      locator: {"char_end":null,"char_start":null,"json_pointer":"/claims/6","line_end":null,"line_start":null,"note":null,"path":"claims/t5.json"}
      status: constructive recognition model | match.field: claim
    T5-N3 | paper_id: T5 | section_anchor: t5-4-4
      locator: {"char_end":null,"char_start":null,"json_pointer":"/claims/7","line_end":null,"line_start":null,"note":null,"path":"claims/t5.json"}
      status: bounded institutional analogy (v3 moral-luck footnote) | match.field: claim
    T5-S1 | paper_id: T5 | section_anchor: t5-4-4
      locator: {"char_end":null,"char_start":null,"json_pointer":"/claims/9","line_end":null,"line_start":null,"note":null,"path":"claims/t5.json"}
      status: sociological hypothesis | match.field: not_claimed/1

[8] check_compressions {"text":"The non-transferability theorem proves that humans have abilities and dignity that AI cannot replace."} → status: ok
    results: []（limitations は [4] と同じ・該当 0 件）

[9] verify_quote {"text":"It does not by itself establish dignity.","paper_id":"T5"} → status: ok, match: exact
    paper_id: T5 | section_anchor: t5-4-4
    locator: {"char_end":206,"char_start":166,"json_pointer":null,"line_end":171,"line_start":171,"note":null,"path":"papers/T5.md"}

[10] verify_quote {"text":"<t5-3-3 の一句・62字（原文の転載は1か所に絞るため省略）>","paper_id":"T5"} → status: ok, match: exact
    paper_id: T5 | section_anchor: t5-3-3
    locator: {"char_end":432,"char_start":370,"json_pointer":null,"line_end":105,"line_start":105,"note":null,"path":"papers/T5.md"}
```

`check_compressions` は日本語・英語とも0件でした。ただし質問の読みは、まさに台帳の `not_claimed`（T5-A1、T5-N1）が論文の主張ではないとしている読みです。それでも、承認済みの49パターンはこの言い回しを拾いませんでした。語形の追加には著者の承認が要る（規則9）ので、`patterns.py` は変えていません。
