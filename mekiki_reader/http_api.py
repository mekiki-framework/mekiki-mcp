"""HTTP 併設（SPEC v2.5.4 §2.12・docs/rules/HTTP.md の HTTP-1.3.0）の、通信に触れない部分。

経路の表・引数の読み取り・表現の選択（JSON か Markdown か）・Markdown の組み立て・ETag。標準ライブラリだけで、
gradio も七ツールも import しない。ツールを呼ぶのは app.py の Guard の中で、MCP と同じ入口の関数を使う
（同じ入力なら MCP と同じ JSON 文字列になる）。入力の上限と形の検査はツールの側にあり、ここでは HTTP の形
（引数の名前・重複・百分率符号化・文字コード・本文の JSON）だけを見る。

百分率復号は自前（`_unquote`）。`urllib.parse` を使わないのは、`mekiki_reader` が通信系の module を import しない
という静的検査（`tests/test_safety.py::test_s03_reader_has_no_network_imports`。`urllib` は `urllib.request` を含む
パッケージなので名前ごと禁じている）に従うため。規則は docs/rules/HTTP.md §2。
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

HTTP_VERSION = "HTTP-1.3.0"  # 1.1.0：verify に language。1.2.0：要求行の上限・同名ヘッダの結合。1.3.0：HTML 表現と format
PREFIX = "/api/v1/"
NAMESPACE = "/api"  # 早期拒否にも共通ヘッダを付ける範囲（`/api` と `/api/…`。未知の版・経路を含む）
REQUEST_TARGET_MAX = 16 * 1024  # 要求行の経路＋問い合わせ（`?` を含むバイト数）。超えたら 414（HTTP-1.2.0）
QUERY_FIELDS_MAX = 8  # 問い合わせの項目数（どの経路も引数は3つまで。空の項目は数えない）
CACHE_GET = "public, max-age=3600"  # GET の読み取り応答（データは版で固定）
CACHE_NONE = "no-store"             # POST・400・404・そのほか
JSON_TYPE = "application/json; charset=utf-8"
MARKDOWN_TYPE = "text/markdown; charset=utf-8"
HTML_TYPE = "text/html; charset=utf-8"
# 表現（HTTP-1.3.0）。引数 format は九経路すべてで問い合わせに置ける（POST でも問い合わせに置けるのは format だけ）
REPRESENTATIONS = ("json", "markdown", "html")
FORMAT = "format"
HTML_HEADERS = ((b"content-security-policy", b"default-src 'none'; style-src 'unsafe-inline'"),
                (b"referrer-policy", b"no-referrer"))


@dataclass(frozen=True)
class Route:
    """経路一つ（メソッドと経路の組）。params は問い合わせ（GET）か本文の JSON（POST）で受ける引数。"""

    name: str
    method: str
    path: str
    tool: "str | None"
    params: tuple[str, ...]
    path_params: tuple[str, ...] = ()


# 九経路（SPEC §2.12。並びは試験と README・HTTP.md の表と同じ）
ROUTES: tuple[Route, ...] = (
    Route("index", "GET", "/api/v1/", None, ()),
    Route("papers", "GET", "/api/v1/papers", "list_papers", ()),
    Route("section", "GET", "/api/v1/papers/{paper_id}/sections/{anchor}", "get_section", ("language",),
          ("paper_id", "anchor")),
    Route("search", "GET", "/api/v1/search", "search_passages", ("q", "paper_id", "k")),
    Route("claims", "GET", "/api/v1/claims", "get_claim_record", ("claim_id", "query")),
    Route("guide", "GET", "/api/v1/guide", "get_reading_guide", ("part",)),
    Route("verify", "GET", "/api/v1/verify", "verify_quote", ("text", "paper_id", "language")),
    Route("verify", "POST", "/api/v1/verify", "verify_quote", ("text", "paper_id", "language")),
    Route("check", "POST", "/api/v1/check", "check_compressions", ("text",)),
)
_SECTION_RE = re.compile(r"/api/v1/papers/([^/]+)/sections/([^/]+)")
_EXACT = {r.path: r.name for r in ROUTES if not r.path_params}
_PERCENT = re.compile(rb"%([0-9A-Fa-f]{2})")
_BAD_PERCENT = re.compile(rb"%(?![0-9A-Fa-f]{2})")  # `%` の後に16進2桁が続かない（`%`・`%G1`・`%4`）


class HttpInputError(ValueError):
    """HTTP の形の誤り（引数の名前・重複・文字コード・本文）。invalid_input として 400 で返す。"""


def in_namespace(path: str) -> bool:
    """HTTP 併設の名前空間（`/api` か `/api/` で始まる経路）。早期拒否の応答にも共通ヘッダを付ける。"""
    return path == NAMESPACE or path.startswith(NAMESPACE + "/")


def common_headers(cache: str = CACHE_NONE) -> list[tuple[bytes, bytes]]:
    """HTTP 併設のすべての応答に付けるヘッダ（Guard の早期拒否と `_send_api` で共通。HTTP-1.2.0）。"""
    return [(b"cache-control", cache.encode("ascii")), (b"vary", b"Accept"), (b"x-content-type-options", b"nosniff")]


def target_length(raw_path: bytes, query_string: bytes) -> int:
    """要求行の経路＋問い合わせのバイト数（`?` を含む。問い合わせが空なら経路だけ）。"""
    return len(raw_path) + (1 + len(query_string) if query_string else 0)


def joined(headers: Sequence[tuple[bytes, bytes]], name: bytes) -> "str | None":
    """同名のリスト型ヘッダ（Accept・If-None-Match）を、全行を順序どおりカンマで結合して一つにする（RFC 9110 §5.2）。
    無ければ None。Host・Content-Length の重複拒否はこれを使わない（Guard の既存の検査）。"""
    values = [v.decode("latin-1", "replace") for k, v in headers if k.lower() == name]
    return ", ".join(values) if values else None


def match(path: str) -> "tuple[str, dict[str, str]] | None":
    """経路の名前と、経路に埋めた値。どれにも当たらなければ None（404）。末尾の / の付け外しは別の経路。"""
    if path in _EXACT:
        return _EXACT[path], {}
    m = _SECTION_RE.fullmatch(path)
    if m:
        return "section", {"paper_id": m.group(1), "anchor": m.group(2)}
    return None


def methods(name: str) -> tuple[str, ...]:
    """経路が受けるメソッド（ほかは 405）。"""
    return tuple(r.method for r in ROUTES if r.name == name)


def route(name: str, method: str) -> Route:
    return next(r for r in ROUTES if r.name == name and r.method == method)


# ---------------------------------------------------------------- 引数


def parse_query(raw: bytes, allowed: Sequence[str]) -> dict[str, str]:
    """問い合わせを読む。`+` は空白、`%XX` はそのバイト、全体を UTF-8（厳格）で読む。名前は allowed だけ・
    重複なし・項目は8つまで。形の崩れた `%` と UTF-8 でない列は HttpInputError（400）。

    生の UTF-8（百分率符号化していないもの）も受ける。空の項目（`&&`）は飛ばす。値の中身の検査はツールが行う。
    """
    out: dict[str, str] = {}
    pieces = [p for p in raw.split(b"&") if p]
    if len(pieces) > QUERY_FIELDS_MAX:
        raise HttpInputError(f"問い合わせの項目は{QUERY_FIELDS_MAX}個まで")
    for piece in pieces:
        name_b, _, value_b = piece.partition(b"=")
        try:
            name, value = _unquote(name_b), _unquote(value_b)
        except UnicodeDecodeError:
            raise HttpInputError("問い合わせは UTF-8（百分率符号化）で送る") from None
        except ValueError:
            raise HttpInputError("百分率符号化の形が崩れている（`%` の後は16進2桁）") from None
        if name not in allowed:
            raise HttpInputError(_unknown(allowed))
        if name in out:
            raise HttpInputError(f"引数 {name} が重複している")
        out[name] = value
    return out


def _unquote(raw: bytes) -> str:
    """`+` を空白に、`%XX` をそのバイトにしてから UTF-8（厳格）で読む。形の崩れた `%` は ValueError
    （`urllib.parse` は崩れた `%` をそのまま残すが、ここでは誤りとして返す）。リテラルの `+` は `%2B` で送る。"""
    if _BAD_PERCENT.search(raw):
        raise ValueError("bad percent-encoding")
    return _PERCENT.sub(lambda m: bytes([int(m.group(1), 16)]), raw.replace(b"+", b" ")).decode("utf-8")


def parse_body(body: bytes, allowed: Sequence[str]) -> dict[str, str]:
    """POST の本文を読む：UTF-8 の JSON オブジェクト。名前は allowed だけ・重複なし・値は文字列か null（null は省略と同じ）。

    Content-Type は見ない（curl の `-d` の既定でも通るように）。
    """
    def pairs(items):
        seen: dict[str, Any] = {}
        for key, value in items:
            if key in seen:  # 文に入力のキーを入れない（孤立サロゲートのキーで応答が UTF-8 にできなくなる。Codex⑤ F1）
                raise HttpInputError("本文の JSON に重複したキーがある")
            seen[key] = value
        return seen

    try:
        obj = json.loads(body.decode("utf-8"), object_pairs_hook=pairs)
    except HttpInputError:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise HttpInputError("本文は UTF-8 の JSON オブジェクト") from None
    if not isinstance(obj, dict):
        raise HttpInputError("本文は UTF-8 の JSON オブジェクト")
    out: dict[str, str] = {}
    for key, value in obj.items():
        if key not in allowed:  # 文は許可名の一覧だけ（入力のキーは入れない）
            raise HttpInputError(_unknown(allowed))
        if value is None:
            continue
        if not isinstance(value, str):
            raise HttpInputError("本文の JSON の値は文字列か null")
        out[key] = value
    return out


def _unknown(allowed: Sequence[str]) -> str:
    return ("この経路の引数は " + "・".join(allowed) + " だけ") if allowed else "この経路は引数を取らない"


def parse_k(value: "str | None") -> Any:
    """k の問い合わせを整数にする。省略は既定の5（MCP と同じ）。5桁以内の十進数字だけを整数にし、
    ほかの形はそのまま渡してツールの検査（invalid_input）に任せる。"""
    if value is None:
        return 5
    if value.isascii() and value.isdigit() and len(value) <= 5:
        return int(value)
    return value


# ---------------------------------------------------------------- 表現・状態・ETag


def wants_markdown(accept: "str | None") -> bool:
    """`Accept` のどれかの項目が `text/markdown`（q が 0 でない）なら Markdown。ほかは JSON（既定）。"""
    for item in (accept or "").split(","):
        media, *params = [p.strip() for p in item.split(";")]
        if media.lower() != "text/markdown":
            continue
        q = next((p.split("=", 1)[1].strip() for p in params if p.lower().startswith("q=")), "1")
        try:
            if float(q) > 0:
                return True
        except ValueError:
            continue
    return False


def _accept_ranges(accept: "str | None") -> list[tuple[str, float, int]]:
    """`Accept` を (media, q, 位置) の列にする。q の読めない項目は捨てる。"""
    out = []
    for pos, item in enumerate((accept or "").split(",")):
        media, *params = [p.strip() for p in item.split(";")]
        if not media:
            continue
        q = next((p.split("=", 1)[1].strip() for p in params if p.lower().startswith("q=")), "1")
        try:
            out.append((media.lower(), float(q), pos))
        except ValueError:
            continue
    return out


def choose(accept: "str | None", fmt: "str | None") -> str:
    """表現を選ぶ（HTTP-1.3.0）。format があれば Accept より優先（値は json・markdown・html。ほかは 400）。

    Accept では、q の降順・書かれた順で最初の項目が `text/html`（q>0）なら HTML（ブラウザの既定の Accept が
    これに当たる）。そうでなければ従来どおり、`text/markdown`（q>0）がどこかにあれば Markdown、ほかは JSON。
    """
    if fmt is not None:
        if fmt not in REPRESENTATIONS:
            raise HttpInputError("format は json・markdown・html のいずれか")
        return fmt
    ranges = sorted(_accept_ranges(accept), key=lambda r: (-r[1], r[2]))
    if ranges and ranges[0][0] == "text/html" and ranges[0][1] > 0:
        return "html"
    return "markdown" if wants_markdown(accept) else "json"


def http_status(status: str) -> int:
    """応答の status から HTTP の状態コード（invalid_input＝400・unknown_id＝404・ほかは 200）。"""
    return {"invalid_input": 400, "unknown_id": 404}.get(status, 200)


def etag(bundle_hash: str, name: str, args: Sequence[Any], representation: str) -> str:
    """ETag：規則の版・bundle_hash・経路・ツールに渡す引数（既定を埋めた後）・表現から決める（強い ETag）。"""
    key = json.dumps([HTTP_VERSION, bundle_hash, name, list(args), representation],
                     ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return '"' + hashlib.sha256(key.encode("utf-8")).hexdigest()[:32] + '"'


def not_modified(if_none_match: "str | None", tag: str) -> bool:
    """If-None-Match に同じ ETag（弱い比較・`*` を含む）があるか。"""
    if not if_none_match:
        return False
    for item in if_none_match.split(","):
        item = item.strip()
        if item == "*" or item.removeprefix("W/") == tag:
            return True
    return False


# ---------------------------------------------------------------- 経路の一覧


def index(meta: Mapping[str, str]) -> dict:
    """GET /api/v1/ の本文（経路の一覧）。meta は schema_version・corpus_version・source_commit・bundle_hash。"""
    return {
        "api_version": HTTP_VERSION,
        **{k: meta[k] for k in ("schema_version", "corpus_version", "source_commit", "bundle_hash")},
        "accept": ["application/json", "text/markdown"],
        "routes": [{"method": r.method, "path": r.path, "tool": r.tool,
                    "params": list(r.path_params + r.params),
                    "in": "path+query" if r.path_params else ("json_body" if r.method == "POST" else "query")}
                   for r in ROUTES],
    }


# ---------------------------------------------------------------- Markdown

TEXT_TOOLS = frozenset({"get_section", "get_reading_guide"})  # 本文（payload.text）を行のまま入れる
_CELL_KEYS = ("matched_text", "excerpt", "source_quote", "source_excerpt", "title", "text", "description")


def _dash(value: Any) -> str:
    return "-" if value is None or value == "" else str(value)


def _lines(r: Mapping[str, Any]) -> str:
    loc = r.get("locator") or {}
    if loc.get("line_start") is not None:
        return f"{loc['line_start']}-{loc.get('line_end', loc['line_start'])}"
    if loc.get("json_pointer"):
        return str(loc["json_pointer"])
    return "-"


def source_line(r: Mapping[str, Any], env: Mapping[str, Any]) -> str:
    """出典行：paper_id・paper_version・section_anchor・行範囲（無ければ JSON 位置）・path・corpus_version・source_commit。"""
    return ("Source: " + " · ".join((
        f"paper_id={_dash(r.get('paper_id'))}",
        f"paper_version={_dash(r.get('paper_version'))}",
        f"section_anchor={_dash(r.get('section_anchor'))}",
        f"lines={_lines(r)}",
        f"path={_dash((r.get('locator') or {}).get('path'))}",
        f"corpus_version={env['corpus_version']}",
        f"source_commit={env['source_commit']}",
    )))


def envelope_line(env: Mapping[str, Any], tool: "str | None") -> str:
    """表の文書の先頭行（結果ごとの出典は表の列）。"""
    return ("Source: " + " · ".join((
        f"tool={_dash(tool)}", f"status={_dash(env.get('status'))}",
        f"corpus_version={env['corpus_version']}", f"source_commit={env['source_commit']}",
        f"bundle_hash={env['bundle_hash']}")))


def _cell(text: Any) -> str:
    """表のセル：改行は空白に、`|` は `\\|` に（表の中だけ。本文として入れる payload.text は変えない）。"""
    s = _dash(text)
    return s.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _row_text(payload: Mapping[str, Any]) -> str:
    parts = []
    for key in ("pattern_id", "id", "status", "match"):
        if isinstance(payload.get(key), str):
            parts.append(f"{key}={payload[key]}")
    matched = payload.get("matched")
    if isinstance(matched, list) and matched:
        parts.append("matched=" + "・".join(str(m.get("form")) for m in matched if isinstance(m, Mapping)))
    body = next((payload[k] for k in _CELL_KEYS if isinstance(payload.get(k), str)), None)
    if body is not None:
        parts.append(body)
    return " — ".join(parts) if parts else "-"


def _table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    out = ["| # | paper_id | paper_version | section_anchor | lines | path | text |",
           "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        out.append("| " + " | ".join(_cell(v) for v in (
            i, r.get("paper_id"), r.get("paper_version"), r.get("section_anchor"), _lines(r),
            (r.get("locator") or {}).get("path"), _row_text(r.get("payload") or {}))) + " |")
    return out


def _footer(env: Mapping[str, Any]) -> list[str]:
    out = ["", "---", "", f"status: {env['status']}", "", "limitations:", ""]
    out += [f"- {lim}" for lim in env.get("limitations") or ()] or ["- (none)"]
    return out


def render_markdown(env: Mapping[str, Any], tool: "str | None") -> str:
    """応答（JSON から戻した外枠）を Markdown にする（SPEC §2.12）。

    節とガイド（ok）：結果ごとに出典行、空行、payload.text を行を変えずに。検索・照合・検出・台帳・一覧と ok 以外：
    先頭に外枠の出典行、結果の表（列に論文・版・節・行範囲）。候補は別の表。最後に status と limitations。
    """
    lines: list[str] = []
    results = env.get("results") or []
    if tool in TEXT_TOOLS and results:
        for i, r in enumerate(results):
            if i:
                lines += ["", "---", ""]
            lines += [source_line(r, env), ""]
            text = (r.get("payload") or {}).get("text")
            if isinstance(text, str):
                lines.append(text.rstrip("\n"))
            else:
                lines.append("(" + _row_text(r.get("payload") or {}) + ")")
        templates = env.get("templates")
        if isinstance(templates, Mapping) and templates.get("items"):
            lines += ["", "---", "", f"templates: {templates.get('version')} ({templates.get('status')})"]
            for item in templates["items"]:
                lines += ["", f"### {item.get('name')} ({item.get('language')})", "", str(item.get("text", "")).rstrip("\n")]
    else:
        lines.append(envelope_line(env, tool))
        if results:
            lines += ["", "results:", ""] + _table(results)
    candidates = env.get("candidates") or []
    if candidates:
        lines += ["", "candidates:", ""] + _table(candidates)
    lines += _footer(env)
    return "\n".join(lines) + "\n"


def render_index_markdown(doc: Mapping[str, Any]) -> str:
    lines = [f"Source: api_version={doc['api_version']} · corpus_version={doc['corpus_version']} · "
             f"source_commit={doc['source_commit']} · bundle_hash={doc['bundle_hash']}", "",
             "| method | path | tool | params | in |", "|---|---|---|---|---|"]
    for r in doc["routes"]:
        lines.append(f"| {r['method']} | `{r['path']}` | {_dash(r['tool'])} | {_dash('・'.join(r['params']))} | {r['in']} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- HTML（HTTP-1.3.0）


def esc(value: Any) -> str:
    """HTML に入れる文字列の唯一のエスケープ関数（`& < > " '`）。利用者由来の文字列（引用文・検索語・ID・
    エラー文）もコーパス由来の文字列も、ページに入る値はすべてここを通す。"""
    return html.escape(_dash(value) if not isinstance(value, str) else value, quote=True)


_HTML_STYLE = (":root{color-scheme:light dark}body{margin:0;font:15px/1.6 system-ui,sans-serif}"
               "main{max-width:60rem;margin:0 auto;padding:1rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;"
               "padding:.6rem;border:1px solid #8884;border-radius:4px}table{border-collapse:collapse;width:100%}"
               "td,th{border:1px solid #8884;padding:.25rem .4rem;vertical-align:top;text-align:left;"
               "overflow-wrap:anywhere}.source{font-family:ui-monospace,monospace;font-size:.85em}")


def alternate_links(raw_path: bytes, query_string: bytes) -> list[tuple[str, str]]:
    """同じ内容の JSON と Markdown への URL（format= だけを替える。ほかの項目は受け取ったバイトのまま並べる）。"""
    pieces = [p for p in query_string.split(b"&") if p and p.partition(b"=")[0] != FORMAT.encode()]
    base = raw_path.decode("latin-1")
    out = []
    for rep in ("json", "markdown"):
        query = "&".join([p.decode("latin-1") for p in pieces] + [f"{FORMAT}={rep}"])
        out.append((rep, f"{base}?{query}"))
    return out


def _html_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    out = ["<table>", "<tr><th>#</th><th>paper_id</th><th>paper_version</th><th>section_anchor</th>"
                      "<th>lines</th><th>path</th><th>text</th></tr>"]
    for i, r in enumerate(rows, 1):
        cells = (i, r.get("paper_id"), r.get("paper_version"), r.get("section_anchor"), _lines(r),
                 (r.get("locator") or {}).get("path"), _row_text(r.get("payload") or {}))
        out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr>")
    out.append("</table>")
    return out


def _html_page(title: str, body: list[str], links: "list[tuple[str, str]] | None", post_note: bool) -> str:
    foot: list[str] = ["<nav>"]
    if links:
        foot.append("同じ内容 / Same content: " + " · ".join(
            f'<a href="{esc(url)}">{esc(rep.upper() if rep == "json" else rep.capitalize())}</a>' for rep, url in links))
    if post_note:
        foot.append("POST の結果は URL で再現できない。同じ本文を <code>?format=json</code> か "
                    "<code>?format=markdown</code> を付けた同じ経路へ送り直す。 / A POST result cannot be reproduced "
                    "by URL; send the same body again to the same route with <code>?format=json</code> or "
                    "<code>?format=markdown</code>.")
    foot.append("</nav>")
    return ("<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{esc(title)}</title>\n<style>{_HTML_STYLE}</style>\n</head>\n<body>\n<main>\n"
            + "\n".join(body) + "\n" + "\n".join(foot) + "\n</main>\n</body>\n</html>\n")


def render_html(env: Mapping[str, Any], tool: "str | None", links: "list[tuple[str, str]] | None",
                post_note: bool = False) -> str:
    """Markdown 表現と同じ中身（出典行・本文または結果の表・候補・status・limitations）を静的な HTML 一枚にする。
    JS・外部資産なし。値はすべて esc を通す。本文（payload.text）は <pre> に行のまま入れる。"""
    body: list[str] = [f"<h1>Mekiki Reader — {esc(tool or 'api')}</h1>"]
    results = env.get("results") or []
    if tool in TEXT_TOOLS and results:
        for i, r in enumerate(results):
            if i:
                body.append("<hr>")
            body.append(f'<p class="source">{esc(source_line(r, env))}</p>')
            text = (r.get("payload") or {}).get("text")
            if isinstance(text, str):
                body.append(f"<pre>{esc(text.rstrip(chr(10)))}</pre>")
            else:
                body.append(f"<p>({esc(_row_text(r.get('payload') or {}))})</p>")
        templates = env.get("templates")
        if isinstance(templates, Mapping) and templates.get("items"):
            body.append(f"<h2>templates: {esc(templates.get('version'))} ({esc(templates.get('status'))})</h2>")
            for item in templates["items"]:
                body.append(f"<h3>{esc(item.get('name'))} ({esc(item.get('language'))})</h3>")
                body.append(f"<pre>{esc(str(item.get('text', '')).rstrip(chr(10)))}</pre>")
    else:
        body.append(f'<p class="source">{esc(envelope_line(env, tool))}</p>')
        if results:
            body += ["<h2>results</h2>"] + _html_table(results)
    candidates = env.get("candidates") or []
    if candidates:
        body += ["<h2>candidates</h2>"] + _html_table(candidates)
    body.append("<hr>")
    body.append(f"<p>status: {esc(env['status'])}</p>")
    body.append("<h2>limitations</h2>")
    body.append("<ul>" + "".join(f"<li>{esc(lim)}</li>" for lim in env.get("limitations") or ()) + "</ul>")
    return _html_page(f"Mekiki Reader — {tool or 'api'}", body, links, post_note)


def render_index_html(doc: Mapping[str, Any], links: "list[tuple[str, str]] | None") -> str:
    body = ["<h1>Mekiki Reader — /api/v1/</h1>",
            f'<p class="source">{esc(render_index_markdown(doc).split(chr(10), 1)[0])}</p>',
            "<table>", "<tr><th>method</th><th>path</th><th>tool</th><th>params</th><th>in</th></tr>"]
    for r in doc["routes"]:
        cells = (r["method"], r["path"], r["tool"], "・".join(r["params"]), r["in"])
        body.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr>")
    body.append("</table>")
    return _html_page("Mekiki Reader — /api/v1/", body, links, False)
