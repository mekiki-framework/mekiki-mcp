# docs/rules — 規則の一覧

版の付け方は Q49（意味つき版 MAJOR.MINOR.PATCH。表を持つ規則は、表の正準 JSON の SHA-256 も記す）。**値はそれぞれの規則文書にだけ書く**（一覧に写すと、表を作り直したときに片方だけ古くなるため。Codex② 6）。状態と採用の経緯は `DECISIONS.md` にある。

| 規則ID | 版 | 状態 | 施工段階 | 本文 |
|---|---|---|---|---|
| NORM | 1.0.0（表の SHA-256 は [NORM.md](NORM.md)） | 確定（実装済み） | 2 | [NORM.md](NORM.md) |
| SEARCH | 1.0.0 | 確定（実装済み。順位は語の種類数→直接一致→総出現数→論文順→行番号。SPEC v2.1 §5.3 は方針側の誤りとして v2.2 で訂正） | 2 | [SEARCH.md](SEARCH.md) |
| TERMS | 0.1.1（30項目・語形78。表の SHA-256 は [TERMS.md](TERMS.md)） | 確定（著者承認 2026-09-18） | 2〜4 | [TERMS.md](TERMS.md) |
| CAND | 1.0.0 | 提案（実装済み） | 2 | [CAND.md](CAND.md) |
| NEAR | 1.0.0 | 提案（実装済み） | 2 | [NEAR.md](NEAR.md) |
| GUIDE | 1.0.0 | 確定（実装済み） | 2 | [GUIDE.md](GUIDE.md) |
| LIMITS | 1.0.0 | 提案（実装済み・値は実測） | 2 | [LIMITS.md](LIMITS.md) |
| JSON | 1.0.0 | 提案（実装済み） | 2 | [JSON.md](JSON.md) |
| SCHEMA | 1.0.0 | 提案（実装済み。資料種別の表は著者承認 2026-09-18・derivative_of 欄つき） | 2 | [SCHEMA.md](SCHEMA.md) |
| PATTERNS | 0.1.1（49件。表の SHA-256 は [PATTERNS.md](PATTERNS.md)）・照合 PATTERNS-MATCH-1.0.0 | 一覧は確定（著者承認 2026-09-18。0.1.0＝47件は撤回） | 2〜4 | [PATTERNS.md](PATTERNS.md) |
| PROMPTS | 0.1.0（6件：日本語3・英語3） | 確定（著者承認 2026-09-18。英語版は `_en` の別名で同版・案B） | 2〜4 | [PROMPTS.md](PROMPTS.md) |
| TERMS-SRC | 1.0.0 | 提案（施工用の道具） | 2 | `scripts/find_term_sources.py` |
| PATTERNS-SRC | 1.0.0 | 提案（施工用の道具。`「見出し」：行 "…"` の指定を含む） | 2〜3 | `scripts/build_patterns.py` |
| BUNDLE | 1.0.0 | 提案（実装済み） | 1 | [BUNDLE.md](BUNDLE.md) |
| LINES | 1.0.0 | 提案（実装済み） | 1 | [LINES.md](LINES.md) |
| LANG | 1.0.0 | 確定（実装済み） | 1 | [LANG.md](LANG.md) |
| SECTION | 1.0.0 | 提案（実装済み） | 1 | [SECTION.md](SECTION.md) |
| T4MAP | 1.0.0 | 提案（実装済み） | 1 | [T4MAP.md](T4MAP.md) |
