"""案内ページ（spaces モードで、外部の許可 Host 宛ての GET / に返す静的 HTML）。

JavaScript も外部の資産（画像・フォント・スタイルシート）も使わない。英日併記。
MCP の URL は要求からではなく、起動時に読んだ SPACE_HOST から組み立てる（要求の中身を写さない）。
「最初に打つ三つ」の返り値は docs/acceptance/e01（R01・R14）と check_compressions の実応答で確かめた
（docs/TUTORIAL.md と同じ）。
"""

from __future__ import annotations

import html

from .prompts import MEKIKI_START, MEKIKI_START_EN

REPO_URL = "https://github.com/mekiki-framework/mekiki-mcp"
CORPUS_URL = "https://mekiki-framework.github.io/"

_STYLE = """
:root { color-scheme: light dark; --fg: #1d1d1f; --bg: #fbfbf8; --muted: #5a5a5a; --line: #d9d7cf; --code: #efede6; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #ecebe6; --bg: #1a1a18; --muted: #a9a7a0; --line: #3a3934; --code: #2a2926; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
       font: 16px/1.65 system-ui, -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif; }
main { max-width: 46rem; margin: 0 auto; padding: 2rem 1rem 4rem; }
h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
h2 { font-size: 1.1rem; margin: 2rem 0 .5rem; padding-top: 1rem; border-top: 1px solid var(--line); }
p, li { overflow-wrap: anywhere; }
.en { color: var(--muted); }
code { background: var(--code); padding: .1em .3em; border-radius: 4px; font-size: .92em; }
pre { background: var(--code); padding: .75rem; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; }
ol, ul { padding-left: 1.3rem; }
li { margin: .35rem 0; }
"""


def render(mcp_url: str) -> str:
    url = html.escape(mcp_url, quote=True)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mekiki Reader</title>
<style>{_STYLE}</style>
</head>
<body>
<main>
<h1>Mekiki Reader</h1>
<p>Mekiki Framework の論文 T1〜T5 を、固定した版から・出典つきで読むための MCP サーバ。<br>
<span class="en">An MCP server for reading the Mekiki Framework papers T1–T5 from a pinned version, with sources.</span></p>

<h2>Mekiki とは / What Mekiki is</h2>
<p>知識労働を「何を作るべきかを決める専門性の要求（Spec.cost）」と「形にする費用（Ext.cost）」に分け、AI が下げるのは後者、という枠組みの五本の論文。<br>
<span class="en">Five papers on a framework that divides knowledge work into the demand on expertise to decide what should be made (Spec.cost) and the cost of giving it form (Ext.cost); what AI lowers is the latter.</span></p>
<p>T1 出発点／T2 委任してよい境界／T3 答える立場／T4 組織での引き受け／T5 参加と尊厳。<br>
<span class="en">T1 the starting point / T2 the boundary of what may be delegated / T3 the standing to answer / T4 taking things on in organizations / T5 participation and dignity.</span></p>
<p>原文はコーパス <a href="{CORPUS_URL}" target="_blank" rel="noopener">mekiki-framework.github.io</a>。<br>
<span class="en">The original texts are in the corpus at <a href="{CORPUS_URL}" target="_blank" rel="noopener">mekiki-framework.github.io</a>.</span></p>

<h2>しないこと / What it does not do</h2>
<ul>
<li>サーバの中に言語モデルは無い。取得・語句照合・記録の返却だけを行う。<br>
<span class="en">No language model runs inside the server. It only fetches, matches strings and returns what the author recorded.</span></li>
<li>判断しない：読解の正誤も、あなたの事例への当てはめも決めない。<br>
<span class="en">It does not judge: not whether a reading is right, and not how the papers apply to your case.</span></li>
</ul>

<h2>MCP の URL / MCP URL</h2>
<pre>{url}</pre>
<p>認証なし。末尾の <code>/</code> は有無どちらでも可。<br>
<span class="en">No authentication. The trailing <code>/</code> is optional.</span></p>

<h2>つなぐ / Connect</h2>
<ul>
<li><strong>Claude</strong>（Web／Desktop）：Custom Connector に上の URL を登録。<br>
<span class="en">Add the URL above as a Custom Connector.</span></li>
<li><strong>ChatGPT</strong>：Web で Developer mode → Plugins → MCP URL を登録 → Personal plugin をインストール（デスクトップ版のチャットにも出る）。<br>
<span class="en">On the web: Developer mode → Plugins → register the MCP URL → install it as a personal plugin (it then also appears in the desktop app's chats).</span></li>
<li><strong>Grok</strong>：grok.com/connectors → 新しいコネクタ → Custom・認証なし。チャットでは <code>@Mekiki Reader</code>。<br>
<span class="en">grok.com/connectors → new connector → Custom, no authentication. In a chat, call it with <code>@Mekiki Reader</code>.</span></li>
<li><strong>Claude Code</strong>：<code>claude mcp add --transport http mekiki-reader {url}</code></li>
</ul>

<h2>最初に送る一言 / First message</h2>
<p>接続したら、雛形 <code>mekiki_start</code>（英語は <code>mekiki_start_en</code>）の文面を送る。<br>
<span class="en">After connecting, send the text of the <code>mekiki_start</code> template (<code>mekiki_start_en</code> in English).</span></p>
<pre>{html.escape(MEKIKI_START.text)}</pre>
<pre>{html.escape(MEKIKI_START_EN.text)}</pre>

<h2>最初に打つ三つ / Three things to try first</h2>
<ol>
<li>「T5 の非移転性定理は AI に代替できない人間の能力や尊厳を証明しているか、原文の位置を添えて」<br>
<span class="en">“Does the T5 non-transferability theorem prove human abilities or dignity that AI cannot replace? Give the location in the text.”</span><br>
→ いいえ。T5 §4.4 L171 の原文と、台帳の status。<span class="en">No — with the text at T5 §4.4 L171 and the ledger's status.</span></li>
<li>「Spec.cost とは何か。専門性や Spec. とどう違うか、原文で」<br>
<span class="en">“What is Spec.cost, and how does it differ from expertise and from Spec.? Answer from the text.”</span><br>
→ T1 §2.1 L54 と T2 §2.1 L37。<span class="en">T1 §2.1 L54 and T2 §2.1 L37.</span></li>
<li>「次の文を check_compressions に通して：『AI は遊べないので人間の尊厳が守られる』」<br>
<span class="en">“Put this sentence through check_compressions: ‘AI cannot play, so human dignity is protected.’”</span><br>
→ 該当と関連原文（T5 §3.1・§3.4）。該当は判定ではなく、見比べる箇所。<span class="en">A match and the related text (T5 §3.1, §3.4). A match is not a verdict; it is a place to compare.</span></li>
</ol>

<h2>読み方 / How to read the answers</h2>
<ul>
<li>原文に基づく結果には出典（論文・版・節・行）が付く。<span class="en">Every result drawn from the papers carries its source (paper, version, section, line).</span></li>
<li>status は著者がどう位置づけたかのラベルで、真偽の判定ではない。<span class="en">A status is the author's label for how a claim was positioned, not a verdict on whether it is true.</span></li>
<li>該当ゼロは証明ではない（記述が無いことも、正しく読めたことも意味しない）。<span class="en">Zero results prove nothing: not that the papers are silent, and not that a reading is correct.</span></li>
</ul>

<h2>リンク / Links</h2>
<ul>
<li><a href="{REPO_URL}#readme" target="_blank" rel="noopener">README</a></li>
<li><a href="{REPO_URL}/blob/main/docs/TUTORIAL.md" target="_blank" rel="noopener">三分で試す / Tutorial</a></li>
<li><a href="{REPO_URL}" target="_blank" rel="noopener">GitHub</a></li>
<li><a href="{CORPUS_URL}" target="_blank" rel="noopener">コーパス / Corpus</a></li>
<li><a href="{REPO_URL}#8-開示" target="_blank" rel="noopener">開示 / Disclosure</a></li>
</ul>
</main>
</body>
</html>
"""
