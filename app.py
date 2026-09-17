"""Mekiki Reader — MCP サーバ（Gradio 6.27.0・gr.api・UI なし。SPEC §6・§9、docs/PLAN.md A-4）。

起動：`.venv/bin/python app.py`（インタプリタを明示する。Q79）
ポート：環境変数 `MEKIKI_READER_PORT`（1024〜65535。既定 7860。Q12）
読むデータ：リポジトリ内の `data/` だけ。環境変数でも引数でも変えられない（Q12）。
"""

import os
import re
import sys
import threading
from collections import deque

# ---- gradio を import する前に環境を整える（Q93・Q80。import gradio は下の方にある） ----

KEEP_GRADIO_ENV = {"GRADIO_ANALYTICS_ENABLED": "False"}
# HF へは一切つながない。実測で、配信中に huggingface_hub が利用者のトークンファイルを開いたため、
# 読み先を /dev/null に向けて暗黙のトークン利用も切る（S03・2026-09-18）。
# プロキシは、自分自身への loopback 接続が外へ迂回しないように無効化する（Codex① P1-3）。
PROXY_ENV_NAMES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "FTP_PROXY", "NO_PROXY",
                   "http_proxy", "https_proxy", "all_proxy", "ftp_proxy", "no_proxy")
NO_PROXY_VALUE = "127.0.0.1,localhost,::1"
KEEP_OTHER_ENV = {"HF_HUB_DISABLE_TELEMETRY": "1", "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
                  "HF_HUB_OFFLINE": "1", "HF_TOKEN_PATH": os.devnull,
                  "NO_PROXY": NO_PROXY_VALUE, "no_proxy": NO_PROXY_VALUE}


def sanitize_environ(env=None) -> list[str]:
    """GRADIO_* とプロキシ系を全部消してから、許可した値だけを入れ直す。消した変数名を返す。"""
    env = os.environ if env is None else env
    removed = sorted(k for k in env if k.startswith("GRADIO_") or k in PROXY_ENV_NAMES)
    for key in removed:
        del env[key]
    env.update(KEEP_GRADIO_ENV)
    env.update(KEEP_OTHER_ENV)
    return removed


REMOVED_GRADIO_ENV = sanitize_environ()

import gradio as gr  # noqa: E402  （環境を整えた後に読み込む）
from starlette.middleware import Middleware  # noqa: E402

from mekiki_reader import corpus as C  # noqa: E402
from mekiki_reader import prompts as PR  # noqa: E402
from mekiki_reader import schema as S  # noqa: E402
from mekiki_reader import tools as T  # noqa: E402

TITLE = "Mekiki Reader"
PORT_ENV = "MEKIKI_READER_PORT"
DEFAULT_PORT = 7860
SERVER_NAME = "127.0.0.1"  # 環境変数では変えない（Q67）

# ---- 同時実行（Q65。上限超過は status ではなく通信層で返す） ----

MAX_CONCURRENCY = 4
MAX_THREADS = 8
QUEUE_MAX_SIZE = 16            # Gradio の待ち行列の長さ（Codex① P2-4）
QUEUE_INFLIGHT_MAX = MAX_CONCURRENCY + 4  # 同時に受け付ける queue/join の数（未回収の結果を溜めない）
GUARD_LOG_MAX = 256            # 遮断の記録の保持数（固定長。Codex① P2-5）
SENTINEL_MESSAGE = ("unknown prompt: this server has only read_with_guards, four_modes and answer_format "
                    "(the requested name is not passed to this endpoint by the server framework)")
BUSY_MESSAGE = f"busy: this reader accepts at most {MAX_CONCURRENCY} concurrent calls"
_SLOTS = threading.BoundedSemaphore(MAX_CONCURRENCY)
_QUEUE_SLOTS = threading.BoundedSemaphore(QUEUE_INFLIGHT_MAX)

# ---- 標準経路の遮断（Q66） ----

ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})
MAX_BODY_BYTES = 64 * 1024
# 明示して拒む経路（403）。UI が無くても登録される。
BLOCKED_MARKS = ("file=", "proxy=", "/upload", "/run-history", "/vibe", "/dev/reload",
                 "/monitoring", "/profiling", "/component_server", "/reset", "/cancel",
                 "/login", "/logout", "/deep_link", "/process_recording")
# 通す経路。MCP 本体と、resources/read・prompts/get が自分自身に出す要求（gradio_client）。
ALLOWED_EXACT = frozenset({"/", "/config", "/config/", "/gradio_api/info", "/gradio_api/info/",
                           "/gradio_api/startup-events",
                           # resources/read と prompts/get は、サーバが自分自身に出す要求で実行される。
                           "/gradio_api/queue/join", "/gradio_api/queue/data"})
ALLOWED_PREFIXES = ("/gradio_api/mcp", "/gradio_api/heartbeat/")
# 自分自身への呼び出しでだけ使う経路。外から来た分も含めて同時数を絞る（Codex① P2-4）。
SELF_CALL_PATHS = frozenset({"/gradio_api/queue/join"})
GUARD_LOG: "deque[tuple[int, str]]" = deque(maxlen=GUARD_LOG_MAX)  # 遮断の記録（固定長・S01 の証跡）
GUARD_COUNTS: dict[int, int] = {}  # 応答コードごとの総数（記録が溢れても件数は残す）

# ---- resources（Q70。12件・静的URI・テンプレート変数なし） ----

RESOURCE_BASE = f"mekiki://v{C.CORPUS_VERSION}/"
MD = "text/markdown"
TXT = "text/plain"
RESOURCES: tuple[tuple[str, str, str, str], ...] = (
    ("llms.txt", "llms_txt", TXT, "Machine-readable index of the pinned Mekiki corpus."),
    ("FOR_AI_READERS.md", "for_ai_readers", MD, "Reading guide for AI readers: four modes and cautions."),
    ("THEORY_MAP.md", "theory_map", MD, "Map of the five papers: terms, claims and forbidden compressions."),
    ("SOURCE_INDEX.md", "source_index", MD, "Index of the published sources and their canonical DOIs."),
    ("papers/T1.md", "paper_t1", MD, "T1, full text (English)."),
    ("papers/T2.md", "paper_t2", MD, "T2, full text (English)."),
    ("papers/T3.md", "paper_t3", MD, "T3, full text (English)."),
    ("papers/T4.md", "paper_t4", MD, "T4, full text (Japanese; the only Japanese original)."),
    ("papers/T5.md", "paper_t5", MD, "T5, full text (English)."),
    ("translations/T4.en.md", "paper_t4_en", MD, "T4, English edition (translation, with translator notes)."),
    ("AI_READING_TESTS.md", "reading_tests", MD,
     "The 17 published reading questions. Reference material only; this server does not grade answers."),
    ("claims/t5.json", "claims_ledger", TXT, "T5 claim ledger (JSON): status labels recorded by the author."),
)


_ASCII_DIGITS = re.compile(r"[0-9]+")
BODY_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _host_name(value: str) -> str:
    """Host ヘッダからポートを外す。ホスト名は大小を区別しない。IPv6 は括弧のまま比べる。"""
    value = value.strip().lower()
    if value.startswith("["):
        end = value.find("]")
        return value if end < 0 else value[:end + 1]
    return value.rsplit(":", 1)[0] if value.count(":") == 1 else value


def _replayer(body: bytes, receive):
    """読み終えた本文を後段のアプリに一度だけ渡し、その後は本物の receive に戻す。

    二度目以降を即 http.disconnect にすると、応答が SSE の経路で打ち切られる（実測）。
    """
    sent = False

    async def wrapped():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return await receive()

    return wrapped


def _guard_middleware():
    """Gradio の標準経路を遮断する ASGI ミドルウェア（Q66・Codex① P1-2・P2-4）。"""

    async def _reply(send, status: int, text: str, path: str = "") -> None:
        GUARD_LOG.append((status, path))
        GUARD_COUNTS[status] = GUARD_COUNTS.get(status, 0) + 1
        print(f"blocked {status} {path}", file=sys.stderr, flush=True)
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"text/plain; charset=utf-8")]})
        await send({"type": "http.response.body", "body": text.encode("utf-8")})

    class Guard:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "lifespan":
                return await self.app(scope, receive, send)
            if scope["type"] != "http":
                return  # websocket などは受け付けない
            path = scope.get("path", "")
            raw = scope.get("headers", [])
            hosts = [v.decode("latin-1", "replace") for k, v in raw if k.lower() == b"host"]
            if len(hosts) != 1 or _host_name(hosts[0]) not in ALLOWED_HOSTS:
                return await _reply(send, 400, "bad host", path)

            # 本文の長さの表明（Codex① P1-2）：TE と CL の併記は拒み、CL は ASCII 数字だけを受ける。
            lengths = [v.decode("latin-1", "replace").strip() for k, v in raw if k.lower() == b"content-length"]
            encodings = [v.decode("latin-1", "replace").strip().lower()
                         for k, v in raw if k.lower() == b"transfer-encoding"]
            chunked = any("chunked" in v for v in encodings)
            if lengths and encodings:
                return await _reply(send, 400, "conflicting framing", path)
            if len(lengths) > 1 or len(set(lengths)) > 1:
                return await _reply(send, 400, "conflicting framing", path)
            declared = None
            if lengths:
                if not _ASCII_DIGITS.fullmatch(lengths[0]):
                    return await _reply(send, 400, "bad content-length", path)
                declared = int(lengths[0])
                if declared > MAX_BODY_BYTES:
                    return await _reply(send, 413, "request body too large", path)

            if any(mark in path for mark in BLOCKED_MARKS):
                return await _reply(send, 403, "route disabled", path)
            if path not in ALLOWED_EXACT and not path.startswith(ALLOWED_PREFIXES):
                return await _reply(send, 404, "not found", path)

            # 本文は実際に届いたバイト数で打ち切る（表明を信じない）。
            forward = receive
            if declared is not None or chunked or scope.get("method", "GET").upper() in BODY_METHODS:
                chunks, total = [], 0
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunks.append(message.get("body", b""))
                    total += len(chunks[-1])
                    if total > MAX_BODY_BYTES:
                        return await _reply(send, 413, "request body too large", path)
                    if not message.get("more_body", False):
                        break
                if declared is not None and total != declared:
                    return await _reply(send, 400, "conflicting framing", path)
                forward = _replayer(b"".join(chunks), receive)

            if path in SELF_CALL_PATHS:  # 自己呼び出しの経路は同時数を絞る（未回収の結果を溜めない）
                if not _QUEUE_SLOTS.acquire(blocking=False):
                    return await _reply(send, 503, "busy", path)
                try:
                    return await self.app(scope, forward, send)
                finally:
                    _QUEUE_SLOTS.release()
            return await self.app(scope, forward, send)

    return Guard


def read_port(raw: str | None) -> int:
    """MEKIKI_READER_PORT を読む（Q12）。形式が違えば ValueError。"""
    if raw is None or raw == "":
        return DEFAULT_PORT
    if not re.fullmatch(r"[0-9]{1,5}", raw):
        raise ValueError(f"{PORT_ENV} は 1024〜65535 の十進の整数で指定する")
    port = int(raw)
    if not 1024 <= port <= 65535:
        raise ValueError(f"{PORT_ENV} は 1024〜65535 の範囲で指定する")
    return port


def _call(fn, *args) -> str:
    """七ツールの共通の入口。JSON 文字列を返す（Q63）。上限超過は例外で返す（Q65）。"""
    if not _SLOTS.acquire(blocking=False):
        raise RuntimeError(BUSY_MESSAGE)
    try:
        return S.to_json(fn(READER, *args))
    finally:
        _SLOTS.release()


# ---------------------------------------------------------------- 七ツール（SPEC §5）


def list_papers() -> str:
    """Lists the five pinned Mekiki papers with their sections, versions and DOIs.

    Returns:
        A JSON object: status, results (one per paper), limitations.
    """
    return _call(T.list_papers)


def get_section(paper_id: str, anchor: str, language: str = "") -> str:
    """Returns one section of a paper as recorded in the pinned corpus, with citation fields.

    Args:
        paper_id: Paper id: T1, T2, T3, T4 or T5.
        anchor: Section anchor as listed by list_papers.
        language: Edition to read. Empty for the original text; "en" for the English edition of T4.

    Returns:
        A JSON object: status, results, limitations. Unknown ids return status unknown_id with candidates.
    """
    return _call(T.get_section, paper_id, anchor, language or None)


def search_passages(query: str, paper_id: str = "", k: int = 5) -> str:
    """Searches the five papers for literal words and phrases. No model, no embedding: lexical only.

    Args:
        query: Words or phrases. Fragments are split on spaces and punctuation; at most 8 fragments.
        paper_id: Optional paper id (T1..T5) to restrict the search.
        k: Number of results, 1 to 20.

    Returns:
        A JSON object: status, results (lines that matched every fragment), candidates, limitations.
    """
    return _call(T.search_passages, query, paper_id or None, k)


def get_claim_record(claim_id: str = "", query: str = "") -> str:
    """Returns what the T5 ledger records for a claim. The status is the author's label, not a truth value.

    Args:
        claim_id: Claim id, for example T5-N3. Give either claim_id or query.
        query: Words to look for in the ledger when the claim id is unknown.

    Returns:
        A JSON object: status, results, candidates, limitations. Unrecorded fields are null.
    """
    return _call(T.get_claim_record, claim_id or None, query or None)


def verify_quote(text: str, paper_id: str = "", language: str = "") -> str:
    """Checks whether a quotation appears in the pinned corpus, and reports where and how it differs.

    Args:
        text: The quotation to check, up to 2000 characters.
        paper_id: Optional paper id (T1..T5) to restrict the search.
        language: Edition to search. Empty for the originals; "en" for the English edition of T4.

    Returns:
        A JSON object: status (ok or quote_not_found), results with positions and diffs, limitations.
    """
    return _call(T.verify_quote, text, paper_id or None, language or None)


def check_compressions(text: str) -> str:
    """Finds wordings that the author has listed as compressions of the papers' distinctions.

    Each hit returns the related source text. A hit is a place to check against the paper; it is not a
    judgment that the text is wrong, and zero hits is not a proof that a reading is correct.

    Args:
        text: The text to check, up to 2000 characters.

    Returns:
        A JSON object: status, results (pattern id, matched forms, source excerpt), limitations.
    """
    return _call(T.check_compressions, text)


def get_reading_guide(part: str = "all") -> str:
    """Returns the author's reading guide for AI readers, and the reading templates.

    Args:
        part: One of all, interpretation, core-terms, japanese-terms, t4-languages, modes, mode-1, mode-2, mode-3, mode-4, boundaries. Gradio keeps only the first line of an argument description, so this line stays long on purpose.

    Returns:
        A JSON object: status, results quoted from FOR_AI_READERS.md, templates, limitations.
    """
    return _call(T.get_reading_guide, part)


TOOLS = (list_papers, get_section, search_passages, get_claim_record,
         verify_quote, check_compressions, get_reading_guide)


# ---------------------------------------------------------------- resources と prompts


def _in_slot(make_value):
    """七ツール以外（resources・prompts）にも同じ実行枠を使わせる（Codex① P2-4）。"""
    if not _SLOTS.acquire(blocking=False):
        raise RuntimeError(BUSY_MESSAGE)
    try:
        return make_value()
    finally:
        _SLOTS.release()


def _resource_fn(path: str, name: str, mime: str, description: str):
    def read() -> str:
        return _in_slot(lambda: READER.corpus.raw[path].decode("utf-8"))

    read.__name__ = name
    read.__doc__ = f"{description}\n\nReturns:\n    The file as it is stored in the pinned corpus.\n"
    return gr.mcp.resource(RESOURCE_BASE + path, description=description, mime_type=mime)(read)


def _prompt_fn(template):
    def show() -> str:
        return _in_slot(lambda: template.text)

    show.__name__ = template.name
    lang = "Japanese" if template.language == "ja" else "English"
    show.__doc__ = f"{template.title}\n\nReturns:\n    The template text ({lang}, {PR.PROMPTS_VERSION}).\n"
    return gr.mcp.prompt(description=template.title)(show)


def _sentinel():
    """最後に登録する番兵（Q64）。prompts/get は名前が一致しないと最後の endpoint を呼ぶ。"""

    def mekiki_sentinel() -> str:
        raise gr.Error(SENTINEL_MESSAGE)

    # tools/list・resources/list・prompts/list のどれにも載らない印を付ける（上流は "tool" 以外を外す）。
    mekiki_sentinel._mcp_type = "sentinel"
    return mekiki_sentinel


def build_blocks() -> "gr.Blocks":
    """UI コンポーネントを置かない Blocks を作る。登録の順番＝MCP の endpoint の順番。"""
    with gr.Blocks(analytics_enabled=False, title=TITLE) as demo:
        for fn in TOOLS:
            gr.api(fn, api_visibility="public", queue=False)
        for path, name, mime, description in RESOURCES:
            gr.api(_resource_fn(path, name, mime, description), api_visibility="public", queue=False)
        for template in PR.TEMPLATES:
            gr.api(_prompt_fn(template), api_visibility="public", queue=False)
        gr.api(_sentinel(), api_visibility="public", queue=False)  # 必ず最後
    demo.queue(max_size=QUEUE_MAX_SIZE, default_concurrency_limit=MAX_CONCURRENCY)
    return demo


def verify_blocks(demo, launched: bool = False, port: int | None = None) -> list[str]:
    """環境変数だけで有効になる経路が無効であることを確かめる（Q93・Codex① P1-3）。問題の一覧を返す。"""
    problems = []
    checks: list[tuple[str, object]] = [("vibe_mode", False), ("dev_mode", False), ("analytics_enabled", False)]
    if launched:  # 起動してから決まる値
        checks += [("share", False), ("ssr_mode", False), ("enable_monitoring", False),
                   ("run_history", False), ("pwa", False), ("mcp_server", True),
                   ("server_name", SERVER_NAME), ("max_threads", MAX_THREADS), ("root_path", "")]
        if port is not None:
            checks.append(("server_port", port))
    for attr, want in checks:
        value = getattr(demo, attr, "missing")
        if value is not want and value != want:
            problems.append(f"{attr}={value!r}")
    for attr in ("allowed_paths", "blocked_paths"):
        value = getattr(demo, attr, "missing")
        if value not in ([], ()):
            problems.append(f"{attr}={value!r}")
    queue = getattr(demo, "_queue", None)
    if getattr(queue, "max_size", None) != QUEUE_MAX_SIZE:
        problems.append(f"queue.max_size={getattr(queue, 'max_size', 'missing')!r}")
    if getattr(queue, "default_concurrency_limit", None) != MAX_CONCURRENCY:
        problems.append(f"queue.concurrency={getattr(queue, 'default_concurrency_limit', 'missing')!r}")
    if launched:
        url = getattr(demo, "local_url", "") or ""
        if not url.startswith(f"http://{SERVER_NAME}:"):
            problems.append(f"local_url={url!r}")
    return problems


def launch(demo, port: int):
    """loopback で起動する。環境変数では bind 先が変わらない（Q67）。"""
    return demo.launch(
        mcp_server=True,
        share=False,
        server_name=SERVER_NAME,
        server_port=port,
        ssr_mode=False,
        enable_monitoring=False,
        run_history=False,
        footer_links=[],
        max_threads=MAX_THREADS,
        max_file_size="1kb",
        show_error=False,
        inbrowser=False,
        allowed_paths=[],
        blocked_paths=[],
        quiet=False,
        prevent_thread_lock=True,
        app_kwargs={"middleware": [Middleware(_guard_middleware())]},
    )


def main() -> int:
    global READER
    try:
        port = read_port(os.environ.get(PORT_ENV))
    except ValueError as exc:
        print(f"起動しない：{exc}", file=sys.stderr, flush=True)
        return 2
    try:
        corpus = C.load_corpus()
    except C.BundleError as exc:
        print(f"起動しない：同梱データの検査に失敗した（{exc.kind} {exc.path}）", file=sys.stderr, flush=True)
        return 3
    READER = T.Reader(corpus)
    demo = build_blocks()
    problems = verify_blocks(demo)
    if problems:
        print("起動しない：Gradio の設定が想定と違う：" + "・".join(problems), file=sys.stderr, flush=True)
        return 4
    try:
        launch(demo, port)
    except OSError as exc:  # ポートが塞がっているなど
        print(f"起動しない：ポート {port} で待ち受けられない（{type(exc).__name__}）。"
              f"{PORT_ENV} で別のポートを指定する", file=sys.stderr, flush=True)
        return 6
    problems = verify_blocks(demo, launched=True, port=port)
    if problems:
        demo.close()
        print("停止する：起動後の確認に失敗した：" + "・".join(problems), file=sys.stderr, flush=True)
        return 5
    print(f"corpus {C.CORPUS_VERSION} ({C.CORPUS_COMMIT[:7]})・bundle {C.EXPECTED_BUNDLE_SHA256[:12]}…", flush=True)
    print(f"tools 7・resources {len(RESOURCES)}・prompts {len(PR.TEMPLATES)}（{PR.PROMPTS_VERSION}）", flush=True)
    print(f"消した環境変数：{'・'.join(REMOVED_GRADIO_ENV) or 'なし'}", flush=True)
    try:
        demo.block_thread()
    except KeyboardInterrupt:
        demo.close()
    return 0


READER: T.Reader | None = None

if __name__ == "__main__":
    sys.exit(main())
