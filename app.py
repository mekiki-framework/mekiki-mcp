"""Mekiki Reader — MCP サーバ（Gradio 6.27.0・gr.api・UI なし。SPEC §6・§9、docs/PLAN.md A-4）。

起動：`.venv/bin/python app.py`（インタプリタを明示する。Q79）
ポート：環境変数 `MEKIKI_READER_PORT`（1024〜65535。既定 7860。Q12）
読むデータ：リポジトリ内の `data/` だけ。環境変数でも引数でも変えられない（Q12）。
"""

import asyncio
import http.client
import logging
import os
import re
import signal
import sys
import threading
import time
import traceback
import urllib.parse
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


# ---- 配置モード（SPEC v2.4 §2.10） ----
# local（既定）と spaces の二値。spaces で変わるのは三つだけ：bind が 0.0.0.0、許可 Host が起動時に読んだ
# SPACE_HOST（カンマ区切りは各値）と localhost・127.0.0.1、`/` だけは健康検査のために Host を問わない。
MODE_ENV = "MEKIKI_READER_MODE"
MODES = ("local", "spaces")
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1", "[::1]")
# Spaces が入れる変数のうち、Gradio と依存の分岐を変えるもの（Spaces 用の監視スレッド・pwa の既定・ツール名の
# 接頭辞・spaces パッケージの関数包装・OAuth・トークン・ワーカー数・転送元の信用）。SPACE_HOST を読んだ後に消す。
# local でも同じく消す（どのモードでも、これらの変数で挙動が変わらないように）。
SPACES_ENV_NAMES = ("SYSTEM", "SPACE_ID", "SPACE_AUTHOR_NAME", "SPACE_REPO_NAME", "SPACES_ZERO_GPU",
                    "HF_TOKEN", "WEB_CONCURRENCY", "FORWARDED_ALLOW_IPS")
SPACES_ENV_PREFIXES = ("OAUTH_",)
_DNS_NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*")


def read_deploy(env=None) -> dict:
    """配置モードと、待ち受けるアドレス・許可 Host を読む（import gradio の前）。誤りは error に入れる。

    誤りがあっても import は止めない（試験が app を import するため）。起動は verify_blocks が止める。
    """
    env = os.environ if env is None else env
    mode = env.get(MODE_ENV, "") or "local"
    if mode not in MODES:
        return {"mode": mode, "bind": "127.0.0.1", "hosts": LOCAL_HOSTS,
                "error": f"{MODE_ENV} は local か spaces（受け取った値の形が違う）"}
    if mode == "local":
        return {"mode": mode, "bind": "127.0.0.1", "hosts": LOCAL_HOSTS, "error": None}
    hosts = [h.strip().lower() for h in env.get("SPACE_HOST", "").split(",") if h.strip()]
    if not hosts or not all(len(h) <= 253 and _DNS_NAME.fullmatch(h) for h in hosts):
        return {"mode": mode, "bind": "0.0.0.0", "hosts": ("localhost", "127.0.0.1"),
                "error": "spaces では SPACE_HOST（ホスト名。カンマ区切り可）が要る"}
    return {"mode": mode, "bind": "0.0.0.0", "hosts": tuple(dict.fromkeys([*hosts, "localhost", "127.0.0.1"])),
            "error": None}


def sanitize_environ(env=None) -> list[str]:
    """GRADIO_*・プロキシ系・Spaces の分岐を変える変数を消してから、許可した値だけを入れ直す。消した変数名を返す。"""
    env = os.environ if env is None else env
    removed = sorted(k for k in env if k.startswith("GRADIO_") or k in PROXY_ENV_NAMES
                     or k in SPACES_ENV_NAMES or k.startswith(SPACES_ENV_PREFIXES))
    for key in removed:
        del env[key]
    env.update(KEEP_GRADIO_ENV)
    env.update(KEEP_OTHER_ENV)
    return removed


DEPLOY = read_deploy()  # SPACE_HOST は消す前に読む
REMOVED_GRADIO_ENV = sanitize_environ()

import gradio as gr  # noqa: E402  （環境を整えた後に読み込む）
import gradio.queueing  # noqa: E402
import gradio.routes  # noqa: E402
import gradio.utils  # noqa: E402
import gradio_client  # noqa: E402
import orjson  # noqa: E402  （Gradio の依存。queue/data と同じ直列化で大きさを測る）
import uvicorn  # noqa: E402
import uvicorn.protocols.http.h11_impl as uvicorn_h11  # noqa: E402  （httptools は入れていないので h11 が使われる）
from starlette.middleware import Middleware  # noqa: E402

from mekiki_reader import corpus as C  # noqa: E402
from mekiki_reader import prompts as PR  # noqa: E402
from mekiki_reader import schema as S  # noqa: E402
from mekiki_reader import tools as T  # noqa: E402

TITLE = "Mekiki Reader"
PORT_ENV = "MEKIKI_READER_PORT"
DEFAULT_PORT = 7860
SERVER_NAME = DEPLOY["bind"]  # local は "127.0.0.1"。変えられるのは配置モードだけ（Q67・SPEC v2.4 §2.10）
LOOPBACK = "127.0.0.1"         # 自分自身に当てる確認（check_cors）の宛先（どのモードでも許可 Host に入る）
# spaces で Host を問わない `/`（健康検査）に返す固定の HTML（要求の中身を写さない）
HEALTH_HTML = "<!doctype html><title>Mekiki Reader</title><p>Mekiki Reader (MCP): /gradio_api/mcp/</p>\n"

# ---- 同時実行（Q65。上限超過は status ではなく通信層で返す） ----

MAX_CONCURRENCY = 4
MAX_THREADS = 8
QUEUE_MAX_SIZE = 72            # Gradio の待ち行列の長さ（＝queue/join の受付8＋待機64。断るのはこちらの層にする）
# 受付枠（Codex③ 1）：要求の種類ごとに（同時に受け付ける数, 順番待ちの数）。本文を読む前に取り、応答を送り
# 終えるまで持つ。順番待ちも埋まっていれば通信層で 503。総受付枠は三つの和（受付56・順番待ち192）で、こちらが
# 本文を読むのは受付の分だけ（HTTP の層は読む前の本文も接続ごとに一定量まで抱える。LIMITS に記す）。種類を
# 分けるのは、MCP の要求が内部クライアントの queue/join の完了を待つため（同じ枠だと互いに塞ぐ）。MCP の 32＋96 は、起動直後の同時100本（SPEC §7 S01）を通す値。
# queue/join の 8＋64 は Codex② 1 の値をそのまま本文の前へ移したもの。
ADMISSION_LIMITS = {"mcp": (32, 96), "queue_join": (MAX_CONCURRENCY + 4, 64), "other": (16, 32)}
ADMISSION_WAIT_SECONDS = 20.0  # 順番待ちの時間の上限（超えたら 503）
REQUEST_SECONDS = 60.0         # 受付から応答を送り終えるまでの期限（受け取りを止めた相手の枠を取り戻す）
RESULT_TTL_SECONDS = 120.0     # 回収されない結果を残す時間（結果ができた時刻から数える）
RESULT_MESSAGES_MAX = 64       # 同じセッションに溜める結果の数
RESULT_BYTES_MAX = 4 * 1024 * 1024   # 同じセッションに溜める結果の大きさ（queue/data が送る UTF-8 の JSON で数える）
RESULT_SWEEP_SECONDS = 5.0     # 掃除の間隔
BODY_READ_SECONDS = 10.0       # 本文が届き切るまでの上限（受信ループ全体で一つ。超えたら 408）
DRAIN_SECONDS = 1.0            # 断る前に本文を読み捨てる時間の上限（64 KiB まで。閉じる前に相手が送り終えるように）
GUARD_LOG_MAX = 256            # 遮断の記録の保持数（固定長。Codex① P2-5）
SENTINEL_MESSAGE = ("unknown prompt: this server has only read_with_guards, four_modes and answer_format "
                    "(the requested name is not passed to this endpoint by the server framework)")
BUSY_MESSAGE = f"busy: this reader accepts at most {MAX_CONCURRENCY} concurrent calls"
_SLOTS = threading.BoundedSemaphore(MAX_CONCURRENCY)
_ADMISSION = {kind: {"active": 0, "waiting": 0, "max_active": 0, "max_waiting": 0, "rejected": 0, "expired": 0,
                     "aborted": 0}
              for kind in ADMISSION_LIMITS}  # 受付枠の実測（S01 の証跡）
_ADMISSION_SEM: "dict[str, asyncio.Semaphore]" = {}  # 要求は同じ event loop で走る
_READY = {"mcp": False}  # 内部クライアントと起動後の確認が済むまで、外からの MCP を受けない（Codex③ 5）
# 塞げない長時間接続（GET の流れ）の同時数の上限。超えた分は通信層で 503（LIMITS-2.0.0）。
# 値は実測（2026-09-19）：内部クライアントは heartbeat 1本・queue/data 最大1本（resources/read 同時80本・
# 8セッション混在でも同じ）。GET /gradio_api/mcp/ は mcp SDK（Python）が0本、mcp-remote@0.14.2 が
# 1クライアントあたり最大4本（呼び出しを重ねても増えず、落ち着くと2本）。上限は内部分に余裕を足した8と、
# mcp-remote 8クライアント分の32。内部クライアントの分も数えるが、断らない：heartbeat は 503 を受けると
# 間を置かずに再試行するため（上流のクライアントとの互換）。内部かどうかは名乗るセッションで見分ける。
STREAM_LIMITS = {"heartbeat": 8, "queue_data": 8, "mcp_get": 32}
_STREAMS = {"open": dict.fromkeys(STREAM_LIMITS, 0), "peak": dict.fromkeys(STREAM_LIMITS, 0),
            "internal_open": dict.fromkeys(STREAM_LIMITS, 0), "internal_peak": dict.fromkeys(STREAM_LIMITS, 0),
            "rejected": dict.fromkeys(STREAM_LIMITS, 0)}
_SWEEP = {"task": None, "dropped": 0, "runs": 0, "evicted": 0}  # 回収されない結果の掃除
_BORN: "dict[int, list]" = {}      # 未回収の結果：id → [できた時刻, 結果, UTF-8 の大きさ]（結果を持つので id は重ならない）
_COLLECTING: "dict[str, int]" = {}  # queue/data で回収中のセッション（開いている流れの数）


def _admission_kind(method: str, path: str) -> str:
    """受付枠の種類（長時間接続は別に数える）。"""
    if path == "/gradio_api/queue/join":
        return "queue_join"
    if path in ("/gradio_api/mcp", "/gradio_api/mcp/") and method not in ("GET", "HEAD"):
        return "mcp"
    return "other"


async def _admit(kind: str) -> bool:
    """受付枠を取る。空きが無ければ順番待ち（上限つき・時間つき）。取れなければ False。"""
    state = _ADMISSION[kind]
    active_max, waiting_max = ADMISSION_LIMITS[kind]
    sem = _ADMISSION_SEM.get(kind)
    if sem is None:
        sem = _ADMISSION_SEM[kind] = asyncio.Semaphore(active_max)
    if sem.locked():  # 空きが無いか、先に待っている要求がある
        if state["waiting"] >= waiting_max:
            state["rejected"] += 1
            return False
        state["waiting"] += 1
        state["max_waiting"] = max(state["max_waiting"], state["waiting"])
        try:
            await asyncio.wait_for(sem.acquire(), ADMISSION_WAIT_SECONDS)
        except (asyncio.TimeoutError, TimeoutError):
            state["rejected"] += 1
            return False
        finally:
            state["waiting"] -= 1
    else:
        await sem.acquire()
    state["active"] += 1
    state["max_active"] = max(state["max_active"], state["active"])
    return True


def _release(kind: str) -> None:
    _ADMISSION[kind]["active"] -= 1
    _ADMISSION_SEM[kind].release()


def mark_ready() -> None:
    """起動後の確認が済んだ。ここから外からの MCP を受ける。"""
    _READY["mcp"] = True

# ---- 標準経路の遮断（Q66） ----

ALLOWED_HOSTS = frozenset(DEPLOY["hosts"])  # local は 127.0.0.1・localhost・::1。spaces は SPACE_HOST と loopback
MAX_BODY_BYTES = 64 * 1024
# 明示して拒む経路（403）。UI が無くても登録される。
BLOCKED_MARKS = ("file=", "proxy=", "/upload", "/run-history", "/vibe", "/dev/reload",
                 "/monitoring", "/profiling", "/component_server", "/reset", "/cancel",
                 "/login", "/logout", "/deep_link", "/process_recording")
# 通す経路は、実測で要ると分かったものだけ（SPEC v2.3 との照合・2026-09-18〜19）。
#   /                           Gradio が起動時に到達を確かめる（HEAD /。塞ぐと起動しない）。
#                               自己呼び出しの内部クライアントは /config が 404 だと GET / の HTML に
#                               埋め込まれた設定（window.gradio_config）を読む（塞ぐと resources/prompts が失敗）
#   /gradio_api/startup-events  起動時の確認（塞ぐと起動しない）
#   /gradio_api/info（と末尾 / 付き）  自己呼び出しが読む（塞ぐと McpError）
#   /gradio_api/queue/join・/queue/data  同じく自己呼び出しの実行と結果の受け取り
#   /gradio_api/mcp/            MCP 本体（Streamable HTTP）。/gradio_api/mcp は / 付きへ 307
#   /gradio_api/mcp/schema      ツールの JSON スキーマ（上流が同じ下に置く）
#   （旧 SSE の /gradio_api/mcp/sse・/messages/ と、Streamable HTTP の別名 /gradio_api/mcp/http は閉じた。
#    /gradio_api/mcp/ だけで三機能・SDK 検収・mcp-remote（http-only）が動くことを実測・2026-09-19。
#    /schema は三機能には要らないが、著者の指示で開けている）
#   /gradio_api/heartbeat/*     自己呼び出しの内部クライアントが送り続ける。上流のクライアントは断られると
#                               間を置かずに再試行するので塞がない（同時数で絞る。上流との互換）
# /config は塞いでも三機能が動き、再試行も起きないことを確かめたので塞いだ（設定は上のとおり / から出る）。
ALLOWED_EXACT = frozenset({"/", "/gradio_api/info", "/gradio_api/info/", "/gradio_api/startup-events",
                           "/gradio_api/queue/join", "/gradio_api/queue/data",
                           "/gradio_api/mcp", "/gradio_api/mcp/", "/gradio_api/mcp/schema"})
ALLOWED_PREFIXES = ("/gradio_api/heartbeat/",)
# 自己呼び出しの経路（/gradio_api/queue/join）は、外から来た分も含めて受付枠で絞る（Codex① P2-4・Codex③ 1）。
# 断るのではなく順番待ちにする：即 503 にすると、正規の resources/read・prompts/get が
# 上流のクライアントの中で失敗する（検算で確かめた。上流との互換）。
# 本文を読み切ってから渡す経路。ここ以外は本文に触れない（触ると送り切らない要求で待たされる）。
PRE_READ_PREFIXES = ("/gradio_api/mcp", "/gradio_api/queue/join")
# ブラウザからの読み取りを許さない（Codex① の反映後の点検で見つかった面）。
# Gradio は http://localhost:<任意のポート> などの Origin に Access-Control-Allow-Origin を返すため、
# 同じ機械の別のローカルサーバが配ったページから応答を読めてしまう。Origin 付きの要求には
# CORS の許可ヘッダを一切返さない（loopback 由来も含む）。接続先の MCP クライアントは Origin を送らない。
CORS_RESPONSE_HEADERS = frozenset({
    b"access-control-allow-origin", b"access-control-allow-credentials", b"access-control-allow-methods",
    b"access-control-allow-headers", b"access-control-expose-headers", b"access-control-max-age",
    b"access-control-allow-private-network", b"timing-allow-origin",
})
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
    """Host ヘッダからホスト名を取り出す（大小は区別しない）。形が変なら "" を返して拒ませる。

    ポートは省略か、十進 1〜65535 のときだけ認める（検算⑨）。IPv6 は括弧のまま比べる。
    """
    value = value.strip().lower()
    if value.startswith("["):
        end = value.find("]")
        if end < 0:
            return ""
        host, rest = value[:end + 1], value[end + 1:]
        if rest and not rest.startswith(":"):
            return ""  # `[::1]x80` のような接尾辞は受け付けない（Codex② 5）
    elif value.count(":") == 1:
        host, _, port = value.partition(":")
        rest = ":" + port
    elif ":" in value:
        return ""  # 括弧なしの IPv6 や、ポートの書き間違い
    else:
        host, rest = value, ""
    if rest:
        port = rest[1:]
        if not (port.isascii() and port.isdigit() and 1 <= int(port) <= 65535):
            return ""
    return host


class _PassThroughCORS:
    """Gradio の CORS 中間層の差し替え（このサーバはブラウザに応答を読ませない）。

    上流の `CustomCORSMiddleware` は `http://localhost:<任意のポート>`・`http://127.0.0.1:<任意のポート>` の
    Origin に `Access-Control-Allow-Origin` と `allow-credentials: true` を返す。それを使うと、同じ機械の
    別のローカルサーバが配ったページから、この読み手の応答を読めてしまう（実測）。UI を持たないサーバなので
    CORS の許可は一切出さない。差し替えが効いているかは `check_cors()` が起動後に自分自身へ当てて確かめる。
    """

    def __init__(self, app, *args, **kwargs) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)


gradio.routes.CustomCORSMiddleware = _PassThroughCORS  # create_app が add_middleware に使う名前


def _exception_label(exc: "BaseException | None") -> str:
    """例外の型と、起きた場所（ファイル名と行）だけ。例外の文（入力の値を含みうる）は出さない。"""
    where = ""
    if exc is not None and exc.__traceback__ is not None:
        last = traceback.extract_tb(exc.__traceback__)[-1]
        where = f" at {os.path.basename(last.filename)}:{last.lineno}"
    return f"{type(exc).__name__}{where}"


class _QuietTraceback:
    """gradio.queueing が例外を印字するときに、例外の文を出さない（上流の差し替え。Codex③ 7）。

    上流は待ち行列で起きた例外を `traceback.print_exc()` で標準エラーに出す。入力の検証エラーの文には
    受け取った値がそのまま入る（引数が足りない呼び出しを /gradio_api/queue/join に送ると再現した）。
    ここでは例外の型と、起きた場所（ファイル名と行）だけを出す。ほかの属性は本物の traceback に渡す。
    """

    @staticmethod
    def print_exc(*_args, **_kwargs) -> None:
        print(f"queue error: {_exception_label(sys.exc_info()[1])}", file=sys.stderr, flush=True)

    def __getattr__(self, name):
        return getattr(traceback, name)


gradio.queueing.traceback = _QuietTraceback()  # queueing.py が参照する名前


class _RedactedLog(logging.Handler):
    """ログを「水準・名前・出した場所」だけにして標準エラーに出す（文も値も出さない。Codex③ 7）。

    実測で、mcp は未知のツール名や JSON-RPC の中身を（f 文字列で組み立てた文として）、uvicorn は例外の文を
    含む traceback をログに出した。文そのものに値が埋め込まれうるので、文は出さない。
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            text = f"{record.levelname}:{record.name} at {os.path.basename(record.pathname)}:{record.lineno}"
            if record.exc_info and record.exc_info[1] is not None:
                text += f" [{_exception_label(record.exc_info[1])}]"
            sys.stderr.write(text + "\n")
            sys.stderr.flush()
        except Exception:  # noqa: BLE001 - ログで落とさない
            pass


LOG_HANDLER = _RedactedLog()
# 出口を持つロガー。uvicorn.error は出口を持たず uvicorn へ伝わる（両方に置くと二重に出る）。
REDACTED_LOGGERS = ("", "uvicorn", "uvicorn.access")


def redact_logs() -> None:
    """ログの出口を差し替える。uvicorn は設定を読むときに自分の出口を作るので、その直後にも呼ぶ（下）。"""
    for name in REDACTED_LOGGERS:
        logging.getLogger(name).handlers = [LOG_HANDLER]
    logging.getLogger("uvicorn.error").handlers = []
    logging.lastResort = LOG_HANDLER


_UVICORN_CONFIGURE_LOGGING = uvicorn.Config.configure_logging


def _configure_logging_redacted(self) -> None:
    """uvicorn がログの出口を作った直後に差し替える（待ち受けを始める前。Codex③ 7 の検算）。"""
    _UVICORN_CONFIGURE_LOGGING(self)
    redact_logs()


uvicorn.Config.configure_logging = _configure_logging_redacted
redact_logs()

_UVICORN_RUN_ASGI = uvicorn_h11.RequestResponseCycle.run_asgi


async def _run_asgi_with_abort(self, app) -> None:
    """要求ごとに、接続をすぐ切る手段をガードへ渡す（上流の差し替え。Codex③ 1 の検算）。

    送信期限で打ち切っても、uvicorn は接続を「送り終えてから閉じる」ので、受け取らない相手では閉じない。
    ガードは期限切れのときにこれで接続を切り、未送信の応答を捨てる。
    """
    self.scope["mekiki.abort"] = self.transport.abort
    return await _UVICORN_RUN_ASGI(self, app)


uvicorn_h11.RequestResponseCycle.run_asgi = _run_asgi_with_abort



def _message_bytes(message) -> int:
    """結果の大きさ。queue/data が送るのと同じ直列化（UTF-8 の JSON）で数える（Codex③ 4）。"""
    try:
        return len(orjson.dumps(message.model_dump(), default=str))
    except Exception:  # noqa: BLE001 - 形が違うもの（試験の作り物など）は表示形の UTF-8 で数える
        return len(str(message).encode("utf-8"))


def _working(queue, session: str) -> bool:
    """セッションに、待ち行列の中か実行中の呼び出しがあるか。"""
    events = getattr(queue, "event_ids_to_events", {})
    return any(event_id in events for event_id in getattr(queue, "pending_event_ids_session", {}).get(session, ()))


def _protected(queue, session: str) -> bool:
    """期限や追い出しで消してはいけないセッション（内部クライアント・回収中・処理中）。"""
    return session == _internal_session() or _COLLECTING.get(session, 0) > 0 or _working(queue, session)


def _release_session(queue, session: str, events: bool = True) -> None:
    """追い出したセッションに結びつく記録を一度に消す（イベント ID・イベント・状態・時刻。Codex③ 2）。

    events=False は、上流が自分で消した（queue/data の切断）ときに使う。イベントは上流の clean_events が片づける。
    """
    for event_id in getattr(queue, "pending_event_ids_session", {}).pop(session, None) or ():
        if events:
            getattr(queue, "event_ids_to_events", {}).pop(event_id, None)
    holder = getattr(getattr(queue, "blocks", None), "state_holder", None)
    if holder is not None:
        with holder.lock:
            holder.session_data.pop(session, None)
            holder.time_last_used.pop(session, None)


class _SessionTable(gradio.utils.LRUCache):
    """未回収の結果を持つセッションの表（上流の LRU の差し替え。Codex③ 2）。

    上流は溢れた分を古い順に捨てるだけで、そのセッションのイベント ID などは残り続ける。
    ここでは追い出すときに関連する記録を一緒に消し、内部クライアント・回収中・処理中のセッションは追い出さない
    （追い出すと、その呼び出しの結果を入れる先が無くなって失敗する）。
    """

    def __init__(self, max_size: int, owner) -> None:
        super().__init__(max_size)
        self.owner = owner

    def __setitem__(self, key, value) -> None:
        if key not in self and len(self) >= self.max_size:
            victim = next((k for k in self if not _protected(self.owner, k)), None)
            if victim is None:  # すべて保護（起こらない想定：処理中は待ち行列72まで・回収中は流れ8本まで）
                victim = next(iter(self))
            super().pop(victim, None)
            _release_session(self.owner, victim)
            _SWEEP["evicted"] += 1
        super().__setitem__(key, value)

    def __delitem__(self, key) -> None:
        """上流が消すとき（queue/data の切断）も、関連する記録を一緒に消す（Codex③ 2 の検算）。"""
        super().__delitem__(key)
        _release_session(self.owner, key, events=False)


def install_queue_hooks(demo) -> None:
    """待ち行列にセッション表の差し替えと、結果ができた時刻の記録を入れる（build_blocks から一度だけ）。"""
    queue = getattr(demo, "_queue", None)
    if queue is None or isinstance(queue.pending_messages_per_session, _SessionTable):
        return
    table = _SessionTable(queue.pending_messages_per_session.max_size, queue)
    table.update(queue.pending_messages_per_session)
    queue.pending_messages_per_session = table
    original = queue.send_message

    def send_message(event, event_message):
        original(event, event_message)
        _BORN[id(event_message)] = [time.monotonic(), event_message, None]

    send_message.mekiki_stamp = True  # verify_blocks が差し替えを確かめる印
    queue.send_message = send_message


def sweep_results(queue, now: float) -> int:
    """回収されない結果を、できた時刻からの経過・件数・大きさで捨てる。捨てた結果の数を返す（Codex③ 2〜4）。

    Gradio の待ち行列は、`/queue/join` で作った結果を `/queue/data` が取りに来るまで持ち続ける。
    取りに来ない相手がいると溜まり続けるので、ここで打ち切る。セッションそのものは消さない（処理中の
    呼び出しが結果を入れる先を失わないように）。回収中（queue/data が開いている）のセッションには期限を
    当てないが、件数と大きさの上限は当てる（受け取りを止めた相手でも溜まり続けないように）。
    内部クライアントのセッションには手を付けない。捨てた完了の結果のイベント ID も片づける。
    """
    sessions = getattr(queue, "pending_messages_per_session", None)
    if not isinstance(sessions, dict):
        return 0
    live: set[int] = set()
    dropped = 0
    internal = _internal_session()
    events = getattr(queue, "event_ids_to_events", {})
    ids_by_session = getattr(queue, "pending_event_ids_session", {})
    for session in list(sessions):
        pending = sessions.get(session)
        items = list(getattr(pending, "_queue", []) or [])
        if not items:
            continue  # 空のセッションは期限では消さない
        stamps = []
        for item in items:
            born = _BORN.get(id(item))
            if born is None or born[1] is not item:  # 記録の無い結果（上流が直接入れたもの）は、見つけた時刻から数える
                born = _BORN[id(item)] = [now, item, None]
            if born[2] is None:
                born[2] = _message_bytes(item)
            stamps.append(born)
            live.add(id(item))
        if session == internal:
            continue  # 内部クライアント：自分で取りに来続ける
        collecting = _COLLECTING.get(session, 0) > 0
        keep = [b for b in stamps if collecting or now - b[0] <= RESULT_TTL_SECONDS]
        while keep and (len(keep) > RESULT_MESSAGES_MAX or sum(b[2] for b in keep) > RESULT_BYTES_MAX):
            keep.pop(0)  # 古いものから捨てる
        if len(keep) == len(stamps):
            continue
        kept = {id(b[1]) for b in keep}
        pending._queue = deque(item for item in items if id(item) in kept)
        dropped += len(stamps) - len(keep)
        for born in stamps:
            if id(born[1]) in kept:
                continue
            live.discard(id(born[1]))
            event_id = getattr(born[1], "event_id", None)
            if getattr(born[1], "msg", None) == "process_completed" and event_id and event_id not in events:
                ids = ids_by_session.get(session)
                if ids is not None:  # 終わった呼び出しの ID は、完了の結果を捨てたら持たない（Codex③ 2 の検算）
                    ids.discard(event_id)
                    if not ids:
                        ids_by_session.pop(session, None)
    for key in [k for k in _BORN if k not in live]:  # 回収された・捨てた結果の記録を片づける
        _BORN.pop(key, None)
    _SWEEP["dropped"] += dropped
    return dropped


def start_sweeper(demo) -> None:
    """掃除を、要求を処理している event loop の上で回す（最初の要求のときに一度だけ）。"""
    if _SWEEP["task"] is not None:
        return

    async def loop_body():
        while True:
            await asyncio.sleep(RESULT_SWEEP_SECONDS)
            _SWEEP["runs"] += 1
            try:
                sweep_results(getattr(demo, "_queue", None), time.monotonic())
            except Exception as exc:  # noqa: BLE001 - 掃除で落とさない
                print(f"sweep failed: {type(exc).__name__}", file=sys.stderr, flush=True)

    _SWEEP["task"] = asyncio.get_running_loop().create_task(loop_body())


def check_cors(port: int) -> list[str]:
    """Origin 付きの要求に CORS の許可ヘッダが付かないことを、自分自身に当てて確かめる。"""
    conn = http.client.HTTPConnection(LOOPBACK, port, timeout=5)
    try:
        conn.request("GET", "/gradio_api/info", headers={"Origin": "http://localhost:1"})  # 開いている経路で確かめる
        response = conn.getresponse()
        response.read()
        allowed = sorted({k.lower() for k, _ in response.getheaders() if k.lower().startswith("access-control")})
        return [f"cors={'・'.join(allowed)}"] if allowed else []
    except OSError as exc:
        return [f"cors-check-failed={type(exc).__name__}"]
    finally:
        conn.close()


def _no_cors(send):
    """応答から CORS の許可ヘッダを落とす（Origin 付きの要求にだけ使う）。"""

    async def wrapped(message):
        if message.get("type") == "http.response.start":
            message = dict(message)
            message["headers"] = [(k, v) for k, v in message.get("headers", [])
                                  if k.lower() not in CORS_RESPONSE_HEADERS]
        await send(message)

    return wrapped


def _stream_kind(method: str, path: str) -> "str | None":
    """長時間つながったままになる経路の種類（上限を数える単位）。"""
    if path.startswith("/gradio_api/heartbeat/"):
        return "heartbeat"
    if path == "/gradio_api/queue/data":
        return "queue_data"
    if path == "/gradio_api/mcp/" and method == "GET":  # Streamable HTTP の待ち受け（切られるまで続く）
        return "mcp_get"
    return None


def _stream_session(kind: str, scope) -> "str | None":
    """要求が名乗るセッション（heartbeat は経路の末尾、queue/data は問い合わせの session_hash の最後の値）。"""
    if kind == "heartbeat":
        return scope.get("path", "").rsplit("/", 1)[-1]
    if kind == "queue_data":
        pairs = urllib.parse.parse_qsl(scope.get("query_string", b"").decode("latin-1"), keep_blank_values=True)
        values = [v for k, v in pairs if k == "session_hash"]
        return values[-1] if values else None
    return None


def _internal_session(demo=None) -> "str | None":
    """自己呼び出しの内部クライアントのセッション（まだ作られていなければ None）。"""
    server = getattr(DEMO if demo is None else demo, "mcp_server_obj", None)
    return getattr(getattr(server, "_client_instance", None), "session_hash", None)


def warm_internal_client(demo) -> None:
    """内部クライアント（resources/read・prompts/get の自己呼び出し）を、起動の直後に一つだけ作る。

    上流は最初の呼び出しのときに worker thread で鍵なしに作るため、同時に来ると複数できる
    （余りは heartbeat を張ったまま残り、内部と見分けられない）。
    作成に鍵をかけると、待つ thread が共有の thread pool を塞ぎ、作成の自己要求（GET /）が進まなくなる
    （検算）。そこで要求を受ける前に作っておき、それまでは外からの MCP を受けない（mark_ready）。
    引数は上流（gradio/mcp.py の _get_or_create_client・Gradio 6.27.0）と同じ。失敗は verify_blocks が拾う。
    """
    server = getattr(demo, "mcp_server_obj", None)
    if server is None or getattr(server, "_client_instance", None) is not None:
        return
    try:
        server._client_instance = gradio_client.Client(
            server.local_url,
            download_files=False,
            verbose=False,
            analytics_enabled=False,
            ssl_verify=False,
            _skip_components=False,
            headers={"x-gradio-user": "mcp"},
        )
    except Exception as exc:  # noqa: BLE001 - 起動後の確認で止める
        print(f"internal client failed: {type(exc).__name__}", file=sys.stderr, flush=True)


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


async def _read_body(receive, declared: "int | None"):
    """本文を読み切る。期限は受信ループ全体で一つ（小分けに送って総時間を延ばせないように。Codex② 3）。

    返り値：("ok", 後段に渡す receive) ／ ("reply", 状態コード, 文) ／ ("gone",)（相手が切った）。
    """
    chunks, total = [], 0
    loop = asyncio.get_running_loop()
    deadline = loop.time() + BODY_READ_SECONDS
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            return ("reply", 408, "request body timeout")
        try:
            message = await asyncio.wait_for(receive(), remaining)
        except (asyncio.TimeoutError, TimeoutError):
            return ("reply", 408, "request body timeout")
        if message["type"] == "http.disconnect":
            return ("gone",)
        chunks.append(message.get("body", b""))
        total += len(chunks[-1])
        if total > MAX_BODY_BYTES:
            return ("reply", 413, "request body too large")
        if not message.get("more_body", False):
            break
    if declared is not None and total != declared:
        return ("reply", 400, "conflicting framing")
    return ("ok", _replayer(b"".join(chunks), receive))


def _guard_middleware():
    """Gradio の標準経路を遮断する ASGI ミドルウェア（Q66・Codex① P1-2・P2-4）。"""

    async def _drain(receive) -> None:
        """断る前に本文を読み捨てる（64 KiB・1秒まで。保持はしない）。

        応答の後に接続を閉じるとき、相手が本文を送り終えていないと、閉じた側から RST が飛び、
        相手が応答を読めないことがある（検算で再現）。
        """
        loop = asyncio.get_running_loop()
        deadline, total = loop.time() + DRAIN_SECONDS, 0
        while total <= MAX_BODY_BYTES:
            remaining = deadline - loop.time()
            if remaining <= 0:
                return
            try:
                message = await asyncio.wait_for(receive(), remaining)
            except (asyncio.TimeoutError, TimeoutError):
                return
            if message["type"] == "http.disconnect":
                return
            total += len(message.get("body", b""))
            if not message.get("more_body", False):
                return

    async def _reply(send, status: int, text: str, path: str = "", drain=None) -> None:
        if drain is not None:
            await _drain(drain)
        safe = path.encode("unicode_escape").decode("ascii")[:200]  # 記録に制御文字を通さない
        GUARD_LOG.append((status, safe))
        GUARD_COUNTS[status] = GUARD_COUNTS.get(status, 0) + 1
        # 標準エラーには経路を出さない（経路・問い合わせは利用者の入力。記録は上の固定長の表だけ。Codex③ 7）
        print(f"blocked {status} {text}", file=sys.stderr, flush=True)
        # 断った要求の接続は閉じる（HTTP の層が先に受け取った本文も一緒に手放す。Codex③ 1 の検算）
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"text/plain; charset=utf-8"), (b"connection", b"close")]})
        await send({"type": "http.response.body", "body": text.encode("utf-8")})

    async def _health(send, method: str, receive) -> None:
        await _drain(receive)
        body = HEALTH_HTML.encode("utf-8")
        await send({"type": "http.response.start", "status": 200,
                    "headers": [(b"content-type", b"text/html; charset=utf-8"),
                                (b"content-length", str(len(body)).encode("ascii")), (b"connection", b"close")]})
        await send({"type": "http.response.body", "body": b"" if method == "HEAD" else body})

    async def _finish_read(send, read, path: str) -> None:
        if read[0] == "reply":
            return await _reply(send, read[1], read[2], path)
        return None  # 相手が切った

    class Guard:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "lifespan":
                return await self.app(scope, receive, send)
            if _SWEEP["task"] is None and DEMO is not None:
                start_sweeper(DEMO)
            if scope["type"] != "http":
                return  # websocket などは受け付けない
            path = scope.get("path", "")
            raw = scope.get("headers", [])
            if any(k.lower() == b"origin" for k, v in raw):  # ブラウザからの読み取りを許さない
                send = _no_cors(send)
            hosts = [v.decode("latin-1", "replace") for k, v in raw if k.lower() == b"host"]
            if len(hosts) != 1 or _host_name(hosts[0]) not in ALLOWED_HOSTS:
                # spaces では `/` だけ Host を問わない（健康検査が送る Host は決まっていない。SPEC v2.4 §2.10）
                health = (DEPLOY["mode"] == "spaces" and path == "/"
                          and scope.get("method", "GET").upper() in ("GET", "HEAD"))
                if not health:
                    return await _reply(send, 400, "bad host", path, receive)
                # 健康検査には固定の短い HTML だけを返す（Gradio の画面は要求の Host から設定を組み立てるため、
                # 許可していない Host には渡さない）
                return await _health(send, scope.get("method", "GET").upper(), receive)

            # 本文の長さの表明（Codex① P1-2）：TE と CL の併記は拒み、CL は ASCII 数字だけを受ける。
            lengths = [v.decode("latin-1", "replace").strip() for k, v in raw if k.lower() == b"content-length"]
            encodings = [v.decode("latin-1", "replace").strip().lower()
                         for k, v in raw if k.lower() == b"transfer-encoding"]
            chunked = any("chunked" in v for v in encodings)
            if lengths and encodings:
                return await _reply(send, 400, "conflicting framing", path)
            if len(lengths) > 1:  # 値の違う重複は h11 が先に 400 にする。同値は畳まれてここには来ない
                return await _reply(send, 400, "conflicting framing", path)
            declared = None
            if lengths:
                if not _ASCII_DIGITS.fullmatch(lengths[0]):
                    return await _reply(send, 400, "bad content-length", path)
                declared = int(lengths[0])
                if declared > MAX_BODY_BYTES:
                    return await _reply(send, 413, "request body too large", path)

            if any(mark in path for mark in BLOCKED_MARKS):
                return await _reply(send, 403, "route disabled", path, receive)
            if path not in ALLOWED_EXACT and not path.startswith(ALLOWED_PREFIXES):
                return await _reply(send, 404, "not found", path, receive)

            method = scope.get("method", "GET").upper()
            if path.startswith("/gradio_api/mcp") and not _READY["mcp"]:  # 起動の確認が済むまで（Codex③ 5）
                return await _reply(send, 503, "starting", path, receive)
            takes_body = (declared is not None or chunked or method in BODY_METHODS)
            pre_read = takes_body and path.startswith(PRE_READ_PREFIXES)

            kind = _stream_kind(method, path)
            if kind is not None and (chunked or (declared or 0) > 0):  # 長時間接続に本文は要らない（受付枠の外で抱えない）
                return await _reply(send, 400, "body not allowed", path, receive)
            if kind is not None:  # 長時間接続は種類ごとに同時数を絞る（内部クライアントは数えるが断らない）
                session = _stream_session(kind, scope)
                internal = session is not None and session == _internal_session()
                if not internal and _STREAMS["open"][kind] >= STREAM_LIMITS[kind]:
                    _STREAMS["rejected"][kind] += 1
                    return await _reply(send, 503, "too many open streams", path, receive)
                _STREAMS["open"][kind] += 1
                _STREAMS["peak"][kind] = max(_STREAMS["peak"][kind], _STREAMS["open"][kind])
                if internal:
                    _STREAMS["internal_open"][kind] += 1
                    _STREAMS["internal_peak"][kind] = max(_STREAMS["internal_peak"][kind],
                                                          _STREAMS["internal_open"][kind])
                if kind == "queue_data" and session is not None:
                    _COLLECTING[session] = _COLLECTING.get(session, 0) + 1
                try:
                    return await self.app(scope, receive, send)
                finally:
                    _STREAMS["open"][kind] -= 1
                    if internal:
                        _STREAMS["internal_open"][kind] -= 1
                    if kind == "queue_data" and session is not None:
                        left = _COLLECTING.get(session, 1) - 1
                        if left > 0:
                            _COLLECTING[session] = left
                        else:
                            _COLLECTING.pop(session, None)

            # 受付枠は本文を読む前に取り、応答を送り終えるまで持つ（Codex③ 1）。
            admission = _admission_kind(method, path)
            if not await _admit(admission):
                return await _reply(send, 503, "busy", path, receive)
            started = False

            async def tracked(message):
                nonlocal started
                if message.get("type") == "http.response.start":
                    started = True
                await send(message)

            try:
                async with asyncio.timeout(REQUEST_SECONDS):
                    forward = receive
                    if pre_read:  # 本文は実際に届いたバイト数で打ち切る（表明を信じない）
                        read = await _read_body(receive, declared)
                        if read[0] != "ok":
                            return await _finish_read(tracked, read, path)
                        forward = read[1]
                    return await self.app(scope, forward, tracked)
            except TimeoutError:  # 期限までに送り終わらない（受け取りを止めた相手など）。枠を返して切る
                _ADMISSION[admission]["expired"] += 1
                if not started:
                    return await _reply(send, 503, "request timeout", path)
                abort = scope.get("mekiki.abort")
                if abort is not None:  # 送信の途中：接続をすぐ切り、未送信の応答を捨てる
                    abort()
                    _ADMISSION[admission]["aborted"] += 1
                return None
            finally:
                _release(admission)

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
    install_queue_hooks(demo)
    global DEMO
    DEMO = demo
    return demo


def verify_blocks(demo, launched: bool = False, port: int | None = None) -> list[str]:
    """環境変数だけで有効になる経路が無効であることを確かめる（Q93・Codex① P1-3）。問題の一覧を返す。"""
    problems = []
    if DEPLOY["error"]:
        problems.append(f"mode={DEPLOY['error']}")
    left = sorted(k for k in os.environ if k in SPACES_ENV_NAMES or k.startswith(SPACES_ENV_PREFIXES))
    if left:
        problems.append(f"spaces-env-left={','.join(left)}")
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
    if not isinstance(gradio.queueing.traceback, _QuietTraceback):
        problems.append("queue-traceback=unpatched")
    if launched and any(logging.getLogger(n).handlers != [LOG_HANDLER] for n in REDACTED_LOGGERS):
        problems.append("log-handlers=unredacted")
    if uvicorn.Config.configure_logging is not _configure_logging_redacted:
        problems.append("uvicorn-logging=unpatched")
    if uvicorn_h11.RequestResponseCycle.run_asgi is not _run_asgi_with_abort:
        problems.append("uvicorn-abort=unpatched")
    if any(getattr(fn, "validator", None) is not None for fn in demo.fns.values()):
        problems.append("validator=present")  # 上流は validator の例外文を印字する（queueing.py の push）
    queue = getattr(demo, "_queue", None)
    if not isinstance(getattr(queue, "pending_messages_per_session", None), _SessionTable):
        problems.append("queue-session-table=unpatched")
    if not getattr(getattr(queue, "send_message", None), "mekiki_stamp", False):
        problems.append("queue-send-message=unpatched")
    if getattr(queue, "max_size", None) != QUEUE_MAX_SIZE:
        problems.append(f"queue.max_size={getattr(queue, 'max_size', 'missing')!r}")
    if getattr(queue, "default_concurrency_limit", None) != MAX_CONCURRENCY:
        problems.append(f"queue.concurrency={getattr(queue, 'default_concurrency_limit', 'missing')!r}")
    if launched:
        url = getattr(demo, "local_url", "") or ""
        url_host = "localhost" if SERVER_NAME == "0.0.0.0" else SERVER_NAME  # 上流は 0.0.0.0 を localhost で表す
        if not url.startswith(f"http://{url_host}:"):
            problems.append(f"local_url={url!r}")
        if port is not None:
            problems += check_cors(port)
        if _internal_session(demo) is None:
            problems.append("internal-client=missing")
    return problems


def launch(demo, port: int):
    """loopback で起動する。環境変数では bind 先が変わらない（Q67）。内部クライアントもここで作る。"""
    launched = demo.launch(
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
        pwa=False,  # 上流は Spaces 上で既定を True にする（SYSTEM を消しても明示する。SPEC v2.4 §2.10）
        inbrowser=False,
        allowed_paths=[],
        blocked_paths=[],
        quiet=False,
        prevent_thread_lock=True,
        app_kwargs={"middleware": [Middleware(_guard_middleware())]},
    )
    redact_logs()
    warm_internal_client(demo)
    return launched


def _stop_requested(_signum, _frame) -> None:
    """停止の合図（SIGTERM）。block_thread が KeyboardInterrupt を受けて待ち受けを閉じる。"""
    raise KeyboardInterrupt


def startup_lines(port: int) -> list[str]:
    """起動表示（版・件数・消した環境変数の名前・モードと許可 Host）。値そのものは出さない。"""
    return [
        f"corpus {C.CORPUS_VERSION} ({C.CORPUS_COMMIT[:7]})・bundle {C.EXPECTED_BUNDLE_SHA256[:12]}…",
        f"tools 7・resources {len(RESOURCES)}・prompts {len(PR.TEMPLATES)}（{PR.PROMPTS_VERSION}）",
        f"消した環境変数：{'・'.join(REMOVED_GRADIO_ENV) or 'なし'}",
        f"モード {DEPLOY['mode']}・待ち受け {SERVER_NAME}:{port}・許可 Host：{'・'.join(DEPLOY['hosts'])}",
    ]


def main() -> int:
    global READER
    if DEPLOY["error"]:
        print(f"起動しない：{DEPLOY['error']}", file=sys.stderr, flush=True)
        return 7
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
    mark_ready()
    for line in startup_lines(port):
        print(line, flush=True)
    # コンテナでは PID 1 になり、SIGTERM は処理を置かないと届かない。停止の合図は Ctrl-C と同じに扱う
    signal.signal(signal.SIGTERM, _stop_requested)
    try:
        demo.block_thread()
    except KeyboardInterrupt:
        demo.close()
    return 0


READER: T.Reader | None = None
DEMO = None  # 掃除がたどる Blocks（build_blocks で入れる）

if __name__ == "__main__":
    sys.exit(main())
