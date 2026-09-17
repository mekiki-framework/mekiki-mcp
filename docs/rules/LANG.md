# LANG — 原文の言語

| 項目 | 値 |
|---|---|
| 規則ID・版 | LANG-1.0.0 |
| 状態 | 確定（Q21・Q22） |
| 実装 | `mekiki_reader/corpus.py` の `PAPER_LANGUAGE`・`GUIDE_LANGUAGE` |

| 対象 | language |
|---|---|
| T1・T2・T3・T5（papers/*.md） | en |
| T4（papers/T4.md） | ja |
| T4 英訳（translations/T4.en.md） | en（source_kind=translation・translation_note） |
| ガイド類（THEORY_MAP・FOR_AI_READERS・SOURCE_INDEX・T5_CLAIM_STATUS・AI_READING_TESTS・llms.txt） | en |

根拠（`docs/stage0_facts.md`・DECISIONS.md「論文の本文言語」行）：日本語文字数は T1=6・T2=0・T3=0・T4=18003・T5=0。T4 manifest の originalLanguage=ja・inLanguage=en。T4 が日本語であることは llms.txt:29・SOURCE_INDEX.md:12・papers/T4.md:11 にも書かれている。起動時に文字種で判定することはしない（推定を避ける）。
