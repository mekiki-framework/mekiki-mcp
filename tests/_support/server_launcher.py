"""試験用の起動器（S01〜S03）。監査フックを入れてから app を起動し、記録をファイルに書く。

`sys.addaudithook` は import gradio より前に入れる（Codex① P2-6 の差分案）。
- 宛先は host:port で記録する（ポートまで見る）。
- 免除するのは**実際の自己接続だけ**（loopback かつ自分の待ち受けポート）。
- Unix ソケットは免除しない。
- `open` は flags・mode まで、**起動前から停止まで**記録する（段階の札を付ける）。
- パスは操作ごとに絶対パスへ直す（相対パスは cwd、dir_fd つきはその記述子の指す先。Codex③ 6）。
  解決できないものは `unresolved:…` と記録し、書き換えなら止める（検出できたことにしない）。
- 最後に陽性対照を行い、フック自体が効いていることを確かめる。

環境変数：MEKIKI_AUDIT_LOG（記録の書き出し先）・MEKIKI_TEST_*（試験だけが上限や間隔を変える。main() を見る）。
ポートは起動器の内部引数 `--port N` で受ける（MEKIKI_READER_PORT は読まない。spaces は本番では 7860 固定なので、
試験の空きポートは app の設定とは別に渡す。Codex④ F7）。
"""

import fcntl
import functools
import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = str(REPO_ROOT / "data")
DATA_DIRS = (DATA_DIR, os.path.realpath(DATA_DIR))
# data/ の中身を「同じもの」で見分ける印（別名のパス・ハードリンクでも見逃さない。Codex③ 6 の検算）
DATA_IDS = frozenset((st.st_dev, st.st_ino) for st in (
    os.stat(os.path.join(root, name)) for root, dirs, files in os.walk(DATA_DIR) for name in [".", *dirs, *files]))
INSIDE_WRAPPER = threading.local()  # os.open の包みの中（監査事象 open を二重に記録しない）
sys.path.insert(0, str(REPO_ROOT))

AUDIT_LOG = Path(os.environ["MEKIKI_AUDIT_LOG"])
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "ip6-localhost", "0.0.0.0", ""})
NET_EVENTS = ("socket.connect", "socket.getaddrinfo", "socket.sendto", "socket.sendmsg",
              "socket.gethostbyname", "socket.gethostbyname_ex", "socket.gethostbyaddr",
              "socket.getnameinfo", "urllib.Request", "http.client.connect")
# 子プロセスは別のプロセスなのでフックが届かない。起こすこと自体を記録する（検算⑥a）。
PROCESS_EVENTS = ("subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "os.forkpty",
                  "os.exec", "os.spawn", "pty.spawn")
# open 以外の書き換え経路（検算⑥c）。リポジトリ配下に出たら S03 が落ちる。
MUTATE_EVENTS = ("os.rename", "os.remove", "os.unlink", "os.mkdir", "os.rmdir", "os.symlink",
                 "os.link", "os.truncate", "os.chmod", "os.chown", "os.replace", "shutil.rmtree",
                 "shutil.move", "shutil.copyfile")
BIND_EVENTS = ("socket.bind",)
OPEN_MAX = 20000  # 記録の上限（起動前の import も全部入るため）

STATE = {"phase": "import", "port": None, "control": False, "bound": []}
NET: list[list] = []          # 通信の記録（全部・[event, target, phase]）
OUTBOUND: list[list] = []     # 自己接続以外（例外にした分。陽性対照の分は含めない）
CONTROL_NET: list[list] = []  # 陽性対照で自分から試みた分
OPENED: list[list] = []       # 開いたファイル（[パス, mode, flags, phase]）
OPEN_DROPPED = {"n": 0}       # 上限で捨てた件数（黙って空振りしないため）
PROCESS: list[list] = []      # 子プロセスを起こした記録
MUTATED: list[list] = []      # open 以外の書き換え（rename・remove ほか）
BOUND: list[list] = []        # 待ち受けた宛先
CONTROL: dict[str, str] = {}  # 陽性対照の結果


def _target(event: str, args) -> str:
    """宛先を host:port の形にする。Unix ソケットは unix:<パス>。"""
    if event in ("socket.connect", "socket.sendto", "socket.sendmsg"):
        address = args[1] if len(args) > 1 else None
        if address is None and event != "socket.connect" and args:
            # 宛先を付けない sendmsg は、つながっている相手へ送る（asyncio は溜まった応答をこれで書く）。
            # 自分の待ち受けで受けた接続なら自分の側の宛先で、そうでなければ相手の宛先で記録する
            # （外向きの接続なら、相手の宛先で同じく止まる）。
            try:
                local = args[0].getsockname()
                address = local if str(local[1]) == str(STATE["port"]) else args[0].getpeername()
            except (OSError, AttributeError, IndexError, TypeError):
                address = None
        if isinstance(address, tuple) and address:
            host = str(address[0])
            port = address[1] if len(address) > 1 else ""
            return f"{host}:{port}"
        if isinstance(address, (str, bytes, os.PathLike)):
            name = address.decode("utf-8", "replace") if isinstance(address, bytes) else os.fspath(address)
            return f"unix:{name}"
        return "" if address is None else str(address)[:80]
    if event in ("socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyname_ex"):
        host = args[0] if args else ""
        name = host.decode("utf-8", "replace") if isinstance(host, bytes) else str(host)
        port = args[1] if len(args) > 1 else ""
        return f"{name}:{port}"
    if event == "http.client.connect":
        # args[0] は HTTPConnection。宛先は host/port 属性から取る（object の repr にしない）。
        conn = args[0] if args else None
        return f"{getattr(conn, 'host', '')}:{getattr(conn, 'port', '')}"
    if event == "urllib.Request":
        return str(args[0])[:120] if args else ""
    return str(args[0]) if args else ""


def _fd_path(fd: int) -> "str | None":
    """ファイル記述子が指す先の絶対パス（macOS は F_GETPATH、Linux は /proc）。分からなければ None。

    /dev/fd の readlink は macOS では EINVAL になり、使えない（Codex③ 6）。
    """
    try:
        if hasattr(fcntl, "F_GETPATH"):
            raw = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024))
            return os.fsdecode(raw.split(b"\0", 1)[0]) or None
        return os.readlink(f"/proc/self/fd/{fd}")
    except (OSError, ValueError, TypeError):
        return None


def _resolve(value, dir_fd=None) -> str:
    """操作の対象を絶対パスにする。解決できなければ "unresolved:…"（検出できたことにしない）。"""
    if value is None:
        return ""
    if isinstance(value, int) and not isinstance(value, bool):  # 記述子そのもの
        return _fd_path(value) or f"unresolved:fd={value}"
    try:
        name = os.fsdecode(value)
    except TypeError:
        return f"unresolved:{type(value).__name__}"
    if not name:
        return ""
    if os.path.isabs(name):
        return os.path.normpath(name)
    if isinstance(dir_fd, int) and dir_fd >= 0:
        base = _fd_path(dir_fd)
        return os.path.normpath(os.path.join(base, name)) if base else f"unresolved:dir_fd={dir_fd}"
    return os.path.abspath(name)


# 書き換えの対象になる引数（パスの位置, dir_fd の位置）。CPython の監査事象の引数の並び。
MUTATE_TARGETS = {
    "os.rename": ((0, 2), (1, 3)), "os.replace": ((0, 2), (1, 3)), "os.link": ((0, 2), (1, 3)),
    "os.remove": ((0, 1),), "os.unlink": ((0, 1),), "os.rmdir": ((0, 1),), "os.mkdir": ((0, 2),),
    "os.symlink": ((1, 2),), "os.truncate": ((0, None),), "os.chmod": ((0, 2),), "os.chown": ((0, 3),),
    "shutil.rmtree": ((0, 1),), "shutil.move": ((0, None), (1, None)), "shutil.copyfile": ((1, None),),
}


def _paths_of(event: str, args) -> list[str]:
    """書き換えの元・先を、操作ごとの dir_fd で解決した絶対パスにする（Codex② 4・Codex③ 6）。"""
    paths = []
    for index, fd_index in MUTATE_TARGETS.get(event, ((0, None), (1, None))):
        if index >= len(args):
            continue
        dir_fd = args[fd_index] if fd_index is not None and fd_index < len(args) else None
        paths.append(_resolve(args[index], dir_fd))
    while len(paths) < 2:
        paths.append("")
    return paths


def _in_data(path: str) -> bool:
    """data/ の中か。文字列（そのままと実体のパス）に加えて、実体の同一性（dev・inode）でも見る。

    まだ無いファイルは、いちばん近くにある親の同一性で見る（data/ の別名のパスの下に作る場合）。
    """
    if not path or path.startswith("unresolved:"):
        return False
    real = os.path.realpath(path)
    if any(p == d or p.startswith(d + os.sep) for p in (path, real) for d in DATA_DIRS):
        return True
    probe = path
    while probe and probe != os.path.dirname(probe):
        try:
            st = os.stat(probe)
        except OSError:
            probe = os.path.dirname(probe)
            continue
        return (st.st_dev, st.st_ino) in DATA_IDS
    return False


def _is_write_open(mode, flags) -> bool:
    if isinstance(mode, str) and any(c in mode for c in "wax+"):
        return True
    if isinstance(flags, int):
        return bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
    return False


def _is_self(event: str, target: str) -> bool:
    """自分自身への接続だけを免除する（実際に bind した宛先と自分のポートに限る。Codex② 4）。"""
    if target.startswith("unix:"):
        return False  # Unix ソケットは免除しない
    host, _, port = target.rpartition(":")
    bound = {h for h, _p in STATE["bound"]} or {"127.0.0.1"}
    if event in ("socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyname_ex",
                 "socket.gethostbyaddr", "socket.getnameinfo"):
        return host in bound  # 名前ではなく、実際に bind したアドレスのときだけ免除
    if host not in bound:
        return False  # localhost・0.0.0.0・bind していない ::1 は免除しない
    return STATE["port"] is not None and port == str(STATE["port"])


def _audit(event, args) -> None:
    if event in NET_EVENTS:
        target = _target(event, args)
        record = [event, target, STATE["phase"]]
        NET.append(record)
        if not _is_self(event, target):
            (CONTROL_NET if STATE["control"] else OUTBOUND).append(record)
            raise RuntimeError(f"outbound connection blocked in the test launcher: {event} {target}")
    elif event == "open":
        if getattr(INSIDE_WRAPPER, "active", False):
            return  # os.open の包みが dir_fd で解決して記録・判定済み
        path = args[0] if args else ""
        mode = args[1] if len(args) > 1 else ""
        flags = args[2] if len(args) > 2 else ""
        resolved = _resolve(path)  # 相対パスは cwd 基準で絶対パスに（Codex③ 6）
        writing = _is_write_open(mode, flags)
        if len(OPENED) >= OPEN_MAX:
            OPEN_DROPPED["n"] += 1
        else:
            OPENED.append([resolved, str(mode), str(flags), STATE["phase"]])
        if writing and (_in_data(resolved) or resolved.startswith("unresolved:")):
            raise RuntimeError(f"data/ write blocked in the test launcher: open {resolved}")
    elif event.startswith(PROCESS_EVENTS):
        PROCESS.append([event, str(args[0])[:120] if args else "", STATE["phase"]])
        raise RuntimeError(f"child process blocked in the test launcher: {event}")
    elif event in MUTATE_EVENTS:
        paths = _paths_of(event, args)
        MUTATED.append([event, *paths, STATE["phase"]])
        # 原文は書き換えさせない（記録だけにしない）。解決できない対象も止める（検出漏れを成功にしない）。
        if any(_in_data(p) or p.startswith("unresolved:") for p in paths if p):
            raise RuntimeError(f"data/ write blocked in the test launcher: {event} {paths[:2]}")
    elif event in BIND_EVENTS:
        address = args[1] if len(args) > 1 else None
        if isinstance(address, tuple) and address:
            STATE["bound"].append((str(address[0]), address[1] if len(address) > 1 else ""))
        BOUND.append([event, str(address)[:80], STATE["phase"]])


sys.addaudithook(_audit)

# 監査事象 "open" には dir_fd が載らない。Python から os.open(…, dir_fd=…) を呼ぶ経路は包んで解決する
# （C の拡張が直接 openat を呼ぶ経路はここでも見えない。既知の限界。Codex③ 6）。
_OS_OPEN = os.open


@functools.wraps(_OS_OPEN)
def _open_with_dir_fd(path, flags, mode=0o777, *, dir_fd=None):
    if dir_fd is not None:
        resolved = _resolve(path, dir_fd)
        OPENED.append([resolved, "", str(flags), STATE["phase"]])
        if _is_write_open("", flags) and (_in_data(resolved) or resolved.startswith("unresolved:")):
            raise RuntimeError(f"data/ write blocked in the test launcher: os.open {resolved}")
        INSIDE_WRAPPER.active = True
        try:
            return _OS_OPEN(path, flags, mode, dir_fd=dir_fd)
        finally:
            INSIDE_WRAPPER.active = False
    return _OS_OPEN(path, flags, mode)


os.open = _open_with_dir_fd
# shutil・filelock は os.supports_dir_fd を見て経路を選ぶ。包んだ後も本番と同じ経路を通らせる。
if _OS_OPEN in os.supports_dir_fd:
    os.supports_dir_fd.add(_open_with_dir_fd)

import app  # noqa: E402  （監査フックの後に読み込む）
import gradio_client  # noqa: E402

CLIENTS = {"created": 0}  # 内部クライアントを作った回数（起動の競合で増えないこと。Codex③ 5）
_CLIENT_INIT = gradio_client.Client.__init__


def _counting_init(self, *args, **kwargs):
    CLIENTS["created"] += 1
    return _CLIENT_INIT(self, *args, **kwargs)


gradio_client.Client.__init__ = _counting_init


def _control(name: str, run) -> None:
    """陽性対照を一つ実行し、結果を残す（フラグは必ず戻す）。"""
    STATE["control"] = True
    try:
        run()
        CONTROL[name] = "NOT BLOCKED"
    except RuntimeError as exc:
        CONTROL[name] = f"blocked: {exc}"[:140]
    except Exception as exc:  # noqa: BLE001
        CONTROL[name] = f"other: {type(exc).__name__}"
    finally:
        STATE["control"] = False


def _positive_control() -> None:
    """フックが効いていることを確かめる（実際には一歩も外に出ない）。"""
    STATE["control"] = True
    try:
        socket.getaddrinfo("mekiki-control.invalid", 80)
        CONTROL["getaddrinfo"] = "NOT BLOCKED"
    except RuntimeError as exc:
        CONTROL["getaddrinfo"] = f"blocked: {exc}"[:120]
    except Exception as exc:  # noqa: BLE001
        CONTROL["getaddrinfo"] = f"other: {type(exc).__name__}"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        sock.connect(("203.0.113.1", 80))  # TEST-NET-3（到達しない）
        CONTROL["connect"] = "NOT BLOCKED"
    except RuntimeError as exc:
        CONTROL["connect"] = f"blocked: {exc}"[:120]
    except Exception as exc:  # noqa: BLE001
        CONTROL["connect"] = f"other: {type(exc).__name__}"
    finally:
        sock.close()
    # 自己接続は通ること（免除が効いていること）も確かめる。
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(1.0)
    try:
        probe.connect(("127.0.0.1", int(STATE["port"])))
        CONTROL["self"] = "allowed"
    except RuntimeError as exc:
        CONTROL["self"] = f"BLOCKED: {exc}"[:120]
    except OSError:
        # 監査は停止処理の後に取るので、待ち受けは終わっている。フックが通したこと（RuntimeError で
        # はないこと）が確かめたい点なので、OS に断られた場合も「通した」と記録する。
        CONTROL["self"] = "allowed"
    except Exception as exc:  # noqa: BLE001
        CONTROL["self"] = f"other: {type(exc).__name__}"
    finally:
        probe.close()
        STATE["control"] = False  # フラグは必ず戻す（Codex② 4）

    # 検出漏れの各項も対照にかける（どれも実際には何も起こさない）。
    import subprocess

    _control("child_process", lambda: subprocess.Popen([sys.executable, "-c", "pass"]))
    _control("sendmsg", lambda: socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
             .sendmsg([b"x"], [], 0, ("203.0.113.2", 9)))
    _control("ipv6_other_port", lambda: socket.create_connection(("::1", 9), timeout=0.2))
    control_dir = Path(os.environ.get("TMPDIR", "/tmp")) / "mekiki-control"
    control_dir.mkdir(parents=True, exist_ok=True)
    # 元は存在しないファイルにする：フックが止め損ねても、rename は FileNotFoundError で何も作らない（Codex③ 6 の検算）
    src = control_dir / "no-such-src.txt"
    src.unlink(missing_ok=True)
    target = REPO_ROOT / "data" / "control-should-not-exist"
    _control("rename_into_data", lambda: os.rename(src, target))
    CONTROL["rename_target_recorded"] = str(any(
        DATA_DIR in " ".join(str(x) for x in row[1:3]) for row in MUTATED))
    CONTROL["rename_did_nothing"] = str(not target.exists())  # 一歩も進んでいないこと

    # 相対パスの open・記述子を宛先にした操作・解決できない記述子（Codex③ 6）。どれも一歩も進ませない。
    names = ("control-relative-open", "control-fd-rename", "control-dirfd-open", "control-unresolved")
    # 開くほうは作らない指定（r+・O_WRONLY だけ）にする：止め損ねても FileNotFoundError で終わる
    _control("relative_open_into_data", lambda: open(os.path.join("data", names[0]), "r+").close())
    data_fd = _OS_OPEN(DATA_DIR, os.O_RDONLY)
    try:
        _control("fd_rename_into_data", lambda: os.rename(src, names[1], dst_dir_fd=data_fd))
        _control("dirfd_open_into_data", lambda: os.close(os.open(names[2], os.O_WRONLY, dir_fd=data_fd)))
    finally:
        os.close(data_fd)
    stale_fd = _OS_OPEN(str(control_dir), os.O_RDONLY)
    os.close(stale_fd)  # 閉じた記述子：指す先が分からない
    _control("unresolved_dir_fd", lambda: os.rename(src, names[3], dst_dir_fd=stale_fd))
    CONTROL["relative_open_recorded"] = str(any(
        row[0] == os.path.join(DATA_DIR, names[0]) and row[3] == "stopping" for row in OPENED))
    CONTROL["fd_rename_recorded"] = str(any(
        row[0] == "os.rename" and row[2] == os.path.join(os.path.realpath(DATA_DIR), names[1]) for row in MUTATED))
    CONTROL["unresolved_recorded"] = str(any(
        row[0] == "os.rename" and str(row[2]).startswith("unresolved:dir_fd=") for row in MUTATED))
    CONTROL["controls_did_nothing"] = str(not any((REPO_ROOT / "data" / n).exists() for n in names))
    # 停止処理の中の操作も記録に入ること（段階の札が stopping になる）。
    marker = control_dir / "stopping-phase.txt"
    marker.write_text("x", encoding="utf-8")
    CONTROL["stopping_recorded"] = str(any(
        row[0] == os.path.realpath(marker) or row[0] == str(marker) for row in OPENED if row[3] == "stopping"))
    marker.unlink(missing_ok=True)
    src.unlink(missing_ok=True)


def _write_log() -> None:
    AUDIT_LOG.write_text(json.dumps({
        "net": NET, "outbound": OUTBOUND, "opened": OPENED, "open_dropped": OPEN_DROPPED["n"],
        "process": PROCESS, "mutated": MUTATED, "bound": BOUND,
        "control": CONTROL, "control_net": CONTROL_NET,
        "guard": [list(x) for x in app.GUARD_LOG], "guard_counts": app.GUARD_COUNTS,
        "admission": app._ADMISSION, "streams": app._STREAMS, "sweep": {k: v for k, v in app._SWEEP.items() if k != "task"},
        "clients_created": CLIENTS["created"], "ready": app._READY["mcp"], "queue_sizes": QUEUE_SIZES,
        "removed_env": app.REMOVED_GRADIO_ENV,
        "server_name": app.SERVER_NAME,
        "deploy": {k: (list(v) if isinstance(v, tuple) else v) for k, v in app.DEPLOY.items()},
        "pwa": getattr(DEMO, "pwa", "missing"),
        "port": STATE["port"],
        "vibe_mode": getattr(DEMO, "vibe_mode", "missing"),
        "dev_mode": getattr(DEMO, "dev_mode", "missing"),
        "allowed_paths": list(getattr(DEMO, "allowed_paths", []) or []),
        "blocked_paths": list(getattr(DEMO, "blocked_paths", []) or []),
        "analytics_enabled": getattr(DEMO, "analytics_enabled", "missing"),
        "share": getattr(DEMO, "share", "missing"),
        "ssr_mode": getattr(DEMO, "ssr_mode", "missing"),
        "run_history": getattr(DEMO, "run_history", "missing"),
        "enable_monitoring": getattr(DEMO, "enable_monitoring", "missing"),
        "queue_max_size": getattr(getattr(DEMO, "_queue", None), "max_size", "missing"),
        "queue_concurrency": getattr(getattr(DEMO, "_queue", None), "default_concurrency_limit", "missing"),
        "mcp_server": bool(getattr(DEMO, "mcp_server", False)),
        "local_url": getattr(DEMO, "local_url", None),
        "endpoints": list(getattr(DEMO, "_mekiki_endpoints", []) or []),
    }, ensure_ascii=False), encoding="utf-8")


DEMO = None
QUEUE_SIZES: dict[str, int] = {}


def _internal_port(argv: list[str]) -> int:
    """起動器の内部引数 `--port N`（試験用の空きポート）。無ければ止める。"""
    if len(argv) != 2 or argv[0] != "--port" or not argv[1].isascii() or not argv[1].isdigit():
        raise SystemExit("usage: server_launcher.py --port N")
    port = int(argv[1])
    if not 1024 <= port <= 65535:
        raise SystemExit("port out of range")
    return port


def _queue_sizes() -> dict[str, int]:
    """セッションごとに増える表の大きさ（Codex③ 2 の上限の検査）。"""
    queue = getattr(DEMO, "_queue", None)
    holder = getattr(DEMO, "state_holder", None)
    return {
        "pending_messages_per_session": len(getattr(queue, "pending_messages_per_session", {})),
        "pending_event_ids_session": len(getattr(queue, "pending_event_ids_session", {})),
        "event_ids_to_events": len(getattr(queue, "event_ids_to_events", {})),
        "state_session_data": len(getattr(holder, "session_data", {})),
        "state_time_last_used": len(getattr(holder, "time_last_used", {})),
        "born": len(app._BORN), "collecting": len(app._COLLECTING),
        "queued_messages": sum(q.qsize() for q in getattr(queue, "pending_messages_per_session", {}).values()),
    }


def _peer_ports() -> list[int]:
    """サーバ側でまだ開いている接続の相手のポート（切ったはずの接続が残っていないかを見る。Codex③ 1 の検算）。"""
    server = getattr(DEMO, "server", None)
    state = getattr(server, "server_state", None)
    ports = []
    for protocol in list(getattr(state, "connections", ()) or ()):
        transport = getattr(protocol, "transport", None)
        peer = transport.get_extra_info("peername") if transport is not None else None
        if isinstance(peer, tuple) and len(peer) > 1:
            ports.append(int(peer[1]))
    return sorted(ports)


def main() -> int:
    global DEMO
    limit = os.environ.get("MEKIKI_TEST_CONCURRENCY")  # 試験だけが同時実行の上限を下げる（S01）
    if limit:
        app.MAX_CONCURRENCY = int(limit)
        app.BUSY_MESSAGE = f"busy: this reader accepts at most {limit} concurrent calls"
        app._SLOTS = threading.BoundedSemaphore(int(limit))
    waiting = os.environ.get("MEKIKI_TEST_QUEUE_WAITING")  # queue/join の順番待ちの上限（Codex② 1 の試験）
    inflight = os.environ.get("MEKIKI_TEST_QUEUE_INFLIGHT")  # queue/join の受付の数（同上）
    if waiting is not None or inflight is not None:
        active, queued = app.ADMISSION_LIMITS["queue_join"]
        app.ADMISSION_LIMITS["queue_join"] = (int(inflight) if inflight is not None else active,
                                              int(waiting) if waiting is not None else queued)
    admission = os.environ.get("MEKIKI_TEST_ADMISSION")  # 例 "mcp=4:4,other=2:2"（Codex③ 1）
    for part in filter(None, (admission or "").split(",")):
        kind, _, values = part.partition("=")
        active, _, queued = values.partition(":")
        app.ADMISSION_LIMITS[kind] = (int(active), int(queued))
    request_seconds = os.environ.get("MEKIKI_TEST_REQUEST_SECONDS")  # 応答を送り終えるまでの期限
    if request_seconds:
        app.REQUEST_SECONDS = float(request_seconds)
    warm_delay = os.environ.get("MEKIKI_TEST_WARM_DELAY")  # 内部クライアントを作る前に待つ（起動の競合の試験）
    if warm_delay:
        warm = app.warm_internal_client

        def delayed_warm(demo):
            time.sleep(float(warm_delay))
            return warm(demo)

        app.warm_internal_client = delayed_warm
    resource_delay = os.environ.get("MEKIKI_TEST_RESOURCE_DELAY")  # resources・prompts の実行を遅らせる
    if resource_delay:
        in_slot = app._in_slot

        def slow_in_slot(make_value):
            time.sleep(float(resource_delay))
            return in_slot(make_value)

        app._in_slot = slow_in_slot
    streams = os.environ.get("MEKIKI_TEST_STREAMS")  # 長時間接続の同時数の上限（三種とも。S01）
    if streams is not None:
        app.STREAM_LIMITS = dict.fromkeys(app.STREAM_LIMITS, int(streams))
    sweep = os.environ.get("MEKIKI_TEST_SWEEP")  # 掃除の間隔と保持（同上）
    if sweep:
        app.RESULT_SWEEP_SECONDS = float(sweep)
        app.RESULT_TTL_SECONDS = float(sweep)
        app.RESULT_MESSAGES_MAX = 2
    bind = os.environ.get("MEKIKI_TEST_BIND")  # spaces の試験でも待ち受けは loopback にする（手元の網に出さない）
    if bind:
        app.SERVER_NAME = bind
    ttl = os.environ.get("MEKIKI_TEST_RESULT_TTL")  # 期限だけを変える（Codex③ 3 の境界の試験）
    if ttl:
        app.RESULT_TTL_SECONDS = float(ttl)
    port = _internal_port(sys.argv[1:])
    STATE["port"] = port
    app.READER = app.T.Reader(app.C.load_corpus())
    DEMO = app.build_blocks()
    DEMO._mekiki_endpoints = list(DEMO.get_api_info()["named_endpoints"])  # 番兵が最後であることの証跡
    problems = app.verify_blocks(DEMO)
    if problems:
        print("VERIFY-FAILED " + "・".join(problems), flush=True)
        return 4
    app.launch(DEMO, port)
    problems = app.verify_blocks(DEMO, launched=True, port=port)
    if problems:
        print("VERIFY-FAILED " + "・".join(problems), flush=True)
        DEMO.close()
        return 4
    app.mark_ready()
    STATE["phase"] = "serving"
    for line in app.startup_lines(port):
        print(line, flush=True)
    print(f"READY {DEMO.local_url}", flush=True)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    try:
        stop.wait()
    except KeyboardInterrupt:
        pass
    QUEUE_SIZES.update(_queue_sizes())  # 停止の前に測る（停止で表が空になるため）
    QUEUE_SIZES["peer_ports"] = _peer_ports()
    STATE["phase"] = "stopping"
    DEMO.close()          # 停止処理も記録に入れる（Codex② 4）
    _positive_control()
    _write_log()
    return 0


if __name__ == "__main__":
    sys.exit(main())
