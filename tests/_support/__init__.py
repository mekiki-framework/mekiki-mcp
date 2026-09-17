"""テスト用の補助（一時コピーの作成と bundle_manifest.json の書き換え）。実物の data/ は変えない。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

from mekiki_reader import corpus as C


def copy_bundle(tmp_path: Path) -> Path:
    dest = tmp_path / "data"
    shutil.copytree(C.DATA_DIR, dest, symlinks=False)
    return dest


def rewrite_manifest(data_dir: Path, mutate: Callable[[dict[str, Any]], None]) -> str:
    """一時コピーの bundle_manifest.json を正準形で書き換え、新しい期待ハッシュを返す。"""
    path = data_dir / C.BUNDLE_MANIFEST
    obj = json.loads(path.read_bytes())
    mutate(obj)
    raw = C.canonical_manifest_bytes(obj)
    path.write_bytes(raw)
    return C.sha256_hex(raw)


def resync_entry(data_dir: Path, rel: str) -> str:
    """一時コピーのファイルの現在の値で manifest の該当項目を更新し、新しい期待ハッシュを返す。"""
    content = (data_dir / rel).read_bytes()

    def mutate(obj: dict[str, Any]) -> None:
        for f in obj["files"]:
            if f["path"] == rel:
                f.update(bytes=len(content), git_blob_sha1=C.git_blob_sha1(content), sha256=C.sha256_hex(content))
                return
        raise KeyError(rel)

    return rewrite_manifest(data_dir, mutate)


def same_length_change(data: bytes) -> bytes:
    """最初の ASCII 母音を別の母音に替える（バイト数と UTF-8 の妥当性を保つ）。"""
    swap = {ord("a"): ord("e"), ord("e"): ord("a"), ord("i"): ord("o"), ord("o"): ord("i"), ord("u"): ord("a")}
    buf = bytearray(data)
    for i, b in enumerate(buf):
        if b in swap:
            buf[i] = swap[b]
            return bytes(buf)
    raise ValueError("no ASCII vowel to change")
