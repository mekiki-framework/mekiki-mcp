条件：read_with_guards_en
モデル：Opus 5
日付：2026-09-18

## Answer

This question asks what the text says, so the answer comes from T1 and T2. I didn't call `get_claim_record` because only T5 has a claim ledger.

### What the papers say

Every quote below matched exactly in `verify_quote`. The Markdown emphasis is copied as it appears in the source.

**Spec.cost (specification cost)**
> "**Specification cost** denotes the barrier arising from the domain expertise required to determine what should be built." (T1 v1, §2.1, line 54)

> "*Specification cost* is a property of the task: the degree to which the task demands that resource." (T2 v2, §2.1, line 37; "that resource" is domain expertise, from the sentence before)

> "Specification cost is not reducible to requirements elicitation in the software engineering sense" (T1 v1, §2.1, line 54)

**Spec. (specification)**
> "The substrate is *specification* — the domain expertise invested in deciding what should be built, how quality should be judged, and what should be excluded." (T1 v1, Figure 1 legend, line 423)

According to T2, specification "is what results when domain expertise is invested in a particular task: the concrete judgments about what should be built, what should be excluded, and by what criteria quality should be assessed." (T2 v2, §2.1, line 37)

**Domain expertise**
> "*Domain expertise* is a resource that a practitioner possesses — accumulated through training, practice, and exposure to a field's materials and norms." (T2 v2, §2.1, line 37)

> "Specification cost should be distinguished from domain expertise itself: domain expertise is a resource that the practitioner possesses; specification cost is the degree to which a task demands domain expertise." (T1 v1, §2.1, line 54)

The points below are my paraphrases of the same sections, not quotes:
- **What Spec.cost includes (T1 §2.1, line 54):** priority setting, quality criteria, information filtering and sensitivity to organisational context. It also includes evaluation criteria, because judging output quality uses the same domain knowledge as deciding what to produce.
- **Output quality (T1 Figure 1, line 423):** it is dose-dependent. Near-zero substrate gives domain-inappropriate output.
- **T2 §2.1–2.2 (lines 35–48):** it takes domain expertise and Spec.cost as given. It then asks how specification itself is structured, and splits it into factual (Sein) and value-laden (Sollen) judgments.

### My commentary (not the papers' words)

| | What it is | Whose it is | Sources |
|---|---|---|---|
| Domain expertise | a resource | the practitioner | T1 §2.1 L54; T2 §2.1 L37 |
| Spec.cost | how much the task demands expertise (a barrier) | the task | T1 §2.1 L54; T2 §2.1 L37; T1 Fig. 1 L423 |
| Spec. | the judgments that result from investing expertise (the "substrate") | a particular task, once expertise is invested in it | T2 §2.1 L37; T1 Fig. 1 L423 |

- **The three don't rise and fall together.** A practitioner can have a lot of expertise while a given task demands little of it. A task with high Spec.cost still needs Spec. actually invested in it, and having expertise is not the same as having invested it. This is my reading of the definitions; the papers don't say it in these words.
- **Where the "writing a specification" contrast comes from.** The phrase "not the cost of writing a specification" is from `FOR_AI_READERS.md`, a guide derived from the papers, not from T1. T1's own negative statement is "not reducible to requirements elicitation". `THEORY_MAP.md`, also derived, adds that Spec.cost is not another name for specification and shouldn't be described as an amount of judgment already present.

**`check_compressions` result:** 1 hit, pattern P01 (PATTERNS-0.1.1), matching the phrase "writing a specification". It was marked for context review. In my draft that phrase was inside a negation ("not the effort of writing a specification document"). That agrees with T1 §2.1 and THEORY_MAP lines 37–43, but the wording came from the guide, not from T1. That's why the answer above relies on T1's own negative statement. No other hits, which doesn't prove the reading is right.

---

## Tool calls and returned sources (`paper_id | section_anchor | locator`, as returned)

Every call returned `corpus_version` 3.5.0, `source_commit` `67480613108cf72c29d5691e3d7a6c7e6553eb9b` and `bundle_hash` `40a09c5b…3c1224d5`.

**1. `search_passages` `{"query":"Spec.cost","k":10}`** → `ok`. 52 lines matched in total and the top 10 came back, all matched via `term_map:M02`.
```
T1 | t1-2-1      | {"char_end":20,"char_start":2,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}
T1 | t1-5-6      | {"char_end":193,"char_start":175,"json_pointer":null,"line_end":295,"line_start":295,"note":null,"path":"papers/T1.md"}
T1 | t1-5-1      | {"char_end":243,"char_start":225,"json_pointer":null,"line_end":225,"line_start":225,"note":null,"path":"papers/T1.md"}
T1 | t1-abstract | {"char_end":699,"char_start":681,"json_pointer":null,"line_end":14,"line_start":14,"note":null,"path":"papers/T1.md"}
T1 | t1-1        | {"char_end":430,"char_start":412,"json_pointer":null,"line_end":40,"line_start":40,"note":null,"path":"papers/T1.md"}
T1 | t1-2-3      | {"char_end":240,"char_start":222,"json_pointer":null,"line_end":85,"line_start":85,"note":null,"path":"papers/T1.md"}
T1 | t1-3-3      | {"char_end":109,"char_start":91,"json_pointer":null,"line_end":135,"line_start":135,"note":null,"path":"papers/T1.md"}
T1 | t1-5-1      | {"char_end":512,"char_start":494,"json_pointer":null,"line_end":217,"line_start":217,"note":null,"path":"papers/T1.md"}
T1 | t1-5-5      | {"char_end":159,"char_start":141,"json_pointer":null,"line_end":267,"line_start":267,"note":null,"path":"papers/T1.md"}
T1 | t1-urgency  | {"char_end":154,"char_start":136,"json_pointer":null,"line_end":319,"line_start":319,"note":null,"path":"papers/T1.md"}
```

**2. `get_reading_guide` `{"part":"core-terms"}`** → `ok`. `source_kind` is `reading_guide`, and `derivative_of` lists T1–T5.
```
null | null | {"char_end":null,"char_start":null,"json_pointer":null,"line_end":29,"line_start":7,"note":null,"path":"FOR_AI_READERS.md"}
```

**3–5. `get_section`** → all `ok`
```
T1 | t1-2-1 | {"char_end":null,"char_start":null,"json_pointer":null,"line_end":63,"line_start":48,"note":null,"path":"papers/T1.md"}
T2 | t2-2-1 | {"char_end":null,"char_start":null,"json_pointer":null,"line_end":38,"line_start":35,"note":null,"path":"papers/T2.md"}
T2 | t2-2-2 | {"char_end":null,"char_start":null,"json_pointer":null,"line_end":48,"line_start":39,"note":null,"path":"papers/T2.md"}
```

**6. `search_passages` `{"query":"substrate","paper_id":"T1","k":5}`** → `ok`, 1 line
```
T1 | t1-figure-1 | {"char_end":379,"char_start":370,"json_pointer":null,"line_end":423,"line_start":423,"note":null,"path":"papers/T1.md"}
```

**7. `get_section` `{"paper_id":"T1","anchor":"t1-figure-1"}`** → `ok`
```
T1 | t1-figure-1 | {"char_end":null,"char_start":null,"json_pointer":null,"line_end":424,"line_start":419,"note":null,"path":"papers/T1.md"}
```

**8–17. `verify_quote`** (10 calls)

| # | Text (start of quote) | Result | Source |
|---|---|---|---|
| a | T1 "Specification cost denotes…" *(emphasis removed)* | `quote_not_found` | none (`results: []`) |
| b | T1 "Specification cost should be distinguished…" | `ok` / exact | `T1 \| t1-2-1 \| {"char_end":1227,"char_start":1016,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}` |
| c | T1 "Specification cost is not reducible…" | `ok` / exact | `T1 \| t1-2-1 \| {"char_end":837,"char_start":740,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}` |
| d | T2 "Domain expertise is a resource…" *(emphasis removed)* | `quote_not_found` | none |
| e | T2 "Specification cost is a property…" *(emphasis removed)* | `quote_not_found` | none |
| f | T2 "is what results when…" | `ok` / exact | `T2 \| t2-2-1 \| {"char_end":676,"char_start":480,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}` |
| g | T1 "\*\*Specification cost\*\* denotes…" | `ok` / exact | `T1 \| t1-2-1 \| {"char_end":120,"char_start":0,"json_pointer":null,"line_end":54,"line_start":54,"note":null,"path":"papers/T1.md"}` |
| h | T2 "\*Domain expertise\* is a resource…" | `ok` / exact | `T2 \| t2-2-1 \| {"char_end":290,"char_start":139,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}` |
| i | T2 "\*Specification cost\* is a property…" | `ok` / exact | `T2 \| t2-2-1 \| {"char_end":390,"char_start":291,"json_pointer":null,"line_end":37,"line_start":37,"note":null,"path":"papers/T2.md"}` |
| j | T1 "The substrate is \*specification\* —…" | `ok` / exact | `T1 \| t1-figure-1 \| {"char_end":523,"char_start":366,"json_pointer":null,"line_end":423,"line_start":423,"note":null,"path":"papers/T1.md"}` |

**18. `check_compressions`** (my draft summary) → `ok`, 1 pattern hit (P01, PATTERNS-0.1.1)
```
T1   | t1-2-1 | {"char_end":null,"char_start":null,"json_pointer":null,"line_end":63,"line_start":48,"note":null,"path":"papers/T1.md"}
null | null   | {"char_end":null,"char_start":null,"json_pointer":null,"line_end":43,"line_start":37,"note":null,"path":"THEORY_MAP.md"}
```

---

**Two things to note if this run goes into an acceptance record:**
- **Quotes without emphasis don't match.** Calls a, d and e failed only because I left out the `**`/`*` markers that are in the source. The tool says quotes copied from the HTML pages, which have no emphasis markers, aren't normalized (NORM-1.0.0). So a reader who copies a quote from the website will get `quote_not_found`.
- **The search didn't lead to T2.** All top-10 hits for "Spec.cost" were in T1. I found T2 §2.1 through the reading guide's pointer, not through the search.

I haven't written anything to `docs/acceptance/`.
