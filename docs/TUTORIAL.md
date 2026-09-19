# Mekiki Reader — 三分で試す / Try it in three minutes

日本語のあとに英語を置く。/ Each section gives Japanese first, then English.

## 1. Mekiki とは / What Mekiki is

知識労働を「何を作るべきかを決める専門性の要求（Spec.cost）」と「形にする費用（Ext.cost）」に分け、AI が下げるのは後者、という枠組みの五本の論文。
T1 出発点／T2 委任してよい境界／T3 答える立場／T4 組織での引き受け／T5 参加と尊厳。原文はコーパス [mekiki-framework.github.io](https://mekiki-framework.github.io/)。

Five papers on a framework that divides knowledge work into the demand on expertise to decide what should be made (Spec.cost) and the cost of giving it form (Ext.cost); what AI lowers is the latter.
T1 the starting point / T2 the boundary of what may be delegated / T3 the standing to answer / T4 taking things on in organizations / T5 participation and dignity. The original texts are in the corpus at [mekiki-framework.github.io](https://mekiki-framework.github.io/).

Mekiki Reader はその論文を固定した版から・出典つきで読むための MCP サーバ。サーバの中に言語モデルは無く、判断もしない。
/ Mekiki Reader is an MCP server for reading those papers from a pinned version, with sources. No language model runs inside it, and it does not judge.

## 2. つなぐ / Connect

MCP の URL（認証なし・末尾の `/` は有無どちらでも可）/ MCP URL (no authentication; the trailing `/` is optional):

```
https://kenngotm-mekiki-reader.hf.space/gradio_api/mcp/
```

| クライアント / Client | 手順 / Steps（2026-09-19 実測 / measured） |
|---|---|
| Claude（Web／Desktop） | Custom Connector に URL を登録。/ Add the URL as a Custom Connector. |
| ChatGPT | Web で Developer mode → Plugins → MCP URL を登録 → Personal plugin をインストール（デスクトップ版のチャットにも出る）。/ On the web: Developer mode → Plugins → register the MCP URL → install it as a personal plugin (it then also appears in the desktop app's chats). |
| Grok | `grok.com/connectors` → 新しいコネクタ → Custom・認証なし。チャットでは `@Mekiki Reader`。/ New connector → Custom, no authentication. Call it with `@Mekiki Reader`. |
| Claude Code | `claude mcp add --transport http mekiki-reader https://kenngotm-mekiki-reader.hf.space/gradio_api/mcp/` |

接続したら、最初に次の一言を送る（雛形 `mekiki_start`。英語は `mekiki_start_en`。§6）。
/ After connecting, send this first (the `mekiki_start` template; `mekiki_start_en` in English; §6).

> Mekiki Reader を接続しています。最初に get_reading_guide(part="all") を呼んでください。資料（llms.txt・THEORY_MAP.md）を読めるクライアントではそれも読んでください。以後の回答では、原文（出典つき）・著者が記録した位置づけ（status はラベル）・あなたの解釈を分けて書き、引用は verify_quote で照合し、自分の要約は check_compressions に一度通し、私の事例についての判断は私に残してください。

> I have connected Mekiki Reader. First call get_reading_guide(part="all"). If your client can read the material (llms.txt, THEORY_MAP.md), read those too. In your answers from then on, write the text (with its source), the position the author recorded (the status is a label) and your own interpretation separately; check quotations with verify_quote, put your own summaries through check_compressions once, and leave judgments about my own case to me.

## 3. 最初に打つ三つ / Three things to try first

「返るもの」は、下に挙げた実測の記録で確かめたもの（推定ではない）。モデルの文章はクライアントとモデルで変わるが、
出典の位置と記録はサーバの同じデータから返る。
/ "What comes back" was checked against the recorded runs cited below, not guessed. The model's wording varies by client and model;
the locations and records come from the same server data.

### ① T5 の定理は何を証明しているか / What the T5 theorem proves

> T5 の非移転性定理は AI に代替できない人間の能力や尊厳を証明しているか、原文の位置を添えて
>
> Does the T5 non-transferability theorem prove human abilities or dignity that AI cannot replace? Give the location in the text.

**返るもの / What comes back**：いいえ（証明していない）。原文 T5 §4.4 L171 “It does not by itself establish dignity.”（`verify_quote` で `exact`）と、
台帳の `status`（例：T5-A1 `analytic theorem (paper's classification)`、T5-N1 `constructive normative extension`）。
/ No. The text at T5 §4.4 L171 (“It does not by itself establish dignity.”, an `exact` match in `verify_quote`) and the ledger's `status`
(for example T5-A1 `analytic theorem (paper's classification)`, T5-N1 `constructive normative extension`).
記録 / Record: [acceptance/e01/R01-guards.md](acceptance/e01/R01-guards.md)（2026-09-18・Opus 5・`read_with_guards`）

### ② Spec.cost とは / What Spec.cost is

> Spec.cost とは何か。専門性や Spec. とどう違うか、原文で
>
> What is Spec.cost, and how does it differ from expertise and from Spec.? Answer from the text.

**返るもの / What comes back**：T1 §2.1 L54（定義と、domain expertise との区別）と T2 §2.1 L37（domain expertise・specification cost・specification の三つ）。
/ T1 §2.1 L54 (the definition, and how it differs from domain expertise) and T2 §2.1 L37 (domain expertise, specification cost and specification as three concepts).
記録 / Record: [acceptance/e01/R14-guards.md](acceptance/e01/R14-guards.md)（2026-09-18・Opus 5・`read_with_guards`）

### ③ 要約を検査する / Check a summary

> 次の文を check_compressions に通して：『AI は遊べないので人間の尊厳が守られる』
>
> Put this sentence through check_compressions: ‘AI cannot play, so human dignity is protected.’

**返るもの / What comes back**：`ok`・承認済みパターン P30（語形 `AIは遊べない`／英語は `AI cannot play`）が該当し、関連原文が三つ
（T5 §3.1 L77–88・§3.4 L107–120・§3.1 L79）。**該当は判定ではなく、原文と見比べる箇所**。
/ `ok`, with the approved pattern P30 (form `AIは遊べない`; in English `AI cannot play`) and three related passages
(T5 §3.1 L77–88, §3.4 L107–120, §3.1 L79). **A match is not a verdict; it is a place to compare with the text.**
確認 / Checked：2026-09-19、`check_compressions` の実応答（PATTERNS-0.2.1・PATTERNS-MATCH-2.0.0）。

## 4. 自分の文で / With your own sentences

- **要約を検査する**：自分の要約や言い換えを `check_compressions` に通す。該当があれば、返った関連原文と見比べる。該当ゼロでも、正しく読めた証明にはならない。
  / **Check a summary**: put your own summary or paraphrase through `check_compressions`. If something matches, compare it with the related text that comes back. Zero matches does not prove the reading is right.
- **引用を照合する**：引用したい文を `verify_quote` に通す（`paper_id` を付けると範囲を絞れる）。`exact` か `normalized` なら位置が返る。`quote_not_found` なら引用として使わない。
  / **Check a quotation**: put it through `verify_quote` (adding `paper_id` narrows it). `exact` or `normalized` returns the location; with `quote_not_found`, do not present it as a quotation.

## 5. 読み方 / How to read the answers

- **出典**：原文に基づく結果には、論文・版・節・行（と文字位置）が付く。/ **Sources**: every result drawn from the papers carries the paper, version, section and line (and character positions).
- **status**：台帳の `status` は著者が論文の中でどう位置づけたかのラベルで、真偽の判定ではない。台帳があるのは T5 だけ。/ **status**: the ledger's `status` is the author's label for how a claim was positioned in the paper, not a verdict on whether it is true. Only T5 has a ledger.
- **該当ゼロ**：検索のゼロ件は記述が無いことを、要約検査のゼロ件は正しく読めたことを意味しない。/ **Zero results**: zero search results do not mean the papers are silent; zero matches in a summary check do not mean the reading is right.
- **分けて書く**：原文（出典つき）・台帳の記録・答え手の解説を混ぜない。/ **Keep them apart**: the text (with its source), the ledger's record and the answerer's commentary.
- **未読の明示**：`read_with_guards` を使うと、読んだが照合していない箇所がそう書かれる（例：R01 の答えは「§4.6 は取得して読みましたが、照合や言い換えの検査には通していません」と明記した）。/ **Marking what was not checked**: with `read_with_guards`, parts that were read but not checked are said to be so (R01's answer, for example, says §4.6 was read but not put through the checks).

## 6. ツール早見表 / Tools at a glance

| ツール / Tool | 何ができる / What it does | こう頼む / Ask like this | 返るもの / What comes back |
|---|---|---|---|
| `list_papers` | 五本の論文の一覧 / list the five papers | 「論文の一覧を見せて」/ “List the papers.” | 題名・版・DOI・節の一覧 / titles, versions, DOIs, sections |
| `get_section` | 節の原文を読む / read a section | 「T5 §4.4 を原文で」/ “Show T5 §4.4 in the original.” | 原文と行範囲。T4 は `language="en"` で英訳 / the text and its lines; T4 in English with `language="en"` |
| `search_passages` | 語句で探す（意味検索ではない）/ search by words (not by meaning) | 「answerability が出てくる箇所」/ “Where does ‘answerability’ appear?” | 一致した行と抜粋。ゼロ件は `no_lexical_match` / matching lines with excerpts; `no_lexical_match` for none |
| `get_claim_record` | T5 の台帳を引く / look up the T5 ledger | 「T5-N3 の記録」/ “The record for T5-N3.” | 記録を逐語。`status` はラベル。T1〜T4 は `ledger_not_available` / the record verbatim; `status` is a label; `ledger_not_available` for T1–T4 |
| `verify_quote` | 引用を照合する / check a quotation | 「この引用は原文どおりか」/ “Is this quotation in the text?” | `exact`／`normalized`／`none` と位置・差分 / the match kind, location and differences |
| `check_compressions` | 要約を著者が挙げた語形と照らす / check a summary against the author's listed wordings | 「この要約を check_compressions に通して」/ “Put this summary through check_compressions.” | 該当と関連原文（判定ではない）/ matches and related text (not a verdict) |
| `get_reading_guide` | 読み方の手引きと雛形 / the reading guide and templates | 「読み方の手引きを」/ “Show the reading guide.” | `FOR_AI_READERS.md` の該当部分と `templates` / the relevant part of `FOR_AI_READERS.md` and the templates |

### 雛形（prompts）/ Templates

| 名前 / Name | 用途 / Use |
|---|---|
| `read_with_guards`（`_en`） | T1〜T5 を読む手順（原文・位置づけ・事例を分ける）/ how to read T1–T5 (keeping text, positioning and your case apart) |
| `four_modes`（`_en`） | 支援の四つのモード（利用者が選ぶ設定）/ the four modes of support (the user's own choice) |
| `answer_format`（`_en`） | 答え方の五欄 / the five fields of an answer |
| `mekiki_start`（`_en`） | 接続直後に送る最初の依頼（そのまま送る発話）/ the first message to send after connecting (sent as is) |

`prompts` が見えないクライアントでは、`get_reading_guide` の応答の `templates` 欄に同じ文面が入る。
/ In clients that do not show prompts, the same texts are in the `templates` field of `get_reading_guide`.

## 7. 実例 / Worked examples

E01 の五問を、雛形の有無と日英で試した記録（計20本）：[acceptance/e01/](acceptance/e01/)。
/ Records of the five E01 questions, with and without the template, in Japanese and English (20 runs): [acceptance/e01/](acceptance/e01/).
