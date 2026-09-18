"""試験用の起動器（S01〜S03）。監査フックを入れてから app を起動し、記録をファイルに書く。

`sys.addaudithook` は import gradio より前に入れる（Codex① P2-6 の差分案）。
- 宛先は host:port で記録する（ポートまで見る）。
- 免除するのは**実際の自己接続だけ**（loopback かつ自分の待ち受けポート）。
- Unix ソケットは免除しない。
- `open` は flags・mode まで、**起動前から停止まで**記録する（段階の札を付ける）。
- 最後に陽性対照を行い、フック自体が効いていることを確かめる。

環境変数：MEKIKI_AUDIT_LOG（記録の書き出し先）・MEKIKI_READER_PORT（app.py が読む）・
MEKIKI_TEST_CONCURRENCY（試験だけが同時実行の上限を下げる）。
"""

import json
import os
import signal
import socket
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = str(REPO_ROOT / "data")
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


def _abspath(value) -> str:
    """相対パスを絶対パスに直す（cwd 基準）。パスでないものはそのまま短く返す。"""
    if isinstance(value, (str, bytes, os.PathLike)):
        try:
            name = value.decode("utf-8", "replace") if isinstance(value, bytes) else os.fspath(value)
        except TypeError:
            return str(value)[:120]
        return os.path.abspath(name) if name else name
    return "" if value is None else str(value)[:120]


def _paths_of(args) -> list[str]:
    """書き換えの元・先と dir_fd を記録する（Codex② 4）。dir_fd つきは解決先を添える。"""
    paths = [_abspath(a) for a in args[:2]]
    fds = [a for a in args[2:] if isinstance(a, int)]
    for fd in fds:
        try:
            base = os.readlink(f"/dev/fd/{fd}")
        except OSError:
            base = f"dir_fd={fd}"
        paths.append(base)
    while len(paths) < 2:
        paths.append("")
    return paths


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
        if len(OPENED) >= OPEN_MAX:
            OPEN_DROPPED["n"] += 1
            return
        path = args[0] if args else ""
        if isinstance(path, (str, bytes, os.PathLike)):
            name = path.decode("utf-8", "replace") if isinstance(path, bytes) else os.fspath(path)
            mode = args[1] if len(args) > 1 else ""
            flags = args[2] if len(args) > 2 else ""
            OPENED.append([str(name), str(mode), str(flags), STATE["phase"]])
    elif event.startswith(PROCESS_EVENTS):
        PROCESS.append([event, str(args[0])[:120] if args else "", STATE["phase"]])
        raise RuntimeError(f"child process blocked in the test launcher: {event}")
    elif event in MUTATE_EVENTS:
        paths = _paths_of(args)
        MUTATED.append([event, *paths, STATE["phase"]])
        if any(p.startswith(DATA_DIR) for p in paths if p):  # 原文は書き換えさせない（記録だけにしない）
            raise RuntimeError(f"data/ write blocked in the test launcher: {event} {paths[:2]}")
    elif event in BIND_EVENTS:
        address = args[1] if len(args) > 1 else None
        if isinstance(address, tuple) and address:
            STATE["bound"].append((str(address[0]), address[1] if len(address) > 1 else ""))
        BOUND.append([event, str(address)[:80], STATE["phase"]])


sys.addaudithook(_audit)

import app  # noqa: E402  （監査フックの後に読み込む）


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
    src = control_dir / "src.txt"
    src.write_text("x", encoding="utf-8")
    target = REPO_ROOT / "data" / "control-should-not-exist"
    _control("rename_into_data", lambda: os.rename(src, target))
    CONTROL["rename_target_recorded"] = str(any(
        DATA_DIR in " ".join(str(x) for x in row[1:3]) for row in MUTATED))
    CONTROL["rename_did_nothing"] = str(not target.exists())  # 一歩も進んでいないこと
    src.unlink(missing_ok=True)


def _write_log() -> None:
    AUDIT_LOG.write_text(json.dumps({
        "net": NET, "outbound": OUTBOUND, "opened": OPENED, "open_dropped": OPEN_DROPPED["n"],
        "process": PROCESS, "mutated": MUTATED, "bound": BOUND,
        "control": CONTROL, "control_net": CONTROL_NET,
        "guard": [list(x) for x in app.GUARD_LOG], "guard_counts": app.GUARD_COUNTS,
        "queue_state": dict(app._QUEUE_STATE), "sweep": {k: v for k, v in app._SWEEP.items() if k != "task"},
        "removed_env": app.REMOVED_GRADIO_ENV,
        "server_name": app.SERVER_NAME,
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


def main() -> int:
    global DEMO
    limit = os.environ.get("MEKIKI_TEST_CONCURRENCY")  # 試験だけが同時実行の上限を下げる（S01）
    if limit:
        app.MAX_CONCURRENCY = int(limit)
        app.BUSY_MESSAGE = f"busy: this reader accepts at most {limit} concurrent calls"
        app._SLOTS = threading.BoundedSemaphore(int(limit))
    waiting = os.environ.get("MEKIKI_TEST_QUEUE_WAITING")  # 待機の上限（Codex② 1 の試験）
    if waiting is not None:
        app.QUEUE_WAITING_MAX = int(waiting)
    inflight = os.environ.get("MEKIKI_TEST_QUEUE_INFLIGHT")  # 受付の数（同上）
    if inflight is not None:
        app.QUEUE_INFLIGHT_MAX = int(inflight)
    sweep = os.environ.get("MEKIKI_TEST_SWEEP")  # 掃除の間隔と保持（同上）
    if sweep:
        app.RESULT_SWEEP_SECONDS = float(sweep)
        app.RESULT_TTL_SECONDS = float(sweep)
        app.RESULT_MESSAGES_MAX = 2
    port = app.read_port(os.environ.get(app.PORT_ENV))
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
    STATE["phase"] = "serving"
    print(f"READY {DEMO.local_url}", flush=True)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    try:
        stop.wait()
    except KeyboardInterrupt:
        pass
    STATE["phase"] = "stopping"
    DEMO.close()          # 停止処理も記録に入れる（Codex② 4）
    _positive_control()
    _write_log()
    return 0


if __name__ == "__main__":
    sys.exit(main())
