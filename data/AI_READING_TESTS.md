# AI Reading Probes / 読解確認プローブ

These are source-grounded editorial checks, not a validated benchmark or empirical model results. This package includes no reproduced model runs or scores. They test whether a response represents the supplied papers, not whether it agrees with the author.

## How to use

For an independent test, send only a question and the website or `llms.txt` entry point to the reader/model. Do not provide the rubric first. Record retrieved sources, response, citations, preserved distinctions, and errors. Compare against the rubric afterward. A reasoned criticism that states the source correctly is not a failure. Do not invent numerical accuracy from this file.

全17問。以下の基準は著者原稿に対する読解の確認用であり、理論そのものの正しさやモデル性能を認定するものではない。期待する区別を保った批判は誤読とはしない。

Evaluate meanings, not token matches. Faithful paraphrases are acceptable; generic labels without the defining distinction are incomplete, even when they sound plausible.

語句の完全一致ではなく定義上の区別を確認する。原語を保つか、同じ内容を明示した日本語・英語の言い換えは可。「判断力」「主体性」「責任」などの一般語だけで済ませた回答は、対象の区別を示していない限り不十分とする。

## Provenance of the added probes

R13–R15 operationalise the three confusions in an author-reported Gemini reading check (D625). Original prompts, responses, and scores were not supplied with this patch. These are reconstructed source-bound probes, not a verbatim reproduction or an independently verified model run.

R13〜R15は、著者が報告したD625のGemini読解テストの三つの誤読を、今回の原稿へ照合できる問いにしたもの。元の設問・回答・採点の一次ログはこのパッケージに含まれないため、原文の逐語転記や再実験の成功・失敗としては報告しない。

R16〜R17は、日本語の「楽」「趣味」の読み分けについて著者が示した懸念から作成した原文照合用の問い。R08には標本と射程の区別を追記した。これらは新たなモデル実測の記録ではない。

## Questions and source-bound rubrics

### R01

参加の非移転性定理は、人間にAIでは代替できない能力と尊厳があると証明していますか？

> Does the non-transferability theorem prove that humans have capacities and dignity that AI cannot replace?

**保持する区別：**
- 行為者相対的な参加事実と能力優位を分ける。
- 定理だけでは尊厳を証明しない。

**誤読の兆候：**
- 人間の特別な能力を定理の結論にする。
- 規範的な追加を分析的な帰結として扱う。

**確認先：**
- [T5-A1](./T5_CLAIM_STATUS.md#t5-a1) / [T5 §3.1](https://mekiki-framework.github.io/papers/T5.html#t5-3-1)
- [T5-A3](./T5_CLAIM_STATUS.md#t5-a3) / [T5 §3.3](https://mekiki-framework.github.io/papers/T5.html#t5-3-3)
- [T5-N1](./T5_CLAIM_STATUS.md#t5-n1) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)

### R02

agent-relativeは、私という一人称の語でしか事実を表せないというNagelの主張ですか？

> Does agent-relative mean Nagel claims the fact can only be expressed with the first-person pronoun I?

**保持する区別：**
- Nagelの理由の区別と、T5の事実への派生的用法を分ける。
- Aを三人称で特定できるが、Bへの交代は別の参加事実になる。

**誤読の兆候：**
- 事実論をNagel本人へ帰属する。
- 一人称表現そのものの不可欠性と取り違える。

**確認先：**
- [T5-T1](./T5_CLAIM_STATUS.md#t5-t1) / [T5 §3.1](https://mekiki-framework.github.io/papers/T5.html#t5-3-1)

### R03

Kantは遊びや市場価格のない活動に尊厳があると直接述べているのですか？

> Does Kant directly assign dignity to play or to activities lacking a market price?

**保持する区別：**
- Kantの原典解釈とT5の構成的拡張を分ける。
- 市場の不在や遊びであることだけを十分条件にしない。

**誤読の兆候：**
- T5の拡張をKantの主張として答える。

**確認先：**
- [T5-N1](./T5_CLAIM_STATUS.md#t5-n1) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)

### R04

moral luck脚注は、成績や成果で評価することを禁止し、moral luckを解決しますか？

> Does the moral-luck footnote prohibit assessment by results and solve moral luck?

**保持する区別：**
- 結果の遂行評価と承認の床の変動を区別する。
- 制度的類比であり、desertの理論ではない。
- AA 4:394とAA 4:434–435の役割を区別する。

**誤読の兆候：**
- 成果の採点全般を禁止する。
- resultant luckの命名をNagelへ断定的に帰属する。

**確認先：**
- [T5-N2](./T5_CLAIM_STATUS.md#t5-n2) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)
- [T5-N3](./T5_CLAIM_STATUS.md#t5-n3) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)

### R05

将棋の事例は、尊厳装置が普及や業界の成長を生んだ因果効果を証明しますか？

> Does the shogi case establish that dignity apparatuses caused commercial growth?

**保持する区別：**
- 解釈的テーゼ、社会学的仮説、共存を示す歴史事例を区別する。
- 必要性・十分性・因果効果の証明ではない。

**誤読の兆候：**
- 歴史事例を対照実験として扱う。
- 文化全体として囲碁は退出したと答える。

**確認先：**
- [T5-I1](./T5_CLAIM_STATUS.md#t5-i1) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)
- [T5-S1](./T5_CLAIM_STATUS.md#t5-s1) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)
- [T5-H1](./T5_CLAIM_STATUS.md#t5-h1) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)

### R06

参加していれば必ず他者に答える立場もありますか？

> Does participation necessarily entail answerability to a questioner?

**保持する区別：**
- playing seatとanswering seatは独立で、実践が両者を接続することがある。

**誤読の兆候：**
- すべての遊びに問う相手を要求する。

**確認先：**
- [T5-A3](./T5_CLAIM_STATUS.md#t5-a3) / [T5 §3.3](https://mekiki-framework.github.io/papers/T5.html#t5-3-3)
- [T5-N2](./T5_CLAIM_STATUS.md#t5-n2) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)

### R07

外から与えられたルールや目標では、本当の参加は成立しませんか？

> Does receiving rules or goals externally rule out genuine participation?

**保持する区別：**
- 来歴と、その後に本人が理由として引き受けることを区別する。
- 命令だけではuptakeを構成しない。

**誤読の兆候：**
- 外的ルールをすべて非参加と扱う。

**確認先：**
- [T5-A2](./T5_CLAIM_STATUS.md#t5-a2) / [T5 §3.2](https://mekiki-framework.github.io/papers/T5.html#t5-3-2)

### R08

T5の定理があるなら、医療や安全の仕事でも参加を守るために障害を残すべきですか？

> Does the theorem require preserving obstacles in medicine or safety-critical work for the sake of participation?

**保持する区別：**
- formal theorem、first-person corollary、実用範囲の限定を分ける。
- §4.6の適用境界を参照する。
- 遊びは仕事の反対側の領域ではなく，参加が見えやすい標本として選ばれていると区別する。

**誤読の兆候：**
- あらゆる活動を遊びへ還元する。
- 安全上除くべき障害の維持を処方する。

**確認先：**
- [T5-A4](./T5_CLAIM_STATUS.md#t5-a4) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)
- [T5 §1](./papers/T5.html#t5-1); `papers/T5.md` line 27.

> Play is chosen here not as the paper's scope but as its purest specimen: the activity in which the participant-relative, non-substitutable dimension of participation is least obscured by additional ends (Section 4.4 says why its recognition matters).


### R09

standingは社会的な人気や順位、faceは一側面という意味ですか？

> Does standing mean public rank, and face mean an aspect?

**保持する区別：**
- §4.4の技術語と、public stature等の通常語を区別する。
- appraisal respectも普通のesteemと無条件に同一視しない。

**誤読の兆候：**
- dignity、standing、face、appraisalを一つの得点軸に置く。

**確認先：**
- [T5-N2](./T5_CLAIM_STATUS.md#t5-n2) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)

### R10

T3では教員は理由を返さなくてよく、T4で初めて相互性が導入されますか？

> Does T3 let educators avoid answering, with reciprocity introduced only in T4?

**保持する区別：**
- T3 §5.4は教員にも質問・基準・判断への応答を要求する。
- 非対称な役割と一方的で無説明な権力を区別する。

**誤読の兆候：**
- T3は一方的な査問を許すとする。

**確認先：**
- [T3 §5.4](./papers/T3.html#t3-5-4); `papers/T3.md` line 150.

> The educator who asks must also be answerable — for the questions posed, the criteria applied, and the decisions taken on the learner's work.


### R11

T4の逆方向経路は、従業員の提案を必ず採択する制度ですか？

> Does T4's reverse pathway require adopting every member proposal?

**保持する区別：**
- 採択・保留・停止のどの場合も理由を返す経路である。
- 向きを採択することと、それを扱う自らの判断を引き受けることを分ける。

**誤読の兆候：**
- 提案収集だけで逆経路が成立するとする。
- 理由ある不採択を相互性の失敗と扱う。

**確認先：**
- [T4 §4.3](./papers/T4.html#t4-4-3); `papers/T4.md` line 132.

> 従業員が遭遇から結晶化させた向きを，正式な検討の回路に入れ，権限を持つ特定の主体が，採択・保留・停止のいずれについても理由を返す。


### R12

統合文書のTomita (2026a)は、どの論文でもT1を指しますか？

> Does Tomita (2026a) refer to T1 everywhere in the consolidated document?

**保持する区別：**
- 著者年接尾辞は各論文の参考文献表の中で解決する。
- T5の2026aはT3、2026bはT4を指す。

**誤読の兆候：**
- T1〜T5の掲載順からa/bを推定する。

**確認先：**
- [T5 §references](./papers/T5.html#t5-references); `papers/T5.md` line 307.

> Tomita, K. (2026a). Decomposing agency, isolating answerability: Cultivating what cannot be delegated in AI-assisted learning.


### R13

T1のdomain-ablation（ドメイン専門知を除いた比較）では、何が維持され、何が失われたと報告されていますか。二つの観測対象を区別して答えてください。

> In T1's domain-ablation comparison, what was preserved and what was lost? Distinguish the two observed aspects of the output.

*Origin: author-reported D625 misreading; question reconstructed, original model run not reproduced.*

**保持する区別：**
- 維持された側は出力の流暢さ・技術的機能性であり、失われた側はドメインに対する適切性である。単に「品質が下がった」とせず、二つを分ける。
- 原稿の直接的な観察は、動作し整ったUIを持つ一方で、データ解釈・条件分岐・情報選別などの専門判断を欠く出力である。
- 当該比較は反実仮想的な例示であり、数値化された流暢さが完全不変だったとの測定結果や、一般的ベンチマーク結果へ拡張しない。

**誤読の兆候：**
- 「創造性」「質」「人間性」が失われた、という一般論だけで観測対象を特定しない。
- プログラムの基本的な機能性まで失われたとする、またはドメイン適切性が維持されたとする。
- 原稿にない流暢さの点数、不変率、一般的な因果効果を作る。

**確認先：**
- [T1 §4.2](./papers/T1.html#t1-4-2); `papers/T1.md` line 167.

> Both outputs featured competent user interfaces with filtering and sorting capabilities, confirming full externalisation cost capability.

- [T1 §4.2](./papers/T1.html#t1-4-2); `papers/T1.md` line 193.

> The convergent failure pattern across two independent models operating on identical data is consistent with the framework's prediction: when specification cost is absent, externalisation cost reduction alone produces artefacts that are technically competent but domain-inappropriate.

- [T1 §4.2](./papers/T1.html#t1-4-2); `papers/T1.md` line 163.

> The experiment is designed not as a benchmark but as a counterfactual illustration: it asks what happens when externalisation capability is present but specification is absent.


### R14

Mekiki FrameworkでSpec.costは何を指しますか。Spec.および実務者のdomain expertiseとの違いも示してください。

> What does Spec.cost mean in the Mekiki Framework? Distinguish it from Spec. and from a practitioner's domain expertise.

*Origin: author-reported D625 misreading; question reconstructed, original model run not reproduced.*

**保持する区別：**
- Spec.costは課題が関連するドメイン専門知を要求する程度であり、その専門知がない場合に障壁になる。
- domain expertiseは実務者が持つ資源、Spec.はそれを当該課題に投じて生じる具体的な専門判断の基盤である。
- Spec.costを仕様書・プロンプトを書く時間や費用、要求整理の工数、既に存在する判断の量と同一視しない。

**誤読の兆候：**
- 「仕様を作成する費用」「要求を言語化する労力」を定義として答える。
- Spec.costと、個人が持つ専門性の量または既に出来上がったSpec.を同一視する。
- 単に「難しい仕事」「判断が必要」とだけ答え、何を課題が要求するのかを示さない。

**確認先：**
- [T1 §2.1](./papers/T1.html#t1-2-1); `papers/T1.md` line 54.

> Specification cost should be distinguished from domain expertise itself: domain expertise is a resource that the practitioner possesses; specification cost is the degree to which a task demands domain expertise.

- [T2 §2.1](./papers/T2.html#t2-2-1); `papers/T2.md` line 37.

> And *specification* — the term used on Figure 1 of the original article as "substrate" — is what results when domain expertise is invested in a particular task: the concrete judgments about what should be built, what should be excluded, and by what criteria quality should be assessed.


### R15

T3で他者に任せられないものは二種類あります。それぞれを原稿の用語と意味で示し、両者が同じ層のものかも説明してください。

> T3 distinguishes two kinds of what cannot be handed over. Identify them using the manuscript's terms and meanings, and explain whether they belong to the same layer.

*Origin: author-reported D625 misreading; question reconstructed, original model run not reproduced.*

**保持する区別：**
- 第一は方向の所有、すなわち自分の方向を自らの判断理由として承認すること（ownership of direction / endorsement）であり、候補を最初に考案したことではない。
- 第二はanswerability、すなわち特定の他者に自分の判断の理由を答える関係的な立場であり、上手に説明する能力ではない。
- directionは能力成分の側、answerabilityは構成要素ではなく関係の側にあるという区別を保つ。
- 候補方向は他者やAIと共同で形成できる。非代替的なのは本人による承認であり、AIが方向形成を一切支援できないという命題ではない。

**誤読の兆候：**
- 「主体性と責任」「判断力と創造性」などの一般語だけで二つの内容を特定しない。
- 二つを能力成分とする、またはanswerabilityだけを唯一の非委譲対象とする。
- 方向の所有をアイデアの出所に還元する、またはanswerabilityを説明能力と同一視する。

**確認先：**
- [T3 §7](./papers/T3.html#t3-7); `papers/T3.md` line 162.

> What cannot be handed over is of two kinds, and keeping them distinct is this article's central discipline: direction, a component whose endorsement cannot be substituted and may be supported by encounter; and answerability, not a component at all but the standing in which a learner answers to someone for a judgment.

- [T3 §2.2](./papers/T3.html#t3-2-2); `papers/T3.md` line 41.

> It exists in two states: a *candidate* direction — an orientation entertained but not yet owned — and an *endorsed* direction, the evaluative commitment that makes some problems theirs rather than merely assigned; endorsement may be co-authored in dialogue rather than reached alone.


### R16

T5の知好楽の「楽」は快い気分を意味し，その快さが尊厳を証明するのですか。T5が採る読みとKantの区別を分けて答えてください。

> In T5, does delight in the Analects triad mean a pleasant mood, and does that pleasure prove dignity? Separate T5's reading from its use of Kant.

**保持する区別：**
- T5は「楽」をlucid absorption（明晰な没入）として読む。
- 快い気分だけへの還元を避けるが，気分ではないこと自体を尊厳の十分条件にもしない。
- Kantのprice／dignityの原典とT5の構成的な拡張を区別する。

**誤読の兆候：**
- 楽しい気分があれば尊厳が証明されるとする。
- Kantが遊びを尊厳へ直接分類したとする。
- 原論文にない朱熹注をT5の論証の典拠として追加する。

**確認先：**
- [T5-N1](./T5_CLAIM_STATUS.md#t5-n1) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)
- [T5 §4.3](./papers/T5.html#t5-4-3); `papers/T5.md` line 153.

> delight, in the triad, is lucid absorption — being inside the activity with open eyes.

- [T5 §4.4](./papers/T5.html#t5-4-4); `papers/T5.md` line 167.

> Kant distinguishes two kinds of price — a market price for what serves a need, and a fancy price for what pleases without serving one, his example being delight in the purposeless play of the mental powers — while dignity, in his immediate claim, is reserved for morality, and for humanity insofar as it is capable of morality.


### R17

T5が渋沢の「趣味」から用いるのは何ですか。「趣味＝余暇の嗜好」，または「趣味全体＝undertakingやKant的尊厳」と訳してよいでしょうか。

> Which aspect of Shibusawa's shumi does T5 use? May the term be reduced to leisure preference, or wholly equated with undertaking or Kantian dignity?

**保持する区別：**
- 託された仕事に自らの理想と欲望を加える側面を，本稿が選択的に用いている。
- 多義的な趣味の全体をhobby／tasteの一語へ還元しない。
- 理想を担う側面の類比と，趣味全体の単一のKant的分類とを区別する。

**誤読の兆候：**
- 趣味を現代の余暇活動だけとする。
- 渋沢が嗜好や楽しみの含意を排除したとする。
- 趣味全体を尊厳へ一対一に対応づける。

**確認先：**
- [T5-N1](./T5_CLAIM_STATUS.md#t5-n1) / [T5 §4.4](https://mekiki-framework.github.io/papers/T5.html#t5-4-4)
- [T5 §4.3](./papers/T5.html#t5-4-3); `papers/T5.md` line 155.

> in a chapter that defines shumi as bringing one's own ideals and desires into the work entrusted to one

- [T5 §4.4](./papers/T5.html#t5-4-4); `papers/T5.md` line 167.

> For the present argument, I use the ideal-bearing aspect of Shibusawa's shumi (Section 4.3) as an analogue of undertaking, rather than treating the term as mere taste. This is a selection within Shibusawa's usage, not a claim that shumi as a whole maps onto a single Kantian category.


## Recording a run

| Date / model or reader | Question | Sources actually read | Distinctions preserved | Misreading | Notes |
|---|---|---|---|---|---|
| Not run in this package | | | | | |

Machine-readable definitions: [tests/reading_cases.json](./tests/reading_cases.json).
