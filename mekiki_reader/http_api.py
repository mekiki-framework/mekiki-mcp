"""HTTP 併設（SPEC v2.5 §2.12・docs/rules/HTTP.md の HTTP-1.0.0）の、通信に触れない部分。

経路の表・引数の読み取り・表現の選択（JSON か Markdown か）・Markdown の組み立て・ETag。標準ライブラリだけで、
gradio も七ツールも import しない。ツールを呼ぶのは app.py の Guard の中で、MCP と同じ入口の関数を使う
（同じ入力なら MCP と同じ JSON 文字列になる）。入力の上限と形の検査はツールの側にあり、ここでは HTTP の形
（引数の名前・重複・文字コード・本文の JSON）だけを見る。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

HTTP_VERSION = "HTTP-1.0.0"
PREFIX = "/api/v1/"
QUERY_FIELDS_MAX = 8  # 問い合わせの項目数（どの経路も引数は3つまで。空の項目は数えない）
CACHE_GET = "public, max-age=3600"  # GET の読み取り応答（データは版で固定）
CACHE_NONE = "no-store"             # POST・400・404・そのほか
JSON_TYPE = "application/json; charset=utf-8"
MARKDOWN_TYPE = "text/markdown; charset=utf-8"


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
    Route("verify", "GET", "/api/v1/verify", "verify_quote", ("text", "paper_id")),
    Route("verify", "POST", "/api/v1/verify", "verify_quote", ("text", "paper_id")),
    Route("check", "POST", "/api/v1/check", "check_compressions", ("text",)),
)
_SECTION_RE = re.compile(r"/api/v1/papers/([^/]+)/sections/([^/]+)")
_EXACT = {r.path: r.name for r in ROUTES if not r.path_params}
_PERCENT = re.compile(rb"%([0-9A-Fa-f]{2})")


class HttpInputError(ValueError):
    """HTTP の形の誤り（引数の名前・重複・文字コード・本文）。invalid_input として 400 で返す。"""


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
    """問い合わせを読む。`+` は空白、`%XX` は UTF-8（厳格）。名前は allowed だけ・重複なし・項目は8つまで。

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
        if name not in allowed:
            raise HttpInputError(_unknown(allowed))
        if name in out:
            raise HttpInputError(f"引数 {name} が重複している")
        out[name] = value
    return out


def _unquote(raw: bytes) -> str:
    """`+` を空白に、`%XX` をそのバイトにしてから UTF-8（厳格）で読む。形の崩れた `%` はそのまま残す。"""
    return _PERCENT.sub(lambda m: bytes([int(m.group(1), 16)]), raw.replace(b"+", b" ")).decode("utf-8")


def parse_body(body: bytes, allowed: Sequence[str]) -> dict[str, str]:
    """POST の本文を読む：UTF-8 の JSON オブジェクト。名前は allowed だけ・重複なし・値は文字列か null（null は省略と同じ）。

    Content-Type は見ない（curl の `-d` の既定でも通るように）。
    """
    def pairs(items):
        seen: dict[str, Any] = {}
        for key, value in items:
            if key in seen:
                raise HttpInputError(f"引数 {key} が重複している")
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
        if key not in allowed:
            raise HttpInputError(_unknown(allowed))
        if value is None:
            continue
        if not isinstance(value, str):
            raise HttpInputError(f"引数 {key} は文字列（か null）")
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


def http_status(status: str) -> int:
    """応答の status から HTTP の状態コード（invalid_input＝400・unknown_id＝404・ほかは 200）。"""
    return {"invalid_input": 400, "unknown_id": 404}.get(status, 200)


def etag(bundle_hash: str, name: str, args: Sequence[Any], markdown: bool) -> str:
    """ETag：規則の版・bundle_hash・経路・ツールに渡す引数（既定を埋めた後）・表現から決める（強い ETag）。"""
    key = json.dumps([HTTP_VERSION, bundle_hash, name, list(args), "markdown" if markdown else "json"],
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
