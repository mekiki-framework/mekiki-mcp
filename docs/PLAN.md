# PLAN.md — 施工計画

版：段階0起草（2026-09-18、DECISIONS.md 付録Aから分離）＋同日の回答票（`docs/stage0_answers.md`）を反映。

正本は `SPEC.md` v2。本書と SPEC が食い違う場合は SPEC に従う。Qnn は `DECISIONS.md` の段階0の要確認事項で、すべて回答票で確定した。SPEC v2.1 の改版項目（回答票 §11）は検査室が起草中で、施工はそれまで回答票を仮確定として進める（Q05）。規則の版は Q49（意味つき版＋表の SHA-256）に従い、規則の本文は `docs/rules/` に置く。確認した現物は `docs/stage0_facts.md`。

## A-0 共通方針

- `mekiki_reader/` は標準ライブラリだけで書き、gradio を import しない（施工段階1・2のテストを Gradio なしで回すため）。
- 同梱データは起動時に一度だけメモリへ読み込み、以後はファイルを開かない。
- 決定性（SPEC §2.3）
  - 出力の配列（results・candidates・limitations・normalization_applied）は、出力前に必ず全順序で並べる。set や dict の反復順に依存しない。
  - 文字種（CJK・数字・ひらがな）の判定は、明示したコードポイント範囲で行い、`unicodedata.category` や `re` の `\d`・`\w` には頼らない。
  - JSON の直列化は規則 JSON-1.0.0（`sort_keys=True`、`ensure_ascii=False`、`separators=(",", ":")`、`allow_nan=False`）。
  - 所要時間や通信IDは結果データに入れない。
- 規則にはすべて版を付け、`docs/rules/` と `DECISIONS.md` に記録し、応答の limitations に載せる（Q49）。

## A-1 守則 §2 の担保

| 守則 | 担保する場所 | テスト |
|---|---|---|
| 2.1 公開・承認済みのみ、資料種別と従属 | `corpus.ALLOWED_PATHS`（SPEC §3 の16本＋LICENSE・CITATION.md＝18本。Q06・Q07）、`data/bundle_manifest.json`、`corpus.verify_bundle()`、`schema.SourceKind`、パスと種別の固定表・派生物の表示（Q38⑦） | D02・D03・T12 |
| 2.2 読み取り専用・許可済みIDのみ | `corpus.load_corpus()`（書き込みAPIなし）、`tools.py`（引数はIDと語句だけ。IDは形式を検査してから索引で照合）、`app.py`（GRADIO_* の無効化と allowed_paths が空であることの確認 Q93、標準経路の遮断 Q66、データ根は固定 Q12）、resources は静的URI（Q70） | S01・S02 |
| 2.3 LLMなし・決定的 | A-0 の決定性の規則、`schema.to_json()`、vibe_mode が False であることの起動時確認（Q93）、`mekiki_reader` の禁止 import（openai・anthropic・transformers・huggingface_hub・socket・urllib.request・httpx・requests・subprocess・random）の静的検査 | R01・S03 |
| 2.4 出典 | `schema.make_envelope()`：status が ok でなければ results は空。論文に属する結果では paper_id・paper_version・section_anchor・canonical_doi を必須にし（Q88）、source_hash が bundle 上の値と一致し、section_anchor が索引に実在することを検査する。candidates にも同じ検査をかける。コーパス由来の文は出典付きで返す（Q38⑨） | T03・T05・T06・T12・M01・D04 |
| 2.5 版固定 | `bundle_manifest.json`、`corpus.verify_bundle()`、`corpus.EXPECTED_BUNDLE_SHA256`（Q03）、`corpus.verify_internal_hashes()`。Pages や raw の URL は文字列として返すだけで、取得しない | D01〜D03 |
| 2.6 資料は資料 | `tools.py` は本文を文字列として扱うだけ。`prompts.py` に上書きしない旨の定型文（Q39）。命令風テキストは tests/fixtures/ にだけ置く | S02・E02 |
| 2.7 状態を分ける | `schema.Status`（6値）と各ツールの状態遷移（A-3）。同時実行と処理時間の上限超過は status に混ぜない（Q65・Q85）。結果数の上限を超えたときの返し方は Q84 | T03・T04・T06・T10・M03 |
| 2.8 記録はラベル | get_claim_record は status を逐語で返し、区分欄を作らない（Q31）。author_answerable は null。check_compressions は判定の欄を持たない | T05・T06・T11 |
| 2.9 保守規律 | D テストは一時コピーだけを改変する。`tests/conftest.py` で実物の data/ の前後ハッシュを比べる（Q12）。各段階の終わりに `git status --porcelain -- data/` が期待どおりであること（未追跡ファイルも検出する）と bundle のハッシュ照合 | D01〜D03・全テスト |
| 2.10 通信と設定 | `app.py`：import 前に GRADIO_* を整理し（Q93）`HF_HUB_DISABLE_TELEMETRY=1` を設定、`gr.Blocks(analytics_enabled=False)`、`launch(share=False, server_name="127.0.0.1", ssr_mode=False, enable_monitoring=False, run_history=False, max_file_size=<小>, max_threads=<Q65>)`、入力・結果数・処理時間・同時数の上限（Q56・Q65・Q84・Q85）、標準経路の遮断（Q66）。宣言範囲は SPEC §2.10 の文言どおり（Q86） | S01・S03・M03 |
| 2.11 開示 | README 末尾の開示の章（A-5。文面と配置は著者の承認・署名 Q89） | 施工段階4の検収 |
| CLAUDE.md 規則9 | `patterns.py` は `PATTERNS = ()` で起動できる | T11 の前提 |

## A-2 施工段階1：data/ の取得・bundle_manifest.json・corpus.py（完了条件 D01〜D04）

着手の条件：Q01・Q03〜Q12・Q22・Q26・Q27・Q34・Q49・Q83（Q06 の前提として）・Q94（段階0の作業の追認）の回答と、実行環境（Q74〜Q76）。Q02 は記録だけ。

**取得の手順**（Q04 の案A＋案D。作業は一時領域で行い、最後にだけリポジトリへ写す）
1. `git ls-remote <url> refs/tags/v3.5.0 'refs/tags/v3.5.0^{}'` で、タグが 6748061 を指し `^{}` 行がないことを確かめる（main は照会しない）。`gh api …/git/refs/tags/v3.5.0` の object.type が commit であることも確かめる。一致しなければ止めて報告する。
2. 空のリポジトリで `git -c protocol.version=2 fetch --depth 1 --no-tags <url> 67480613108cf72c29d5691e3d7a6c7e6553eb9b` を実行し、`FETCH_HEAD` と `FETCH_HEAD^{tree}` を照合する。
3. 許可ファイルごとに `git cat-file blob <SHA>:<path>` で書き出す（checkout を経ないので改行変換を受けない）。コーパスの tools/*.py は実行しない。
4. ファイルごとに、`git hash-object`・SHA-256・bytes・CR 0件を`docs/stage0_facts.md` の C-1 と照合する（CITATION.md は取得時に記録する）。
5. 独立の照合として、`raw.githubusercontent.com/<SHA>/<path>` を GET して SHA-256 を比べる。GitHub trees API と `git ls-tree -r --long` も比べる。
6. コーパス内部の記録のうち同梱ファイルにかかるものを照合する（ログ表「同梱許可ファイルの現物」の内訳。規則は `corpus.verify_internal_hashes` と D04④ と同じ）。
7. bundle_manifest.json を生成する（生成スクリプトの置き場は Q04）。
8. 著者の確認を得てから data/ へ写す。Q09 が承認されていれば `.gitattributes` を置く。`pytest tests/test_data.py` を実行する。
9. `git status --short` に出るのが、次だけであることを確かめる：data/・`mekiki_reader/{__init__,corpus}.py`・tests/test_data.py・tests/conftest.py と tests/_support/（Q12）・DECISIONS.md。条件付きで .gitattributes（Q09）・scripts/（Q04）・requirements-dev.txt（Q76）・.gitignore（Q10）・SPEC.md（Q05）。

**data/ の配置**（SPEC §3 どおり）：`source_manifest.json`・`bundle_manifest.json`・`papers/T1〜T5.md`・`claims/t5.json`・`tests/reading_cases.json`・`translations/T4.en.md`・`translations/T4.en.manifest.json`・`THEORY_MAP.md`・`FOR_AI_READERS.md`・`SOURCE_INDEX.md`・`T5_CLAIM_STATUS.md`・`AI_READING_TESTS.md`・`llms.txt`・`LICENSE`・`CITATION.md`（Q06・Q07）。`data/tests/` とリポジトリの `tests/` を混同しないよう、テストは常に `pytest tests/` で起動する。

**bundle_manifest.json の形式案（BUNDLE-1.0.0）**
```json
{
  "format": "mekiki-reader-bundle-manifest",
  "format_version": 1,
  "corpus": {
    "repository": "https://github.com/mekiki-framework/mekiki-framework.github.io",
    "git_ref": "refs/tags/v3.5.0", "ref_type": "lightweight-tag",
    "commit": "67480613108cf72c29d5691e3d7a6c7e6553eb9b",
    "tree": "7c50a4fc2bf20f1529aebe8a8b7898e26332f1a1",
    "corpus_version": "3.5.0"
  },
  "hash_algorithm": "sha256",
  "files": [{"path": "…", "bytes": 0, "git_blob_sha1": "…", "sha256": "…"}],
  "not_bundled_references": ["…"]
}
```
- `format_version` は BUNDLE 規則の MAJOR と一致させる。files はパスの昇順。files は `corpus.ALLOWED_PATHS` と一致しなければならない（多すぎれば disallowed、少なければ manifest_invalid）。自分自身は含めない（SPEC §4）。直列化は JSON-1.0.0 に `indent=2` と末尾の LF 1個を加えたもの（BUNDLE の規則に含める）。
- bundle_hash は、このファイルの生のバイト列の SHA-256。期待値は `corpus.EXPECTED_BUNDLE_SHA256` と `DECISIONS.md` に固定する（Q03。想定は事故検出までで、改竄耐性は主張しない）。
- not_bundled_references は検査対象外であることを示すためだけの一覧で、存在は確かめない（Q11）。

**corpus.py（標準ライブラリのみ）**
- 定数：`DATA_DIR`、`ALLOWED_PATHS`、`EXPECTED_BUNDLE_SHA256`、`LINES_RULE="LINES-1.0.0"`（`text.split("\n")` で末尾の空要素を1個除く。splitlines() と件数が一致することを起動時に確かめる）、`LANG_RULE` と `PAPER_LANGUAGE`（Q22）、`SECTION_RULE`（親＝直前にある、自分より水準の小さい節。heading_only の定義は Q34）、`T4MAP_RULE`（sourceLine を節範囲に当てる規則と、D04④ の sourceSha256・translationSegmentSha256 の算出規則を含む。Q27）、`PAGES_BASE`、`RAW_BASE`（文字列として返すだけ）。
- 例外：`BundleError(kind, path)`。kind の意味：manifest_invalid（bundle_manifest.json の形式違反・パスの不正〔`..`・絶対パス・`\`・重複〕・許可一覧の不足）／bundle_hash_mismatch（bundle_manifest.json のバイト列が期待値と違う）／disallowed（ALLOWED_PATHS にないパスが files にある）／extra（data/ に、bundle_manifest.json と files 以外のファイル・symlink などのエントリがある。ディレクトリは files の親に当たるもの以外。.DS_Store を含む。Q10）／missing（files にあるのに存在しない）／not_regular（symlink・ディレクトリなど通常ファイルでない）／size_mismatch・hash_mismatch（ファイルのバイト数・SHA-256 の不一致）／internal_mismatch（コーパス内部に記録されたハッシュ・バイト数・行数との不一致。ハッシュの照合は `verify_internal_hashes` だけが行う）／index_invalid（索引の構造・位置・一意性の検査の失敗。`validate_*` が担う）。
- データ型（frozen dataclass）：`FileEntry`、`CorpusRef`、`BundleManifest`、`Section`（paper_id・id・title・level・line_start・line_end・parent_id・child_ids・heading_only）、`Paper`（paper_id・title・alternate_title・preprint_version・canonical_doi・language・path・sha256・lines・sections）、`TranslationUnit`、`TranslatorNote`、`Corpus`。
- `load_corpus(data_dir=DATA_DIR, expected_bundle_sha256=EXPECTED_BUNDLE_SHA256)` の検査順：①bundle_manifest.json のバイト列の SHA-256 を期待値と照合 → ②形式と ALLOWED_PATHS との一致 → ③`os.walk(followlinks=False)` で data/ の全エントリを列挙し、extra・missing・not_regular を検出 → ④各ファイルの bytes と SHA-256 → ⑤コーパス内部の記録（`verify_internal_hashes`）→ ⑥索引の構築と検査（`validate_section_index`・`validate_translation_index`・`validate_ledger`・`validate_reading_cases`）。どこかで失敗すれば BundleError を出し、app.py は非ゼロで終了する。data_dir はテストだけが使う内部引数（Q12）。④で読み込んだバイト列だけを以後使う。
- ほかの関数：`split_lines(text)`、`build_section_index(source_manifest, texts)`（題名は `inputs.release_3_5_0_inputs.canonical_identity[Tn].name`、T4 は alternateName も。版は `preprint_version`。節は `sections[]` の id・title・line_start・line_end・level をそのまま使う。キー名は anchor ではなく id）、`build_translation_index(manifest, t4, t4en_lines)`、`get_lines(corpus, path, line_start, line_end)`（1始まり・終端を含む。範囲外は例外）。

**D01〜D04（tests/test_data.py）**
- 共通：`bundle_copy(tmp_path)` で data/ を一時ディレクトリにコピーし、改変はすべてそのコピーに対して行う。陽性対照として、無改変のコピーが読み込めることを確かめる。

| ID | 操作 | 期待する kind |
|---|---|---|
| D01 | コピー上の papers/T1〜T5.md を1本ずつ、①1字の置換（バイト数は変えない）②末尾に空白を追加 ③LF→CRLF ④空ファイル化 | ①hash_mismatch ②〜④size_mismatch |
| D02-a | claims/t5.json（status を1字変える）・ガイド類・reading_cases.json・T4.en.md・T4.en.manifest.json・llms.txt・source_manifest.json をそれぞれ同じ長さで改変 | hash_mismatch |
| D02-b | bundle_manifest.json 内の files[].sha256 だけを書き換える | bundle_hash_mismatch |
| D02-c | ファイルと bundle_manifest.json を揃えて書き換える | bundle_hash_mismatch |
| D03-a | 許可ファイルを1本削除 | missing |
| D03-b | data/extra.md・data/.DS_Store・data/papers/T1.html を置く | extra |
| D03-c | files に許可一覧外のパス（例 metadata.json）を足し、ファイルも置く（期待ハッシュは試験用に差し替える） | disallowed |
| D03-d | 許可ファイルを symlink に置き換える／許可ファイルの名前でディレクトリを作る | not_regular |
| D03-e | files に `../x`・`/etc/hosts`・重複パスを入れる／許可ファイルを files から外す（期待ハッシュは試験用に差し替える） | manifest_invalid |

- D04：実データを読むだけで検査する。
  - ①節158件（40・39・25・25・29）：id が論文内で一意、line_start の行が見出しで `#` の数と見出し文字列が level と title に一致、範囲が隙間も重なりもなく連続、最後の line_end が lines（442・376・251・261・325）に一致、T4 の水準の飛び6か所でも親が導ける、heading_only の値（本文を含む親節13件を含む）。
  - ②主張の17引用（主11＋追加6）：T5.md に逐語で1回だけ現れ、一致行が source_locator の範囲に入り、quote_sha256 が一致し、`'t5-'+section.replace('.','-')` が manifest にあってその節範囲に入り、section_url がそのアンカーと一致する。footnote_url は T5-N3 の source_locator だけにある。source_sha256 が T5.md と一致する。
  - ③reading_cases の additional_sources 15件が一意に一致し、節に入る（R12 は t5-references）。
  - ④T4 英訳：sourceUnits 137件（位置あり126・wrapper 6・separator 5）。sourceSha256＝`sha256("\n".join(T4.md の行[s-1:e]))`（strip の有無で結果は変わらない。137件一致）。translationSegmentSha256＝`sha256("\n".join(T4.en.md の行[s-1:e]) + "\n")`（126件一致）。translationLineStart/End がマーカー行 `<!-- t4-source-unit:N -->` の位置と一致して隙間がない。targetId が T4.en.md に実在する。訳注16件がそれぞれ1つの translated unit の内側にある。author-note-1..5 と ref-1..28 がある。英訳の未被覆が1〜22行と1098〜1105行だけ。manifest の source.sha256・translation.sha256 が同梱ファイルと一致する（htmlSha256 は照合しない。Q11）。
  - ⑤陰性：メモリ上で改変した構造を検査関数に直接渡す。行範囲を1行ずらす・引用を1字変えて一意に一致しなくする → index_invalid。記録された quote_sha256・unit のハッシュ・papers[].sha256 を変える → internal_mismatch。

施工段階1でDECISIONS.md に書くもの：Git 参照（ref・commit・tree・parent・確認日時）、取得経路と取得ログ、bundle の形式と `EXPECTED_BUNDLE_SHA256`、規則 LINES・LANG・SECTION・T4MAP（D04④ のハッシュ規則を含む）・BUNDLE の版、起動時に照合できない記録の一覧、節idの HTML 実在の使い捨て検査の結果、実行した Python の版。

## A-3 施工段階2：schema.py・normalize.py・tools.py・patterns.py・prompts.py（完了条件 T01〜T12・R01）

着手の条件：Q16・Q21〜Q61・Q65・Q68・Q84・Q88・Q92 の該当するもの（特に Q21・Q23・Q24・Q41〜Q44・Q50〜Q52）。

**schema.py**
- `SCHEMA_VERSION`、`JSON_RULE="JSON-1.0.0"`。
- `Status`：ok・unknown_id・quote_not_found・no_lexical_match・invalid_input・ledger_not_available。
- `SourceKind`：paper_md・theory_map・claims・reading_guide・reading_test・translation・translation_note。
- `Locator`（path・line_start・line_end・char_start・char_end・json_pointer・note）。
- `SourcedResult`（source_id・source_kind・paper_id・paper_version・language・source_path・source_hash・section_anchor・locator・canonical_doi・source_url・snapshot_url・payload）。
- `make_envelope(corpus, status, results, candidates, limitations, extra)`、`to_json(envelope)`、`validate_envelope(obj)`（手書きの検証器。jsonschema に依存しない）。
- 共通外枠は SPEC §4 どおり（schema_version・corpus_version="3.5.0"・source_commit・bundle_hash・status・results・candidates・limitations）。ツールごとの外枠の追加欄（verify_quote の match と normalization_applied など）は extra から入れる。normalization_applied は全結果に適用した規則IDの和集合で、結果ごとの変換は payload.diffs に置く（Q48）。細部は Q38、DOI と URL は Q33・Q88。license 欄は足さない（Q16）。

**normalize.py**（NORM-1.0.0。`docs/rules/NORM.md`）
- 明示の対応表（WHITESPACE・ZERO_WIDTH・WIDTH_MAP・半角カナ表・PUNCT_CLASSES・QUOTE_MAP）と、表を正準 JSON にしたものの SHA-256（import 時に再計算して定数と照合する）。
- `normalize_with_offsets(s, *, is_input) -> Normalized(text, spans, applied)`：各文字について原文の区間を持つ（削除と合成があるので区間で持つ）。
- `find_all(hay, needle)`：原文側の文字位置の一覧を返す。`diff_records(original, user_text, limit)`（Q48）。
- 原文側の正規化テキストと区間の表は、起動時に作ってメモリに置く。data/ には書かない。
- 照合は二段：①生テキストの完全一致（match=exact）、②同じ規則を入力と原文の両方にかけた一致（match=normalized）。大文字と小文字は同一視しない。

**検索（SEARCH-1.0.0・CAND・TERMS-0.0.0）**：`docs/rules/SEARCH.md`。用語対応表は `TERMS_VERSION="TERMS-0.0.0"`、`TERMS=()`。承認前は空で起動でき、その間は「断片の部分文字列照合＋英語の単語境界照合」として動く（置き場は Q52）。近接候補と claims の照合は規則 CAND（Q92）。

**tools.py（七ツール。corpus を明示的に受け取る純関数）**
- 共通の入力検査：ID は `^[A-Za-z0-9._-]{1,128}$`。パス区切り・URL・NUL の形をした値は invalid_input。それ以外の形式違反と、形式は正しいが索引にない ID は unknown_id と近傍候補（Q35）。k は `isinstance(k, int) and not isinstance(k, bool)` で、範囲内であること。文字列の長さは Q56・Q84。

| ツール | シグネチャ（案） | 状態 | 結果の中身 |
|---|---|---|---|
| list_papers | `list_papers(corpus)` | 常に ok | 5件（paper_md、アンカー paper-tN）。payload：title・alternate_title（T4）・paper_version・canonical_doi・language（Q22）・available_editions（T4 は ja と en）・line_count・sections（id・title・level・line_start・line_end・parent_id・child_ids・heading_only） |
| get_section | `get_section(corpus, paper_id, anchor, language=<Q21>)` | パスや URL の形→invalid_input。論文が未登録→unknown_id（候補は5本）。アンカーが未登録→unknown_id（候補は Q35）。Q21 案A では T1〜T3・T5 に ja または en→invalid_input、T4 は ja（または None）と en だけ ok | 原文：1件。payload に text（範囲の行を "\n" で連結し、改変しない）・is_excerpt=false・parent_id・child_ids（Q34）・heading_only。T4 の en：節に属する unit を英訳の行の順に返す。訳注は translation_note の別の結果にする（Q26）。欄の埋め方は Q88。各結果に original_locator（papers/T4.md の行・sourceSha256・節）・treatment・translation_version="1.0.0"・source_corpus_version（Q28）・manifest の preparation と authority（Q25）を付ける。位置のない wrapper の description（6件）は、manifest の位置（json_pointer）付きで返す（Q38⑨）。separator（5件、description なし）は原文の行位置だけを返す。英訳の枠部分は Q27 |
| search_passages | `search_passages(corpus, query, paper_id=None, k=5)` | 空・断片0個・上限超過・k が範囲外→invalid_input。paper_id が未登録→unknown_id。全語一致が0件→no_lexical_match。それ以外→ok | 各結果：locator は行と文字位置。payload に excerpt・is_excerpt=true・match_positions・matched_terms・match_via（Q53）・rank・rank_key・route（get_section への paper_id と anchor）。limitations に照合範囲、SEARCH と TERMS の版、「スコアは順位であって確率ではない」「ゼロ件は記述がないことを意味しない」、言語差の注意（Q61）。results が空のとき、エンベロープにも results にも論文のアンカーを置かない。candidates（一部一致。Q55）は、索引に実在するアンカーを付けた場合に限り返してよい |
| get_claim_record | `get_claim_record(corpus, claim_id=None, query=None)` | 両方なし・両方あり→invalid_input。T1〜T4→ledger_not_available（Q32）。T5 だが未登録→unknown_id（候補は実在する11件）。query→Q32・Q92 | 1件ごとに source_kind=claims、source_path=claims/t5.json、source_hash は台帳の SHA-256、locator.json_pointer=/claims/i、paper_id=T5、paper_version="3"、section_anchor は section_url のフラグメント、source_url は section_url、canonical_doi は T5 の DOI（Q88）。payload：id・status（逐語）・claim（台帳の要約と明示）・source_quote（逐語）・not_claimed（配列のまま）・section・source_locator（中身ごと）・additional_source_quotes（Q30）・footnote（N3 以外は null）・author_answerable=null（「未記録（初版）」と注記）・cited_paper_sha256（source_sha256） |
| verify_quote | `verify_quote(corpus, text, paper_id=None, language=<Q21>)` | 空・空白だけ・正規化後に空・最小長未満・上限超過→invalid_input。一致が結果数の上限を超えた場合も invalid_input とし、limitations に `total=n` を書く（部分結果は返さない。Q84）。paper_id が未登録→unknown_id。paper_id と language の組み合わせは get_section と同じ規則。完全一致が1件以上→ok, match=exact。正規化で一致→ok, match=normalized。どちらもない→quote_not_found, match=none（candidates は規則 CAND による語句上の近接候補で、上限5件。「類似の主張がある」とは書かない） | 各結果：locator は行と文字位置。payload に matched_text（原文をそのまま切り出したもの）と diffs。複数か所で一致したら全件を返して曖昧さを表示する（上限内）。完全一致があり、句読点だけが違う箇所が別にある場合、後者は candidates に出す（Q48）。照合範囲は Q24 |
| check_compressions | `check_compressions(corpus, text)`（内部の `_check_compressions(corpus, text, patterns)` でパターンを差し替えられる） | 空・上限超過→invalid_input。それ以外→ok（ゼロ件の扱いは Q36） | 各結果：出典欄は source_excerpt 側（Q38⑧）。payload に入力中の文字位置・pattern_id・pattern_version・needs_context_review=true・source_excerpt。limitations に SPEC §5.6 の契約文と「肯定・否定・引用・疑問は同じ語形として拾いうる」を必ず入れる。判定の欄は持たない |
| get_reading_guide | `get_reading_guide(corpus, part="all")` | part が列挙にない→invalid_input（Q29）。それ以外→ok | FOR_AI_READERS.md の該当する行範囲（reading_guide・language は Q22・DOI は null）と、prompts.py の雛形（置き場は Q38⑤） |

- 関数の内部で処理を時間で打ち切らない。処理時間の上限の扱いは Q85。

**patterns.py**：`PATTERNS_VERSION="PATTERNS-0.0.0"`、`APPROVED_ON=None`、`PATTERNS=()`。Pattern の形は id・version・surface_forms・match_rule・related_sources・approved_on（Q37）。`validate_patterns()` は related_sources の節と行が実在するかを起動時に検査する。施工側ではパターン候補を起草しない（SPEC §10）。

**prompts.py**：`PROMPTS_VERSION`。READ_WITH_GUARDS・FOUR_MODES・ANSWER_FORMAT を定数として持ち、get_reading_guide と MCP の prompts が同じ定数を返す。文面は Q39。

**T01〜T12・R01（tests/test_tools.py。実データは読むだけ）**

| ID | 入力 | 確かめること | 前提 |
|---|---|---|---|
| T01 | list_papers | 5本。paper_version が 1・2・2・1・3。DOI が papers[].canonical_doi と完全に一致（T3 は 10.35542 系）。節数が 40・39・25・25・29。親子が SECTION どおり。言語が LANG どおり | Q22 |
| T02 | 158節すべて | text が行範囲の連結と完全に一致する。親節は記録範囲だけを返し、child_ids は直下の子だけ（例：T4 paper-t4 の子は t4-1〜t4-6・t4-notes・t4-references）。heading_only が定義どおり（本文を含む親節13件を含む） | Q21・Q34 |
| T03 | 存在しないアンカー、存在しない論文、`../x`、「4.2節」、存在しない claim_id | 状態が Q35 の規則どおりで、results は空。candidates の各アンカーが索引に実在し、応答に索引にないアンカーやパスが含まれない | Q35 |
| T04 | 一致する語句、確実に存在しない語句（テスト内で範囲全体に不在であることを確かめてから使う）、同点群の大きい単一語、ひらがなだけの語、日本語の語を空白で区切ったクエリ | ok と件数。ゼロ件のとき no_lexical_match で results は空、candidates のアンカーはすべて索引に実在。順位が全順序で毎回同じ。ひらがなだけの語は invalid_input。空白で区切った日本語の語は別々の断片として照合される。期待値は SEARCH と TERMS の版が確定してから作り、テスト名に版を入れる | Q50〜Q61 |
| T05 | 11件の claim_id と代表的な query | status・source_quote・not_claimed が生の JSON と一致する（not_claimed の長さは 3・3・3・2・4・5・4・4・2・3・3）。additional_source_quotes が A3・A4・N1（2件）・N2・H1 で保たれ、残り6件は Q30 どおり。author_answerable は11件とも null。footnote は N3 以外 null。台帳と引用元論文のハッシュが別の欄にある | Q30・Q32・Q92 |
| T06 | T1〜T4 の claim_id | ledger_not_available。results は空。T5 の status 文字列を含まず、ラベルを作らない | Q32 |
| T07 | 凍結定式二本 | どちらも match=exact・status=ok で、行と節が期待どおり | Q23＝A：T5.md 13行 "AI can deliver the state of affairs; it cannot deliver the fact of participation."（t5-abstract）と223行 "AI can assist play. It cannot take one's place in it."（t5-5-4） |
| T08 | 許容される表記差（T4 引用の「，」→「、」、空白や改行の挿入、曲線引用符、全角英数） | match=normalized。matched_text が原文どおり。normalization_applied に規則IDと NORM の版がある。変形した入力は tests/fixtures/ に置く | Q41〜Q48 |
| T09 | 内容語の置換、否定の付加や削除、数字・小数点・負号・比較記号の変更、語の連結 | quote_not_found・match=none。変形後の文字列が照合範囲の全体に生でも正規化後でも存在しないことを、テストの中で先に確かめる | Q24 |
| T10 | `""`・空白だけ・`"\u3000"`・`"\u200b"`・最小長未満、範囲内に2回以上現れる短文、上限を超えて現れる短文 | 前者は invalid_input。複数一致は全件を返して曖昧さを表示する。完全一致と正規化一致が混在する場合は Q48 の規則どおり。上限を超えて現れる短文は invalid_input で、limitations に `total=n`（Q84）。句読点だけが違う箇所は candidates（Q48） | Q38・Q48・Q84 |
| T11 | 試験用パターン × 肯定・否定・引用・疑問、パターン0件 | 4種とも同じ規則で要確認箇所として返し、needs_context_review=true。判定の欄がない。契約文がある。0件は Q36 どおり | Q36・Q37 |
| T12 | T4 の en、訳注を含む節、T1 の en と ja | 英訳は translation・en・translations/T4.en.md・original_locator 付きで、欄は Q88 どおり。訳注は translation_note で、paper_md にならない。訳注の結果が著者の原文の DOI を学術的な引用先として示さない（Q88）。原著者注（author-note-N）は translation。T1 の en と ja は invalid_input（Q21 案A の場合） | Q21・Q25〜Q28・Q88 |
| R01 | 7ツールそれぞれの固定入力 | 同じプロセスで2回呼んだ結果と、別プロセスで PYTHONHASHSEED を変えて呼んだ結果の to_json 出力が、バイト単位で一致する（過負荷のない条件で） | Q65 |

施工段階2でDECISIONS.md に書くもの：SCHEMA・JSON・NORM（表・表のハッシュ・根拠件数・除外集合・数字の保護）・SEARCH・CAND・TERMS・PATTERNS・PROMPTS・NEAR・GUIDE・LIMITS の版と値、形態素解析器を入れない判断とその理由、T07 に使った文字列と出典、最悪ケースの所要時間、参考値の再計測結果。

## A-4 施工段階3：app.py と接続試験（完了条件 S01〜S03・M01〜M03）

着手の条件：Q12・Q40・Q62〜Q72・Q74〜Q76・Q85〜Q87・Q91・Q93。着手時に PyPI を取り直し、6.27.x の修正版、mcp 1.x の最新、分類子を確認して記録する。

**app.py の骨格**（Gradio 6.27.0 を仮定。Q62）
- import gradio より前に環境変数を整える（Q93）：許可した GRADIO_* だけを残し（`GRADIO_ANALYTICS_ENABLED="False"` は上書き）、ほかの GRADIO_* を消す。`HF_HUB_DISABLE_TELEMETRY="1"` を設定する（MCP 内部の gradio_client は環境変数だけで telemetry を判定し、huggingface_hub は import 時に値を確定するため）。
- `corpus.load_corpus()` が BundleError を出したら、非ゼロで終了する。
- 七つの関数は、名前を SPEC のツール名と完全に一致させる（ツール名は `__name__` から付き、`gr.mcp.tool(name=)` は反映されない）。全引数に型ヒント、戻り値は `-> str`（Q63）、Args 形式の docstring を付ける。`from __future__ import annotations` は使わない。
- `with gr.Blocks(analytics_enabled=False, title="Mekiki Reader")` の中で、各関数を `gr.api(fn, api_visibility="public", queue=<Q65>)` で登録する。UI コンポーネントは置かない。
- resources は12件を静的 URI で登録し（Q70）、prompts は3件を関数名と同じ名前で登録する（`name=` は使わない）。最後に、呼ばれたら例外で止める番兵関数を登録する（Q64）。動かない場合は Q87。
- ポート：`MEKIKI_READER_PORT`（Q12。1024〜65535 の整数で、それ以外は起動を拒否）、既定 7860。
- `launch(mcp_server=True, share=False, server_name="127.0.0.1", server_port=<上記>, ssr_mode=False, enable_monitoring=False, run_history=False, footer_links=[], max_threads=<Q65>, max_file_size=<小>, show_error=False, app_kwargs=<Q66 のミドルウェア>, prevent_thread_lock=True)`。
- 起動後の確認：`demo.mcp_server` が True（Gradio は MCP の初期化に失敗しても起動を続ける）、`demo.vibe_mode` と `demo.dev_mode` が False、`demo.allowed_paths` が空（Q93）。満たさなければ非ゼロで終了する。
- テーマは文字列で渡さない（Hub から取得されるのを避ける）。
- 次の点はコードを読んだだけで、動作は確認していない。施工段階3の最初に実機で確かめる：gr.api だけの Blocks と mcp_server=True の組み合わせ、resources と prompts の登録、queue=False の関数を resources として読めるか、ミドルウェアでの遮断。

**S01〜S03（tests/test_safety.py）**。サーバを起動するテストには server マークを付け、子プロセスを loopback だけで待ち受けさせる。
- S01
  - 関数レベル：paper_id・anchor・claim_id・part に `../../.env`・`/etc/passwd`・`T1/../../.env`・`https://example.com/x`・`file:///etc/hosts`・NUL を含む文字列を渡し、invalid_input になり、エラー文にパスが混ざらないこと。query と text に 1MB を渡すと invalid_input で、所要時間が Q85 の判定値以内。k に -1・0・21・`10**9`・True・"5"・5.0。
  - 起動後のファイルアクセス：open 系を監視し、起動後の呼び出しで開かれたファイル（書き込みを含む）が0件であること。
  - 環境変数：GRADIO_SERVER_NAME=0.0.0.0・GRADIO_VIBE_MODE・GRADIO_WATCH_DIRS・GRADIO_ALLOWED_PATHS などを設定したまま起動しても、127.0.0.1 に bind し、vibe_mode・dev_mode が False で、allowed_paths が空であること（Q67・Q93）。データ根は環境変数などで変えられないこと（Q12）。ポート以外の環境変数で挙動が変わらないこと。
  - HTTP レベル：`/gradio_api/file=../../.env`・`/gradio_api/file=/etc/passwd`・`/gradio_api/file=app.py`・`/gradio_api/file=https://example.com/`・`/gradio_api/proxy=…`・`POST /gradio_api/upload`・`/gradio_api/run-history/connect`・`/vibe-edit` 系・巨大な本文・不正な Host ヘッダが拒否されること（Q66）。応答コードを実測して期待値として記録する。未知の URI や `../` を含む URI での resources/read も拒否されること（Q70）。
  - 同時実行：上限を1超える数を並行して送り、上限どおりに抑えられ、超過が status ではなく通信層で返ること（Q65）。
- S02：tests/fixtures/ の命令風テキスト（Q40）を query・text・claim の query に入れて呼ぶ。状態は通常の規則どおりで、読むファイルは増えず、応答の欄の構成も変わらないこと。コーパス内の命令風の文（台帳の maintenance 欄など）がデータとして返るだけであること。呼び出しの後で bundle のハッシュが変わらないこと。prompts の文面に上書きしない旨の定型文があること。
- S03：子プロセスの先頭で `sys.addaudithook` を登録し、socket.connect・socket.getaddrinfo・socket.sendto を記録する。loopback（127.0.0.1・::1・localhost）以外への接続は例外にして記録する。この状態で import gradio → 起動 → 全ツール・全 resource・全 prompt の呼び出し → 停止 までを行い、記録が空であることを確かめる（resources/read と prompts/get は自分自身への HTTP を伴う）。重点的に見る宛先は api.gradio.app・huggingface.co・cdn-media.huggingface.co・www.gradio.app。補助として、mekiki_reader の禁止 import と app.py の launch 引数・環境変数の整理の静的検査、起動中の `lsof -nP -i -a -p <pid>` の手動記録。これは内部の監査で、README で宣言する範囲は SPEC §2.10 の文言どおり（Q86）。ブラウザで `/` を開いたときの外部資源の取得は範囲外とし、未確認として記録する。

**M01〜M03（tests/test_mcp.py）**。mcp SDK（1.30.0）の Streamable HTTP クライアントで、`http://127.0.0.1:<port>/gradio_api/mcp/` に接続する（起動表示「* Streamable HTTP URL: …」を実測して記録する。旧 SSE は `/gradio_api/mcp/sse` を予備として記録するだけ）。
- M01：tools/list がちょうど7件（Spaces では接頭辞を除いて比べる。Q69）。inputSchema（required・型・enum）が期待どおり。各ツールが isError=false を返し、content[0].text が JSON として読めて validate_envelope を通る。
- M02：resources/list が12件で、resources/read の本文の SHA-256 が bundle と一致する。prompts/list が3件で、prompts/get の本文が prompts.py と一致する。未知の prompt 名での挙動を記録する（Q64）。実クライアントでの確認の段階は Q91。
- M03：スキーマ層の違反（k="abc"。mcp SDK の検証）と、Gradio の引数構築層の違反（未知の引数名。inputSchema に additionalProperties がないため、gradio_client の TypeError から来る見込み）は、いずれも isError=true になるかを実測し、エラー文に内部の情報が含まれないことも確かめる。アプリ層の違反（k=0、未知のアンカー、ゼロ件）は isError=false で status が invalid_input・unknown_id・no_lexical_match。どちらの後でも、同じセッションで list_papers を呼べる（通信が切れていない）。

施工段階3でDECISIONS.md に書くもの：検証に使った環境（`python -VV`・`pip freeze`〔ハッシュ付き〕・`unicodedata.unidata_version`・`pip --version`）、接続 URL、S01〜S03・M01〜M03 の結果、S03 の監査ログと lsof の記録、prompts の名前照合の再現結果、標準経路と環境変数の遮断の検証結果、最悪ケースの所要時間。

## A-5 施工段階4：README・requirements・検収記録

着手の条件：Q13〜Q20・Q71〜Q73・Q77〜Q82・Q86・Q89〜Q91・Q95。

**README.md の章立て**（下書き。開示の章の文面と配置は著者の承認・署名の対象。Q89）
0. YAML front matter（配置段階二の Space 用）：`sdk: gradio`、`sdk_version: "<Q62>"`、`python_version: "<Q74・Q78。引用符付き>"`、`app_file: app.py`（license 欄は Q15）。
1. 設計上の対応：SPEC §1 の表（列名は「設計上保ちたい区別／根拠・参照先」。実装を論文の直接の主張とは書かない）と、SPEC §0 の三層の保証の表。表の直後に SPEC §1 末尾の二文を逐語で置く：「**設計の整合は理論の妥当性の証明ではない。静的な方針の検証は動作の保証でもない。**」
2. これは何で、何をしないか（読み取り専用・サーバ内に LLM なし・SPEC §11 の項目）。
3. 同梱データと版（v3.5.0・commit・tree・bundle_hash・許可一覧・同梱しないもの。Pages は main を配信するので、固定の参照先は snapshot_url）。
4. ツール・resources・prompts の一覧（Spaces での接頭辞付きの名前、状態の意味、上限値、規則の版の一覧）。
5. 起動と接続の手順：インタプリタを明示した起動（Q79）、起動表示の URL、Claude Code（`claude mcp add --transport http mekiki-reader <実測URL>`）、Claude Desktop（Q72：先に HTTP 直結の可否を確かめ、直結できなければ版を固定した mcp-remote）、ChatGPT 開発者モード（Q73）、検収記録へのリンク（Q81）。
6. ライセンス：コードは MIT、`data/` は CC BY 4.0（`data/LICENSE`）。帰属文は CITATION.md L21 の書式。改変の表示は「原文の行は改変しない。行単位で抜粋し JSON に構造化して返す」（Q14）。「同梱物は data/LICENSE（CC BY 4.0）に従う。論文本文中に別の表記があっても同梱物には及ばない」の一行（Q18）。ルートの `NOTICE` を参照（Q13）。
7. テストと検収（`pytest tests/`、`pytest -m server tests/`、テストIDの表）。
8. 開示（SPEC §2.11。末尾に置く。Q89）：制作工程（SPEC → Claude Code による施工 → Codex による独立検査 → Claude による最終検査 → 著者の判断、生成 AI の使用）、参照論文（Q90）、費用と休止（配置段階一は追加料金なし。配置段階二の実測値はそこで記入）、利用者入力の送信先と保存方針（Q20）、外向きの資料取得の宣言（Q86）、既知の制約（英訳の作成経緯 Q25、英訳の出典記録の版 Q28、T1 本文の記述 Q18、日本語の問いが英語の論文に当たりにくいこと、M02 で再現した上流の挙動 Q64、`/` で Gradio 標準のフロント HTML が返ること Q66④。⑥は Q66・Q95 の条件を満たすまで書かない）。

**requirements.txt**：暫定で `gradio[mcp]==6.27.0`・`mcp==1.30.0`・`pydantic==2.12.5`。施工段階3で記録したハッシュ付きの環境をもとに、施工段階4で確定する（固定は推移依存までハッシュ付き〔uv pip compile〕、開発用は requirements-dev.txt。Q76。Spaces との関係は Q77）。固定の根拠（タグのコミット、wheel の SHA-256、PyPI JSON の URL）を DECISIONS.md に記録する。

**E01・E02・P01 と検収記録**
- E01（手動のスモーク試験）：R01（claim_ids は T5-A1・T5-A3・T5-N1）、R08（claim_ids は T5-A4、追加根拠は T5 §1 の27行）、R13（claim_ids は空、追加根拠は T1 §4.2 の163・167・193行）、R14（T1 §2.1 の54行と T2 §2.1 の37行）、R15（T3 §7 の162行と §2.2 の41行）。実施条件（Q82）：ja と en の両方、クライアントは Claude Code、ガイド条件は「なし」と read_with_guards の二つ。AI_READING_TESTS の resource は読ませない（読んだ場合は記録）。判定は SPEC §7 の文言に限り、コーパス基準との照合は記録だけ。記録する項目：正しい原文・位置・記録を保持したか、ガイドの使用条件、ツールを呼んだ順序、AI_READING_TESTS の resource を読んだか、生の応答、原文との突き合わせの結果。
- E02：架空の会社の相談例と、資料中の命令文（Q40）。原文と事例の判断を分けたか、資料を上位の命令として扱わなかったか。
- 公開前の作業（Q95）：DECISIONS.md の「台帳 D656」を「方針書 v2 冒頭の改版行」に置き換える。「段階二」の表記を「配置段階二」に統一する。Q64・Q66⑥ の行番号つき分析を要約にする（未報告の脆弱性の疑いの詳細は出さない）。
- P01：配置段階二で、再起動と休止からの復帰の後に再接続し、復帰時間を実測する。施工段階4では手順と様式だけを用意する。
- 検収記録の様式（接続先ごと。置き場は Q81、対象は Q71・Q91）：日時・クライアントの版・モデル／接続方式と URL（実測）／tools/list（7件）と各呼び出し／resources/list（12件）と read／prompts/list（3件）と get（未知の名前の挙動を含む）／不正な入力とゼロ件／E01・E02 の結果とガイドの使用条件／未対応の機能と備考。

## A-6 テストID総覧

| ID | 施工段階 | ファイル | 自動/手動 | 前提 |
|---|---|---|---|---|
| D01〜D03 | 1 | tests/test_data.py | 自動 | 一時コピー、データ根の注入（Q12）、EXPECTED_BUNDLE_SHA256（Q03）、余剰の厳しさ（Q10） |
| D04 | 1 | tests/test_data.py | 自動 | 実データを読むだけ。陰性はメモリ上の改変（Q22・Q26・Q27・Q34） |
| T01〜T03・T05・T06 | 2 | tests/test_tools.py | 自動 | Q21〜Q35・Q88・Q92 |
| T04 | 2 | tests/test_tools.py | 自動 | Q50〜Q61 |
| T07 | 2 | tests/test_tools.py | 自動 | Q23＝A（T5.md 13・223行） |
| T08〜T10 | 2 | tests/test_tools.py＋tests/fixtures/ | 自動 | NORM（Q41〜Q48）、照合範囲（Q24）、結果数（Q84） |
| T11 | 2 | tests/test_tools.py＋tests/fixtures/ | 自動 | Q36・Q37 |
| T12 | 2 | tests/test_tools.py | 自動 | Q21・Q25〜Q28・Q88 |
| R01 | 2 | tests/test_tools.py | 自動 | 子プロセスで PYTHONHASHSEED を変える（Q65） |
| S01・S02 | 3 | tests/test_safety.py（＋fixtures） | 自動 | サーバ起動、Q12・Q40・Q56・Q65〜Q67・Q70・Q85・Q93 |
| S03 | 3 | tests/test_safety.py＋lsof の手動記録 | 自動＋手動 | サーバ起動、Q66・Q86・Q93 |
| M01〜M03 | 3 | tests/test_mcp.py（M02 は実クライアントでも） | 自動（＋手動） | Q63・Q64・Q68〜Q70・Q87・Q91 |
| E01・E02 | 4 | 検収記録 | 手動 | Q40・Q71〜Q73・Q81・Q82 |
| P01 | —（配置段階二で実施。施工段階4では様式のみ） | 検収記録 | 手動 | Space の公開（著者の判断） |

## A-7 SPEC §11（触れないもの）の確認

- 意味検索・埋め込み：検索は語句の照合と、明示した対応表による展開だけ。ベクトルや類似度のライブラリは入れない（numpy などは gradio の推移的な依存で、mekiki_reader からは import しない）。形態素解析器も入れない。対応表を概念レベルに広げると意味検索に近づくおそれがあるので、範囲は著者が決める（Q53）。
- 外部 LLM：API クライアントを持たず、API キーの環境変数を読まない（Q80）。Gradio の vibe_mode は環境変数を消して無効化し、起動時に確かめる（Q93）。
- チャット UI：Blocks にコンポーネントを置かない。`/` の標準フロントは Q66 で扱う。
- 判断を採点するツール：check_compressions は要確認箇所と原文を返すだけ。E01・E02 は人手による記録で、ツール化しない。AI_READING_TESTS.md は「採点には使わない」と明記して resource として返す。
- 非公開資料の同梱：許可一覧の公開ファイルだけ。fixture は架空のテキスト。
- compare_versions：実装しない。版どうしの比較を応答に出さない（Q28）。
- 理論の妥当性の主張：README に SPEC §1 の二文を置く。
