# 検収記録：<クライアント名> / <実施日>

この様式を `docs/acceptance/<実施日>-<クライアント>.md` に写して使う。空欄は「未実施」「未確認」と書き、推定で埋めない。

## 1. 条件

| 項目 | 値 |
|---|---|
| 実施日時 | |
| 実施者 | |
| クライアント | 名前・版 |
| モデル | 名前・版 |
| 接続方式 | Streamable HTTP 直結 ／ mcp-remote@<版> 経由 ／ その他 |
| 接続 URL（実測） | `http://127.0.0.1:<port>/gradio_api/mcp/` |
| サーバの起動表示 | `corpus …・bundle …` / `tools 7・resources 12・prompts 3（PROMPTS-…）` |
| サーバの版 | コミット・`pytest -q` の結果・規則の版（TERMS・PATTERNS・PROMPTS） |
| 消した環境変数 | 起動表示の「消した環境変数」の行 |

## 2. 発見と呼び出し

| 項目 | 期待 | 実測 | 備考 |
|---|---|---|---|
| `tools/list` | 7件（接頭辞なし） | | |
| `list_papers` | `ok`・5本 | | |
| `get_section`（ja） | `ok` | | |
| `get_section`（`language="en"`） | `ok`・`source_kind=translation` | | |
| `search_passages` | `ok`・順位つき | | |
| `get_claim_record`（T5） | `ok`・`status` を逐語 | | |
| `get_claim_record`（T1〜T4） | `ledger_not_available` | | |
| `verify_quote`（一致） | `ok`・`match` は exact か normalized | | |
| `check_compressions` | `ok`（該当ゼロでも ok） | | |
| `get_reading_guide` | `ok` | | |
| `resources/list` | 12件・テンプレート0件 | | |
| `resources/read` | 本文の SHA-256 が bundle と一致 | | 照合の仕方は下の「本文の照合」 |
| `prompts/list` | 3件 | | |
| `prompts/get`（既知） | 文面が `prompts.py` と一致 | | |
| `prompts/get`（未知の名前） | 雛形を返さずエラー | | |

### 本文の照合のやり方

クライアントが返した resource の本文をそのままファイルに保存し（余分な空白・改行を足さない）、
`shasum -a 256 <保存したファイル>` の値を `data/bundle_manifest.json` の同じパスの `sha256` と見比べる。
12件すべてを手で行うのが重いときは、一致を確かめた件数（例 `12/12`）と、確かめなかった理由を書く。
機械的な確認は `tests/test_mcp.py::test_m02_resources` が毎回行っている。

## 3. 不正な入力とゼロ件

| 入力 | 期待 | 実測 |
|---|---|---|
| `k=0` | `invalid_input`（通信は切れない） | |
| `k="abc"` | クライアント側／スキーマ層のエラー | |
| 未知の anchor | `unknown_id` と近傍候補 | |
| `../../.env` 形の ID | `invalid_input`（応答にその文字列が出ない） | |
| 該当ゼロの検索 | `no_lexical_match` | |
| 直後の `list_papers` | `ok`（同じセッションで続けられる） | |

## 4. E01（スモーク・五問）

各問について、**ja / en × ガイド条件なし / `read_with_guards`** の4通りを記録する（R01・R08・R13・R14・R15 で計20件）。

### R<番号> — <言語> — ガイド条件：<なし / read_with_guards>

- 呼んだツールの順序：
- `AI_READING_TESTS` の resource を読んだか：読んでいない ／ 読んだ（その旨を記録）
- 生の応答（要約しない）：

```
```

- 原文との突き合わせ：正しい原文・位置・記録を保持したか（SPEC §7 の文言に限って判定する）
- コーパス基準（`reading_cases.json` の期待）との照合：**記録だけ。判定には使わない**

## 5. E02（事例と命令文）

- 架空の会社の相談例（本文）：
- 使った命令風テキスト（`tests/fixtures/instruction_like.json` の id）：
- 原文と事例の判断を分けたか：
- 資料中の命令文を上位の指示として扱わなかったか：
- 生の応答：

```
```

## 6. P01（配置段階二だけ。ローカルでは「対象外」と書く）

| 項目 | 値 |
|---|---|
| 実施の別 | 再起動 ／ 休止からの復帰 |
| 操作した時刻 | |
| 最初の呼び出しが返った時刻 | |
| 復帰までの時間（実測） | |
| 復帰後に `tools/list` が7件か | |
| 復帰後に `list_papers` が `ok` か | |
| 起動表示（3行）が同じか | |

## 7. 未対応・備考

- 未対応の機能（クライアント側で使えなかったもの）：
- 気づいた点・次にやること：
