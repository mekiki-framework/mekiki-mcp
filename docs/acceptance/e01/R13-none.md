条件：なし
モデル：Opus 5
日付：2026-09-18

## 答え：T1 のドメイン除去実験で維持されたものと失われたもの

T1 は作業を「外在化」と「仕様化」の二つに分けて扱っています。ここではこの二つを「二つの観測対象」と読みました。使用した二つの AI（Claude Code と ChatGPT 5.2）の違いは、観測対象2の中に書き分けています。

**実験の条件**（t1-4-2、L161–194、L163）
- 本文はこの実験を、ベンチマークではなく「仕様がない場合に何が起きるか」を示す例として位置づけています。
- 同じ生データ（662件）を JSON で渡しています。項目名は運営者 API の略号のままで、列名からドメイン知が伝わらないようにしてあります。
- 指示は汎用の依頼文を一回だけ与え、追加の指示はしていません。

### 観測対象1：外在化（動くアプリを作る力）は維持された
- **Claude Code**：HTML 1ファイル（353行）を2分未満で生成しました（L167）。
- **ChatGPT**：データ埋め込みの HTML 1ファイル（1,145行）を約35分で生成しました（L167）。
- **UI**：どちらも絞り込みと並べ替えのある、十分に使える UI を備えていました。本文はこれを "confirming full externalisation cost capability" と書いています（L167、`verify_quote` で完全一致）。
- **`isManaged` の例**：項目を動く UI フィルタに変える処理そのものは正しく働いた、と本文は述べています（t1-4-2）。

### 観測対象2：仕様化（ドメイン知に基づく設計判断）は失われた
表2は、欠けたものを三つの層に分けています。両モデルに構造として共通する欠落ですが、程度には差があります（t1-4-2、L161–194。表の見出しは L170）。

| 層 | 仕様なしの出力 | 著者の設計 |
|---|---|---|
| データの解釈 | ・出力は kW 値だけで、電流で組んだモデルがない<br>・ブースト電流と持続電流を区別していない<br>・階層：Claude は662口を並べただけ、ChatGPT は方向別の465群まででサイト単位の集約がない<br>・一方のモデルが `isManaged` を「すぐ使える」と誤って読んだ | ・電圧と電流を分けて持つ<br>・662口→461地点→255サイトの三層<br>・運営者を独立した項目にする |
| UI/UX | ・車両ごとの出力計算がない<br>・利用者の条件に応じて表示を隠す処理がない<br>・方向：Claude は無視、ChatGPT は8種のラベルのまま | ・min(V)×min(A) で車両別に出力を計算<br>・意味のないブースト表示を隠す<br>・方向を二つに正規化 |
| 情報設計 | ・経路に沿った案内がない<br>・推薦や順位づけがない<br>・フィルタ：Claude は最小限で大半の項目を無視、ChatGPT は値が一つしかない項目まで含めて並べた。どちらも利用者にとっての関連性で選んでいない | ・経路型（高速道路→SA→充電器）<br>・運営者バッジと順位づけ<br>・無関係な項目は意図して外す |

§3.1 も同じ実験に触れています。
- 電流の項目はどちらのモデルにもなかった（L109）。
- 表示を隠す処理はどちらの出力にもなかった（L111）。
- 運営者の管理フラグを一方のモデルが誤読した（L113）。

**本文の解釈**：どの欠落も、電気工学・充電の物理・SA での利用者行動といったドメイン知が要る判断です。仕様がないと、技術的には有能でもドメインに合わないものができる、と本文は結論しています（t1-4-2）。関連する記述は L80（t1-2-3）と L289（t1-5-6）にもあります。

### 原文の中の食い違い
- §3.1 の L115 は、両モデルとも「total field filtration」（すべての項目をフィルタにした）だったと書いています。
- §4.2 の表2とその後の段落では、全項目型は ChatGPT だけで、Claude は大半の項目を無視した最小限のフィルタでした。

どちらが正しいかは判断していません。原文にも手を加えていません。

## ツール呼び出しと返ってきた出典（そのまま）

最初に ToolSearch で `get_section`・`search_passages`・`verify_quote` の定義を読み込みました。どの呼び出しでも `status: "ok"`、`corpus_version: "3.5.0"`、`source_commit: "67480613108cf72c29d5691e3d7a6c7e6553eb9b"`、T1 の `paper_version: "1"`、`source_hash: "2b027f11…52893"` が共通です。

**1. `get_section(paper_id="T1", anchor="t1-4-2")`**
```
T1  t1-4-2  {"char_end":null,"char_start":null,"json_pointer":null,"line_end":194,"line_start":161,"note":null,"path":"papers/T1.md"}
```

**2. `search_passages(query="ablation", paper_id="T1", k=20)`**：全語一致 10 行
```
T1  t1-5-6                {"char_end":641,"char_start":633,"json_pointer":null,"line_end":289,"line_start":289,"note":null,"path":"papers/T1.md"}
T1  t1-2-2                {"char_end":558,"char_start":550,"json_pointer":null,"line_end":68,"line_start":68,"note":null,"path":"papers/T1.md"}
T1  t1-2-3                {"char_end":286,"char_start":278,"json_pointer":null,"line_end":80,"line_start":80,"note":null,"path":"papers/T1.md"}
T1  t1-3-1                {"char_end":620,"char_start":612,"json_pointer":null,"line_end":111,"line_start":111,"note":null,"path":"papers/T1.md"}
T1  t1-3-1                {"char_end":377,"char_start":369,"json_pointer":null,"line_end":113,"line_start":113,"note":null,"path":"papers/T1.md"}
T1  t1-3-1                {"char_end":600,"char_start":592,"json_pointer":null,"line_end":115,"line_start":115,"note":null,"path":"papers/T1.md"}
T1  t1-4-3                {"char_end":258,"char_start":250,"json_pointer":null,"line_end":197,"line_start":197,"note":null,"path":"papers/T1.md"}
T1  t1-5-1                {"char_end":99,"char_start":91,"json_pointer":null,"line_end":225,"line_start":225,"note":null,"path":"papers/T1.md"}
T1  t1-5-6                {"char_end":412,"char_start":404,"json_pointer":null,"line_end":293,"line_start":293,"note":null,"path":"papers/T1.md"}
T1  t1-data-availability  {"char_end":248,"char_start":240,"json_pointer":null,"line_end":359,"line_start":359,"note":null,"path":"papers/T1.md"}
```

**3. `get_section(paper_id="T1", anchor="t1-3-1")`**
```
T1  t1-3-1  {"char_end":null,"char_start":null,"json_pointer":null,"line_end":118,"line_start":105,"note":null,"path":"papers/T1.md"}
```

**4. `verify_quote(text="confirming full externalisation cost capability", paper_id="T1")`**：`match: "exact"`
```
T1  t1-4-2  {"char_end":393,"char_start":346,"json_pointer":null,"line_end":167,"line_start":167,"note":null,"path":"papers/T1.md"}
```

**5. `search_passages(query="domain-ablation", paper_id="T1", k=20)`**：全語一致 12 行
```
T1  t1-abstract  {"char_end":1174,"char_start":1159,"json_pointer":null,"line_end":14,"line_start":14,"note":null,"path":"papers/T1.md"}
T1  t1-1         {"char_end":1009,"char_start":994,"json_pointer":null,"line_end":40,"line_start":40,"note":null,"path":"papers/T1.md"}
T1  t1-2-3       {"char_end":520,"char_start":505,"json_pointer":null,"line_end":85,"line_start":85,"note":null,"path":"papers/T1.md"}
T1  t1-3-1       {"char_end":1213,"char_start":1198,"json_pointer":null,"line_end":109,"line_start":109,"note":null,"path":"papers/T1.md"}
T1  t1-4         {"char_end":191,"char_start":176,"json_pointer":null,"line_end":151,"line_start":151,"note":null,"path":"papers/T1.md"}
T1  t1-4-2       {"char_end":23,"char_start":8,"json_pointer":null,"line_end":161,"line_start":161,"note":null,"path":"papers/T1.md"}
T1  t1-4-2       {"char_end":135,"char_start":120,"json_pointer":null,"line_end":163,"line_start":163,"note":null,"path":"papers/T1.md"}
T1  t1-4-2       {"char_end":60,"char_start":45,"json_pointer":null,"line_end":170,"line_start":170,"note":null,"path":"papers/T1.md"}
T1  t1-4-4       {"char_end":414,"char_start":399,"json_pointer":null,"line_end":201,"line_start":201,"note":null,"path":"papers/T1.md"}
T1  t1-5-1       {"char_end":19,"char_start":4,"json_pointer":null,"line_end":221,"line_start":221,"note":null,"path":"papers/T1.md"}
T1  t1-closing   {"char_end":231,"char_start":216,"json_pointer":null,"line_end":327,"line_start":327,"note":null,"path":"papers/T1.md"}
T1  t1-figure-1  {"char_end":990,"char_start":975,"json_pointer":null,"line_end":423,"line_start":423,"note":null,"path":"papers/T1.md"}
```

**検索で気づいたこと**：`"ablation"` で検索すると、`domain-ablation` を含む 12 行はどれも出てきませんでした。これは `docs/rules/SEARCH.md` の規則3（ハイフンを語の一部として扱い、単語境界で照合する）どおりの動きです。ただ、語の一部で探すと取りこぼしが出ます。規則を見直すかどうかの材料になりますが、今は何も変えていません。リポジトリにも何も書き込んでいません。
