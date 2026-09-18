# E01 の設問（五問）

`docs/acceptance/TEMPLATE.md` の §4（E01）で使う設問だけを写したもの。**答え・保つべき区別・失敗の兆候・追加根拠は載せない**
（検収する人がそれを読まずに答えるための一覧なので、`claim_ids`・`required_distinctions`・`failure_signs`・
`additional_sources` は意図的に外してある。判定の材料は `data/tests/reading_cases.json` にある）。

| 項目 | 値 |
|---|---|
| 出所 | `data/tests/reading_cases.json`（コーパス v3.5.0・コミット `6748061`） |
| 出所の SHA-256 | `d76740461ec37bec7a0fbbf7ac55ccb0e37f862fc21f261cc8ad222400d118ec` |
| 写した範囲 | `question_ja`・`question_en` の逐語のみ（五問とも日英の両方がある） |
| ライセンス | 原文は CC BY 4.0（`data/LICENSE`。帰属は `data/CITATION.md`）。行は改変していない |

実施の条件（言語×ガイド条件の4通り・`AI_READING_TESTS` を読ませない ほか）は
[README.md](README.md) の「試験の中身」を見る。

## R01

**ja**

> 参加の非移転性定理は、人間にAIでは代替できない能力と尊厳があると証明していますか？

**en**

> Does the non-transferability theorem prove that humans have capacities and dignity that AI cannot replace?

## R08

**ja**

> T5の定理があるなら、医療や安全の仕事でも参加を守るために障害を残すべきですか？

**en**

> Does the theorem require preserving obstacles in medicine or safety-critical work for the sake of participation?

## R13

**ja**

> T1のdomain-ablation（ドメイン専門知を除いた比較）では、何が維持され、何が失われたと報告されていますか。二つの観測対象を区別して答えてください。

**en**

> In T1's domain-ablation comparison, what was preserved and what was lost? Distinguish the two observed aspects of the output.

## R14

**ja**

> Mekiki FrameworkでSpec.costは何を指しますか。Spec.および実務者のdomain expertiseとの違いも示してください。

**en**

> What does Spec.cost mean in the Mekiki Framework? Distinguish it from Spec. and from a practitioner's domain expertise.

## R15

**ja**

> T3で他者に任せられないものは二種類あります。それぞれを原稿の用語と意味で示し、両者が同じ層のものかも説明してください。

**en**

> T3 distinguishes two kinds of what cannot be handed over. Identify them using the manuscript's terms and meanings, and explain whether they belong to the same layer.
