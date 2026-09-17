# BUNDLE — 同梱データの一覧と起動時検査

| 項目 | 値 |
|---|---|
| 規則ID・版 | BUNDLE-1.0.0（`bundle_manifest.json` の `format_version` 1 は MAJOR と一致） |
| 状態 | 提案（施工判断。Q03・Q04・Q09〜Q12 の確定内容にもとづく） |
| 実装 | `mekiki_reader/corpus.py`（`load_corpus` ほか）、`scripts/build_bundle.py` |
| 想定 | 事故検出（同期による改行変換・誤コピー・部分更新・データと manifest の同時改変）まで。改竄耐性は主張しない（Q03） |

## 許可一覧（`corpus.ALLOWED_PATHS`、18本）

SPEC §3 の16本（source_manifest.json・papers/T1〜T5.md・THEORY_MAP.md・FOR_AI_READERS.md・SOURCE_INDEX.md・claims/t5.json・T5_CLAIM_STATUS.md・tests/reading_cases.json・AI_READING_TESTS.md・translations/T4.en.md・translations/T4.en.manifest.json・llms.txt）＋ LICENSE・CITATION.md（Q06・Q07）。

## bundle_manifest.json の形

- キーは `format`（"mekiki-reader-bundle-manifest"）・`format_version`（1）・`corpus`・`hash_algorithm`（"sha256"）・`files`・`not_bundled_references` の6つだけ。
- `corpus` は repository・git_ref（refs/tags/v3.5.0）・ref_type（lightweight-tag）・commit・tree・corpus_version（3.5.0）で、`corpus.py` の定数と一致すること。
- `files` は許可一覧と同じ18本を、パスの昇順に並べる。各項目は path・bytes・git_blob_sha1・sha256 だけ。自分自身は含めない（SPEC §4）。
- `not_bundled_references` は、同梱ファイルがパス名で参照する同梱しないファイル（記録のためだけ。存在は確かめない。Q11）。算出規則：固定コミットの tree にある同梱外の各パスを、前後が `[A-Za-z0-9_-]` でない位置で同梱ファイルの本文から探す。
- 直列化：`json.dumps(sort_keys=True, ensure_ascii=False, indent=2)` に LF を1個加えた UTF-8。これと違うバイト列は manifest_invalid。
- bundle_hash は、このファイルの生のバイト列の SHA-256。期待値は `corpus.EXPECTED_BUNDLE_SHA256` と DECISIONS.md に固定する。

## 検査の順序と失敗の種類（`BundleError.kind`）

| 順 | 検査 | kind |
|---|---|---|
| 0 | data/ が実在する通常のディレクトリ（symlink でない） | missing・not_regular（path は "."） |
| ① | bundle_manifest.json が通常ファイルで、バイト列の SHA-256 が期待値と一致 | missing・not_regular・bundle_hash_mismatch |
| ② | JSON・正準直列化・キーと値の型・corpus 参照・パスの安全性（相対・`..` と `.` と空要素なし・`\` なし・重複なし・昇順）・not_bundled_references | manifest_invalid |
| ② | files に許可一覧外のパス | disallowed |
| ② | 許可一覧のパスが files にない | manifest_invalid |
| ③ | files の各パスと親ディレクトリが実在し、通常ファイル／ディレクトリである（symlink は不可） | missing・not_regular |
| ③ | data/ に、bundle_manifest.json と files 以外のファイル・symlink、files の親でないディレクトリがある | extra（辞書順で最初のもの） |
| ④ | 各ファイル（O_NOFOLLOW で開く）のバイト数・SHA-256・git blob SHA-1 | size_mismatch・hash_mismatch |
| ⑤ | コーパス内部の記録（ハッシュ・バイト数・行数）との照合。照合は `verify_internal_hashes` だけが行う | internal_mismatch |
| ⑥ | 索引の構造・位置・一意性（`validate_*`）。JSON・UTF-8 として読めない場合も含む | index_invalid |

⑤で照合する記録：source_manifest の corpus_version・papers[].sha256・bytes・lines（LINES）・frozen_text_sha256 のうち同梱ファイル、claims の source_sha256・quote_sha256（17件）、T4 manifest の source.sha256・translation.sha256・sourceSha256（137件）・translationSegmentSha256（126件。算出規則は T4MAP）。

照合しない記録（同梱しないファイルのもの）：source_manifest の corpus.sha256・corpus.bytes・frozen_text_sha256 の mekiki-framework-t1-t5.md・baseline_t1_t4_sha256・t5_v3_body_sha256・frozen_html_main_sha256・inputs の外部ファイル4件、T4 manifest の translation.html・htmlSha256。

## 取得の手順（`scripts/build_bundle.py`）

1. `fetch`：`git ls-remote` でタグが固定コミットを指す軽量タグであることを確かめる（main は照会しない）→ 空のリポジトリで SHA 指定の浅い fetch → FETCH_HEAD と tree を照合 → `git cat-file blob` で許可ファイルを書き出し、blob id と段階0の SHA-256 を照合。
2. `crosscheck`：raw.githubusercontent.com の固定コミット URL から18本を GET して SHA-256 を照合し、GitHub trees API と `git ls-tree` を照合。
3. `manifest`：bundle_manifest.json を作る。`install`：空の data/ に写す。`check`：`load_corpus` を実行する。
