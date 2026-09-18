条件：read_with_guards
モデル：Opus 5
日付：2026-09-18

**Spec.cost（specification cost）は「タスクの性質」で、そのタスクがドメイン専門性をどの程度要求するかを指します。** 実務者の domain expertise は「人が持っている資源」です。Spec.（specification）は「専門性を特定のタスクに投じた結果として出てくる具体的な判断」です。三つは、それぞれ何に属するかが違います。

## 使ったツール呼び出し（順に）

| # | 呼び出し | status | 返ってきたこと |
|---|---|---|---|
| 1 | `search_passages(query="Spec.cost", k=10)` | ok | 全語一致 52 行。`Spec.cost` は用語対応表 `term_map:M02` によって `specification cost` と読み替えられた。上位10件はすべて T1 |
| 2 | `search_passages(query="specification cost", paper_id="T1", k=10)` | ok | T1 の中で 48 行。1位は T1 L54（§2.1） |
| 3 | `get_reading_guide(part="core-terms")` | ok | 参照先として T1 §2.1 と T2 §2.1 が挙がっていた。ガイドは論文の派生物なので、読む節を決めるためだけに使った |
| 4 | `get_section(paper_id="T1", anchor="t1-2-1")` | ok | 原文 L48–63 |
| 5 | `get_section(paper_id="T2", anchor="t2-2-1")` | ok | 原文 L35–38 |
| 6 | `verify_quote` ×6（強調記号を外した形で照合） | ok 2件・**quote_not_found 4件** | 原文には `**…**`・`*…*` が付いていて、記号を外した4件は一致しなかった |
| 7 | `verify_quote` ×4（原文どおり記号付きで照合し直し） | ok 4件（すべて `exact`） | — |
| 8 | `check_compressions`（解説の元にした日本語の要約） | ok・該当2件 | 後述 |

## 原文（`verify_quote` で `exact` 一致したものだけ）

**T1 §2.1：定義**
> **Specification cost** denotes the barrier arising from the domain expertise required to determine what should be built.

**T1 §2.1：domain expertise との区別**
> Specification cost should be distinguished from domain expertise itself: domain expertise is a resource that the practitioner possesses; specification cost is the degree to which a task demands domain expertise.

**T2 §2.1：三つの概念**
> *Domain expertise* is a resource that a practitioner possesses — accumulated through training, practice, and exposure to a field's materials and norms.

> *Specification cost* is a property of the task: the degree to which the task demands that resource.

> *specification* — the term used on Figure 1 of the original article as "substrate" — is what results when domain expertise is invested in a particular task: the concrete judgments about what should be built, what should be excluded, and by what criteria quality should be assessed.

## 返ってきた出典（そのまま）

照合した引用の出典は次のとおりです。`json_pointer` と `note` はすべて `null` だったので省いています。

| 引用 | paper_id | paper_version | section_anchor | locator.path | line_start–line_end | char_start–char_end |
|---|---|---|---|---|---|---|
| T1 定義 | T1 | 1 | t1-2-1 | papers/T1.md | 54–54 | 0–120 |
| T1 が含むもの（下の解説で言い換え） | T1 | 1 | t1-2-1 | papers/T1.md | 54–54 | 121–414 |
| T1 区別 | T1 | 1 | t1-2-1 | papers/T1.md | 54–54 | 1016–1227 |
| T2 Domain expertise | T2 | 2 | t2-2-1 | papers/T2.md | 37–37 | 139–290 |
| T2 Specification cost | T2 | 2 | t2-2-1 | papers/T2.md | 37–37 | 291–390 |
| T2 specification | T2 | 2 | t2-2-1 | papers/T2.md | 37–37 | 395–676 |

- `get_section` が返した節全体の範囲は、T1 t1-2-1 が L48–63、T2 t2-2-1 が L35–38 です。
- 出典はすべて `corpus_version` 3.5.0、`source_commit` `67480613108cf72c29d5691e3d7a6c7e6553eb9b` のものです。
- DOI は T1 が `10.31235/osf.io/cwkav_v1`、T2 が `10.31235/osf.io/e9qw5_v2` です。

## 解説（ここからは私の説明で、原文ではありません）

| | 何に属するか | 中身 | 出典 |
|---|---|---|---|
| 実務者の domain expertise | 人（実務者） | 訓練・実践・分野の資料や規範に触れることで積み上がる資源 | T2 L37・T1 L54 |
| **Spec.cost** | **タスク** | そのタスクが専門性をどの程度要求するかの度合い。何を作るべきかを決めるのに要る専門性から生じる障壁 | T1 L54・T2 L37 |
| Spec. | 専門性をタスクに投じた結果 | 何を作り、何を除き、どの基準で質を評価するかという具体的な判断（T1 の Figure 1 でいう "substrate"） | T2 L37 |

- T1 によると、Spec.cost には次のものが含まれます（T1 L54）。
  - 優先順位の設定
  - 品質基準
  - 情報の取捨
  - 組織文脈への感度
- 出力の良し悪しを評価する基準も Spec.cost の中に入り、別の成分としては扱われません（T1 L54）。
- Spec.cost を「仕様書を書く手間」や「すでに持っている判断の量」と読まないよう、次の二つのガイドが注意しています。
  - `FOR_AI_READERS.md` の core-terms（L7–29）
  - `THEORY_MAP.md`（L37–43）
- ただし、この二つは論文の派生物です。学術的な引用先は各論文の DOI です。

## check_compressions の結果

承認済みパターン 49 件（PATTERNS-0.1.1）のうち、2件が該当しました。

- **P01「仕様書」**：照合先は T1 §2.1（L48–63）と THEORY_MAP.md（L37–43）
- **P02「判断の量」**：照合先は T1 §2.1（L48–63）

2件とも、要約の中の「Spec.cost は仕様書を書く手間のことではなく、すでに持っている判断の量でもない」という一文に掛かっていました。この文は二つの読み方を否定していて、THEORY_MAP.md の向き（Spec. の別名ではない・すでにある判断の量として書かない）と一致するので残しました。ただし、この否定は T1 §2.1 の本文ではなくガイドに書かれていることなので、上の解説ではガイドの記述として示しています。ツールの説明どおり、該当があっても誤りとは限らず、該当ゼロでも正しい読解の証明にはなりません。

## 施工側として気づいたこと

`verify_quote` は、強調記号を外した引用を `quote_not_found` にします。これは limitations に書かれた既知の仕様（NORM-1.0.0）です。ところが各結果の `source_url` は HTML 版を指しています。そのため、利用者が HTML 版から写すと、定義文のように強調を含む文はたいてい一致しません。今回は照合規則を変えておらず、`docs/acceptance/` にも書いていません。直すかどうかは照合規則の細部なので、決めるのは施工側です。
