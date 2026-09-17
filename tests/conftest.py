"""テスト共通の設定。実物の data/ がテストの前後で変わっていないことを確かめる（Q12・SPEC §2.9）。"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = REPO_ROOT / "data"
_SNAPSHOT: dict[str, str] = {}


def _snapshot(root: Path) -> dict[str, str]:
    """data/ 配下の全エントリ（ファイルは SHA-256、それ以外は種別）を記録する。"""
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(dirnames + filenames):
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            if full.is_symlink():
                out[rel] = "symlink"
            elif full.is_dir():
                out[rel] = "dir"
            else:
                out[rel] = hashlib.sha256(full.read_bytes()).hexdigest()
    return out


def pytest_sessionstart(session):
    _SNAPSHOT.clear()
    _SNAPSHOT.update(_snapshot(DATA_DIR))


def pytest_sessionfinish(session, exitstatus):
    after = _snapshot(DATA_DIR)
    if after != _SNAPSHOT:
        changed = sorted(set(after) ^ set(_SNAPSHOT) | {k for k in after if _SNAPSHOT.get(k) != after[k]})
        print(f"\nERROR: data/ changed during the test session: {changed[:10]}", file=sys.stderr)
        session.exitstatus = 1
