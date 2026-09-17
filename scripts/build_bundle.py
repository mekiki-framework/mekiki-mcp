#!/usr/bin/env python3
"""data/ の取得と bundle_manifest.json の生成（Q03・Q04。再現のために保存する）。

サーバからは使わない施工用の道具。取得先はタグ v3.5.0 を解決したコミットだけで、main は読まない。
コーパスの tools/*.py は実行しない。

  python scripts/build_bundle.py fetch      --stage DIR   # 案A：SHA 指定の浅い fetch → tree 照合 → blob 書き出し
  python scripts/build_bundle.py crosscheck --stage DIR   # 案D：raw の GET と GitHub trees API で独立に照合
  python scripts/build_bundle.py manifest   --stage DIR   # DIR/data/bundle_manifest.json を作る（BUNDLE-1.0.0）
  python scripts/build_bundle.py install    --stage DIR   # DIR/data を data/ に写す（data/ が空のときだけ）
  python scripts/build_bundle.py check      [--data DIR] [--expected SHA256]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from mekiki_reader import corpus as C  # noqa: E402

CLONE_URL = C.CORPUS_REPOSITORY + ".git"
API_TREE_URL = "https://api.github.com/repos/mekiki-framework/mekiki-framework.github.io/git/trees/{tree}?recursive=1"
TIMEOUT = 30

# 段階0に記録した値（docs/stage0_facts.md C-1）。CITATION.md は段階0では記録していない。
STAGE0_SHA256 = {
    "source_manifest.json": "ec8d9f55cd032534225dd25c7b70dc7371212c27266e60caf80a88ea53b70829",
    "papers/T1.md": "2b027f11fd7a0f9241c02e97e20ebd08588b6d2bcfc6a0aa8bc211b837b52893",
    "papers/T2.md": "ec2437e5418b34de1ad488e5628edb68d0ba98718529b97919319a123ea805fc",
    "papers/T3.md": "0d4a367b297db2b8481d71b71aabf7377abee23715a7c4452ed3a647a659dc5b",
    "papers/T4.md": "9d2e09840323244b58c1fb02586bca79ea78dbe6f8b3deb8f30bc996d17832d5",
    "papers/T5.md": "57d600b36fa60389c2ae66a33c8feca118e516934cf5c6127407f40f48c93937",
    "THEORY_MAP.md": "2225e5a69e3f2968af233af8aee2133b217355085f434e164e611139304d213a",
    "FOR_AI_READERS.md": "ddee2e7370ed9423be4a12f475a68c2acf9e8502b90a478f02c4ef2a5d8c01d7",
    "SOURCE_INDEX.md": "0f9aff163414e48afefdb4d43c24a1c45ce8d61a3579cfdfcc9fa4b299cfc408",
    "claims/t5.json": "26babf80b6779667b452455772350ba2cdbab3f9154ec924b0d608713bc9e003",
    "T5_CLAIM_STATUS.md": "16a6b5ac14fc679fc8643b9fdc157886c6931a2843a0d86ff51c973bbab1c9d9",
    "tests/reading_cases.json": "d76740461ec37bec7a0fbbf7ac55ccb0e37f862fc21f261cc8ad222400d118ec",
    "AI_READING_TESTS.md": "c710fade5cf37fe8ca6adf3abdbdfdcc4f2a55271b21ff0c16171e4630abe57a",
    "translations/T4.en.md": "bdf8690f23f1a79b1b7307fe99629540d07f9a5a97ba210b2c637cb9511ae5d9",
    "translations/T4.en.manifest.json": "d6768d66ce13716caaf64544c8b93454e6659a90cfb6ed03914d7d471e050fc1",
    "llms.txt": "df33559d07e6233c95fc77cd536422dcaabf64d0500b1b4dfef3bb7793290ef9",
    "LICENSE": "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args: str, cwd: Path | None = None) -> bytes:
    cmd = ["git", *args]
    print("$ " + " ".join(cmd), file=sys.stderr)
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True).stdout


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "mekiki-mcp-build-bundle"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310 (固定のURLだけ)
        if r.status != 200:
            fail(f"GET {url} -> {r.status}")
        return r.read()


def read_tree(stage: Path) -> dict[str, tuple[str, str]]:
    tree = {}
    for line in (stage / "tree.tsv").read_text(encoding="utf-8").splitlines():
        mode, typ, sha, path = line.split("\t")
        tree[path] = (typ, sha)
    return tree


def cmd_fetch(stage: Path) -> None:
    repo = stage / "repo"
    data = stage / "data"
    if repo.exists() or data.exists():
        fail(f"{stage} already has repo/ or data/")
    out = git("ls-remote", CLONE_URL, C.CORPUS_GIT_REF, C.CORPUS_GIT_REF + "^{}").decode()
    print(out.strip())
    refs = [line.split("\t") for line in out.strip().splitlines()]
    if refs != [[C.CORPUS_COMMIT, C.CORPUS_GIT_REF]]:
        fail("tag does not resolve to the pinned commit as a lightweight tag")
    repo.mkdir(parents=True)
    git("init", "-q", cwd=repo)
    git("-c", "protocol.version=2", "fetch", "--depth", "1", "--no-tags", "-q", CLONE_URL, C.CORPUS_COMMIT, cwd=repo)
    commit = git("rev-parse", "FETCH_HEAD", cwd=repo).decode().strip()
    tree = git("rev-parse", "FETCH_HEAD^{tree}", cwd=repo).decode().strip()
    print(f"commit {commit}\ntree   {tree}")
    if (commit, tree) != (C.CORPUS_COMMIT, C.CORPUS_TREE):
        fail("fetched commit/tree differ from the pinned values")
    listing = git("ls-tree", "-r", "--full-tree", C.CORPUS_COMMIT, cwd=repo).decode()
    rows = []
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        mode, typ, sha = meta.split()
        rows.append(f"{mode}\t{typ}\t{sha}\t{path}")
    (stage / "tree.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    blobs = {r.split("\t")[3]: r.split("\t")[2] for r in rows if r.split("\t")[1] == "blob"}
    print("path\tbytes\tgit_blob\tsha256\tCR\tstage0")
    for rel in C.ALLOWED_PATHS:
        if rel not in blobs:
            fail(f"{rel} is not in the pinned tree")
        content = git("cat-file", "blob", f"{C.CORPUS_COMMIT}:{rel}", cwd=repo)
        if C.git_blob_sha1(content) != blobs[rel]:
            fail(f"{rel}: blob id mismatch")
        digest = C.sha256_hex(content)
        known = STAGE0_SHA256.get(rel)
        if known is not None and known != digest:
            fail(f"{rel}: sha256 differs from the stage-0 record")
        dest = data / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        print(f"{rel}\t{len(content)}\t{blobs[rel]}\t{digest}\t{content.count(b'\r')}\t{'match' if known else 'new'}")


def cmd_crosscheck(stage: Path) -> None:
    data = stage / "data"
    for rel in C.ALLOWED_PATHS:
        got = C.sha256_hex(http_get(C.RAW_BASE + rel))
        local = C.sha256_hex((data / rel).read_bytes())
        print(f"raw {rel}\t{'ok' if got == local else 'MISMATCH'}")
        if got != local:
            fail(f"raw sha256 mismatch for {rel}")
    api = json.loads(http_get(API_TREE_URL.format(tree=C.CORPUS_TREE)))
    if api.get("truncated"):
        fail("trees API response truncated")
    api_blobs = {e["path"]: e["sha"] for e in api["tree"] if e["type"] == "blob"}
    local_blobs = {p: sha for p, (typ, sha) in read_tree(stage).items() if typ == "blob"}
    print(f"trees API blobs {len(api_blobs)}, local ls-tree blobs {len(local_blobs)}")
    if api_blobs != local_blobs:
        fail("trees API differs from local ls-tree")
    print("crosscheck ok")


def not_bundled_references(stage: Path, texts: dict[str, str]) -> list[str]:
    """同梱ファイルがパス名で参照する、同梱しないファイル（記録のためだけの一覧）。"""
    refs = set()
    candidates = [p for p, (typ, _) in read_tree(stage).items() if typ == "blob" and p not in C.ALLOWED_PATHS]
    for path in candidates:
        pat = re.compile(r"(?<![A-Za-z0-9_\-])" + re.escape(path) + r"(?![A-Za-z0-9_\-])")
        if any(pat.search(t) for t in texts.values()):
            refs.add(path)
    return sorted(refs)


def cmd_manifest(stage: Path) -> None:
    data = stage / "data"
    files = []
    texts = {}
    for rel in C.ALLOWED_PATHS:
        content = (data / rel).read_bytes()
        texts[rel] = content.decode("utf-8")
        files.append({
            "path": rel,
            "bytes": len(content),
            "git_blob_sha1": C.git_blob_sha1(content),
            "sha256": C.sha256_hex(content),
        })
    manifest = {
        "format": C.BUNDLE_FORMAT,
        "format_version": C.BUNDLE_FORMAT_VERSION,
        "corpus": {
            "repository": C.CORPUS_REPOSITORY,
            "git_ref": C.CORPUS_GIT_REF,
            "ref_type": C.CORPUS_REF_TYPE,
            "commit": C.CORPUS_COMMIT,
            "tree": C.CORPUS_TREE,
            "corpus_version": C.CORPUS_VERSION,
        },
        "hash_algorithm": "sha256",
        "files": files,
        "not_bundled_references": not_bundled_references(stage, texts),
    }
    raw = C.canonical_manifest_bytes(manifest)
    (data / C.BUNDLE_MANIFEST).write_bytes(raw)
    print(f"not_bundled_references: {manifest['not_bundled_references']}")
    print(f"bundle_manifest.json sha256 {C.sha256_hex(raw)}")


def cmd_install(stage: Path, dest: Path) -> None:
    src = stage / "data"
    if dest.exists() and any(dest.iterdir()):
        fail(f"{dest} is not empty")
    for rel in (*C.ALLOWED_PATHS, C.BUNDLE_MANIFEST):
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / rel, target)
    print(f"copied {len(C.ALLOWED_PATHS) + 1} files to {dest}")


def cmd_check(data: Path, expected: str) -> None:
    corpus = C.load_corpus(data, expected)
    print(f"ok: bundle {corpus.bundle.bundle_hash}, files {len(corpus.bundle.files)}, "
          f"sections {sum(len(p.sections) for p in corpus.papers.values())}, "
          f"T4 units {len(corpus.t4en.units)}, translator notes {len(corpus.t4en.notes)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("fetch", "crosscheck", "manifest", "install"):
        sp = sub.add_parser(name)
        sp.add_argument("--stage", type=Path, required=True)
        if name == "install":
            sp.add_argument("--dest", type=Path, default=C.DATA_DIR)
    sp = sub.add_parser("check")
    sp.add_argument("--data", type=Path, default=C.DATA_DIR)
    sp.add_argument("--expected", default=C.EXPECTED_BUNDLE_SHA256)
    a = ap.parse_args()
    if a.cmd == "fetch":
        cmd_fetch(a.stage)
    elif a.cmd == "crosscheck":
        cmd_crosscheck(a.stage)
    elif a.cmd == "manifest":
        cmd_manifest(a.stage)
    elif a.cmd == "install":
        cmd_install(a.stage, a.dest)
    else:
        try:
            cmd_check(a.data, a.expected)
        except C.BundleError as e:
            fail(str(e))


if __name__ == "__main__":
    main()
