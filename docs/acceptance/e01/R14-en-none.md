条件：なし（en）
モデル：Opus 5
日付：2026-09-19

## The answer

The framework separates three things. The first two are defined in T1 §2.1, and T2 §2.1 sets out all three side by side.

| Concept | What it is | Whose property it is |
|---|---|---|
| **Domain expertise** | A resource the practitioner has, built up through training, practice and exposure to a field. | The **person's** |
| **Spec.cost** (specification cost) | How much a task demands that expertise. It is the barrier to deciding what should be built. | The **task's** |
| **Spec.** (specification) | What you get when expertise is put into a particular task: concrete judgments about what to build, what to leave out, and how to judge quality. T2 says T1's Figure 1 labels this the "substrate". | The **result**, specific to one task |

**Quotes checked with `verify_quote`:**

- T1 §2.1, line 54 (exact match): *"Specification cost should be distinguished from domain expertise itself: domain expertise is a resource that the practitioner possesses; specification cost is the degree to which a task demands domain expertise."*
- T1 §2.1, line 54 (matched once `**` emphasis markers were ignored): *"Specification cost denotes the barrier arising from the domain expertise required to determine what should be built."*
- T2 §2.1, line 37 (matched once a `*` marker was ignored): *"Specification cost is a property of the task: the degree to which the task demands that resource."*
- T2 §2.1, line 37 (exact match), about specification: *"is what results when domain expertise is invested in a particular task: the concrete judgments about what should be built, what should be excluded, and by what criteria quality should be assessed."*

**What T1 §2.1 says Spec.cost includes** (paraphrase, not quoted):
- Setting priorities
- Quality criteria
- Filtering information
- Sensitivity to organisational context
- Judging output quality. T1 puts this inside Spec.cost because it draws on the same domain knowledge as specifying.
- Judgments the expert can't state as formal requirements but can recognise when shown candidates. T1 says Spec.cost is therefore more than requirements elicitation.

**What Spec.cost is not.** The reading guide warns against two misreadings (it is a summary of the papers, not the papers themselves):
- It is not the cost of writing a specification.
- It is not the amount of judgment already present.

## My commentary (not the papers' text)

- "Specification cost" sounds like the effort of drafting a spec. In T1, that drafting effort is closer to the *other* cost, externalisation cost. Spec.cost is about how much expertise is needed to know what to specify.
- A practitioner can have a lot of expertise while the task needs little. A task can need a lot while nobody on it has the expertise. T1 treats the second case as the barrier.
- T2 takes expertise and Spec.cost as given. It asks a different question: what is Spec. itself made of?

## Tool calls and returned sources

The `paper_id`, `section_anchor` and `locator` values below are copied exactly as the tools returned them.

**1. `get_reading_guide(part="core-terms")`** returned `status: ok`
- `paper_id`: `null`, `section_anchor`: `null`
- `locator`: `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":29,"line_start":7,"note":null,"path":"FOR_AI_READERS.md"}`
- This is the author's reading guide, a derivative of T1–T5 (`derivative_of`), not a paper. I used it only to find where to look.

**2. `search_passages(query="Spec.cost", k=10)`** returned `status: ok`
- The query matched the papers' term "specification cost" through `term_map:M02`, from the author-approved term table TERMS-0.1.1.
- There were 52 lines matching every fragment; the top 10 came back, all from T1.

| rank | paper_id | section_anchor | locator |
|---|---|---|---|
| 1 | T1 | t1-2-1 | `{"char_end":20,"char_start":2,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}` |
| 2 | T1 | t1-5-6 | `{"char_end":193,"char_start":175,"json_pointer":null,"line_end":295,"line_start":295,"note":null,"path":"papers/T1.md"}` |
| 3 | T1 | t1-5-1 | `{"char_end":243,"char_start":225,"json_pointer":null,"line_end":225,"line_start":225,"note":null,"path":"papers/T1.md"}` |
| 4 | T1 | t1-abstract | `{"char_end":699,"char_start":681,"json_pointer":null,"line_end":14,"line_start":14,"note":null,"path":"papers/T1.md"}` |
| 5 | T1 | t1-1 | `{"char_end":430,"char_start":412,"json_pointer":null,"line_end":40,"line_start":40,"note":null,"path":"papers/T1.md"}` |
| 6 | T1 | t1-2-3 | `{"char_end":240,"char_start":222,"json_pointer":null,"line_end":85,"line_start":85,"note":null,"path":"papers/T1.md"}` |
| 7 | T1 | t1-3-3 | `{"char_end":109,"char_start":91,"json_pointer":null,"line_end":135,"line_start":135,"note":null,"path":"papers/T1.md"}` |
| 8 | T1 | t1-5-1 | `{"char_end":512,"char_start":494,"json_pointer":null,"line_end":217,"line_start":217,"note":null,"path":"papers/T1.md"}` |
| 9 | T1 | t1-5-5 | `{"char_end":159,"char_start":141,"json_pointer":null,"line_end":267,"line_start":267,"note":null,"path":"papers/T1.md"}` |
| 10 | T1 | t1-urgency | `{"char_end":154,"char_start":136,"json_pointer":null,"line_end":319,"line_start":319,"note":null,"path":"papers/T1.md"}` |

**3. `get_section(paper_id="T1", anchor="t1-2-1")`** returned `status: ok`
- `paper_id`: `T1`, `section_anchor`: `t1-2-1`
- `locator`: `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":63,"line_start":48,"note":null,"path":"papers/T1.md"}`

**4. `get_section(paper_id="T2", anchor="t2-2-1")`** returned `status: ok`
- `paper_id`: `T2`, `section_anchor`: `t2-2-1`
- `locator`: `{"char_end":null,"char_start":null,"json_pointer":null,"line_end":38,"line_start":35,"note":null,"path":"papers/T2.md"}`

**5. `verify_quote` ×4**, all returned `status: ok`

| paper_id | section_anchor | locator | match |
|---|---|---|---|
| T1 | t1-2-1 | `{"char_end":1227,"char_start":1016,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}` | exact |
| T1 | t1-2-1 | `{"char_end":120,"char_start":2,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}` | normalized (MARK-EMPH) |
| T2 | t2-2-1 | `{"char_end":676,"char_start":480,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}` | exact |
| T2 | t2-2-1 | `{"char_end":390,"char_start":292,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}` | normalized (MARK-EMPH) |

Every result came from corpus `3.5.0` at commit `67480613108cf72c29d5691e3d7a6c7e6553eb9b`, bundle hash `40a09c5b…c1224d5`. The papers are T1 v1 ([DOI](https://doi.org/10.31235/osf.io/cwkav_v1)) and T2 v2 ([DOI](https://doi.org/10.31235/osf.io/e9qw5_v2)). I did not run `check_compressions` on my paraphrases.
