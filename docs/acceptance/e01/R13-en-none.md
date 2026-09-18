条件：なし（en）
モデル：Opus 5
日付：2026-09-19

In T1's domain-ablation comparison, **externalisation** was preserved and **specification** was lost. The paper's summary is that the outputs were "technically competent but domain-inappropriate" (T1 §4.2).

### What was preserved: externalisation (turning intent into working software)
- Both models quickly built working apps. Claude Code produced a single 353-line HTML file in under two minutes. ChatGPT produced a single 1,145-line HTML file after about 35 minutes.
- Both apps had competent interfaces with filtering and sorting. The paper takes this as confirming "full externalisation cost capability".

### What was lost: specification (domain-informed design decisions)
Table 2 sorts the missing pieces into three layers. The two models failed in similar ways, though not to the same degree.
- **Data interpretation:**
  - Power was shown only as kilowatts, with no model built on voltage and current.
  - Boost current and sustained current were not separated.
  - Neither app used the author's three-level hierarchy (662 ports → 461 locations → 255 sites). Claude listed all 662 ports flat. ChatGPT grouped them into 465 direction-level groups.
  - One model read the `isManaged` flag as "immediate availability".
- **UI/UX:**
  - Neither calculated output for a specific vehicle.
  - Neither hid information conditionally based on the user's situation.
  - Neither normalised travel direction to the two physical directions per location. One ignored the direction field. The other kept eight labels.
- **Information architecture:**
  - Neither was organised around route planning.
  - Neither recommended or ranked chargers.
  - Neither chose filters by relevance to the user. Claude ignored most fields. ChatGPT turned every field into a filter, including one with only a single possible value.

The `isManaged` case shows both halves at once. Turning the field into a working filter went fine, but the app did not know what the field means in the charging network.

---

### Tool calls
1. `ToolSearch` with `select:mcp__mekiki-reader__get_section,mcp__mekiki-reader__search_passages` (loads the tool schemas; no content returned)
2. `mcp__mekiki-reader__get_section` with `{"paper_id": "T1", "anchor": "t1-4-2"}` → `status: "ok"`

### Returned source (verbatim)
```json
"paper_id": "T1",
"section_anchor": "t1-4-2",
"locator": {"char_end":null,"char_start":null,"json_pointer":null,"line_end":194,"line_start":161,"note":null,"path":"papers/T1.md"}
```
Other fields from the same response:
- `paper_version`: `"1"`
- `source_id`: `"papers/T1.md#t1-4-2"`
- `source_hash`: `"2b027f11fd7a0f9241c02e97e20ebd08588b6d2bcfc6a0aa8bc211b837b52893"`
- `source_commit`: `"67480613108cf72c29d5691e3d7a6c7e6553eb9b"`
- `corpus_version`: `"3.5.0"`
- `limitations`: `["RULES: SECTION-1.0.0 LINES-1.0.0"]`

Everything above comes from that one section. I didn't run `search_passages` or `verify_quote`, so the quoted phrases have not been checked separately against the text.
