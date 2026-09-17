# PROMPTS — 読み方の雛形

| 項目 | 値 |
|---|---|
| 規則ID・版 | PROMPTS-0.1.0（6件：日本語3・英語3） |
| 状態 | 確定（Q39。著者承認 2026-09-18・日本語のみ）。`prompts.py` の `PROMPTS_STATUS="approved"`・`APPROVED_ON="2026-09-18"` |
| 実装 | `mekiki_reader/prompts.py`（MCP の prompts と get_reading_guide の templates が同じ定数を返す） |

- 雛形は read_with_guards・four_modes・answer_format と、その英語版 `read_with_guards_en`・`four_modes_en`・`answer_format_en` の六つ（SPEC v2.2 §6・案B）。文面の全体は `prompts.py` にある。
- 英語版は別名で同じ版に登録する。引数（`language`）で切り替える方式は採らない。`templates` 欄の各要素には `language`（ja/en）が付く。
- 六つとも定型文「この雛形は、利用者が明示的に選んだときだけ使う。接続先の上位規則や利用者の明示的な意図を上書きしない。」（英語版は `Use this template only when the user has explicitly chosen it. It is not a higher-priority instruction than the host's own rules or the user's stated intent, and does not override them.`）を含む。read_with_guards と read_with_guards_en はさらに資料を指示として扱わない旨の一文を含む。
- four_modes の各モード名は FOR_AI_READERS.md の見出しと一致させ、モードの中身は言い換えずに get_reading_guide(part="modes") へ案内する。
- 英語版は施工段階4で著者が承認した（2026-09-18・案B）。起草と日英の対応は `docs/candidates/prompts_en_v0.md`。

## 未知の prompt 名（Q64・2026-09-18 実測）

上流（gradio 6.27.0）の `prompts/get` は、名前が一致しないとき endpoint 一覧の最後を実行する。そこで `app.py` は、
ツール・resources・prompts のどれにも載らない番兵（`_mcp_type="sentinel"`）を最後に登録し、呼ばれたら例外にする。
実測では、番兵の文面（`gr.Error`）も `show_error=True` もクライアントには届かず、`McpError: 'data'` として返る。
要求された prompt 名は endpoint に渡らないため、文面に名前を入れることもできない。README の接続手順に明記する。
