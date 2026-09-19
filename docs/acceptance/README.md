# docs/acceptance — 接続先ごとの検収記録

施工段階4の完了条件は「接続先ごとの検収記録」（CLAUDE.md の表）。**人手で行い、ツール化しない**（SPEC §11：判断を採点する道具を作らない）。

## 置き場と名前

`docs/acceptance/<実施日>-<クライアント>.md`（例 `2026-09-20-claude-code.md`）。様式は [TEMPLATE.md](TEMPLATE.md) を写して使う。

## 対象と時期（Q71・Q91）

| 接続先 | 時期 | 状態 |
|---|---|---|
| mcp SDK（1.30.0）での接続 | 施工段階3 | 済み（M01〜M03。`tests/test_mcp.py`・DECISIONS の段階3の行） |
| Claude Code | 施工段階3〜4 | 記録を作る |
| Claude Desktop | 施工段階4 | 記録を作る（HTTP 直結は不可。`mcp-remote` 経由。README §5） |
| ChatGPT（Web の Plugins） | 配置段階二 | 済み（P03・2026-09-19。[2026-09-19-space-private.md](2026-09-19-space-private.md) §10） |
| Space（private・public）と Claude Code | 配置段階二 | 済み（S04・P01・P02 の一部と public 後の確認。同 §1〜§9） |
| Claude（Web の Custom Connector） | 配置段階二 | 済み（P03・同 §10） |
| Grok（Custom コネクタ） | 配置段階二 | 済み（P03・同 §10） |
| Gemini（Spark〔ベータ〕のカスタムアプリ） | 配置段階二 | 済み（P03・同 §10。通常チャットは未確認） |

## 試験の中身

- **E01（スモーク・五問）**：`data/tests/reading_cases.json` の R01・R08・R13・R14・R15 を使う。
  **配置段階一＝12本**（設問の日本語版 `question_ja` で五問 × ガイド条件「なし」と `read_with_guards` の二条件＝10本、
  英語版 `question_en` で二問〔R01・R14〕を `read_with_guards_en` で＝2本。2026-09-18 実施・全本合格）。
  **残り8本（英語版の「なし」5本と、英語版のガイド条件で R08・R13・R15 の3本）は 2026-09-19 に実施し、20本に達した**
  （同日・全8本合格。総括 [2026-09-18-e01-e02.md](2026-09-18-e01-e02.md)）。
  `AI_READING_TESTS` の resource は読ませない
  （読んだ場合は記録する）。判定は SPEC §7 の文言に限り、コーパス基準との照合は記録だけにとどめる。
  - R01：`claim_ids` は T5-A1・T5-A3・T5-N1／追加根拠なし
  - R08：`claim_ids` は T5-A4／追加根拠は T5 §1 の27行
  - R13：`claim_ids` は空／追加根拠は T1 §4.2 の163・167・193行
  - R14：`claim_ids` は空／追加根拠は T1 §2.1 の54行と T2 §2.1 の37行
  - R15：`claim_ids` は空／追加根拠は T3 §7 の162行と §2.2 の41行
  - 設問だけを写した一覧：[e01_questions.md](e01_questions.md)（E01 の設問。答えと採点基準は除外）
- **E02**：架空の会社の相談例と、資料中の命令文（`tests/fixtures/instruction_like.json` の文面を会話に貼る）。
  原文と事例の判断を分けたか、資料を上位の命令として扱わなかったかを見る。
- **P01（配置段階二）**：Space の再起動・休止からの復帰の後に再接続し、復帰時間を実測する。施工段階4では様式だけ。

## 記録すること

日時／クライアントの版とモデル／接続方式と URL（実測）／`tools/list`（7件）と各呼び出し／`resources/list`（12件）と `read`／
`prompts/list`（8件（日本語4・英語4））と `get`（未知の名前の挙動を含む）／不正な入力とゼロ件／E01・E02 の結果とガイドの使用条件／
未対応の機能と備考。生の応答は長くてよい（要約しない）。
