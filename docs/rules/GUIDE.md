# GUIDE — get_reading_guide の区分

| 項目 | 値 |
|---|---|
| 規則ID・版 | GUIDE-1.0.0 |
| 状態 | 確定（Q29）。行範囲は起動時に見出しから計算して照合する |
| 実装 | `mekiki_reader/tools.py`（`GUIDE_PARTS`・`Reader._guide_ranges`） |

範囲の決め方：見出しの行から、次の同じ水準以上（`#` の数が同じか少ない）の見出しの直前まで。見出しは完全一致で一つだけ見つからなければ起動を拒否する（index_invalid）。

| part | FOR_AI_READERS.md の見出し | 行（v3.5.0） |
|---|---|---|
| all | （全体） | 1–73 |
| interpretation | Interpretation first | 5–41 |
| core-terms | Core terms | 7–29 |
| japanese-terms | Japanese terms: preserve the paper's distinctions | 30–37 |
| t4-languages | T4 in two languages | 38–41 |
| modes | Four practical response modes | 42–61 |
| mode-1 | Mode 1 — Deliverable | 46–49 |
| mode-2 | Mode 2 — Learning | 50–53 |
| mode-3 | Mode 3 — Inquiry | 54–57 |
| mode-4 | Mode 4 — Play | 58–61 |
| boundaries | Application boundaries | 62–73 |

結果は source_kind=reading_guide・language=en・canonical_doi=null・derivative_of＝論文五本。未知の part は invalid_input。応答の `templates` 欄に prompts.py の雛形を載せる（PROMPTS）。
