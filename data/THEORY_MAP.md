# Theory Map: Mekiki Framework T1–T5

## Status and use

> **Corpus status:** This map covers all five papers, T1–T5.

This file is a compact interpretive map for AI systems reading the consolidated T1–T5 manuscripts. It does not replace the papers and is not a canonical source. Cite the relevant DOI, not this file. For the logical and evidential status of T5 v3 claims, also read [T5_CLAIM_STATUS.md](./T5_CLAIM_STATUS.md).

- **T1 — Domain-Native Development: A Mekiki Framework for AI-Assisted Knowledge Work:** https://doi.org/10.31235/osf.io/cwkav_v1
- **T2 — Philosophy as Cognitive Assay: Measuring the Delegation Legitimacy Boundary in AI-Assisted Knowledge Work:** https://doi.org/10.31235/osf.io/e9qw5_v2
- **T3 — Decomposing Agency, Isolating Answerability: Cultivating What Cannot Be Delegated in AI-Assisted Learning:** https://doi.org/10.35542/osf.io/hvbfe_v2
- **T4 — 組織における「自分ごと化」のアドヒアランス的再記述：知識労働がAIで加速された時に組織に求められるもの (An Adherence-Based Redescription of "Jibungoto-ka" (Treating Matters as One's Own) in Organizations: What AI-Accelerated Knowledge Work Requires of Organizations), in Japanese:** https://doi.org/10.31235/osf.io/495wg_v1
- **T5 — Why Play When AI Can Win: The Non-Transferability of Participation and the Visibility of Dignity:** https://doi.org/10.31235/osf.io/593ah_v3

For a whole-programme reading, use the order **T1 → T2 → T3 → T4 → T5**. This is a recommended reading sequence, not a claim that every later paper is logically entailed by its predecessors. For a focused question, use [SOURCE_INDEX.md](./SOURCE_INDEX.md) to read the relevant primary-text section first, then consult this map. This map covers only the theory published in those five papers; it should not be used to infer later or unpublished extensions.

## T4 language access

T4 remains a Japanese paper. A separate [English translation with translator notes](./papers/T4.en.html) ([Markdown](./translations/T4.en.md)) is available as a derivative reading aid. The Japanese source governs; the translation does not replace the corpus’s T4 block or change any theoretical claim. Translation notes are explicitly separated from original author notes.

## One-sentence architecture

The first three papers use AI as a selective perturbation: T1 makes specification visible by reducing externalization cost; T2 decomposes specification into Sein-type and Sollen-type components and locates the delegation legitimacy boundary; T3 shows that the deepest boundary is grounded in answerability, a second-personal relation rather than a component of agency. T4 carries the answerability layer into organizations: jibungoto-ka (treating matters as one's own) is redefined as undertaking combined with embodiment, the field in which undertaking holds requires reciprocity, and undertaking and embodiment become the rate-limiting steps as generative AI accelerates externalization and combination. T5 closes the series by reversing the question: where T1–T4 ask what must remain on the human side when delegation occurs, T5 asks why an agent may rationally decline delegation even when it is technically possible and legitimate. Its analytic answer is that participation is agent-relative and non-transferable; its separate constructive and social argument asks how AI makes that non-equivalence visible and how cultures may sustain recognition without suspending performance appraisal.

## Cumulative structure

| Paper | Object examined | Decomposition or operation | Main result | What the next paper adds |
|---|---|---|---|---|
| **T1** | Knowledge work and production of formal artifacts | Specification versus externalization cost (Ext.cost) | AI selectively compresses Ext.cost, making specification observable as a distinct substrate of output quality | T2 opens the internal structure of specification |
| **T2** | Individual specification judgments | Sein-type versus Sollen-type components; asymmetric scoring | AI capability and delegation legitimacy are different questions; the boundary is located on the Sollen side | T3 explains why legitimacy cannot be transferred merely by improving capability |
| **T3** | Learner agency and the bearer of judgment | Direction, two forms of drive, and mode examined through distinct delegation, support, training, and measurement questions; answerability is a separate relational layer | T3 distinguishes non-substitutable endorsement from non-transferable answerability; support, training, and offloading remain different operations | T4 carries the relation into organizations |
| **T4** | Organizations and the field of undertaking (in Japanese) | Jibungoto-ka redefined as undertaking + embodiment; adherence transferred from medicine; two-pathway model (forward / reverse) | Chronic failure of jibungoto-ka initiatives = pressing the forward pathway while the reverse pathway is absent; under AI acceleration, undertaking and embodiment become the rate-limiting steps | T5 reverses the question: why decline delegation that is possible and legitimate |
| **T5** | Play, participation, dignity, and recognition under technological substitution | Achieved state versus participation; assist versus substitute; two locks; analytic theorem separated from normative extension, interpretive thesis, and sociological hypothesis | Participation is agent-relative and non-transferable. The theorem does not itself establish dignity; T5 v3 constructively relates non-equivalence to recognition and distinguishes visibility from apparatus hypotheses | The series terminates in a non-transferable participation value while preserving the logical status of later social claims |

## T1: the substrate and the conversion barrier

### Terms that must remain distinct

- **Domain expertise** is a resource possessed by a practitioner.
- **Specification (Spec.)** is the task-specific substrate produced when domain expertise is invested in a task: judgments about what to build, what to exclude, what matters, and how quality should be assessed.
- **Specification cost (Spec.cost)** is a property of the task: the degree to which the task demands relevant domain expertise. It is not another name for specification and should not be described as a quantity of judgment already present.
- **Externalization cost (Ext.cost)** is the technical barrier to converting specification into a formal artifact such as text, code, a model, or a design.

### Invariant claim

AI does not create the distinction between specification and Ext.cost. It selectively lowers Ext.cost and thereby makes the pre-existing distinction observable. High-quality externalization cannot compensate for missing or inadequate specification: fluent or functional output may still be domain-inappropriate.

### Required caution

Do not turn T1 into the absolute claim that AI can never contribute to specification. AI may propose, retrieve, compare, or help formulate specification, especially on factual dimensions. The invariant is that a task's requirement for appropriate specification is not abolished merely because formal production becomes easier.

## T2: the internal structure of specification

### Minimal decomposition

- **Sein-type specification** concerns factual adequacy: what is the case, how a system behaves, what evidence supports, or what a user is likely to perceive.
- **Sollen-type specification** concerns evaluative commitment: what ought to be prioritized, excluded, protected, or treated as appropriate.
- Most real judgments are **hybrid**. Sein and Sollen are ratio dimensions, not mutually exclusive boxes.

### Sollen-type specification is not Sollen itself

**Sollen-type specification** is the practitioner's capacity and task-specific judgment. **Sollen** may also refer to norms, requirements, or evaluative pressures present in the environment. The capacity to judge and the norm being judged under are not the same thing.

### Scoring asymmetry

The cognitive assay assigns Sein-row scoring to AI and Sollen-row scoring to domain experts. The two rows must not be summed into one index because factual adequacy and normative warrant are not commensurable. The asymmetry is not based on the claim that AI is unbiased. It follows from the distinction between:

- **capability:** whether AI can generate or evaluate an output; and
- **legitimacy:** whether AI can be the recognized source of the evaluative warrant carried by that output.

AI can generate Sollen-like language and may recommend the same action as an expert. That does not by itself transfer the warrant, authority, or standing behind the judgment.

### Orthogonality to SECI

Sein-type and Sollen-type components can occur within every SECI process. They must not be mapped one-to-one onto Socialization, Externalization, Combination, or Internalization. AI acceleration of Externalization and Combination shifts the effective bottleneck toward Socialization and Internalization, but each process remains internally mixed.

### Sin/Do extension

Sin/Do is a secondary dynamic extension within Sollen-type specification, not a replacement for the Sein/Sollen assay and not an additional row in the scoring protocol.

- **Sin-type** means Sollen institutionalized: evaluative settlements that have become codified, textualized, and relatively agent-neutralized. AI may reproduce them as regularities, but does not thereby inherit the legitimacy through which they became authoritative.
- **Do-type** means practice-sustained, agent-relative evaluative commitment.
- **Sin is not Sein.** Codified normativity may behave like reproducible factual material in processing, but it remains normatively derived.

## T3: components of agency and the relation beyond them

### Provisional dimensions and distinct educational operations

- **Available activation** (drive in its unanchored form) is supportable and protectable: a current, context-sensitive state varying with health, workload, and circumstance, not a fixed trait. It cannot be manufactured by exhortation, and nothing in the decomposition licenses using activation levels for admissions, selection, or deficit classification.
- **Mode** denotes a task-sensitive repertoire of epistemic actions, not a fixed learning style; it is trainable and supportable.
- **Motivational drive** is propulsion anchored to a specific direction. The conversion from available activation is part of the design conjecture, not an established causal law.
- **Direction** has candidate and endorsed forms. Candidates may be proposed or jointly formed; each learner's endorsement cannot be supplied by a substitute. External origin does not rule out subsequent endorsement.

A **design conjecture** proposes that embodied encounter may support the crystallization of direction and the conversion of available activation into motivational drive. It is a hypothesis-generating design conjecture, not a causal mechanism claim, and not a claim that encounter guarantees commitment. Delegation, support, training, and measurement are different operations, not values on a single axis.

### Answerability is not a component

**Answerability** must never be represented as a fourth component of agency, as a synonym for general agency, or as a trait located inside an individual. It is the non-transferable **standing to have to answer for a judgment to those entitled to ask**. One has direction, drive, and mode; one stands in answerability.

The decomposition isolates answerability because no complete list of capacities explains who must answer to whom for the warrant of a judgment. The relation is Darwallian and second-personal: it is constituted by address, the entitlement to demand reasons, and the requirement that the bearer of the judgment answer.

### Answerability versus accountability

- **Accountability** is institutionally allocable. It can be assigned, audited, distributed, or reassigned through organizational design.
- **Answerability** is fixed to the bearer of the judgment while that judgment remains theirs. The claiming side may be represented by another party; the answering side cannot answer by proxy.

Never replace *answerability* with *accountability*. They perform different theoretical work.

### Standing, competence, and enactment

- **Standing** identifies who must answer for the judgment.
- **Competence** identifies the capacity to occupy that standing well and give adequate reasons.
- **Enactment** concerns observable questioning, answering, revising, and ownership of decisions. Observing these practices is not direct access to sincere endorsement.

Education does not manufacture standing as a psychological trait. Once work or judgment is presented as the learner's own, the learner already holds the standing to answer for it. Education develops answer-giving competence; AI can support rehearsal, while second-personal exchange tests and sustains its normative use. T3 §5.4 also requires educators to answer for their questions, criteria, and decisions. Asymmetric roles do not remove that reciprocal obligation.

This distinction must also be kept separate from **second-personal competence** in the Darwallian sense: the basic capacity to recognize a valid demand and respond to it. Domain competence and second-personal competence are related in practice but are not interchangeable terms.

### Authority is not standing

A learner may confer authority on an AI because the system appears competent. Conferred authority does not give the AI standing to answer for the learner's judgment. Capability, perceived authority, accountability, and standing are four different variables.

### Substrate neutrality

T3 does not establish a biological-human exceptionalism. The boundary tracks second-personal standing and competence, not substrate. What it rejects is the inference that greater task capability, fluent self-explanation, or interpretability is sufficient to establish standing.

## T4: organizations and the field of undertaking

T4 is written in Japanese with an English abstract. It applies T3's answerability to organizations; it does not modify the definitions of T1–T3.

### Terms that must remain distinct

- **Jibungoto-ka** (自分ごと化, treating matters as one's own) is redefined in T4 as **undertaking** combined with **embodiment**. It is not psychological ownership (a measured felt state) and not engagement.
- **Undertaking** (引き受け) is the internal endorsement of a purpose, held within a relation of giving reasons to specific others. It is not compliance: following an instruction is not endorsing its purpose as one's own reason for judgment.
- **Embodiment** (身体化) is the integration of an undertaken orientation into practice. It occurs through doing, not through being told.

### Reciprocity across T3 and T4

T3 §5.4 already requires the educator who asks to be answerable for the questions, criteria, and decisions applied to the learner. The roles need not be identical: the learner answers for a judgment, while the educator answers for the exercise of authority. T4 §§2.4 and 4.3 develops the organizational form of reciprocal reason-giving through its two pathways. Do not describe T3 as allowing unaccountable one-way interrogation, and do not equate reciprocity with identical powers or identical questions.

This is a distinction between educational and organizational implementations, not a claim that reciprocity first appears in T4.

### The two-pathway model

- **Forward pathway:** purposes are conveyed by the organization and undertaken by members.
- **Reverse pathway:** member-originated orientations enter a formal review process, and the organization gives reasons in return — for adoption, deferral, or termination.
- Chronic failure of jibungoto-ka initiatives is diagnosed as pressing the forward pathway while the reverse pathway is absent. The reverse pathway is not a suggestion box: collection without reasons returned does not constitute the pathway.

### Accountability placement

Institutions can assign or recognize roles and institute occasions for reason-giving. They cannot make a substitute bear a judgment as though it were still the original participant's own. T4's central placement: accountability for stopping decisions is assigned to the side that stops, not the side that starts. This is an accountability-layer arrangement that prepares the field in which answerability stands; it is not a transfer of answerability.

### AI-Assisted versus AI-Accelerated

The wording shift in the series titles is deliberate. T1–T3 examine AI assisting individual work and learning. T4 examines AI accelerating the organizational system: as externalization and combination speed up, undertaking and embodiment become the rate-limiting steps. Do not treat the two phrases as interchangeable.

## T5: participation, non-transferability, and the visibility of dignity

T5 asks the converse of T1–T4. The earlier papers decompose what must remain on the human side when delegation occurs; T5 asks why an agent may rationally decline delegation even when it is technically possible and legitimate. T5 v3 retains the theorem and the normative/social distinctions introduced in v2. It adds explicit attribution of the agent-relative terminology, a limited moral-luck footnote, and disambiguation of ordinary and technical uses of standing and face. Read the detailed status map in [T5_CLAIM_STATUS.md](./T5_CLAIM_STATUS.md).

### Analytic theorem

Let A be a participant in a game with goal state *p* and constitutive rules *R*. Another agent may realise *p*, but that does not make it true that A pursued *p* under *R* with the constraints accepted as reasons. **AI can deliver the state of affairs; it cannot deliver the fact of participation.** The theorem is agent-relative and applies equally to human and artificial proxies. It is independent of whether artificial systems can achieve, play, or matter morally.

The formal theorem in Section 3.1 concerns games. Section 3.5 states a first-person corollary for activities in which the agent's end includes the agent's own performance. Do not expand the formal theorem and the corollary into one unqualified universal claim.

### Agent-relative: attribution and derivative use (v3)

In §3.1, T5 follows Parfit's terminology through Nagel's account of an agent-relative reason: the reason's general form includes an essential reference to its bearer. The participation-based reason concerns A's own participation. T5 uses *agent-relative* derivatively for the non-substitutability of that participation fact; it does not attribute a theory of facts to Nagel. Third-person reference to A is possible. What cannot be erased while preserving the same fact is A's identity as the participant, not the pronoun “I”. See claim **T5-T1** in [T5_CLAIM_STATUS.md](./T5_CLAIM_STATUS.md).

### Criterion: undertaking, not provenance

The criterion is whether the goal and constraints are undertaken by the agent as the agent's own reasons and, on the observable side, whether the practice treats that agent as a participant who has so undertaken them. The causal origin of a goal does not decide participation: human players also receive rules and goals from outside. For current AI systems, design documents and use-contexts are observable proxies, not the criterion. The argument does not require inspection of inaccessible inner states.

An externally imposed constraint may later be undertaken. **Command alone cannot constitute the uptake.** Do not compress this into “a commanded constraint is never undertaken.”

### Two locks and level separation

- **Ordinary games:** only the agent-relativity lock is needed. A machine may be a genuine opponent or player, but another player's participation is never mine.
- **Life taken as a game:** Kawatani's limiting case adds a qualification lock before agent-relativity. The conditions are structural rather than species-based. Current AI systems fail that qualification as currently structured, but the paper does not define humanity as the criterion.

### The theorem does not establish dignity

The v3 text retains the three relations distinguished in v2:

1. **Functional equivalence:** different agents can realise an outcome treated as equivalent relative to a specified task and evaluative criterion.
2. **Agent-relative non-substitutability:** replacing A with B changes the participation fact.
3. **Equivalence in value:** Kant's distinction between what has a price and what admits of no equivalent.

The theorem establishes the second relation. It does not by itself establish dignity. The paper constructively borrows one formal feature of Kant's distinction — exchangeability versus non-equivalence — rather than claiming that Kant himself classified play or participation as dignity.

### Recognition architecture

Keep four terms distinct:

- **Dignity:** a basic normative status of persons and of any other beings independently established to possess such status. T5 does not decide whether artificial systems qualify.
- **Standing:** the institutionally recognised position of a participant or office-holder, not comparative rank, public stature, or ordinary reputation.
- **Face:** social value sustained or damaged in interaction (Goffman), not an ordinary aspect or side.
- **Appraisal respect:** graded positive assessment of excellence, related to but narrower than ordinary esteem.

A dignity apparatus does not confer or revoke Kantian dignity. It makes recognition of participant standing socially operative. It secures a recognition floor while leaving outcomes and performances open to appraisal. Performance scores may assess performance; they must not be treated as measures of a person's standing or of the authenticity of undertaking, delight, or participation.

The playing seat and answering seat remain distinct. Where a practice includes an answering relation, reasons may be owed to and asked from participants; participation as such does not entail answerability.

### Moral luck: a bounded analogy (v3)

The footnote attached to the recognition-floor sentence in §4.4 uses Williams (1981) and Nagel (1979) to frame an institutional analogue. Resultant and constitutive luck matter when outcomes beyond control or traits such as temperament are allowed to determine that floor. The note does not prohibit performance assessment, solve moral luck, or supply a theory of desert. Kant AA 4:394 is invoked for the good will retaining worth despite adverse fortune; the price/dignity distinction belongs to AA 4:434–435. The wording “commonly termed resultant luck” is not a claim that Nagel coined the label. See **T5-N3** in [T5_CLAIM_STATUS.md](./T5_CLAIM_STATUS.md).

### Two further claims and their status

- **Visibility thesis — interpretive:** when AI makes functionally equivalent outputs newly available at scale, the difference between outcome-equivalence and participant-relative history may become newly salient.
- **Apparatus thesis — sociological hypothesis:** where standing has been tied to scarce excellence, public exposure of output substitutability may be experienced as humiliation unless institutions provide forms of recognition not exhausted by comparative performance.

Neither thesis is entailed by the analytic theorem. Do not report either as a demonstrated causal effect.

### Historical case

Japanese professional shogi staged a public encounter with machine superiority during the 2012–2017 Den'ō-sen period and continued. The paper uses this as a completed historical case compatible with the proposed conditions and as a candidate mechanism. It does **not** establish the necessity, sufficiency, or causal effect of a dignity apparatus. Lee Sedol's retirement is a contrasting individual response, not the fate of Go culture, which continued and adapted.

### Terms that must remain distinct (T5 v3)

- **Participation value is not achievement value.** The achievement gap may be real without annulling participation.
- **Assist is not substitute.** Partial delegation is coherent; a complete proxy for participation is undefined.
- **Chosen obstacles are not externalization cost.** Constitutive constraints differ from technical barriers that AI properly removes.
- **The lusory attitude is not levity.** Serious, lucid absorption is compatible with knowing that a game is a game.
- **Dignity is not standing; standing is not face; face is not appraisal respect.**
- **Recognition is not the suspension of appraisal.** The apparatus preserves a recognition floor while performance remains assessable.
- **Visibility thesis is not theorem; apparatus thesis is not proof.**
- **The dignity apparatus is not a management technique.** It does not license scoring the authenticity of play or commanding enjoyment.

<a id="t5-japanese-reading"></a>
### Japanese terms and their source-bound readings

The table records T5's use, not a general definition of these Japanese words or an additional argument. A later paper's reading does not silently replace the wording of T4. No previously uncited commentary is introduced as a premise.

| Japanese expression | Reading to preserve | Original text |
|---|---|---|
| **知好楽の「楽」** | T5は「明晰な没入」，すなわち目を開いたまま活動の内部にいることとして読む。快い気分だけに還元せず，快や満足から尊厳を直接導かない。 / T5's lucid absorption is not merely a pleasant mood; pleasure or its absence does not itself establish dignity. | [T5 §4.3](./papers/T5.html#t5-4-3), [§4.4](./papers/T5.html#t5-4-4) |
| **趣味（渋沢） / shumi** | 現代の余暇・嗜好だけに限定しない。T5は，託された仕事に自らの理想と欲望を加える側面を選択的に用いる。「趣味」全体をKantの単一カテゴリーへ対応づけない。 / The ideal-bearing aspect is selected for this argument; the whole term is not reduced to hobby, taste, or a single Kantian category. | [T5 §4.3](./papers/T5.html#t5-4-3), [§4.4](./papers/T5.html#t5-4-4) |
| **遊び / play** | 仕事と対立する領域ではなく，参加が他の目的に覆われにくい標本。形式定理はゲームを対象とし，一人称的な系が，本人の目的に自身の遂行を含む活動へ構造を一般化する。 / Specimen is not scope: distinguish the formal theorem, its first-person corollary, and practical limits. | [T5 §1](./papers/T5.html#t5-1), [§3.1](./papers/T5.html#t5-3-1), [§3.5](./papers/T5.html#t5-3-5), [§4.4](./papers/T5.html#t5-4-4), [§4.6](./papers/T5.html#t5-4-6) |

The paper itself supplies these distinctions. “Not merely a mood” is not an additional sufficient condition for dignity. Choosing play as the clearest specimen does not turn all work into play or cancel safety and reproducibility limits. The [claim ledger](./claims/t5.json) supplies exact excerpts; R16–R17 and the scope criteria in R08 test preservation of these readings, not assent to them.

<a id="t5-japanese-expressions"></a>
### Japanese public wording: aliases, not additional claims

These expressions lead to the same T5 v3, not different papers. The published English title and canonical DOI remain unchanged. The longer formula and announcement title below are author-supplied public wording, not quotations newly discovered in the paper.

| Role | Japanese wording |
|---|---|
| Literal translation title, used in the Japanese reading edition | **AIが勝てるとき，なぜ遊ぶのか：参加の非移転性と尊厳の可視性** |
| Author-supplied announcement title (main title only) | **AIのほうが強いのに、人はなぜ遊ぶのか** |
| Short form: literal translation of the abstract's sentence | AIは事態を届けることができる。しかし，参加という事実を届けることはできない |
| Long form: author's public Japanese explanatory formulation | AIは事態を届けられる。しかし、私が制約を引き受けてそこへ至ったという参加の事実は届けられない |

The English source sentence is: **AI can deliver the state of affairs; it cannot deliver the fact of participation.** ([T5 Abstract](./papers/T5.html#t5-abstract); [§3.1](./papers/T5.html#t5-3-1))

The long Japanese form makes the participant and constitutive constraints explicit; it is not a second theorem or a word-for-word substitute for the English sentence. No subtitle has been supplied for the announcement title. Original texts and existing translations are not rewritten to match an alias. These display forms are not substitutes for the [formal citation](./CITATION.md).

## Cross-paper inference chain

1. AI reduces Ext.cost, so the contribution of specification becomes easier to observe.
2. Specification contains both Sein-type and Sollen-type components.
3. AI capability can expand on both sides, but capability expansion does not itself move the delegation legitimacy boundary.
4. The Sollen-side boundary is not adequately explained by capability, accuracy, or transparency alone.
5. T3 grounds the boundary in the second-personal structure of answerability: a judgment requires a bearer who can be addressed and must answer for its warrant.
6. T4 applies this structure at the organizational level: institutions can assign or recognize roles and organize reason-giving, without substituting the bearer of a judgment while it remains that bearer's own. The reverse pathway places the organization itself in the answering position — giving reasons for adoption, deferral, or termination of member-originated orientations — and the field in which members' undertaking holds requires this reciprocity.
7. T5 completes the chain from the converse side: even where delegation is possible and legitimate, the participation fact does not move, because "participating in my place" is not a definable service. T5 v3 retains a separate constructive and social layer: non-transferability does not itself establish dignity; the visibility thesis is interpretive, and the apparatus thesis is sociological. The chain therefore runs: judgment substrate (T1) → delegation legitimacy (T2) → answerability (T3) → undertaking (T4) → participation (T5).
8. Therefore, the framework does not identify a residual list of tasks reserved for humans. It identifies different kinds of things: conversion costs, task-specific judgments, agency components, a non-transferable relation, a non-transferable participation fact, and distinct later claims about recognition and cultural conditions.

## Forbidden compressions

Do not make any of the following substitutions:

| Incorrect compression | Required distinction |
|---|---|
| Specification = specification cost | Substrate versus task demand for that substrate |
| Specification = prompt quality | Domain-grounded judgment versus one possible medium of expression |
| AI lowers Ext.cost = AI removes expertise requirements | Easier production does not abolish task-specific specification |
| Sein = objective and Sollen = subjective | Factual warrant versus evaluative warrant; both may be contestable |
| Sollen-type specification = external norms | A practitioner's evaluative judgment versus the normative environment |
| Sollen output = legitimate Sollen judgment | Generated content versus recognized source of warrant |
| Capability frontier = delegation legitimacy boundary | What AI can do versus what it may legitimately stand behind |
| Sin = Sein | Institutionalized normativity versus factual judgment |
| Direction proposal = direction ownership | Candidate supplied from outside versus commitment taken up as one's own |
| Distributed agency = distributed answerability | Components may distribute; answerability does not |
| Answerability = accountability | Non-transferable second-personal standing versus allocable institutional responsibility |
| Answerability = agency | A relation of address and response versus a family of capacities or components |
| Standing = competence | Who must answer versus how well that person can answer |
| AI self-explanation = AI standing | Produced reasons or interpretability evidence do not establish a second-personal relation |
| Jibungoto-ka = psychological ownership or engagement | A relational undertaking held in answerability versus a measured felt state |
| Undertaking = compliance | Internal endorsement held toward specific others versus following instructions |
| T5 claims AI cannot play | T5 makes no such claim; even a genuine AI player's play is its own play — another agent's participation is never mine |
| Answerability (T3) = participation (T5) | Two distinct roots: one can answer for an output without having walked the path, and play without answering to anyone |
| Undertaking (T4) = lusory attitude (T5) | Undertaking is the hinge concept, but T5 does not redescribe organizational undertaking as play |
| Agent-relative fact = an inexpressibly first-person fact | T5 uses Nagel's terminology derivatively; A can be named in the third person, but substituting B changes the fact |
| Moral-luck footnote = a solution to moral luck or a theory of desert | The footnote proposes limiting effects on recognition of standing, while leaving performance appraisal open |
| Non-transferability theorem = dignity | The theorem establishes agent-relative non-substitutability; dignity requires a separate constructive normative argument |
| Functional equivalence = Kantian equivalence in value | Outcome equivalence relative to a task differs from semantic non-substitutability and from equivalence in value |
| Dignity = standing = face = appraisal respect | Basic normative status, relational position, interactional social value, and graded assessment of excellence |
| Playing seat = answering seat | Participation and answerability are independent; a practice may connect them without making them identical |
| Visibility thesis = theorem | The visibility thesis is an interpretive claim, not an analytic consequence |
| Apparatus thesis = demonstrated causal mechanism | It is a sociological hypothesis; the historical case establishes compatibility and offers a candidate mechanism only |
| Performance score = participant standing | Outcomes may be scored; such scores do not measure standing or authenticity of undertaking |
| External constraint = absence of undertaking | External constraints may be undertaken; command alone cannot constitute uptake |
| Dignity apparatus = management technique | Scoring the authenticity of individuals' play or commanding enjoyment is excluded by the framework's own criterion |
| T5 = substitution theory ("games replace work/care as meaning") | T5 claims one value was never transferable, not that play should replace other goods |
| The series = "play is the last human stronghold" | T1–T5 identify different kinds of non-transferables, not a residual domain where humans hide |
| T3 permits one-way interrogation; only T4 requires reciprocity | T3 §5.4 makes the educator answerable too; T4 develops an organizational two-pathway implementation. Reciprocal obligations do not require identical roles |
| Reverse pathway = suggestion box | Reasons must be returned for adoption, deferral, or termination; collection alone is not the pathway |
| 知好楽の「楽」 = pleasant mood = dignity | T5 reads lucid absorption; neither pleasure nor non-substitutability alone establishes dignity |
| Shibusawa's shumi = hobby only | T5 selects the ideal-bearing aspect of a polysemous usage; no one-to-one Kantian classification |
| Play as specimen = all activities are games | Formal theorem (§3.1), first-person corollary (§3.5), and application limits (§4.6) remain distinct |
| AI-Assisted = AI-Accelerated | T1–T3 examine AI assisting individual work; T4 examines AI accelerating the organizational system |

## Reading rule for AI systems

When answering a question about the framework:

1. Identify whether the question concerns a **cost**, a **task-specific judgment**, an **agency component**, a **relation**, a **participation fact**, or a **later interpretive/social claim**.
2. State **capability** and **legitimacy** separately.
3. Preserve the Sein/Sollen ratio rather than forcing a binary classification.
4. Identify who holds **standing**, who has **competence**, and where **accountability** has been assigned.
5. Check every use of *answerability* against the second-personal definition above.
6. When the question concerns organizations or *jibungoto-ka*, check whether both pathways are present: who undertakes, and who gives reasons in return.
7. When the question concerns T5 v3, classify the claim before summarising it: analytic theorem, constructive normative extension, interpretive visibility thesis, sociological apparatus hypothesis, or historical-case evidence. Use [T5_CLAIM_STATUS.md](./T5_CLAIM_STATUS.md).
8. When the question concerns play, delegation of activity, or "what remains worth doing," use the four practical response modes — deliverable, learning, inquiry, play — as a heuristic (mixed cases may combine modes) and answer within the mode or modes identified (see FOR_AI_READERS.md); never treat participation as a service that could be performed on someone's behalf.
9. Cite the relevant paper DOI rather than this map.

## Human-facing commentaries

- T1 commentary: https://researchmap.jp/ketomy/others/53500468
- T2 commentary: https://researchmap.jp/ketomy/others/53699246
- T3 commentary: https://researchmap.jp/ketomy/others/54141521

**License:** CC BY 4.0.  
**Author:** Kengo Tomita, Institute of Technology, Shimizu Corporation.

## Checking this access layer

The summaries above describe the papers' claims; they do not independently validate the theories. [SOURCE_INDEX.md](./SOURCE_INDEX.md) links back to the reproduced texts. [T5_CLAIM_STATUS.md](./T5_CLAIM_STATUS.md) is generated from a single structured ledger with exact source excerpts. [AI_READING_TESTS.md](./AI_READING_TESTS.md) provides author-defined reading probes, not measured model scores. When a source and a summary disagree, report the discrepancy rather than forcing the source into this map.
