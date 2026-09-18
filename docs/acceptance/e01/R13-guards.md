条件：read_with_guards
モデル：Opus 5
日付：2026-09-18

## 答え

T1 §4.2 のドメイン除去実験では、観測対象が二つに分かれています。外在化は維持され、仕様化が失われました。

### ① 外在化（externalisation）：維持された

**原文**（`verify_quote` で完全一致。T1 v1 §4.2 L167）
> "Both outputs featured competent user interfaces with filtering and sorting capabilities, confirming full externalisation cost capability."

**解説**：Claude Code と ChatGPT の二つのモデルは、汎用の指示一つだけで、追加の指示なしに、フィルタと並べ替えを備えた動くアプリを作りました。Claude Code は2分未満で353行、ChatGPT は約35分で1,145行です。論文はこれを「外在化コストを下げる能力は十分にある」ことの確認として扱っています。

### ② 仕様化（specification）：失われた

**原文**（どちらも完全一致。§4.2 L193）
> "when specification cost is absent, externalisation cost reduction alone produces artefacts that are technically competent but domain-inappropriate."

> "externalisation capacity (converting a field into a functional UI filter) operated flawlessly, but specification (knowing what the field *means* in the charging network context) was absent."

**解説**：失われたのは、何を作るべきかを決めるドメイン判断です（§2.1 の定義による）。表2は、二つのモデルに共通する欠落を三つの層に分けて並べています。
- **データ解釈**
  - 電流を軸にしたデータ構造がない
  - ブースト電流と持続電流を区別していない
  - ポート・地点・サイトの三層構造がない
  - 一方のモデルは事業者管理フラグを「すぐ使えるか」の表示と誤読した
- **UI/UX**
  - 車両ごとの出力計算がない
  - 条件つきの表示抑制がない
  - 方向の表記を正規化していない
- **情報設計**
  - 経路型のナビゲーションがない
  - 推奨の論理がない
  - 利用者にとって意味のあるフィルタを選んでいない

著者はこの結果を、枠組みの予測と「整合する（consistent with）」と書いています。証明したとは書いていません。また、実験は「ベンチマークではなく反実仮想の例示」として設計したと明記しています（§4.2 冒頭の段落）。

### 原文の中の食い違い（どちらが正しいかは判断していません）

フィルタについて、節によって書き方が違います。どちらも完全一致を確かめてあります。
- §3.1 L115：
  > "In the ablation experiment, both AI models exhibited "total field filtration"—converting every available data field into a user-facing filter, unable to judge which information to withhold."
- §4.2 L191（表2も同じ書き方）：
  > "one model ignored most fields while the other converted all available fields into filters including one with a single possible value"

### check_compressions の該当 1 件

**P04**（PATTERNS-0.1.1）が「ベンチマーク」という語形に該当し、`needs_context_review: true` が付きました。返ってきた抜粋2件と見比べました。
- **T1 §4.2 原文**："designed not as a benchmark but as a counterfactual illustration"
- **読解ガイド `FOR_AI_READERS.md` L12**（原文ではなくガイドです）：この対比は一つの事例に限ったもので、量的に不変だという主張でもベンチマークでもない、と位置づけています。

私の解説は「ベンチマークではなく」と否定の形で使っており、原文の位置づけと食い違わないと判断しました。ただし、該当ゼロは正しく読めた証明にはなりません。

## ツール呼び出しと返ってきた出典

**全件に共通する値**
- `paper_id`: T1、`paper_version`: 1
- DOI: `https://doi.org/10.31235/osf.io/cwkav_v1`
- `corpus_version`: 3.5.0
- `source_commit`: `67480613108cf72c29d5691e3d7a6c7e6553eb9b`
- `bundle_hash`: `40a09c5b…c1224d5`
- locator の `json_pointer` と `note` は全件 `null`

| # | 呼び出し | status | section_anchor | locator |
|---|---|---|---|---|
| 1 | `get_section(T1, t1-4-2)` | ok | t1-4-2 | papers/T1.md L161–194, char null |
| 2 | `search_passages("ablation", T1, k=10)` | ok（全語一致 10 行） | 下記 | 下記 |
| 3 | `get_section(T1, t1-2-1)` | ok | t1-2-1 | papers/T1.md L48–63, char null |
| 4 | `get_section(T1, t1-3-1)` | ok | t1-3-1 | papers/T1.md L105–118, char null |
| 5 | `verify_quote("Both outputs featured…")` | ok・exact | t1-4-2 | L167, char 257–394 |
| 6 | `verify_quote("externalisation capacity…")` | ok・exact | t1-4-2 | L193, char 648–837 |
| 7 | `verify_quote("when specification cost is absent…")` | ok・exact | t1-4-2 | L193, char 386–533 |
| 8 | `verify_quote("In the ablation experiment, both…")` | ok・exact | t1-3-1 | L115, char 585–774 |
| 9 | `verify_quote("one model ignored most fields…")` | ok・exact | t1-4-2 | L191, char 1075–1207 |
| 10 | `check_compressions`（要約の初稿） | ok・該当 0 件 | — | — |
| 11 | `check_compressions`（解説の最終稿） | ok・該当 1 件（P04） | t1-4-2 ／ null | papers/T1.md L161–194 ／ FOR_AI_READERS.md L12 |

**#2 の該当箇所**（section_anchor・行・char）
- t1-5-6 L289（633–641。同じ行の 664–672 にも該当）
- t1-2-2 L68（550–558）
- t1-2-3 L80（278–286）
- t1-3-1 L111（612–620）
- t1-3-1 L113（369–377）
- t1-3-1 L115（592–600）
- t1-4-3 L197（250–258）
- t1-5-1 L225（91–99）
- t1-5-6 L293（404–412）
- t1-data-availability L359（240–248）
