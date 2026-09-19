# docs/rules — 規則の一覧

版の付け方は Q49（意味つき版 MAJOR.MINOR.PATCH。表を持つ規則は、表の正準 JSON の SHA-256 も記す）。**項目を足したら MINOR、既存の値を変えたら MAJOR を上げる**（2026-09-18 著者決定）。**値はそれぞれの規則文書にだけ書く**（一覧に写すと、表を作り直したときに片方だけ古くなるため。Codex② 6）。状態と採用の経緯は `DECISIONS.md` にある。

版の運用規則は main の `72b13eb` 以降の改版に適用。以前の改版は DECISIONS の一覧を正とする。

| 規則ID | 版 | 状態 | 施工段階 | 本文 |
|---|---|---|---|---|
| NORM | 1.2.0（規則8を空白の左右に明記・規則9を追加。表の SHA-256 は [NORM.md](NORM.md)。1.1.0 は MARK-EMPH を追加） | 確定（1.1.0 は著者承認 2026-09-18。1.2.0 は著者の指示 2026-09-19） | 2・検収後・Codex③ | [NORM.md](NORM.md) |
| SEARCH | 1.1.0（ハイフンを語境界に） | 確定（実装済み。順位は語の種類数→直接一致→総出現数→論文順→行番号。SPEC v2.1 §5.3 は方針側の誤りとして v2.2 で訂正） | 2 | [SEARCH.md](SEARCH.md) |
| TERMS | 0.1.1（30項目・語形78。表の SHA-256 は [TERMS.md](TERMS.md)） | 確定（著者承認 2026-09-18） | 2〜4 | [TERMS.md](TERMS.md) |
| CAND | 1.0.0 | 提案（実装済み） | 2 | [CAND.md](CAND.md) |
| NEAR | 1.0.0 | 提案（実装済み） | 2 | [NEAR.md](NEAR.md) |
| GUIDE | 1.0.0 | 確定（実装済み） | 2 | [GUIDE.md](GUIDE.md) |
| LIMITS | 3.1.0（配置モード spaces の値を追加。3.0.0 は Codex③：受付枠を本文の前へ・送信期限・起動の準備・回収されない結果の数え方を変更・ログの項目を追加。2.0.0 は開放経路の値を変更＝旧 SSE を閉じた・長時間接続を追加。1.1.0 は 1.0.0 の値を変えずに項目を追加） | 1.1.0 は確定（著者承認 2026-09-18）。2.0.0・3.0.0・3.1.0 は提案（変更そのものは著者の指示。版の付け方と上限の値は施工判断・値は実測） | 2〜段階一 | [LIMITS.md](LIMITS.md) |
| JSON | 1.0.0 | 提案（実装済み） | 2 | [JSON.md](JSON.md) |
| SCHEMA | 1.0.0 | 提案（実装済み。資料種別の表は著者承認 2026-09-18・derivative_of 欄つき） | 2 | [SCHEMA.md](SCHEMA.md) |
| PATTERNS | 0.2.1（50件。表の SHA-256 は [PATTERNS.md](PATTERNS.md)）・照合 PATTERNS-MATCH-1.1.0（ハイフンを語境界に） | 一覧は確定（著者承認 2026-09-18。0.1.0＝47件は撤回、0.1.1＝49件→0.2.0 で P31・P39 の語形追加と P54 新設→0.2.1 で P54 に英語の語形3つ） | 2〜4 | [PATTERNS.md](PATTERNS.md) |
| PROMPTS | 0.2.0（8件：日本語4・英語4） | 0.1.0 の六つは確定（著者承認 2026-09-18）。0.2.0 の mekiki_start は著者の文面（2026-09-19）、英語版は施工の訳で確認待ち | 2〜4 | [PROMPTS.md](PROMPTS.md) |
| TERMS-SRC | 1.0.0 | 提案（施工用の道具） | 2 | `scripts/find_term_sources.py` |
| PATTERNS-SRC | 1.0.0 | 提案（施工用の道具。`「見出し」：行 "…"` の指定を含む） | 2〜3 | `scripts/build_patterns.py` |
| BUNDLE | 1.0.0 | 提案（実装済み） | 1 | [BUNDLE.md](BUNDLE.md) |
| LINES | 1.0.0 | 提案（実装済み） | 1 | [LINES.md](LINES.md) |
| LANG | 1.0.0 | 確定（実装済み） | 1 | [LANG.md](LANG.md) |
| SECTION | 1.0.0 | 提案（実装済み） | 1 | [SECTION.md](SECTION.md) |
| T4MAP | 1.0.0 | 提案（実装済み） | 1 | [T4MAP.md](T4MAP.md) |
