条件：read_with_guards_en
モデル：Opus 5
日付：2026-09-19

**Question type:** this asks what the text says, so I read the section directly with `get_section`. The list of sections already showed where the experiment is (§4.2), so I didn't need `search_passages`. T1 has no claim ledger, and the question isn't about your own case.

## Tool calls and returned sources (verbatim)

**1. `get_section(paper_id="T1", anchor="t1-4-2")`** → `status: "ok"`
```
"paper_id":"T1","section_anchor":"t1-4-2",
"locator":{"char_end":null,"char_start":null,"json_pointer":null,"line_end":194,"line_start":161,"note":null,"path":"papers/T1.md"}
```

**2. `verify_quote(paper_id="T1", text="Both outputs featured competent user interfaces … confirming full externalisation cost capability.")`** → `status: "ok"`, `match: "exact"`
```
"paper_id":"T1","section_anchor":"t1-4-2",
"locator":{"char_end":394,"char_start":257,"json_pointer":null,"line_end":167,"line_start":167,"note":null,"path":"papers/T1.md"}
```

**3. `verify_quote(paper_id="T1", text="when specification cost is absent, … technically competent but domain-inappropriate.")`** → `status: "ok"`, `match: "exact"`
```
"paper_id":"T1","section_anchor":"t1-4-2",
"locator":{"char_end":533,"char_start":386,"json_pointer":null,"line_end":193,"line_start":193,"note":null,"path":"papers/T1.md"}
```

**4. `verify_quote(paper_id="T1", text="externalisation capacity (converting a field … ) operated flawlessly, but specification (…) was absent.")`** → `status: "ok"`, `match: "exact"`
```
"paper_id":"T1","section_anchor":"t1-4-2",
"locator":{"char_end":837,"char_start":648,"json_pointer":null,"line_end":193,"line_start":193,"note":null,"path":"papers/T1.md"}
```

**5. `check_compressions(<my paraphrase below>)`** → `status: "ok"`, `results: []`. The tool reported "承認済みパターン 50 件（PATTERNS-0.2.1）・該当 0 件", meaning 50 approved patterns were checked and none matched. As the tool itself warns, zero matches doesn't prove my reading is correct.

All results come from corpus 3.5.0, commit `67480613108cf72c29d5691e3d7a6c7e6553eb9b`, T1 version 1 (doi 10.31235/osf.io/cwkav_v1).

## What the text says (verified quotes)

**What was preserved: externalisation.** T1 L167:
> "Both outputs featured competent user interfaces with filtering and sorting capabilities, confirming full externalisation cost capability."

**What was lost: specification.** T1 L193:
> "externalisation capacity (converting a field into a functional UI filter) operated flawlessly, but specification (knowing what the field *means* in the charging network context) was absent."

**How the paper puts the two together.** T1 L193:
> "when specification cost is absent, externalisation cost reduction alone produces artefacts that are technically competent but domain-inappropriate."

## My summary (commentary, not the text)

**Setup (§4.2, L161–165):** Claude Code (Opus 4.6) and ChatGPT 5.2 Pro each got the same 662 charging-port records. The data was raw JSON with abbreviated field names (`im`, `cap`, `typ`) and came with one generic prompt and no follow-up. The paper chose raw API data over the author's CSV because column names like `max_amps` would "encode domain knowledge."

**Preserved (externalisation):** both models quickly built a working single-file HTML app with filtering and sorting. Claude Code took under 2 minutes and produced 353 lines. ChatGPT took about 35 minutes and produced 1,145 lines.

**Lost (specification):** Table 2 lists the missing domain decisions in three layers:
- **Data interpretation:** the apps used kilowatt ratings only, with no voltage/current separation. They didn't distinguish boost from sustained current. They didn't build the 662 → 461 → 255 hierarchy: one app showed all ports flat, and the other grouped them into 465 direction groups. One model misread the `isManaged` flag as "immediate availability."
- **UI/UX:** there was no calculation of output for a specific vehicle and no conditional display logic. Direction labels weren't normalised to two physical directions: one model ignored the field entirely, and the other kept all eight labels.
- **Information architecture:** there was no route-based navigation and no curation or recommendation logic. The filter strategies differed, but neither was chosen for user relevance: one model used minimal filters, and the other made nearly every field a filter.

**How strongly the paper states this:** it calls the experiment "a counterfactual illustration," not a benchmark. It says the convergent pattern across the two models "is consistent with" the framework's prediction; it doesn't claim this proves it. That describes how the author positioned the result, not a verdict on whether it is true.

著者確認：実施日は 9/19
