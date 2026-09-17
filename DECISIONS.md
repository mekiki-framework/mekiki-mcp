# DECISIONS.md — 実装中の判断ログ

運用：一件につき日付・段階・項目・判断・理由・根拠（確認した現物＝コマンド出力・URL・ファイル）・状態（提案／確定／撤回）。
「提案」は著者の確認で「確定」になる。撤回は行を消さず、状態を「撤回」にして理由を書く。

## 必須記録項目（SPEC §2.5・§3・§10）
- [ ] コーパス Git参照 `v3.5.0` → 解決したコミットSHA（`git ls-remote` 等の出力）
- [ ] 採用 Gradio 版・Python 版（検証結果と `requirements.txt` の数値）
- [ ] 正規化規則の版（`normalize.py`・対応表）
- [ ] パターン一覧の版（`patterns.py`）と著者承認日
- [ ] `translations/T4.en.manifest.json` の扱い（v3.5.0 に存在するか／Reader側で作るか）と理由
- [ ] 接続URL（実際の起動表示・接続先ごとの検収結果）
- [ ] 費用と休止復帰時間の実測値（段階二）

## ログ

表記：「段階」は CLAUDE.md の施工段階0〜4。SPEC §9 の段階一（ローカル）・段階二（Spaces）は「配置段階一／二」と書き分ける。Qnn は著者への要確認事項で、計画は付録A、初期案は付録B、確認した現物は付録C にある。外部サイトの公開日は UTC の日付で書く。「参考値」は、段階0に一時領域で動かした使い捨ての集計・試作による数値で、スクリプトは保存していない（施工段階2で規則を実装した後に再計測する）。

| 日付 | 段階 | 項目 | 判断 | 理由 | 根拠 | 状態 |
|---|---|---|---|---|---|---|
| 2026-09-18 | 0 | 正本の配置 | `SPEC_Mekiki_Reader_MCP_v2_20260918.md` を `SPEC.md` としてリポジトリ直下に置く。以後の方針変更は版を上げて記録する | 方針書をリポジトリ直下に置き機械間で共有する（台帳 D656） | SPEC.md 冒頭の改版行 | 確定 |
| 2026-09-18 | 0 | 日付の表記 | 本ファイルの日付は JST（Asia/Tokyo）で書く | 実行環境の UTC 表示とは日付がずれる時間帯がある | `TZ=Asia/Tokyo date` → 2026-09-18T00:21+0900／`date -u` → 2026-09-17T15:21Z | 提案 |
| 2026-09-18 | 0 | 施工計画 | 付録A「段階0 施工計画」を施工段階1〜4の計画とする。未確定の点は Q01〜Q95 で著者に確認し、推定で埋めない | CLAUDE.md 段階0の完了条件（計画と質問を「提案」として記録） | SPEC.md v2 §3〜§8、付録C の現物確認 | 提案 |
| 2026-09-18 | 0 | 段階0で行った作業の範囲 | リポジトリへの書き込みは本ファイルだけ。`data/` は作っていない。現物確認に使った通信は次のとおり：git の smart HTTP（`git ls-remote`、一時領域へのタグ v3.5.0 の浅い clone、SHA 指定の fetch。upload-pack への POST を含む）、GitHub API（gh、GET のみ）、raw.githubusercontent.com・mekiki-framework.github.io・pypi.org・huggingface.co・creativecommons.org・api.osf.io・docs.github.com・devguide.python.org・peps（python の GitHub）・www.python.org・formulae.brew.sh・registry.npmjs.org・endoflife.date への GET。リポジトリ外のローカル環境は、インタプリタの所在と版の確認だけに読んだ。一時領域で使い捨ての分析・試作スクリプトを動かした（Q94）。パッケージの導入・venv 作成・コーパスの tools/*.py の実行はしていない | 段階0の制約（コードを書かない・data/ を取得しない）に照らした自己申告 | `git status --short`（本ファイル以外の変更なし） | 提案 |
| 2026-09-18 | 0 | コーパス Git 参照の解決（必須記録） | `refs/tags/v3.5.0` は軽量タグで、commit `67480613108cf72c29d5691e3d7a6c7e6553eb9b` に解決する（tree `7c50a4fc2bf20f1529aebe8a8b7898e26332f1a1`、親 `8a46b24bce8071a6daa23a0bfd18e29008468042`＝v3.2.1、メッセージ "Release 3.5.0"、2026-09-06）。同名のブランチはない。施工段階1ではタグ名ではなくこのSHAで取得する（Q01・Q03・Q04） | 軽量タグは付け替えられる（ruleset なし、Release は immutable=false）。`main` は読みに行かない（SPEC §2.5） | `git ls-remote https://github.com/mekiki-framework/mekiki-framework.github.io.git` → `6748061…␉refs/tags/v3.5.0`、`^{}` 行なし（2026-09-17T14:40Z と 15:21Z の2回。同じ出力に main も同SHAで出たが、施工では照会しない）／`gh api repos/mekiki-framework/mekiki-framework.github.io/git/refs/tags/v3.5.0` → object.type=commit／浅い clone で `git rev-parse HEAD HEAD^{tree}` → 上記2値 | 提案 |
| 2026-09-18 | 0 | Release の日付の食い違い（事実） | GitHub Release v3.5.0（id 342506822）の published_at は 2026-06-21T11:05:05Z で、タグのコミット日 2026-09-06 より早い。created_at（仕様上はコミット日）は 2026-09-06T06:11:38Z。原因は未確認。履歴の書き換えの形跡はない（main は分岐のない19コミットで、Pages のデプロイ18件はすべてその中）。版の同定に Release の日付は使わない（Q02） | 版同定の根拠を「タグ→SHA・tree・ファイルごとのハッシュ」に限るため | `gh api …/releases/tags/v3.5.0`／GitHub REST docs（releases）"The created_at attribute is the date of the commit used for the release"／`gh api …/commits?sha=main`、`gh api …/deployments` | 提案 |
| 2026-09-18 | 0 | `translations/T4.en.manifest.json` の扱い（必須記録） | v3.5.0 に実在する（66107 bytes、blob `1aa13cb36af22e8067d27f02129c985e9a1c6540`、SHA-256 `d6768d66ce13716caaf64544c8b93454e6659a90cfb6ed03914d7d471e050fc1`）。Reader 側では作らず、そのまま同梱する。sourceUnits は137件で、うち126件が英訳側の行位置とハッシュ（translation* の3キー）を持つ。ja↔en の機械的な対応づけは manifest だけで足りる。`translations/T4.en.meta.json`（許可一覧外）の sourceUnits は、manifest から translation* の3キーを除いたものと一致する。meta にはほかに方針文4欄（notesPolicy・citationsPolicy・referencesPolicy・authorEnglishAbstract）と書誌欄（name・sourceTitle・author など）がある。meta は同梱しない案とする（Q08） | SPEC §3 は「機械的対応づけのため追加」としている。manifest 以外に英訳の行位置の記録はない | `gh api …/git/trees/6748061…?recursive=1`（truncated=false）／`shasum -a 256`／manifest の source.sha256 が papers/T4.md（`9d2e0984…`）と、translation.sha256 が translations/T4.en.md（`bdf8690f…`）と一致 | 提案 |
| 2026-09-18 | 0 | コーパス LICENSE の現物確認 | v3.5.0 の `LICENSE`（18657 bytes、blob `da6ab6cc8f333d7e89a99812866df8f24374d47c`、SHA-256 `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411`）は、CC BY 4.0 の公式 legalcode.txt とバイト単位で一致する。独自の前置き・追記・例外はない。著作者名はファイル内になく、帰属の書式は許可一覧外の CITATION.md L19–23 にある。許可ファイルのうちライセンスを明記しているのは llms.txt:51・FOR_AI_READERS.md:73・THEORY_MAP.md:336・T5_CLAIM_STATUS.md:236 で、`papers/*.md`・claims/t5.json・source_manifest.json・`translations/*` には表記がない。原論文5本の OSF 登録も CC BY 4.0。mekiki-mcp の LICENSE は MIT。SPEC §3 の同梱許可一覧に LICENSE はない（Q06・Q13〜Q19・Q83） | 同梱と表示の要否・置き場を著者が決めるための現物。ライセンスの解釈はしない | `diff <(curl -sSL https://creativecommons.org/licenses/by/4.0/legalcode.txt) LICENSE` → 差分なし（2026-09-18 再確認）／`gh api repos/mekiki-framework/mekiki-framework.github.io/license?ref=v3.5.0` → spdx CC-BY-4.0／`curl https://api.osf.io/v2/preprints/{cwkav_v1,e9qw5_v2,hvbfe_v2,495wg_v1,593ah_v3}/?embed=license` → 5本とも "CC-By Attribution 4.0 International" | 提案 |
| 2026-09-18 | 0 | 同梱許可ファイルの現物 | SPEC §3 の許可ファイル16本は、すべて 6748061 に存在する。bytes・blob・SHA-256 は付録C-1 のとおり。コーパス内に記録された値のうち同梱ファイルにかかるものは、すべて実ファイルと一致した：source_manifest の papers[].sha256・bytes・lines（15値）、frozen_text_sha256 のうち同梱6本、claims の source_sha256（1）と quote_sha256（主11＋追加6）、T4 manifest の source.sha256・translation.sha256（2）、sourceSha256（137件）、translationSegmentSha256（126件）。改行はすべて LF で、CR も .gitattributes もない | 施工段階1の照合の期待値 | 付録C-1／`git hash-object`・`shasum -a 256`・`grep -c $'\r'`／GitHub trees API と `git ls-tree -r --long` が完全一致 | 提案 |
| 2026-09-18 | 0 | 論文の本文言語（事実） | T1・T2・T3・T5 は英語で、T4 だけが日本語（日本語文字数は T1=6・T2=0・T3=0・T4=18003・T5=0）。source_manifest.json に言語の欄はない。T4 が日本語であることは llms.txt:29・SOURCE_INDEX.md:12・papers/T4.md:11 に文章で書かれているが、T1〜T3・T5 の言語を明記した同梱ファイルはない（Q21・Q22） | SPEC §5.2・§5.5 の既定値 `language="ja"` と食い違う | 文字種の計数（2026-09-18 再確認）／tools/build_access.py の `lang='ja' if pid=='T4' else 'en'`（読んだだけ）／`papers/*.html` の `<html lang>` | 提案 |
| 2026-09-18 | 0 | Q01 v3.5.0 の同定 | 要確認。著者が公開した v3.5.0 は 6748061 か。選択肢：A 6748061 を正とする／B 別のSHAを著者が指定する／C Release 側の整理が済むまで保留する。暫定案：A | 版表示（metadata.version・source_manifest.corpus_version＝3.5.0）、タグ、Pages のデプロイ、Release 本文の日付がすべて 6748061 を指し、3.5.0 と表示する他のコミットがない | 上の「コーパス Git 参照の解決」行 | 提案 |
| 2026-09-18 | 0 | Q02 Release の published_at の記録 | 要確認。選択肢：A 既存の release を流用したものと注記する（著者の記憶で確認できる場合）／B 原因未確認の事実としてだけ記録する／C コーパス側で Release を整理する（Reader の施工範囲外）。暫定案：B | release ID の並びからは 2026-06-21 ごろに作られた可能性があるが、間接的な根拠しかない | `gh api …/releases`（v3.5.0 の1件だけ） | 提案 |
| 2026-09-18 | 0 | Q03 版固定の記録の粒度 | 要確認。選択肢：commit だけ／commit＋tree＋ファイルごとの blob と SHA-256。あわせて、期待する bundle_hash を `corpus.py` の定数と本ファイルに固定し、起動時に照合するか（データと bundle_manifest.json を揃えて書き換えた場合も起動を拒否するため）。どこまでの脅威を想定するかも確認したい。暫定案：後者で、定数も置く | bundle_manifest.json は自分自身を一覧に含めない（SPEC §4）ので、定数がないと同時改変を検出できない | SPEC §2.5・§4 | 提案 |
| 2026-09-18 | 0 | Q04 取得経路と生成スクリプト | 要確認。選択肢：A SHA を指定した浅い fetch（tree を照合し、`git cat-file blob` で書き出す）／B タグ名で clone してから SHA を照合する／C GitHub の tarball／D `raw.githubusercontent.com/<SHA>/<path>` を1本ずつ取得。bundle_manifest.json の生成スクリプトを `scripts/` などに置くか（SPEC §3 の構成外）、一時領域に留めて要点だけ本ファイルに残すか。暫定案：A を主経路、D を独立の照合に使う。スクリプトの置き場は著者の判断 | A は内容アドレスで検証でき、checkout を経ないので改行変換も受けない。一時領域での試行は成功している | `git -c protocol.version=2 fetch --depth 1 --no-tags <url> 6748061…` が成功し、`FETCH_HEAD^{tree}` も一致／raw の SHA URL は HTTP 200 で、内容がバイト一致 | 提案 |
| 2026-09-18 | 0 | Q05 SPEC 改版の手続き | 要確認。次を SPEC を v2.1 などに改版して扱うか、本ファイルの「確定」だけで扱うか：許可一覧の追加（Q06〜Q08）、引数の既定値の変更（Q21）、構成外ファイルの新設（`mekiki_reader/__init__.py`・Q04 の scripts/・Q09・Q12・Q13 の NOTICE・Q52 の terms.py・Q76・Q81）、応答の欄の追加（Q16・Q38⑤・Q38⑩）、一式の変更（Q19）、YAML 項目の追加（Q15）、処理時間や宣言範囲の読み替え（Q85・Q86）。暫定案：SPEC を改版する | CLAUDE.md は SPEC を正本とし、既存の行は「方針変更は版を上げて記録する」としている | SPEC §3（T4 manifest の追加は SPEC 本文に書かれている） | 提案 |
| 2026-09-18 | 0 | Q06 コーパス LICENSE の同梱 | 要確認（Q83 が前提）。選択肢：A v3.5.0 の LICENSE をバイト一致で `data/LICENSE` として同梱する（許可一覧の改版が先）／B 同梱せず、README や NOTICE に CC BY 4.0 の URI を示す／C A と B の両方／D さらに CITATION.md も同梱する。暫定案：C（ライセンスの解釈に基づく推しではなく、公開ファイルをバイト一致で添えれば bundle 検査の枠内に収まるという施工上の理由） | 許可一覧を変えずに data/LICENSE を置くと、許可外パスとして起動を拒否することになる。配置段階二では一式を公開配布する | 関係する条文の所在（解釈はしない）：LICENSE L215–259（§3(a)） | 提案 |
| 2026-09-18 | 0 | Q07 CITATION.md の同梱 | 要確認。選択肢：同梱しない（README から Pages の CITATION.md にリンクする）／許可一覧に追加する。同梱しない場合、THEORY_MAP.md L258 と translations/T4.en.md L1105 の相対リンクは同梱範囲の外を指すことを README に書く。暫定案：なし | 帰属文の書式（L21）と、英訳の文言を引用するときの書式の例（L37）は CITATION.md にしかない。英訳の引用規則そのものは同梱予定の translations/T4.en.md L18・FOR_AI_READERS.md L40 にもある | THEORY_MAP.md L258、T4.en.md L1105、llms.txt L42・L51 | 提案 |
| 2026-09-18 | 0 | Q08 `T4.en.meta.json` の同梱 | 要確認。選択肢：許可一覧の外のままにする（manifest だけ同梱）／追加する（方針文4欄と書誌欄を原文のまま返せる）。暫定案：外したまま | 対応づけは manifest で足りる。訳注の区別は T4.en.md の `<details class="translation-note">` で取れる | manifest.sourceUnits から translation* の3キーを除くと、meta.sourceUnits と一致する | 提案 |
| 2026-09-18 | 0 | Q09 `.gitattributes` の追加 | 要確認。`data/** -text` を置き、改行の自動変換（Windows や autocrlf の環境）による起動拒否を防ぐか。SPEC §3 の構成外。暫定案：追加する | SHA-256 で検査するので、1バイトでも変われば起動を拒否する | コーパスは全ファイル LF・CR 0件 | 提案 |
| 2026-09-18 | 0 | Q10 余剰ファイル検査の厳しさ | 要確認。`.DS_Store` なども含めて一律に拒否するか、無視するリストを設けるか。`.gitignore` に `.DS_Store` を足すか。暫定案：一律に拒否（SPEC §2.5 の文面どおり）。.gitignore への追加は著者の判断 | Finder で data/ を開くと余剰として起動を拒否しうる | `.gitignore` に `.DS_Store` はない | 提案 |
| 2026-09-18 | 0 | Q11 bundle 検査の範囲 | 要確認。同梱したファイルだけを検査し、同梱ファイルが名前で参照するが同梱しないファイル（mekiki-framework-t1-t5.md・`papers/*.html`・papers/T4.en.html・CITATION.md・LICENSE・metadata.json・`tools/*.py`）は `not_bundled_references` に列挙するだけにしてよいか。起動時に照合できない記録（source_manifest の corpus.sha256・corpus.bytes・frozen_text_sha256 の mekiki-framework-t1-t5.md・baseline_t1_t4_sha256・t5_v3_body_sha256・frozen_html_main_sha256、inputs の外部ファイル4件〔zip 3件と T5_submission_6_20260905.md〕、T4 manifest の translation.html・htmlSha256）は、一覧を記録するだけにしてよいか。節idが HTML に実在するかは、施工段階1で使い捨ての検査として一度だけ確かめて記録する。暫定案：そのとおり | HTML と統合MDは許可一覧にない | source_manifest.json の corpus・html・frozen_*・inputs、T4.en.manifest.json の translation | 提案 |
| 2026-09-18 | 0 | Q12 テスト補助・データ根・ポート | 要確認。改変データを使う D01〜D03 のため、データ根は `corpus.load_corpus(data_dir)` の内部引数としてだけ受け取り、テストが一時ディレクトリのコピーを渡す。app.py は固定の `data/` しか読まず、環境変数や CLI 引数ではデータ根を変えられないようにする（S01 で確認）。`tests/conftest.py`（実物の data/ の前後ハッシュ比較、server マーク）と `tests/_support/` を新設してよいか（SPEC §3 の構成外）。テスト用ポートを環境変数（名前は `MEKIKI_READER_PORT` 案、1024〜65535 の整数、既定 7860）で指定できるようにするか。暫定案：いずれもそのとおり | データ根を外から変えられると、利用者指定の任意パスの入口になる（SPEC §2.2） | SPEC §2.2・§2.9 | 提案 |
| 2026-09-18 | 0 | Q13 data/ に適用するライセンスとその表示 | 要確認（Q83 が前提）。ルートの LICENSE は MIT（コード用）で、同梱コーパスは v3.5.0 で CC BY 4.0 と表示されている。data/ にどのライセンスを適用するか（MIT を及ぼすかを含め、権利者の選択）と、その表示の場所（README の節／ルートに NOTICE を追加／`LICENSES/` に分ける／ルートのライセンスを変える）。暫定案：なし（著者の選択） | ライセンスの選択と適用は著者の判断事項 | mekiki-mcp/LICENSE L1–13 | 提案 |
| 2026-09-18 | 0 | Q14 帰属文と改変の有無の表示 | 要確認。帰属文に CITATION.md L21 の書式を使うか。行を変えずに抜粋して JSON に入れることを、表示上「改変なし」と書くか、「抜粋・構造化あり」と書くか。暫定案：なし（著者の指定を待つ） | コーパス側の CITATION.md L23 が改変の有無の表示を求めている。ライセンス条項がどう適用されるかは判断しない | CITATION.md L19–23 | 提案 |
| 2026-09-18 | 0 | Q15 Space の YAML の license 欄 | 要確認。選択肢：`mit`（data/ の条件は欄に出ない）／`cc-by-4.0`（コードの条件は欄に出ない）／`other`＋license_name・license_link／省略。暫定案：なし（Q13・Q19・Q83 の回答に従う） | SpaceCardData の license は単一の文字列。Spaces の設定リファレンスの項目一覧に license はない | https://huggingface.co/docs/hub/repositories-licenses、https://huggingface.co/docs/hub/spaces-config-reference | 提案 |
| 2026-09-18 | 0 | Q16 応答への license 欄 | 要確認。応答に license・attribution の欄を加えるか（SPEC §4 の改版事項）。暫定案：なし（施工側では欄を加えない） | SPEC §4 に該当する欄がない | SPEC §4 | 提案 |
| 2026-09-18 | 0 | Q17 MIT の著作権者表記 | 要確認。MIT の著作権者は「mekiki-framework」のままでよいか。コーパスの著作者表示は個人名。暫定案：なし（著者が決める） | 著者が決める事項 | mekiki-mcp/LICENSE L3、CITATION.md L15 | 提案 |
| 2026-09-18 | 0 | Q18 T1 本文の別条件の記述 | 要確認。papers/T1.md L359（Data availability 節）に "All materials are licensed under CC BY-NC 4.0." とある。対象の範囲（同梱物に及ぶか）の確認と、README に注記するか、その文面。暫定案：なし（範囲と文面は著者が確かめる） | 検索結果に出たとき、同梱物の条件と取り違えないため | papers/T1.md L355–361 | 提案 |
| 2026-09-18 | 0 | Q19 配置段階二の一式にライセンス文書を含めるか | 要確認。Space にアップロードする一式（SPEC §9）に LICENSE・NOTICE を含めるか。暫定案：含める | SPEC §9 の一式の列挙に LICENSE がない | SPEC §9 | 提案 |
| 2026-09-18 | 0 | Q20 利用者入力の送信先と保存方針 | 要確認。README の開示（SPEC §2.11）の文面。Reader は入力をファイルにもログにも保存しない方針とし、Gradio の標準出力や一時ファイル、Spaces のログに入力が残るかは施工段階3で実測してから起草する。暫定案：実測後に起草して承認を得る（Q89） | verify_quote・check_compressions の入力には未公開の情報が入りうる | SPEC §2.11 | 提案 |
| 2026-09-18 | 0 | Q21 language 引数の意味と既定値 | 要確認。SPEC §5.2・§5.5 は既定を `language="ja"` とするが、T1〜T3・T5 は英語が原文。選択肢：A 既定を None（原文の言語）とし、`en` は T4 の英訳だけを指す。T1〜T3・T5 に `ja` や `en` を指定したら invalid_input／B 引数を `edition` に変え、値を "original" と "en_translation" にする／C SPEC のまま `"ja"` を「原文」の意味に読み替える（返す language 欄は en になる）。暫定案：A（SPEC の改版が必要） | 既定値のままでは、英語の原文や claims の英語引用を照合する経路の意味が曖昧になる | 上の「論文の本文言語」行 | 提案 |
| 2026-09-18 | 0 | Q22 言語の値の出典 | 要確認。選択肢：A `corpus.py` に版つきの固定表 LANG（T1〜T3・T5=en、T4=ja）を置き、根拠を本ファイルに書く／B metadata.json を同梱する（T1〜T3 の記録はそれでもない）／C 起動時に文字種で判定する（推定になる）。ガイド類（FOR_AI_READERS.md は英文に日本語の用語を含む）に付ける language の値も決めたい。暫定案：A。ガイド類は en | 構造化された言語の欄は T4 manifest（originalLanguage=ja、inLanguage=en）だけで、T1〜T3・T5 を明記したものはない | source_manifest.json に lang 系のキーはない | 提案 |
| 2026-09-18 | 0 | Q23 T07「凍結定式二本」の同定 | 要確認。同梱予定ファイル中の「定式」は papers/T4.md 33・124行の「定式化」2件だけ（同梱しない統合MDと T4.html にも同文が各2件）で、「凍結」は0件。「凍結定式」や二本の定式を名指す語はない。候補：A T5.md 13行 "AI can deliver the state of affairs; it cannot deliver the fact of participation."（t5-abstract）と223行 "AI can assist play. It cannot take one's place in it."（t5-5-4）。どちらも T5.md に1回ずつ現れ、コーパスの validate_corpus.py が protected sentence として扱う／B THEORY_MAP.md 253・254行の日本語 Short form と Long form（どの論文 MD にもない）／C 別の二本（文字列と照合先を指定してほしい）。暫定案：決め打ちしない。回答があるまで T07 の期待値は作らない | T07 は施工段階2の完了条件で、照合範囲（Q24）の決定と連動する | 許可16ファイルの検索：「定式」2件（T4.md:33・124）、「凍結」0件、「frozen」は source_manifest.json のキー名だけ／tools/validate_corpus.py L49–51（読んだだけ）／THEORY_MAP.md L247–256 | 提案 |
| 2026-09-18 | 0 | Q24 verify_quote の照合範囲 | 要確認。選択肢：論文 MD だけ／論文＋英訳（language=en のときだけ T4.en.md を加える）／さらにガイド類も（source_kind で分ける）／`scope` 引数を設ける。ガイド類を含めると、Q23 の案Aの2文はどちらも複数一致になる（1文目は THEORY_MAP.md 163・256行にも、2文目は FOR_AI_READERS.md 71行にもある）。暫定案：論文＋英訳。Q21 案A と揃え、paper_id=None のとき language=None は論文5本の原文、language=en は T4.en.md だけ、language=ja は invalid_input（T4 だけの原文を指したい場合は paper_id=T4 を使う）。Q23 が B なら見直す | SPEC §5.5 は照合範囲を明記していない。原文と派生物を分ける方針（SPEC §2.1）にかかわる | 出現回数の集計 | 提案 |
| 2026-09-18 | 0 | Q25 T4 英訳と「著者承認済み」 | 要確認。T4 英訳は ChatGPT で作成され、著者のレビューを認証する記述はない。これは SPEC §2.1 の「著者承認済みの読解補助」に当たるか。当たらない場合、SPEC §3 の許可はそのまま維持し、英訳の結果すべてに manifest の preparation と authority を添える運用でよいか。暫定案：後者の運用 | SPEC §2.1 と §3 が緊張関係にある。コーパス側の MAINTENANCE.md L48 は「ビルドが通ったことから承認を推定しない」としている | T4.en.manifest.json の preparation "…no separate author-review certification is asserted" | 提案 |
| 2026-09-18 | 0 | Q26 訳注の切り出しとマーカー行 | 要確認。訳注16件（`<details class="translation-note" id="tn-NN">`〜`</details>`、各6行）は英訳 unit の行範囲の内側にある。選択肢：行で分けて translation_note の別の結果にする／範囲をそのまま返して訳注の位置を注記する／訳注を返さない。範囲内のマーカー行（`<!-- t4-source-unit:N -->`、`<a id>`、「[Japanese source: …]」）を translation の結果に含めるか。暫定案：別の結果に分ける。マーカー行は行を改変しないので含める | T12（翻訳・訳注を別の種別にし、原文への帰属を偽らない）の実装方法が決まらない。manifest に訳注の位置はない | TN01 は37–42行で、unit 19（30–44行）の内側にある | 提案 |
| 2026-09-18 | 0 | Q27 ja↔en の位置対応と英訳の枠部分 | 要確認。対応は sourceLine を source_manifest の節範囲に当てて決めてよいか（unit.section は、t4-notes の範囲の6単位と t4-references の範囲の31単位〔書誌28・見出し・末尾の英文要旨2〕の計37単位で '6'、前付けの3単位で null になっており、manifest と食い違う。separator と wrapper には section キーがない）。英訳にしかない1〜22行（翻訳の告知・方針・Terms at a glance）と1098〜1105行を get_section で返すか。返すならどの ID で返すか。暫定案：sourceLine で決める。枠部分は別の ID で明示的に要求されたときだけ返し、英訳の由来は常に添える | SPEC §5.2「日本語原文への位置情報を添付」の実装規則 | unit.section と manifest の不一致の集計 | 提案 |
| 2026-09-18 | 0 | Q28 英訳の source.corpusVersion=3.2.1 | 要確認。manifest の source.corpusVersion は "3.2.1"。選択肢：記録どおり別の欄で返し、「記録された source.sha256 が同梱の papers/T4.md と一致する」という同梱データで確かめられる事実だけを補足する／返さない。版どうしの比較（3.2.1 と 3.5.0 で同じ blob であること）は本ファイルの記録にとどめ、応答には出さない。暫定案：前者 | 記録を改変しない。compare_versions（SPEC §11）に近づかない | 施工時の確認：papers/T4.md は v3.2.1 と v3.5.0 で同じ blob `42c943d0…` | 提案 |
| 2026-09-18 | 0 | Q29 get_reading_guide の part | 要確認。FOR_AI_READERS.md には明示のアンカーがない。選択肢：見出しにもとづく固定の列挙（`all`・`interpretation`・`core-terms`・`japanese-terms`・`t4-languages`・`modes`・`mode-1`〜`mode-4`・`boundaries`）／build_access の規則で slug を自動生成する／水準2の見出しだけで粗く分ける。未知の part は invalid_input。暫定案：固定の列挙（規則 GUIDE として版を付ける） | 行範囲は起動時に見出しの位置から再計算して照合できる | FOR_AI_READERS.md の見出し走査（73行） | 提案 |
| 2026-09-18 | 0 | Q30 主張レコードの欠けたキーと SPEC 外のキー | 要確認。`additional_source_quotes` は11件中6件でキー自体がない。`author_answerable` は11件すべてにない。選択肢：欠けた欄は null（未記録。[] で「追加根拠なし」とは言い切らない）とし、最上位の SPEC 外のキー（id・claim・footnote。footnote は N3 以外では null）は保持し、source_locator は中身（section_url・quote_sha256・canonical_doi、N3 の footnote_url など）ごと保持する／欠けた欄を [] にする／欠けたキーは出さない。`claim` は「台帳の要約で、逐語の引用ではない」と表示する。台帳全体の editorial_status と source_role は、出典（json_pointer）付きで返す（Q38⑨）。暫定案：前者 | 推定で埋めない（SPEC §2.8）。欄が件ごとに変わると M01 のスキーマ照合と相性が悪い | claims/t5.json のキー集計 | 提案 |
| 2026-09-18 | 0 | Q31 「四つの身分」の指す内容 | 要確認。SPEC §2.8 の「四つの身分」とは何か。claims の status は重複のない11種の文字列で、コーパスの分類（THEORY_MAP.md L326・llms.txt L7）は五区分。Reader は status を逐語で返し、区分や集約の欄を作らない方針でよいか。暫定案：その方針 | 推定で区分を当てると「統合しない」に反するおそれがある | claims/t5.json の status 11種 | 提案 |
| 2026-09-18 | 0 | Q32 get_claim_record の細部 | 要確認。①claim_id の形式（案 `^T[1-5]-[A-Z]+[0-9]+$`）と、論文IDだけ（例 "T2"）を渡した場合の状態。②T1〜T4 の判定は claim_id の接頭辞で行う。③query の照合規則（Q92）と、ゼロ件を no_lexical_match とすること。query の経路では limitations に「台帳は T5 のみ」を常に入れる。④ledger_not_available のときの「関連原文の候補」は、candidates に出典付きの節だけを入れ、別経路の案内文は limitations に置く。節一覧で足りるか。暫定案：①〜④のとおり | candidates は「出典付きの語句上の近接候補」なので、案内文を混ぜない（SPEC §4） | SPEC §5.4 | 提案 |
| 2026-09-18 | 0 | Q33 論文に属さない結果の DOI・URL | 要確認。選択肢：canonical_doi は null、source_url は Pages の URL（フラグメントは実在する id に限る）、snapshot_url は `https://raw.githubusercontent.com/mekiki-framework/mekiki-framework.github.io/<commit>/<path>`／GitHub の blob URL に `#Lx-Ly` を付ける／関連論文の DOI を付ける。source_kind ごとの canonical_doi の値の表は Q88。暫定案：前者 | DOI は論文の学術的引用先で、ガイド類には付けない。Pages は main を配信するので、固定の参照先は snapshot_url | raw の SHA URL は HTTP 200 で、内容がバイト一致。Pages の T1.html も現時点では v3.5.0 と一致 | 提案 |
| 2026-09-18 | 0 | Q34 親見出しの子節ID と本文 | 要確認。選択肢：直下の子だけ／子孫すべて。親は「直前にある、自分より水準の小さい節」とする（T4 は水準1の直下が水準3で、飛びが6か所ある）。親節の記録範囲には、見出し行と空行だけのもの（例 T1 t1-2 は46–47行）と、前付け・要旨・導入文を含むもの（13件。例 paper-t4 の1–24行）がある。`heading_only` は「範囲内の空でない行が見出し行だけ」と定義する。暫定案：直下の子だけ | SPEC §5.2「親見出しは記録範囲のみ＋子節IDを提示」 | source_manifest.json の sections（キーは id・title・line_start・line_end・level の5つで、親子のキーはない）の走査 | 提案 |
| 2026-09-18 | 0 | Q35 unknown_id の近傍候補と形式違反 | 要確認。同じ論文のアンカーを（共通接頭辞の長さ↓、編集距離↑、manifest の順↑）で並べ、上位5件を返す。論文が未登録なら5本を返す（規則 NEAR として版を付ける）。ID の形式（`^[A-Za-z0-9._-]{1,128}$`）に合わない入力のうち、パスや URL の形でないもの（例「4.2節」「§3.1」）を、invalid_input にするか、unknown_id と近傍候補にするか。暫定案：前者の規則。形式違反は、パスや URL の形なら invalid_input、それ以外は unknown_id と近傍候補 | SPEC §5.2「未登録→unknown_id と実在する近傍候補」 | SPEC §5.2 | 提案 |
| 2026-09-18 | 0 | Q36 check_compressions のゼロ件 | 要確認。一致ゼロのときと、承認済みパターンが0件のときの状態。選択肢：ok で results は空にし、limitations に契約文と「承認済みパターン0件」を書く／別の状態を設ける（SPEC の改版が必要）。暫定案：前者 | SPEC §4 の状態に該当するものがない。該当ゼロは正しい読解の証明ではない（SPEC §5.6） | SPEC §5.6 | 提案 |
| 2026-09-18 | 0 | Q37 パターン候補の起草者と記録形式 | 要確認。SPEC §10 により、パターン候補の起草は Claude（最終検査）、承認は著者の役割で、施工側では起草しない理解でよいか。記録形式（語形・版・関連原文の locator・承認日）と、各パターンに対応づける関連原文（source_excerpt）も承認の対象にするか。T11 用の試験パターンを tests/fixtures に置き、テストから内部関数の引数としてだけ注入してよいか（環境変数や本番の patterns.py からは入れない）。暫定案：そのとおり | 承認前の patterns.py は空（CLAUDE.md 絶対規則9）なので、そのままでは T11 を検証できない | SPEC §5.6・§10 | 提案 |
| 2026-09-18 | 0 | Q38 応答スキーマの細部 | 要確認。①source_id の形式（案 `<path>#<fragment>`）。②limitations の形式（案 `"CODE: 本文"` の文字列。Reader 自身の注意書きだけを置く）。③規則の版の示し方（案：limitations に `RULES:` 行）。④曖昧さの表示（案 `AMBIGUOUS: total=n`）。⑤読み方の雛形の置き場（案：results の外の追加欄 `templates`。SPEC §4 にない欄）。⑥監査用メタデータ（案：初版では出さない）。⑦SPEC §2.1 の資料種別7種と §4 の source_kind 7値の対応表（SOURCE_INDEX・llms.txt・T5_CLAIM_STATUS の種別を含む）と、派生物であることの表示（案 `derivative_of`）。⑧check_compressions の結果は、source_excerpt 側を出典欄に置き、入力中の位置は payload に置く。⑨コーパス由来の文（manifest の description、台帳の editorial_status など）は、出典付きで結果の payload か専用の欄に置き、limitations には入れない。⑩結果の本文と付随情報（text・excerpt・match_via・original_locator・diffs など）を入れる payload 欄（SPEC §4 の「各出典付き結果」にない欄）。暫定案：①〜⑥・⑧〜⑩は案のとおり。⑦は表を起草して承認を得る | SPEC §4 は欄の名前だけを定めている。SPEC §2.4 は結果ごとの出典を求める | SPEC §2.1・§2.4・§4 | 提案 |
| 2026-09-18 | 0 | Q39 prompts の三つの雛形の文面 | 要確認。施工側が SPEC §6 から起草し、著者が承認する。三つとも「利用者が明示的に選んだときだけ使い、接続先の上位規則や利用者の明示的な意図を上書きしない」という定型文を含める。暫定案：そのとおり | SPEC §2.6 | SPEC §6 | 提案 |
| 2026-09-18 | 0 | Q40 試験用テキストの文面 | 要確認。S02 の命令風テキストと E02 の相談例（いずれも架空で、非公開の情報を含まない）は、施工側が起草して著者が承認し、tests/fixtures/ に置く。暫定案：そのとおり | 公開原文には足さない（CLAUDE.md 絶対規則8） | SPEC §7 S02・E02 | 提案 |
| 2026-09-18 | 0 | Q41 正規化：空白類 | 要確認。選択肢：A1 空白類の畳み込みだけ／A2 A1 に加えて、両隣が CJK の空白の並びを削除する（判定は写像する前の元の文字で、明示のコードポイント範囲で行う）／A3 空白をすべて削除する。照合の単位は行とし、行をまたぐ一致は認めない（論文は実質1段落1行で、claims と reading_cases の引用32件はすべて1行内。原文の行をまたぐ引用は quote_not_found とし、limitations に書く）。暫定案：A2 と行単位（付録B-1） | 参考値：写像前に判定する形に直した試作で、A2 は日本語引用への空白・改行の挿入149通りをすべて回復し、改変97件の誤一致は0件。A1 は0/149。A3 は97件中33件が誤一致 | 空白類の出現（論文5本・THEORY_MAP・T4.en）は U+0020 と U+3000（T4.md の4件）だけ。行内で両隣が CJK の空白は T4.md の3件（15行の U+3000 2件、221行の U+0020 1件） | 提案 |
| 2026-09-18 | 0 | Q42 正規化：全角と半角 | 要確認。選択肢：B1 全角英数だけ／B2′ U+FF01–FF5E から除外集合（， ． － ＋ ＜ ＝ ＞ ～）を除いたものを ASCII にする／B2′ に半角カナの明示表を加える／B3 NFKC（数字・負号・比較記号まで変わり、Unicode の版にも依存するので非推奨）。暫定案：B2′＋半角カナを明示表で実装し、NFKC は使わない | 参考値：除外しない場合、「75．6」「－0.26」「＝」「200，000」が誤って一致した | 全角形の出現（論文5本・THEORY_MAP・T4.en）は ，918・（）167組・：24・／2・ＳＤＧｓ・？2・＝1。全角数字・．・－・～は0件 | 提案 |
| 2026-09-18 | 0 | Q43 正規化：句読点と数字の保護 | 要確認。選択肢：c-i 日本語の句読点どうしだけ（{、，､}・{。．｡}）／c-ii ASCII も含めて同一視し（{、，､,}・{。．｡.}）、元の文字の両隣が数字（ASCII と全角の明示表）なら写像しない／c-iii 変換しない。数字の保護の範囲。案：すべての句読点で両隣が数字なら写像しない。加えて「.」「．」だけは、直後が数字なら写像しない（先頭の0を省いた小数 .05 型。現行の論文本文に0件。副作用として DOI や「Vol.18」などの書誌表記29か所が対象外になる）。「直後が数字」の保護を読点や「。」にまで広げると、T4.md の「，」44件・「。」11件と T4.en.md の「，」27件（例 T4.md:33「，2003年」）が正規化の対象から外れるので採らない。暫定案：c-ii とこの保護。保守的にするなら c-i | 論文 MD の「、」は0件（T4 本文は「，」と「。」だけ）。同梱ファイル全体では THEORY_MAP 2・reading_cases.json 53・AI_READING_TESTS.md 60 で、日本語の設問は「、」を使う。数字の保護がないと「4。1節」「200、000」が一致してしまう | T1.md:159・167、T2.md:139・196、T4.md:55・245・247 | 提案 |
| 2026-09-18 | 0 | Q44 正規化：引用符・かぎ括弧・ダッシュ | 要確認。これらを SPEC の「句読点」に含めるか。選択肢：d-0 含めない／d-i 曲線引用符（‘’→'、“”→"）だけ／d-ii d-i にかぎ括弧どうしを加える（T4.md:220–221 では『』が書名に使われるので推さない）／d-iii d-i にダッシュ類を加える。暫定案：d-i | 論文 MD は、T1.md 337・341行の ’ 2件を除いて直線引用符（T1.html も同じ）。’ を使う入力では、アポストロフィを含む claims 引用17件中10件が不一致になる | 参考値：d-i で回復16/16、誤一致0/97 | 提案 |
| 2026-09-18 | 0 | Q45 正規化：比較記号・負号の全角形 | 要確認。SPEC の「小数点・負号・比較記号は対象外」は、全角形（＜ ＞ ＝ －）と半角形の同一視も禁じるという意味か。暫定案：全角形も含めて一切変換しない | 同一視すると「－0.26」と「-0.26」が一致する | ＝ は T4.md:93 の1件、≤ は T1.md:181 の1件、負号は T2.md:103 の ASCII「-」 | 提案 |
| 2026-09-18 | 0 | Q46 Markdown 記法と HTML からのコピー | 要確認。Pages の HTML からコピーした引用（強調記号がなく、脚注が番号になっている）をどう扱うか。選択肢：SPEC のまま quote_not_found と語句上の近接候補を返し、limitations に明記する／表示用テキストの索引を作る（SPEC の改版が必要）／強調記号の除去だけを加える。暫定案：初版は SPEC のまま | SPEC の許す正規化（空白・全角半角・句読点）の範囲外。claims の T5-T1 は `*agent-relative*` を含む | T4 の `[^b12]` は HTML では `<sup>16</sup>` になる | 提案 |
| 2026-09-18 | 0 | Q47 入力側の NFC 合成 | 要確認。NFD の入力（例：分解された濁点）を、入力側だけ NFC に合成するか。採用する場合の実装（明示の合成表か、`unicodedata.normalize('NFC')` を Unicode 版への依存の例外として認めるか）。暫定案：なし（著者の判断） | コーパスは全ファイル NFC 済みで、結合文字は0件 | `unicodedata.is_normalized('NFC')` が全ファイルで True | 提案 |
| 2026-09-18 | 0 | Q48 normalization_applied の置き場と曖昧さ | 要確認。外枠の normalization_applied は、全結果に適用した規則IDの和集合（整列済み）とし、結果ごとの変換（位置・入力の字・原文の字、件数に上限あり）は payload.diffs に置く案でよいか。完全一致が1件あり、句読点だけが違う箇所も別にある場合、後者を candidates に出すか。quote_not_found のときの近接候補の規則は Q92。暫定案：上記の置き方。後者の扱いは規則に明記し、T10 で試す | SPEC §5.5 は normalization_applied を外枠の欄とし、「複数箇所に同じ短文→全候補」とする | SPEC §5.5 | 提案 |
| 2026-09-18 | 0 | Q49 規則の版番号の体系 | 要確認。対象は NORM・SEARCH・CAND・TERMS・PATTERNS・PROMPTS・SCHEMA・JSON・LINES・LANG・SECTION・NEAR・GUIDE・T4MAP・LIMITS・BUNDLE。選択肢：MAJOR.MINOR.PATCH の意味つき版／整数の連番／意味つき版に、表の正準 JSON の SHA-256 を加える。暫定案：意味つき版＋表のハッシュ。schema_version とは別に上げる（本ファイルの付録ではこの形で仮の版を書く） | Codex の独立検査で、表が同一かを機械的に確かめられる | CLAUDE.md 作法「規則に版番号を付ける」 | 提案 |
| 2026-09-18 | 0 | Q50 検索：語句の分割方式 | 要確認。選択肢：a 日本語は文字 bigram、英語は単語／b 文字種で切り、ひらがなを捨てる（残すと「の」「と」で雑音が大きい）／c 空白・句読点で分けた断片を部分文字列として照合する／d c の英語断片を単語境界での照合に変え、版つきの用語対応表を加える／形態素解析器（決定的だが数十MBの辞書に依存する）。暫定案：d。承認前は対応表が空で、「c＋英語の単語境界」として動く。形態素解析器は入れない（付録B-2） | 参考値：クエリ11件で c・d は雑音が出なかった。a の OR では non-transferability で雑音28行。日本語の論文は T4 だけ | 参考値の集計（使い捨て） | 提案 |
| 2026-09-18 | 0 | Q51 検索用の正規化 | 要確認。選択肢：NFKC＋casefold／NORM の明示表（WS・WIDTH・QUOTE-CURLY）と ASCII の小文字化。CJK でも ASCII でもない文字（—・アクセント付き文字など。’ は QUOTE-CURLY で ' になり ASCII の断片に入る）を含む断片の照合規則（案：部分文字列）。検索では、空白と区切り文字での分割を正規化より先に行い、WS-CJK は使わない（「尊厳 承認」が「尊厳承認」に結合されるのを防ぐ）。暫定案：後者の正規化と、その断片の部分文字列照合。原文の位置へは区間の対応表で戻し、起動時に抜粋・一致位置が原文と一致することを確かめる | Unicode の版（Python の minor 版ごとに違う）に依存させず、R01 を保つため | Python 3.14 の unidata は 16.0.0、3.9 は 13.0.0 | 提案 |
| 2026-09-18 | 0 | Q52 用語対応表の出典・承認・置き場 | 要確認。選択肢：著者承認分だけにし、初版は空にする／許可ファイルから候補を機械的に抽出し、著者が承認する（THEORY_MAP.md L232〜・L245〜、SOURCE_INDEX.md L20〜38、T4.md の「日本語（English）」形式〔正規表現の一致26件：本文23・要旨とキーワード2・参考文献1。英語表記10種。日本語側の語の境界は手で確かめる〕、T1.md L58 など。各項目に出典の行を付ける）／T4.en の訳注16件も使う（ChatGPT 作成）／metadata.json（許可一覧外なので使わない）／対応表を置かない。置き場は `mekiki_reader/terms.py` の新設（SPEC §3 の構成外）か、tools.py 内の定数か。暫定案：抽出した候補を著者が承認し、初版は空。置き場は terms.py | 許可ファイルに独立した用語集や日英対訳表はない。E01 の日本語の問いは、英語の論文に語句としてほとんど一致しない | SPEC §5.3 は承認者を定めていない／T4.md に `([぀-ヿ一-鿿]+)（([A-Za-z][^）]*)）` をかけて26件 | 提案 |
| 2026-09-18 | 0 | Q53 対応表の意味の範囲 | 要確認。選択肢：コーパスが自ら示す対訳と表記揺れに限る／概念レベルの対応（例 外化↔externalization、参加↔participation）も入れる（SPEC §11 が外す意味検索に近づくおそれがある）。どちらの場合も、各結果に一致の経路（`match_via`: `query` か `term_map:<id>`）を返す。暫定案：match_via は必ず返す。範囲は著者の判断 | 語句上の対応であって、意味の一致ではないことを示すため | SPEC §11 | 提案 |
| 2026-09-18 | 0 | Q54 英語の照合単位と表記揺れ | 要確認。選択肢：ハイフンを含む単語の完全一致にし、揺れは対応表に列挙する／前方一致／部分文字列／英綴り・米綴りの汎用規則。暫定案：一つ目 | 部分文字列では art が174行、play が display などを含めて73行一致する。T1 は英綴り（externalisation 102回）、T2〜T4 は米綴り | 論文 MD の計数 | 提案 |
| 2026-09-18 | 0 | Q55 語の結合と状態 | 要確認。選択肢：全語一致だけ／OR で順位付け／全語一致を results、一部一致を candidates に入れ、全語一致が0件なら no_lexical_match とする。暫定案：最後の案。SPEC §2.7 の「ゼロ件」の定義と整合するか確認したい | 参考値：自然文をそのまま入れると、OR では論文879行の大半が一致し、全語一致では0件になる | R01〜R03 の設問での試算 | 提案 |
| 2026-09-18 | 0 | Q56 入力の上限 | 要確認。案：query は正規化後200字・断片8個まで。ひらがなだけの断片は捨て、断片が0個になったら invalid_input。超えたら invalid_input とし、切り詰めない。verify_quote と check_compressions の text は2000字まで（verify_quote の最小長と結果数は Q84）。claim の query は search と同じ。英語の停止語表を置くか。暫定案：上記のとおり（規則 LIMITS）。停止語表は著者の判断 | 計算量を有限にする（SPEC §2.10）。読解試験の設問は最長165字（en） | tests/reading_cases.json の設問の長さ | 提案 |
| 2026-09-18 | 0 | Q57 検索の単位 | 要確認。選択肢：行／空行で区切ったブロック／manifest の節／行で照合して節ごとにまとめる。暫定案：行。各結果に section_anchor と get_section への経路を付ける | 論文は実質「1段落＝1行」（空でない行は879行） | 論文 MD の計数 | 提案 |
| 2026-09-18 | 0 | Q58 検索の範囲 | 要確認。paper_id=None のとき、論文の原文だけにするか。T4 英訳の本文・訳注・案内文書（THEORY_MAP・SOURCE_INDEX・FOR_AI_READERS）を加えるか。参考文献の節を含めるか。暫定案：論文の原文だけで、参考文献も含める | SPEC §5.3 の引数に language がなく、範囲も明示されていない | SPEC §5.3 | 提案 |
| 2026-09-18 | 0 | Q59 検索の順位と同点処理 | 要確認。選択肢：A 語の種類数↓→総出現数↓→論文順↑→行番号↑／B A に「直接一致（対応表を経由しない）を優先」を加える／C 出現密度を使う／D 論文ごとに1件ずつ取る。スコアは順位の鍵と順位番号で返し、確率にはしない。暫定案：B | 参考値：単一語のクエリでは k=5 の境界で同点群が大きく（最大34）、同点処理が表示順を実質的に決める | 参考値の集計 | 提案 |
| 2026-09-18 | 0 | Q60 k と抜粋の幅 | 要確認。k の範囲：1〜20（範囲外は invalid_input）／1〜50／範囲外は丸める。抜粋：最初の一致の前後±100字／±60字／±150字。一致位置を上限付きで全件並べるか。暫定案：k は1〜20・既定5、抜粋は±100字、一致位置は上限付きで全件 | 論文の行の長さの中央値は124〜258字、最大は2681字 | 論文 MD の計数 | 提案 |
| 2026-09-18 | 0 | Q61 言語差の注意書き | 要確認。「T1〜T3・T5 は英語の原文、T4 は日本語の原文。語句の照合であり、ゼロ件は記述がないことを意味しない」を、いつ limitations に出すか。選択肢：常に／日本語を含むクエリで英語の論文が範囲に入るとき／no_lexical_match のときだけ。暫定案：二つ目と三つ目の両方 | 「尊厳」「知好楽」は、対応表なしでは論文で0件になる | 論文 MD の計数 | 提案 |
| 2026-09-18 | 0 | Q62 採用する Gradio の版 | 要確認。選択肢：6.27.0（2026-09-11、最新）／6.26.0（2026-08-24）／6.23.1（2026-08-11）／5.50.0（5.x の最終版。mcp==1.10.1 に固定され、2026-02 公開の勧告の修正版が 5.x にないので非推奨）。暫定案：6.27.0。`launch(run_history=False)` を必須にする（6.27.0 の run_history は、トークン付きの要求を受けると HF Hub と通信する経路 `/gradio_api/run-history/*` を登録する）。次点は 6.26.0。施工段階3の着手時に PyPI を取り直して再比較する | MCP のコードは 6.23〜6.27 でほぼ同じで、最新のセキュリティ修正を取れる。動作は未確認（インストールも実行もしていない） | `curl -s https://pypi.org/pypi/gradio/json` → version 6.27.0、requires_python ">=3.10"、分類子 3.10〜3.13（2026-09-18 再確認）／gradio[mcp] 6.27.0 は `mcp>=1.21.0,<2.0.0` と `pydantic>=2.11.10,<=2.12.5` を要求（mcp の最新は 2.2.0 だが除外され、1.x の最新は 1.30.0）／付録C-2 | 提案 |
| 2026-09-18 | 0 | Q63 ツールの戻り値の形式 | 要確認。選択肢：JSON 文字列（`-> str`、直列化規則 JSON）／dict（Gradio が `str(output)` で Python の repr にする）／`gr.mcp.tool(structured_output=True)`（structuredContent は `{"result": …}` で、outputSchema も付かない）。暫定案：JSON 文字列 | R01 と M01 を検査しやすい | gradio@6.27.0 gradio/mcp.py L1578 `TextContent(text=str(output))`（読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q64 prompts/get の名前照合 | 要確認。gradio@6.27.0 のコードを読んだ限り、prompts/get は名前が一致しないとき、エンドポイント一覧（named_endpoints の順）の最後の要素を実行すると読める。また Spaces では prompts/list の名前に接頭辞が付き、照合に使う名前と一致しない（いずれも未再現。M02 で確認）。選択肢：そのまま使い、M02 の結果を記録する／最後に例外を投げる番兵関数を登録する／サーバ実装を継承して差し替える／上流に知らせる（公開 issue か非公開の報告かを含め、外部への投稿なので著者が判断する）。README に書くのは M02 で再現してから。暫定案：配置段階一ではそのまま使って M02 で確かめ、配置段階二の前に判断する | 上流の該当コードは 6.27.0 と main で同じで、既存の issue は見つからなかった | gradio@6.27.0 gradio/mcp.py L554–577・L1010–1071（読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q65 同時実行と超過時の返し方 | 要確認。選択肢：`queue=False` とアプリ側のセマフォ（`max_threads` も併用）／`queue=True` と concurrency_limit・max_size。上限を超えたときは、結果データではなく通信層（MCP の isError か HTTP 429/503）で返し、SPEC §4 の status に混ぜない。部分的な結果は返さない。R01 は過負荷のない条件で行う。処理時間の上限は Q85。暫定案：queue=False とセマフォ | 負荷によって結果データが変わると R01 と衝突する（SPEC §2.3 は所要時間を監査用メタデータとして分離する） | gradio@6.27.0 mcp.py L782–815（読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q66 Gradio 標準の経路 | 要確認。UIコンポーネントがなくても登録される経路のうち、守則に関わるもの：①`/gradio_api/file=<http URL>`（6.20 以降、コードを読んだ限りではサーバ自身が外部 URL を取得する）。②`POST /gradio_api/upload`（max_file_size を指定しなければ上限がなく、一時ディレクトリに書き込む）。③`/gradio_api/proxy=`。④`/` のフロント HTML。⑤巨大な本文。⑥Host ヘッダ：gradio@6.27.0 は mcp の StreamableHTTPSessionManager を security_settings なしで生成しており、mcp 1.30.0 はその場合 DNS rebinding 保護を有効にしない。Gradio の CustomCORSMiddleware は Host を CORS 応答の判定に使うだけで、要求は拒否しない（いずれもコードを読んだだけで、実際の動作は未確認）。案：ASGI ミドルウェア（launch の app_kwargs）で①②③を拒否し、Host を 127.0.0.1／localhost に限る。④は開示する。S01・S03 で検証する。遮断できない場合は、守則 §2.2・§2.10 に反するので実装を止めて報告し、SPEC の改版か版の選び直しを著者が判断する（「受け入れて開示する」は採らない）。⑥が実際に再現した場合に上流へ非公開で報告するか（GitHub の Report a vulnerability。外部への投稿なので著者が判断）。再現と報告の状況を著者が確かめるまで、⑥を README に書かない。暫定案：この案 | CLAUDE.md「守則に反する実装が必要になったら、実装せず報告する」。上流の SECURITY.md は脆弱性の疑いを非公開で報告するよう求めている | gradio@6.27.0 routes.py L1191–1197・L1931–1963、route_utils.py L1062–1071・L1392–1452、mcp.py L391–393／mcp 1.30.0 server/transport_security.py L47–50（いずれも読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q67 server_name | 要確認。ローカルでは常に `server_name="127.0.0.1"` を明示し、環境変数（GRADIO_SERVER_NAME など）では変わらないようにする（S01 で確認。GRADIO_* 全般は Q93）。配置段階二の bind 先と切り替え条件は、Spaces の環境変数を実測してから決める。暫定案：そのとおり | 環境変数一つで非 loopback に bind すると、SPEC §2.10 に反する | gradio@6.27.0 http_server.py L33・L112（読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q68 型の誤りの返し方 | 要確認。選択肢：厳密な型ヒント（int・Literal。違反は mcp SDK の検証で isError になり、JSON の外枠を通らない）／str で受けてアプリ側で検証する（invalid_input）／混在（k は int、language と part は str）。暫定案：混在。どちらで返るかを README に書き、M03 で両方の経路を試す | 通信断とは区別して返す（SPEC §7 M03） | mcp 1.30.0 server/lowlevel/server.py L531–538（読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q69 Spaces でのツール名の接頭辞 | 要確認。Spaces ではツール名が `<Space名>_list_papers` のように変わる。選択肢：受け入れて README に併記し、M01 は接頭辞を除いて照合する／回避する（内部の挙動に依存するので非推奨）。暫定案：受け入れる | 上流の仕様 | gradio@6.27.0 mcp.py L384–385（読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q70 resources の URI と MIME | 要確認。12件（llms.txt・FOR_AI_READERS.md・THEORY_MAP.md・SOURCE_INDEX.md・papers/T1〜T5.md・translations/T4.en.md・AI_READING_TESTS.md・claims/t5.json）を、引数なしの関数に静的な URI を一つずつ付けて登録し、テンプレート変数は使わない（案 `mekiki://v3.5.0/<固定パス>`）。MIME は .md が text/markdown、llms.txt と claims/t5.json が text/plain（application/json にすると Gradio は戻り値を base64 として扱う）。説明文は docstring から作られる（デコレータの description は使われない）ので、AI_READING_TESTS に「公開17問・採点には使わない」を docstring で示す。暫定案：そのとおり | URI にテンプレート変数を置くと、任意のパスの入口になる（SPEC §2.2） | gradio@6.27.0 mcp.py L893–1008・L1588–1640（読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q71 対応クライアントの範囲 | 要確認。SPEC §8 の検収と M02 で対象にするクライアントはどれか：Claude Code／Claude Desktop／ChatGPT 開発者モード。暫定案：なし（SPEC §10 で著者が判断する事項） | SPEC §10 | SPEC §8・§10 | 提案 |
| 2026-09-18 | 0 | Q72 Claude Desktop の橋渡し | 要確認。Claude Desktop が HTTP に直結できない場合、`mcp-remote` を npx で取得して実行してよいか（npm からの取得と実行を伴う）。使う版を固定するか（最新は 0.14.2 で、必要な Node の版は記載がない）。手元の Node は 24 系で、Node 24 の通常サポートは 2026-10-20 まで。暫定案：許可が出れば版を固定して使い、動作を記録する | 外部からの取得を伴うので許可が要る | https://registry.npmjs.org/mcp-remote/latest、https://endoflife.date/api/nodejs.json | 提案 |
| 2026-09-18 | 0 | Q73 ChatGPT 開発者モード | 要確認。ChatGPT への接続は配置段階二（Spaces）まで待つか。配置段階一で Secure MCP Tunnel を使うか（外向きの通信と認証を伴う）。暫定案：配置段階二まで待つ（施工段階4の完了条件との関係は Q91） | ローカル URL へは直結できない（SPEC §8）。Tunnel は SPEC §2.10 の loopback の方針と緊張する | SPEC §8 | 提案 |
| 2026-09-18 | 0 | Q74 Python の minor 版 | 要確認。ローカルと Spaces で同じ minor 版にそろえる（Unicode の版が minor ごとに違うため）。選択肢：3.12（gradio の分類子にあり、公開ビルドも 3.12。参考値：公開 Gradio Space の標本8000件で宣言が最多〔付録C-3〕。すでにセキュリティ修正のみで EOL 2028-10。Unicode 15.0.0）／3.13（gradio 6.27.0 と mcp 1.30.0 の分類子にある版の中で EOL が最も遅い 2029-10。ただし通常のバグ修正は 3.13.16〔2026-10-06 予定〕で終わる。audioop-lts が依存に加わる。Unicode 15.1.0）／3.14（手元にある Homebrew の 3.14 系がそのまま使える。EOL 2030-10。gradio の分類子にはなく、上流 CI は 3.10 だけ。gradio/utils.py:1077 で DeprecationWarning が出る。Unicode 16.0.0）／3.10・3.11（非推奨。3.10 は EOL 2026-10）。暫定案：3.13。導入をしない方針なら 3.14、Spaces での実績を最優先するなら 3.12 | 手元の既定の python3 は gradio の要件（>=3.10）を満たさない。gradio[mcp]==6.27.0 の C 拡張依存13件は、cp312・cp313・cp314 のいずれも macOS arm64 と manylinux x86_64 の wheel が PyPI にある（メタデータで確認、ダウンロードはしていない） | https://devguide.python.org/versions/（3.10 EOL 2026-10、3.12 EOL 2028-10、3.13 EOL 2029-10、3.14 EOL 2030-10）／PEP 719（3.13.16 が最後の定期バグ修正版）／https://pypi.org/pypi/gradio/6.27.0/json／https://pypi.org/pypi/mcp/1.30.0/json（分類子 3.10〜3.14）／付録C-3 | 提案 |
| 2026-09-18 | 0 | Q75 ローカルへの Python の導入方法 | 要確認。システムまたはユーザー環境が変わるので、許可する方法を決めてほしい（施工側はどれも実行していない）。選択肢：`brew install python@3.13`（依存の openssl@3・sqlite・xz などが一緒に更新されうる。事前に `HOMEBREW_NO_AUTO_UPDATE=1 brew install -n python@3.13` で確認できる）／`brew install uv` のあと `uv python install 3.13`（Homebrew の Python 群には触れない）／何も入れず、手元の 3.14 系を使う（Q74 で 3.14 を選ぶのと同じ。最新 patch への更新も選べる）／python.org の .pkg（管理者権限が要る）。暫定案：3.13 を選ぶなら uv 経由がやや有利。著者の好みで決めてよい | システムの変更は著者の許可が要る | https://formulae.brew.sh/api/formula/python@3.13.json（3.13.15）、https://formulae.brew.sh/api/formula/uv.json（0.12.15）、astral-sh/python-build-standalone 20260901 | 提案 |
| 2026-09-18 | 0 | Q76 .venv と依存の固定 | 要確認。リポジトリ内への `.venv` の作成（.gitignore で除外済み）と、PyPI からの取得（gradio[mcp] 一式で約62〜63パッケージ）を、いつ許可するか。依存の固定方式（直接の依存だけ `==` にするか、推移的な依存までハッシュ付きで固定するか。後者は uv pip compile か pip-compile が要る）。開発用の依存（pytest）のために `requirements-dev.txt` を新設するか（SPEC §3 の構成外）。暫定案：施工段階1では pytest だけを入れる。施工段階3では検証に使った環境をハッシュ付きで記録し、施工段階4でそれを requirements.txt として確定する。requirements-dev.txt を新設する | D01〜D04 の実行に pytest が要る。CLAUDE.md は requirements.txt の固定を施工段階4に置いている | `git check-ignore -v --no-index .venv/` → `.gitignore:153:.venv` | 提案 |
| 2026-09-18 | 0 | Q77 Spaces 用の requirements と sdk_version | 要確認。Spaces では gradio が sdk_version から入る。requirements.txt にも gradio[mcp] を書くか（二重指定になる）、mcp extra が自動で入るか、ハッシュ付きの完全固定と両立するかは未確認。暫定案：配置段階二の前に実測して決める | 未確認の事項 | https://huggingface.co/docs/hub/spaces-dependencies | 提案 |
| 2026-09-18 | 0 | Q78 Spaces の python_version の粒度 | 要確認。選択肢：minor までを引用符付きで書く（例 `"3.13"`）／patch まで書く（Spaces が最新の patch を提供するかは未確認）。暫定案：minor までを引用符付きで書き、実際の patch は起動ログで記録する | python_version を省くと 3.10（EOL 2026-10）になる。参考値：引用符なしの 3.10 が YAML の数値 3.1 になった公開 Space が、標本8000件中25件あった | https://huggingface.co/docs/hub/spaces-config-reference（"Any valid Python 3.x or 3.x.x version. Defaults to 3.10."）、Hub API の集計 | 提案 |
| 2026-09-18 | 0 | Q79 起動するインタプリタの明示 | 要確認。手元のシェルの `python3` は gradio の要件を満たさない別のインタプリタを指すので、SPEC §9 の `python app.py` をそのまま打つと失敗する。README と手順でインタプリタを明示する（例 `.venv/bin/python app.py`）か、著者がシェルの設定を変えるか。暫定案：明示する | どのインタプリタで動いたかを記録しやすい | `which -a python3` とその版の確認 | 提案 |
| 2026-09-18 | 0 | Q80 起動時の環境変数の絞り込み | 要確認。Reader は外部 LLM を使わず、環境変数の秘密情報を読まない。念のため、起動手順で不要な環境変数（API キーなど）を子プロセスに渡さないようにするか（Gradio の設定変数は Q93）。暫定案：起動手順で外す | 外向き通信なし（SPEC §2.10）とは別の、予防の対策 | SPEC §2.10 | 提案 |
| 2026-09-18 | 0 | Q81 検収記録の置き場 | 要確認。選択肢：`docs/acceptance/<日付>-<クライアント>.md`（SPEC §3 の構成外）／本ファイルの行／README の節。暫定案：なし（著者の判断） | 接続先ごとの検収記録が施工段階4の完了条件 | CLAUDE.md 段階4 | 提案 |
| 2026-09-18 | 0 | Q82 E01 の実施条件 | 要確認。E01（R01・R08・R13・R14・R15）を ja と en の両方で行うか。対象のクライアントとモデル。ガイドの使用条件の組み合わせ（なし／read_with_guards／get_reading_guide）。E01 の間に AI_READING_TESTS の resource（採点基準を含む）を読ませないか、読んだかを記録するか。E01 の判定を SPEC §7 の文言（正しい原文・位置・記録の保持）に限るか、コーパスの基準との照合も記録するか。暫定案：なし（著者の判断） | R14 の「Spec.cost」は論文になく（論文は「Spec. cost」T1 に2回、「specification cost」T1 に63回・T2 に4回〔大文字小文字を区別しない〕）、THEORY_MAP・FOR_AI_READERS・SOURCE_INDEX に計4回、llms.txt に1回、AI_READING_TESTS.md に5回、reading_cases.json に5回ある。SEARCH 案では「.」で分かれて論文にも一致するが、日本語に続けて書くと CJK を含む断片となってゼロ件になりうる | tests/reading_cases.json、論文 MD とガイドの計数 | 提案 |
| 2026-09-18 | 0 | Q83 コーパスの権利者 | 要確認。著者は同梱するコーパス（v3.5.0）の権利者か。そうであれば、data/ の扱い（Q06・Q13〜Q19）は権利者としての選択になり、施工側はライセンス条項の適用を前提にした問いを立てない。暫定案：なし（Q06・Q13〜Q19 の前提として先に確認したい） | 施工側はライセンスの解釈をしない | CITATION.md L15、SPEC §10（コーパス側の改版は著者が行う） | 提案 |
| 2026-09-18 | 0 | Q84 verify_quote の結果数と最小長 | 要確認。SPEC §5.5 は「複数箇所に同じ短文→全候補」、SPEC §2.10 は「最大結果数に上限」を求めており、1文字や一般的な語で数千件が返りうる。選択肢：最小長を決め、未満は invalid_input にする／results に上限 N 件を設ける。上限を超えたときの返し方は、ok と limitations の `TRUNCATED: total=n`（部分的な結果になる）／専用の状態を加える（SPEC 改版）／invalid_input にして、より長い引用や paper_id の指定を促す、から選ぶ。暫定案：最小長と上限の両方を置く。超過時の返し方は著者の判断（値は施工段階2で実測して提案する） | 論文 MD の出現数：'the' 2985、'AI' 426、'，' 787 | SPEC §2.10・§5.5 | 提案 |
| 2026-09-18 | 0 | Q85 処理時間の上限 | 要確認。SPEC §2.10 は処理時間に上限を置くよう求める。案A：関数の内部では打ち切らず、入力・k・候補数の上限で計算量を有界にし、最悪ケースの実測値を README と本ファイルに書いて、それを上限とみなす／案B：通信層で時間の上限をかけ、超えたら isError か HTTP 503 で返す（status には混ぜない）。S01 の判定値（秒）もあわせて決める。暫定案：A（B を併用するかは施工段階3の実測後に判断） | 途中で打ち切った部分結果は R01 と衝突する | SPEC §2.3・§2.10 | 提案 |
| 2026-09-18 | 0 | Q86 S03 の宣言範囲と README の表現 | 要確認。SPEC §2.10 が宣言するのは「起動後の資料取得は同梱データのみ」で、「プロセスが一切外へ通信しない」は初版では表示しない。S03 の監査は loopback 以外への接続を検出する厳しい形で行うが、README ではその結果を「外へ一切通信しない」と読める表現にせず、SPEC §2.10 の範囲だけを宣言する、でよいか。暫定案：そのとおり | SPEC の文言を超える主張を初版で出さない | SPEC §2.10・§7 S03 | 提案 |
| 2026-09-18 | 0 | Q87 resources・prompts が採用版で動かない場合 | 要確認。gr.mcp.resource・gr.mcp.prompt が、採用版と gr.api の組み合わせで動かない場合、実装を止めて報告し、版の選び直しか SPEC の改版を著者が判断する、でよいか（get_reading_guide だけで代替することは選択肢の一つとして示すにとどめる）。暫定案：そのとおり | SPEC §6 と M02 は施工段階3の完了条件 | SPEC §6・§7 M02 | 提案 |
| 2026-09-18 | 0 | Q88 英訳の結果と canonical_doi の表 | 要確認。英訳（source_kind=translation・translation_note）の結果で、SPEC §4 の欄をどう埋めるか。案：paper_id=T4、paper_version はプレプリント版の "1"（翻訳版 1.0.0 は payload の translation_version）、section_anchor は T4.en.html に実在する id（原文の節は original_locator）、source_url は papers/T4.en.html#id、canonical_doi は T4 の DOI。訳注（translation_note）は著者の原文に帰属させないため、canonical_doi は null とし、関連する原文の位置は original_locator に置く（paper_id=T4 は残すか、も確認したい）。あわせて source_kind ごとの canonical_doi の表（案：paper_md・translation・claims は論文の DOI、translation_note・reading_guide・theory_map・reading_test は null）。暫定案：この案 | Q33 は論文に属さない結果だけを扱う。source_manifest は論文 MD 自体も derivative とし、DOI を引用先とする。CITATION.md L35 は訳注を訳注として引用し、著者の原文に帰属させないよう求める | source_manifest.json の canonical_citation_rule、T4.en.manifest.json の translation・source・preparation、CITATION.md L35 | 提案 |
| 2026-09-18 | 0 | Q89 README の開示の配置と承認 | 要確認。SPEC §10 は「README末尾の開示」を著者の判断と署名の事項とする。開示の章を README の末尾に置き、施工側は下書きだけを出して、文面と配置の全体を著者の承認・署名の対象にする、でよいか。暫定案：そのとおり | 著者の判断事項 | SPEC §2.11・§10 | 提案 |
| 2026-09-18 | 0 | Q90 開示する「参照論文」の範囲 | 要確認。SPEC §2.11 の「参照論文」は、型を借りた Paper2Agent（SPEC §0）を指すか、T1〜T5 を指すか、両方か。暫定案：なし（著者の判断） | SPEC §0 と §2.11 の読み方が二通りある | SPEC §0・§2.11 | 提案 |
| 2026-09-18 | 0 | Q91 M02 のクライアント確認と ChatGPT の検収 | 要確認。SPEC §7 M02 は「対応クライアントで」の確認を求め、CLAUDE.md は M01〜M03 を施工段階3の完了条件とする。SDK での確認を施工段階3で、実クライアントでの確認をどの段階で行うか。Q73 で ChatGPT を配置段階二まで待つ場合、施工段階4の完了条件「接続先ごとの検収記録」から ChatGPT を外して配置段階二に回すか。暫定案：施工段階3で SDK と Claude Code、施工段階4で Claude Desktop、ChatGPT は配置段階二 | 段階の完了条件が決まらない | SPEC §7・§8、CLAUDE.md 段階表 | 提案 |
| 2026-09-18 | 0 | Q92 近接候補と claims の照合規則 | 要確認。verify_quote の quote_not_found のときの近接候補と、get_claim_record の query の照合は、SEARCH（論文の行が対象、クエリ200字まで）をそのまま使えない。案：規則 CAND を別に定める（text が長い場合は先頭から一定数の断片だけを使う、照合範囲は Q24 に合わせる、上限5件）。claims は claim・status・source_quote・not_claimed の各欄を単位にする。暫定案：この案（施工段階2で規則案を出して承認を得る） | 規則の版を分けないと、上限や単位が食い違う | SPEC §5.4・§5.5 | 提案 |
| 2026-09-18 | 0 | Q93 Gradio の環境変数の無効化 | 要確認。gradio@6.27.0 は、引数ではなく環境変数で有効になる設定を持つ（コードを読んだ限り、GRADIO_VIBE_MODE は外部 LLM のクライアントとファイルを書き込む経路を有効にし、GRADIO_WATCH_DIRS は dev_mode を有効にし、allowed_paths を指定しないと GRADIO_ALLOWED_PATHS が読まれる。ほかに GRADIO_BLOCKED_PATHS・GRADIO_ROOT_PATH など）。案：app.py で import gradio の前に、許可した GRADIO_* 変数（GRADIO_ANALYTICS_ENABLED=False など）だけを残し、ほかの GRADIO_* を消す。Blocks の生成後と launch の後に vibe_mode・dev_mode が False で allowed_paths が空であることを確かめ、満たさなければ非ゼロで終了する。S01・S03 では、これらの変数を設定したまま起動して確かめる。暫定案：この案 | 守則 §2.2・§2.3・§2.10 と CLAUDE.md 絶対規則2〜4 が、環境変数一つで崩れうる | gradio@6.27.0 blocks.py L1183–1184・L1201・L2956・L2975・L2986、routes.py L2279–2282（InferenceClient）・L2284–2300・L2365–2366（/vibe-edit の書き込み）、http_server.py L37–40（GRADIO_WATCH_DIRS）（いずれも読んだだけ） | 提案 |
| 2026-09-18 | 0 | Q94 段階0の一時領域での試作 | 要確認。段階0では、現物を確かめるためにコーパス（タグ v3.5.0）を一時領域へ浅く clone し、raw の GET も行った。また、正規化と検索の初期案の根拠を得るため、一時領域で使い捨ての分析・試作スクリプトを動かした（どちらもリポジトリには入れておらず、data/ も作っていない）。これらを CLAUDE.md の段階0「コードを書かない・data/ も取得しない」の範囲内とみなしてよいか（追認）。暫定案：なし（著者の判断） | 著者の意図を確かめていない | CLAUDE.md 段階表 | 提案 |
| 2026-09-18 | 0 | Q95 公開前の確認（既存行の参照） | 要確認。リポジトリや Space を公開する前に、次を残すか・直すかを著者が確かめる（施工側では直さない）：①「正本の配置」行（著者の行・確定）の理由欄の「台帳 D656」（非公開の資料を参照している可能性）。②必須記録項目の「（段階二）」（本ファイルの表記規則では「配置段階二」）。③Q64・Q66⑥ の上流の挙動についての行番号つきの分析（残す・要約にする・報告と修正の状況を待つ）。暫定案：なし（著者の判断） | SPEC §2.1 は非公開の判断台帳を同梱しないとしている。上流の SECURITY.md は脆弱性の疑いを非公開で報告するよう求めている | 本ファイル「正本の配置」行・必須記録項目・Q64・Q66 | 提案 |

---

## 付録A 段階0 施工計画（提案・2026-09-18）

正本は `SPEC.md` v2。本付録と SPEC が食い違う場合は SPEC に従う。未確定の点は Qnn を参照し、決め打ちしない。規則の版は Q49 の暫定案（意味つき版）で仮に書いている。

### A-0 共通方針

- `mekiki_reader/` は標準ライブラリだけで書き、gradio を import しない（施工段階1・2のテストを Gradio なしで回すため）。
- 同梱データは起動時に一度だけメモリへ読み込み、以後はファイルを開かない。
- 決定性（SPEC §2.3）
  - 出力の配列（results・candidates・limitations・normalization_applied）は、出力前に必ず全順序で並べる。set や dict の反復順に依存しない。
  - 文字種（CJK・数字・ひらがな）の判定は、明示したコードポイント範囲で行い、`unicodedata.category` や `re` の `\d`・`\w` には頼らない。
  - JSON の直列化は規則 JSON-1.0.0（`sort_keys=True`、`ensure_ascii=False`、`separators=(",", ":")`、`allow_nan=False`）。
  - 所要時間や通信IDは結果データに入れない。
- 規則にはすべて版を付け、応答の limitations と本ファイルに記録する（Q49）。

### A-1 守則 §2 の担保

| 守則 | 担保する場所 | テスト |
|---|---|---|
| 2.1 公開・承認済みのみ、資料種別と従属 | `corpus.ALLOWED_PATHS`（SPEC §3 の16本＋Q06〜Q08 の決定）、`data/bundle_manifest.json`、`corpus.verify_bundle()`、`schema.SourceKind`、パスと種別の固定表・派生物の表示（Q38⑦） | D02・D03・T12 |
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

### A-2 施工段階1：data/ の取得・bundle_manifest.json・corpus.py（完了条件 D01〜D04）

着手の条件：Q01・Q03〜Q12・Q22・Q26・Q27・Q34・Q49・Q83（Q06 の前提として）・Q94（段階0の作業の追認）の回答と、実行環境（Q74〜Q76）。Q02 は記録だけ。

**取得の手順**（Q04 の案A＋案D。作業は一時領域で行い、最後にだけリポジトリへ写す）
1. `git ls-remote <url> refs/tags/v3.5.0 'refs/tags/v3.5.0^{}'` で、タグが 6748061 を指し `^{}` 行がないことを確かめる（main は照会しない）。`gh api …/git/refs/tags/v3.5.0` の object.type が commit であることも確かめる。一致しなければ止めて報告する。
2. 空のリポジトリで `git -c protocol.version=2 fetch --depth 1 --no-tags <url> 67480613108cf72c29d5691e3d7a6c7e6553eb9b` を実行し、`FETCH_HEAD` と `FETCH_HEAD^{tree}` を照合する。
3. 許可ファイルごとに `git cat-file blob <SHA>:<path>` で書き出す（checkout を経ないので改行変換を受けない）。コーパスの tools/*.py は実行しない。
4. ファイルごとに、`git hash-object`・SHA-256・bytes・CR 0件を付録C-1 と照合する。
5. 独立の照合として、`raw.githubusercontent.com/<SHA>/<path>` を GET して SHA-256 を比べる。GitHub trees API と `git ls-tree -r --long` も比べる。
6. コーパス内部の記録のうち同梱ファイルにかかるものを照合する（ログ表「同梱許可ファイルの現物」の内訳。規則は `corpus.verify_internal_hashes` と D04④ と同じ）。
7. bundle_manifest.json を生成する（生成スクリプトの置き場は Q04）。
8. 著者の確認を得てから data/ へ写す。Q09 が承認されていれば `.gitattributes` を置く。`pytest tests/test_data.py` を実行する。
9. `git status --short` に出るのが、次だけであることを確かめる：data/・`mekiki_reader/{__init__,corpus}.py`・tests/test_data.py・tests/conftest.py と tests/_support/（Q12）・DECISIONS.md。条件付きで .gitattributes（Q09）・scripts/（Q04）・requirements-dev.txt（Q76）・.gitignore（Q10）・SPEC.md（Q05）。

**data/ の配置**（SPEC §3 どおり）：`source_manifest.json`・`bundle_manifest.json`・`papers/T1〜T5.md`・`claims/t5.json`・`tests/reading_cases.json`・`translations/T4.en.md`・`translations/T4.en.manifest.json`・`THEORY_MAP.md`・`FOR_AI_READERS.md`・`SOURCE_INDEX.md`・`T5_CLAIM_STATUS.md`・`AI_READING_TESTS.md`・`llms.txt`（Q06・Q07・Q08 で増えうる）。`data/tests/` とリポジトリの `tests/` を混同しないよう、テストは常に `pytest tests/` で起動する。

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
- bundle_hash は、このファイルの生のバイト列の SHA-256。期待値は `corpus.EXPECTED_BUNDLE_SHA256` と本ファイルに固定する（Q03）。
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

施工段階1で本ファイルに書くもの：Git 参照（ref・commit・tree・parent・確認日時）、取得経路と取得ログ、bundle の形式と `EXPECTED_BUNDLE_SHA256`、規則 LINES・LANG・SECTION・T4MAP（D04④ のハッシュ規則を含む）・BUNDLE の版、起動時に照合できない記録の一覧、節idの HTML 実在の使い捨て検査の結果、実行した Python の版。

### A-3 施工段階2：schema.py・normalize.py・tools.py・patterns.py・prompts.py（完了条件 T01〜T12・R01）

着手の条件：Q16・Q21〜Q61・Q65・Q68・Q84・Q88・Q92 の該当するもの（特に Q21・Q23・Q24・Q41〜Q44・Q50〜Q52）。

**schema.py**
- `SCHEMA_VERSION`、`JSON_RULE="JSON-1.0.0"`。
- `Status`：ok・unknown_id・quote_not_found・no_lexical_match・invalid_input・ledger_not_available。
- `SourceKind`：paper_md・theory_map・claims・reading_guide・reading_test・translation・translation_note。
- `Locator`（path・line_start・line_end・char_start・char_end・json_pointer・note）。
- `SourcedResult`（source_id・source_kind・paper_id・paper_version・language・source_path・source_hash・section_anchor・locator・canonical_doi・source_url・snapshot_url・payload）。
- `make_envelope(corpus, status, results, candidates, limitations, extra)`、`to_json(envelope)`、`validate_envelope(obj)`（手書きの検証器。jsonschema に依存しない）。
- 共通外枠は SPEC §4 どおり（schema_version・corpus_version="3.5.0"・source_commit・bundle_hash・status・results・candidates・limitations）。ツールごとの外枠の追加欄（verify_quote の match と normalization_applied など）は extra から入れる。normalization_applied は全結果に適用した規則IDの和集合で、結果ごとの変換は payload.diffs に置く（Q48）。細部は Q38、DOI と URL は Q33・Q88。license 欄は足さない（Q16）。

**normalize.py**（NORM-1.0.0 案。付録B-1）
- 明示の対応表（WHITESPACE・ZERO_WIDTH・WIDTH_MAP・半角カナ表・PUNCT_CLASSES・QUOTE_MAP）と、表を正準 JSON にしたものの SHA-256（import 時に再計算して定数と照合する）。
- `normalize_with_offsets(s, *, is_input) -> Normalized(text, spans, applied)`：各文字について原文の区間を持つ（削除と合成があるので区間で持つ）。
- `find_all(hay, needle)`：原文側の文字位置の一覧を返す。`diff_records(original, user_text, limit)`（Q48）。
- 原文側の正規化テキストと区間の表は、起動時に作ってメモリに置く。data/ には書かない。
- 照合は二段：①生テキストの完全一致（match=exact）、②同じ規則を入力と原文の両方にかけた一致（match=normalized）。大文字と小文字は同一視しない。

**検索（SEARCH-1.0.0 案・CAND・TERMS-0.0.0）**：付録B-2。用語対応表は `TERMS_VERSION="TERMS-0.0.0"`、`TERMS=()`。承認前は空で起動でき、その間は「断片の部分文字列照合＋英語の単語境界照合」として動く（置き場は Q52）。近接候補と claims の照合は規則 CAND（Q92）。

**tools.py（七ツール。corpus を明示的に受け取る純関数）**
- 共通の入力検査：ID は `^[A-Za-z0-9._-]{1,128}$`。パス区切り・URL・NUL の形をした値は invalid_input。それ以外の形式違反と、形式は正しいが索引にない ID は unknown_id と近傍候補（Q35）。k は `isinstance(k, int) and not isinstance(k, bool)` で、範囲内であること。文字列の長さは Q56・Q84。

| ツール | シグネチャ（案） | 状態 | 結果の中身 |
|---|---|---|---|
| list_papers | `list_papers(corpus)` | 常に ok | 5件（paper_md、アンカー paper-tN）。payload：title・alternate_title（T4）・paper_version・canonical_doi・language（Q22）・available_editions（T4 は ja と en）・line_count・sections（id・title・level・line_start・line_end・parent_id・child_ids・heading_only） |
| get_section | `get_section(corpus, paper_id, anchor, language=<Q21>)` | パスや URL の形→invalid_input。論文が未登録→unknown_id（候補は5本）。アンカーが未登録→unknown_id（候補は Q35）。Q21 案A では T1〜T3・T5 に ja または en→invalid_input、T4 は ja（または None）と en だけ ok | 原文：1件。payload に text（範囲の行を "\n" で連結し、改変しない）・is_excerpt=false・parent_id・child_ids（Q34）・heading_only。T4 の en：節に属する unit を英訳の行の順に返す。訳注は translation_note の別の結果にする（Q26）。欄の埋め方は Q88。各結果に original_locator（papers/T4.md の行・sourceSha256・節）・treatment・translation_version="1.0.0"・source_corpus_version（Q28）・manifest の preparation と authority（Q25）を付ける。位置のない wrapper の description（6件）は、manifest の位置（json_pointer）付きで返す（Q38⑨）。separator（5件、description なし）は原文の行位置だけを返す。英訳の枠部分は Q27 |
| search_passages | `search_passages(corpus, query, paper_id=None, k=5)` | 空・断片0個・上限超過・k が範囲外→invalid_input。paper_id が未登録→unknown_id。全語一致が0件→no_lexical_match。それ以外→ok | 各結果：locator は行と文字位置。payload に excerpt・is_excerpt=true・match_positions・matched_terms・match_via（Q53）・rank・rank_key・route（get_section への paper_id と anchor）。limitations に照合範囲、SEARCH と TERMS の版、「スコアは順位であって確率ではない」「ゼロ件は記述がないことを意味しない」、言語差の注意（Q61）。results が空のとき、エンベロープにも results にも論文のアンカーを置かない。candidates（一部一致。Q55）は、索引に実在するアンカーを付けた場合に限り返してよい |
| get_claim_record | `get_claim_record(corpus, claim_id=None, query=None)` | 両方なし・両方あり→invalid_input。T1〜T4→ledger_not_available（Q32）。T5 だが未登録→unknown_id（候補は実在する11件）。query→Q32・Q92 | 1件ごとに source_kind=claims、source_path=claims/t5.json、source_hash は台帳の SHA-256、locator.json_pointer=/claims/i、paper_id=T5、paper_version="3"、section_anchor は section_url のフラグメント、source_url は section_url、canonical_doi は T5 の DOI（Q88）。payload：id・status（逐語）・claim（台帳の要約と明示）・source_quote（逐語）・not_claimed（配列のまま）・section・source_locator（中身ごと）・additional_source_quotes（Q30）・footnote（N3 以外は null）・author_answerable=null（「未記録（初版）」と注記）・cited_paper_sha256（source_sha256） |
| verify_quote | `verify_quote(corpus, text, paper_id=None, language=<Q21>)` | 空・空白だけ・正規化後に空・最小長未満（Q84）・上限超過→invalid_input。paper_id が未登録→unknown_id。paper_id と language の組み合わせは get_section と同じ規則。完全一致が1件以上→ok, match=exact。正規化で一致→ok, match=normalized。どちらもない→quote_not_found, match=none（candidates は規則 CAND による語句上の近接候補で、上限5件。「類似の主張がある」とは書かない） | 各結果：locator は行と文字位置。payload に matched_text（原文をそのまま切り出したもの）と diffs。複数か所で一致したら全件を返して曖昧さを表示する。結果数の上限と超過時の返し方は Q84 の回答に従う。照合範囲は Q24 |
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
| T07 | 凍結定式二本 | どちらも match=exact・status=ok で、行と節が期待どおり | **Q23 の回答待ち** |
| T08 | 許容される表記差（T4 引用の「，」→「、」、空白や改行の挿入、曲線引用符、全角英数） | match=normalized。matched_text が原文どおり。normalization_applied に規則IDと NORM の版がある。変形した入力は tests/fixtures/ に置く | Q41〜Q48 |
| T09 | 内容語の置換、否定の付加や削除、数字・小数点・負号・比較記号の変更、語の連結 | quote_not_found・match=none。変形後の文字列が照合範囲の全体に生でも正規化後でも存在しないことを、テストの中で先に確かめる | Q24 |
| T10 | `""`・空白だけ・`"　"`・`"​"`・最小長未満、範囲内に2回以上現れる短文、上限を超えて現れる短文 | 前者は invalid_input。複数一致は全件を返して曖昧さを表示する。完全一致と正規化一致が混在する場合は Q48 の規則どおり。上限を超える短文の期待値は Q84 の回答まで作らない | Q38・Q48・Q84 |
| T11 | 試験用パターン × 肯定・否定・引用・疑問、パターン0件 | 4種とも同じ規則で要確認箇所として返し、needs_context_review=true。判定の欄がない。契約文がある。0件は Q36 どおり | Q36・Q37 |
| T12 | T4 の en、訳注を含む節、T1 の en と ja | 英訳は translation・en・translations/T4.en.md・original_locator 付きで、欄は Q88 どおり。訳注は translation_note で、paper_md にならない。訳注の結果が著者の原文の DOI を学術的な引用先として示さない（Q88）。原著者注（author-note-N）は translation。T1 の en と ja は invalid_input（Q21 案A の場合） | Q21・Q25〜Q28・Q88 |
| R01 | 7ツールそれぞれの固定入力 | 同じプロセスで2回呼んだ結果と、別プロセスで PYTHONHASHSEED を変えて呼んだ結果の to_json 出力が、バイト単位で一致する（過負荷のない条件で） | Q65 |

施工段階2で本ファイルに書くもの：SCHEMA・JSON・NORM（表・表のハッシュ・根拠件数・除外集合・数字の保護）・SEARCH・CAND・TERMS・PATTERNS・PROMPTS・NEAR・GUIDE・LIMITS の版と値、形態素解析器を入れない判断とその理由、T07 に使った文字列と出典、最悪ケースの所要時間、参考値の再計測結果。

### A-4 施工段階3：app.py と接続試験（完了条件 S01〜S03・M01〜M03）

着手の条件：Q12・Q40・Q62〜Q72・Q74〜Q76・Q85〜Q87・Q91・Q93。着手時に PyPI を取り直し、6.27.x の修正版、mcp 1.x の最新、分類子を確認して記録する。

**app.py の骨格**（Gradio 6.27.0 を仮定。Q62）
- import gradio より前に環境変数を整える（Q93）：許可した GRADIO_* だけを残し（`GRADIO_ANALYTICS_ENABLED="False"` は上書き）、ほかの GRADIO_* を消す。`HF_HUB_DISABLE_TELEMETRY="1"` を設定する（MCP 内部の gradio_client は環境変数だけで telemetry を判定し、huggingface_hub は import 時に値を確定するため）。
- `corpus.load_corpus()` が BundleError を出したら、非ゼロで終了する。
- 七つの関数は、名前を SPEC のツール名と完全に一致させる（ツール名は `__name__` から付き、`gr.mcp.tool(name=)` は反映されない）。全引数に型ヒント、戻り値は `-> str`（Q63）、Args 形式の docstring を付ける。`from __future__ import annotations` は使わない。
- `with gr.Blocks(analytics_enabled=False, title="Mekiki Reader")` の中で、各関数を `gr.api(fn, api_visibility="public", queue=<Q65>)` で登録する。UI コンポーネントは置かない。
- resources は12件を静的 URI で登録し（Q70）、prompts は3件を関数名と同じ名前で登録する（`name=` は使わない。Q64）。動かない場合は Q87。
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

施工段階3で本ファイルに書くもの：検証に使った環境（`python -VV`・`pip freeze`〔ハッシュ付き〕・`unicodedata.unidata_version`・`pip --version`）、接続 URL、S01〜S03・M01〜M03 の結果、S03 の監査ログと lsof の記録、prompts の名前照合の再現結果、標準経路と環境変数の遮断の検証結果、最悪ケースの所要時間。

### A-5 施工段階4：README・requirements・検収記録

着手の条件：Q13〜Q20・Q71〜Q73・Q77〜Q82・Q86・Q89〜Q91・Q95。

**README.md の章立て**（下書き。開示の章の文面と配置は著者の承認・署名の対象。Q89）
0. YAML front matter（配置段階二の Space 用）：`sdk: gradio`、`sdk_version: "<Q62>"`、`python_version: "<Q74・Q78。引用符付き>"`、`app_file: app.py`（license 欄は Q15）。
1. 設計上の対応：SPEC §1 の表（列名は「設計上保ちたい区別／根拠・参照先」。実装を論文の直接の主張とは書かない）と、SPEC §0 の三層の保証の表。表の直後に SPEC §1 末尾の二文を逐語で置く：「**設計の整合は理論の妥当性の証明ではない。静的な方針の検証は動作の保証でもない。**」
2. これは何で、何をしないか（読み取り専用・サーバ内に LLM なし・SPEC §11 の項目）。
3. 同梱データと版（v3.5.0・commit・tree・bundle_hash・許可一覧・同梱しないもの。Pages は main を配信するので、固定の参照先は snapshot_url）。
4. ツール・resources・prompts の一覧（Spaces での接頭辞付きの名前、状態の意味、上限値、規則の版の一覧）。
5. 起動と接続の手順：インタプリタを明示した起動（Q79）、起動表示の URL、Claude Code（`claude mcp add --transport http mekiki-reader <実測URL>`）、Claude Desktop（Q72）、ChatGPT 開発者モード（Q73）、検収記録へのリンク（Q81）。
6. ライセンス（Q06・Q13〜Q19・Q83）。
7. テストと検収（`pytest tests/`、`pytest -m server tests/`、テストIDの表）。
8. 開示（SPEC §2.11。末尾に置く。Q89）：制作工程（SPEC → Claude Code による施工 → Codex による独立検査 → Claude による最終検査 → 著者の判断、生成 AI の使用）、参照論文（Q90）、費用と休止（配置段階一は追加料金なし。配置段階二の実測値はそこで記入）、利用者入力の送信先と保存方針（Q20）、外向きの資料取得の宣言（Q86）、既知の制約（英訳の作成経緯 Q25、英訳の出典記録の版 Q28、T1 本文の記述 Q18、日本語の問いが英語の論文に当たりにくいこと、M02 で再現した上流の挙動 Q64、`/` で Gradio 標準のフロント HTML が返ること Q66④。⑥は Q66・Q95 の条件を満たすまで書かない）。

**requirements.txt**：暫定で `gradio[mcp]==6.27.0`・`mcp==1.30.0`・`pydantic==2.12.5`。施工段階3で記録したハッシュ付きの環境をもとに、施工段階4で確定する（固定方式と requirements-dev.txt は Q76、Spaces との関係は Q77）。固定の根拠（タグのコミット、wheel の SHA-256、PyPI JSON の URL）を本ファイルに記録する。

**E01・E02・P01 と検収記録**
- E01（手動のスモーク試験）：R01（claim_ids は T5-A1・T5-A3・T5-N1）、R08（claim_ids は T5-A4、追加根拠は T5 §1 の27行）、R13（claim_ids は空、追加根拠は T1 §4.2 の163・167・193行）、R14（T1 §2.1 の54行と T2 §2.1 の37行）、R15（T3 §7 の162行と §2.2 の41行）。実施条件は Q82。記録する項目：正しい原文・位置・記録を保持したか、ガイドの使用条件、ツールを呼んだ順序、AI_READING_TESTS の resource を読んだか、生の応答、原文との突き合わせの結果。
- E02：架空の会社の相談例と、資料中の命令文（Q40）。原文と事例の判断を分けたか、資料を上位の命令として扱わなかったか。
- P01：配置段階二で、再起動と休止からの復帰の後に再接続し、復帰時間を実測する。施工段階4では手順と様式だけを用意する。
- 検収記録の様式（接続先ごと。置き場は Q81、対象は Q71・Q91）：日時・クライアントの版・モデル／接続方式と URL（実測）／tools/list（7件）と各呼び出し／resources/list（12件）と read／prompts/list（3件）と get（未知の名前の挙動を含む）／不正な入力とゼロ件／E01・E02 の結果とガイドの使用条件／未対応の機能と備考。

### A-6 テストID総覧

| ID | 施工段階 | ファイル | 自動/手動 | 前提 |
|---|---|---|---|---|
| D01〜D03 | 1 | tests/test_data.py | 自動 | 一時コピー、データ根の注入（Q12）、EXPECTED_BUNDLE_SHA256（Q03）、余剰の厳しさ（Q10） |
| D04 | 1 | tests/test_data.py | 自動 | 実データを読むだけ。陰性はメモリ上の改変（Q22・Q26・Q27・Q34） |
| T01〜T03・T05・T06 | 2 | tests/test_tools.py | 自動 | Q21〜Q35・Q88・Q92 |
| T04 | 2 | tests/test_tools.py | 自動 | Q50〜Q61 |
| T07 | 2 | tests/test_tools.py | 自動 | **Q23 の回答待ち** |
| T08〜T10 | 2 | tests/test_tools.py＋tests/fixtures/ | 自動 | NORM（Q41〜Q48）、照合範囲（Q24）、結果数（Q84） |
| T11 | 2 | tests/test_tools.py＋tests/fixtures/ | 自動 | Q36・Q37 |
| T12 | 2 | tests/test_tools.py | 自動 | Q21・Q25〜Q28・Q88 |
| R01 | 2 | tests/test_tools.py | 自動 | 子プロセスで PYTHONHASHSEED を変える（Q65） |
| S01・S02 | 3 | tests/test_safety.py（＋fixtures） | 自動 | サーバ起動、Q12・Q40・Q56・Q65〜Q67・Q70・Q85・Q93 |
| S03 | 3 | tests/test_safety.py＋lsof の手動記録 | 自動＋手動 | サーバ起動、Q66・Q86・Q93 |
| M01〜M03 | 3 | tests/test_mcp.py（M02 は実クライアントでも） | 自動（＋手動） | Q63・Q64・Q68〜Q70・Q87・Q91 |
| E01・E02 | 4 | 検収記録 | 手動 | Q40・Q71〜Q73・Q81・Q82 |
| P01 | —（配置段階二で実施。施工段階4では様式のみ） | 検収記録 | 手動 | Space の公開（著者の判断） |

### A-7 SPEC §11（触れないもの）の確認

- 意味検索・埋め込み：検索は語句の照合と、明示した対応表による展開だけ。ベクトルや類似度のライブラリは入れない（numpy などは gradio の推移的な依存で、mekiki_reader からは import しない）。形態素解析器も入れない。対応表を概念レベルに広げると意味検索に近づくおそれがあるので、範囲は著者が決める（Q53）。
- 外部 LLM：API クライアントを持たず、API キーの環境変数を読まない（Q80）。Gradio の vibe_mode は環境変数を消して無効化し、起動時に確かめる（Q93）。
- チャット UI：Blocks にコンポーネントを置かない。`/` の標準フロントは Q66 で扱う。
- 判断を採点するツール：check_compressions は要確認箇所と原文を返すだけ。E01・E02 は人手による記録で、ツール化しない。AI_READING_TESTS.md は「採点には使わない」と明記して resource として返す。
- 非公開資料の同梱：許可一覧の公開ファイルだけ。fixture は架空のテキスト。
- compare_versions：実装しない。版どうしの比較を応答に出さない（Q28）。
- 理論の妥当性の主張：README に SPEC §1 の二文を置く。

---

## 付録B 初期案（提案・未承認）

### B-1 正規化対応表 NORM-1.0.0（案。Q41〜Q49 の暫定案を合わせたもの）

適用順：①元の文字の種別を判定する → ②文脈による判定（CJK に挟まれた空白の削除、数字に接する句読点の保護）→ ③写像 → ④空白の畳み込みと前後の除去。文脈判定は必ず写像の前の文字で行う（参考値：写像の後に判定した試作では、空白挿入の回復が149件中131件にとどまった）。

照合の単位は行で、原文側も行ごとに正規化する（行をまたぐ一致は認めない。Q41）。出現数の集計範囲は、papers/T1〜T5.md・THEORY_MAP.md・translations/T4.en.md（v3.5.0）。

| 規則ID | 対象（入力と原文の両方にかける） | 変換 | 出現数 |
|---|---|---|---|
| WS-ZW | U+200B・U+2060・U+FEFF | 削除 | 0（入力側だけに効く） |
| WS-CJK | 両隣（元の文字）がともに CJK である空白類の並び。CJK は明示範囲 U+3001–U+303F・U+3040–U+309F・U+30A0–U+30FF・U+3400–U+4DBF・U+4E00–U+9FFF・U+FF01–U+FF60（全角形）とし、空白類そのものは含めない | 削除 | 行内で該当するのは T4.md の3件（15行の U+3000 2件、221行の U+0020 1件）。83行・190行の U+3000 は左隣が数字なので対象外 |
| WS-COLLAPSE | U+0009・U+000A・U+000D・U+0020・U+00A0・U+2000–U+200A・U+202F・U+205F・U+3000 | 連続を U+0020 1個にし、前後を除く | U+0020 60121件（論文5本だけなら44214件）、U+3000 4件、ほかは0件 |
| WIDTH-ASCII | U+FF01–U+FF5E から除外集合を除いたもの | 対応する ASCII（U+0021–U+007E）へ | （）167組・：24・／2・ＳＤＧｓ・？2 |
| （除外集合） | ，U+FF0C・．U+FF0E・－U+FF0D・＋U+FF0B・＜U+FF1C・＝U+FF1D・＞U+FF1E・～U+FF5E | WIDTH-ASCII では変換しない（，．は PUNCT で扱う） | ，918・＝1、ほかは0 |
| WIDTH-KANA | U+FF61–U+FF9F（半角カナ・半角句読点） | 明示表で全角へ（濁点・半濁点は合成する） | 0（入力側だけに効く） |
| PUNCT-COMMA | 、U+3001・，U+FF0C・､U+FF64・,U+002C | 一つの類にする。ただし元の文字の直前と直後がともに数字（U+0030–0039・U+FF10–FF19）なら変換しない | ，918・、2・, 多数。数字に挟まれた ， は T4.md:245・247 |
| PUNCT-PERIOD | 。U+3002・．U+FF0E・｡U+FF61・.U+002E | 一つの類にする。両隣が数字なら変換しない。加えて「.」「．」は直後が数字なら変換しない（.05 型の小数。副作用は DOI・Vol.18 などの書誌表記29か所） | 。425・．0。小数点の字形は ASCII「.」だけ（例 T2.md:103・196・208） |
| PUNCT-MIDDOT | ･U+FF65 | ・U+30FB へ（幅の違いだけ） | 0 |
| QUOTE-CURLY | ‘U+2018・’U+2019 → 'U+0027、“U+201C・”U+201D → "U+0022 | 変換 | ’ 42（T4.en 39・T1 2・THEORY_MAP 1）・“” 33組 |
| （変換しない） | U+2212・U+2010–U+2015・U+30FC・≤≥≦≧<>＜＞=＝・~～〜・「」『』・大文字と小文字 | そのまま | SPEC §5.5（小数点・負号・比較記号は対象外） |
| NFC-INPUT | 入力側だけ NFC に合成するか | Q47 で決める | コーパスは全ファイル NFC 済み |

- NFKC は使わない。`unicodedata.normalize` は、Q47 で NFC を例外として認めた場合を除いて使わない（Unicode の版への依存を避け、R01 を保つ）。
- U+FF61（｡）と U+FF64（､）は WIDTH-KANA の範囲とも重なるが、句読点の類として扱う。
- normalized 一致では、区間の表から原文の部分文字列（改変なし）と行・列を返す。
- 参考値（写像前に判定する形の試作での評価）：試験引用36件はすべて一意のまま。T09 型の改変97件の誤一致は0件。数値の字形差（75．6・－0.26・＝・200，000・4。1節・200、000）の誤一致は0件。限られた標本によるもので、網羅的な検査ではない。施工段階2で実装した規則で再計測する。

### B-2 語句検索 SEARCH-1.0.0（案。Q50〜Q61 の暫定案を合わせたもの）

1. **検索用の正規化**：NORM-1.0.0 の WS-ZW・WS-COLLAPSE・WIDTH・QUOTE-CURLY 規則に、ASCII の A–Z → a–z を加える（WS-CJK は使わない）。クエリは次の2の分割を先に行い、断片ごとに正規化する。原文の各行にも同じ規則をかけ、区間の表で原文の位置へ戻す。’ は QUOTE-CURLY で ' になる。
2. **分割**：クエリを、空白類（WS-COLLAPSE の対象）と明示した区切り文字（、。，．,.;:!?・「」『』()（）[]{}" と …）で断片に分ける。ハイフン「-」とアポストロフィ「'」は語の一部として残す。空の断片を除き、重複は初出順で1つにする。ひらがな（U+3040–U+309F）だけの断片は捨てる。上限：正規化後200字・断片8個。超えた場合と、断片が0個になった場合は invalid_input（切り詰めない）。
3. **照合**：ASCII だけの断片は、前後が `[a-z0-9'-]` 以外（または行の端）である単語境界で完全に一致したときだけ一致とする。それ以外の断片（CJK や、—・アクセント付きの文字を含むもの）は、行の正規化テキストに部分文字列として現れれば一致とする。用語対応表（TERMS）に承認済みの項目があれば、その語形でも照合し、一致の経路を match_via に記録する（承認前は空）。
4. **単位と範囲**：単位は論文原文（papers/T1〜T5.md）の空でない行（879行）で、参考文献の節を含む。paper_id を指定すればその論文だけ。
5. **results と candidates**：全断片（またはその対応語）が一致した行を results、一部だけ一致した行を candidates（上限 k 件）に入れる。results が0件なら no_lexical_match。そのときも candidates は、索引に実在するアンカーを付けて返してよい。
6. **順位**：（一致した断片の種類数↓、直接一致〔対応表を経由しない〕を優先、総出現数↓、論文順 T1→T5↑、行番号↑）の全順序。スコアとしては rank と rank_key を返し、確率にはしない。
7. **k と抜粋**：k は1〜20の整数（既定5、範囲外は invalid_input）。抜粋は最初の一致の前後100字（原文の文字数で数える）。行がそれより短ければ行全体を返す。切った側に省略の印を付け、is_excerpt=true と文字位置を返す。一致位置は上限付きで全件並べる。
8. **注意書き**：日本語を含むクエリで英語の論文が範囲に入るときと、no_lexical_match のときに、言語差と「ゼロ件は記述がないことを意味しない」を limitations に入れる。
9. 形態素解析器は入れない。停止語表は Q56 で著者の判断。
10. verify_quote の近接候補と get_claim_record の query は、この規則をそのまま使わず、規則 CAND で定める（Q92）。

---

## 付録C 段階0で確認した現物（2026-09-17〜18 JST）

### C-1 同梱許可ファイル（commit 67480613108cf72c29d5691e3d7a6c7e6553eb9b）

| path | bytes | git blob | SHA-256 |
|---|---|---|---|
| source_manifest.json | 36918 | 33f8190b865ba56dd5ba4e95a62a9d356e30fb1f | ec8d9f55cd032534225dd25c7b70dc7371212c27266e60caf80a88ea53b70829 |
| papers/T1.md | 82244 | cc684fbc19a820a0f547bc57a84c41f0ade11412 | 2b027f11fd7a0f9241c02e97e20ebd08588b6d2bcfc6a0aa8bc211b837b52893 |
| papers/T2.md | 78119 | efd57a1603957a784ea5540e83ce5e9194b8cdb9 | ec2437e5418b34de1ad488e5628edb68d0ba98718529b97919319a123ea805fc |
| papers/T3.md | 59409 | 2602eacc29c1406f2b62c3465108c0af0ffec375 | 0d4a367b297db2b8481d71b71aabf7377abee23715a7c4452ed3a647a659dc5b |
| papers/T4.md | 66526 | 42c943d06b05e4ab46498eea768568e3a538cbd0 | 9d2e09840323244b58c1fb02586bca79ea78dbe6f8b3deb8f30bc996d17832d5 |
| papers/T5.md | 85758 | cc094ecc75449bb04c3ffb3e58cd5066157ceb84 | 57d600b36fa60389c2ae66a33c8feca118e516934cf5c6127407f40f48c93937 |
| THEORY_MAP.md | 38291 | c95b7b0da281951897fa85d2363964f5f5cacea1 | 2225e5a69e3f2968af233af8aee2133b217355085f434e164e611139304d213a |
| FOR_AI_READERS.md | 9636 | 993a93d0241b8229bb2b0a7c4cc4d376fd20cd17 | ddee2e7370ed9423be4a12f475a68c2acf9e8502b90a478f02c4ef2a5d8c01d7 |
| SOURCE_INDEX.md | 17118 | b69f731cd819863e54e5d5a4ddc6621876108935 | 0f9aff163414e48afefdb4d43c24a1c45ce8d61a3579cfdfcc9fa4b299cfc408 |
| claims/t5.json | 19250 | f931185fd25d343888decd1f21774d15ba34e2a3 | 26babf80b6779667b452455772350ba2cdbab3f9154ec924b0d608713bc9e003 |
| T5_CLAIM_STATUS.md | 14984 | 687c90b83c9cb73db615a3dcc181fee7f14a60ef | 16a6b5ac14fc679fc8643b9fdc157886c6931a2843a0d86ff51c973bbab1c9d9 |
| tests/reading_cases.json | 21177 | d130e9e46b3e884930217aef27b647c491693522 | d76740461ec37bec7a0fbbf7ac55ccb0e37f862fc21f261cc8ad222400d118ec |
| AI_READING_TESTS.md | 20667 | 8ff18484ca7750ed8c18362e2fc40a3b2cf5fb9d | c710fade5cf37fe8ca6adf3abdbdfdcc4f2a55271b21ff0c16171e4630abe57a |
| translations/T4.en.md | 87137 | 47fce6b3dc8e87c83ea3856c1bcccb86c1cac3d2 | bdf8690f23f1a79b1b7307fe99629540d07f9a5a97ba210b2c637cb9511ae5d9 |
| translations/T4.en.manifest.json | 66107 | 1aa13cb36af22e8067d27f02129c985e9a1c6540 | d6768d66ce13716caaf64544c8b93454e6659a90cfb6ed03914d7d471e050fc1 |
| llms.txt | 6519 | 64ea2e6996c1cfe702632361cf5018309bfb6e91 | df33559d07e6233c95fc77cd536422dcaabf64d0500b1b4dfef3bb7793290ef9 |
| （Q06 で採用した場合のみ）LICENSE | 18657 | da6ab6cc8f333d7e89a99812866df8f24374d47c | 9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411 |

同梱しないもの：README.md・MAINTENANCE.md・CITATION.md（Q07）・metadata.json・translations/T4.en.meta.json（Q08）・`papers/*.html`・mekiki-framework-t1-t5.md・`tools/*`・`index.*`・sitemap.xml・robots.txt・404.html・.nojekyll・mekiki-framework-t1-t3.md・mekiki-framework-t1-t4.md。

### C-2 Gradio（読み取りのみ。インストールも実行もしていない。日付は UTC）

- PyPI：gradio の最新は 6.27.0（2026-09-11）。直近は 6.26.0（08-24）・6.25.0（08-19）・6.24.0（08-12）・6.23.1（08-11）。5.x の最終安定版は 5.50.0（2025-11-21）。7.x はない。extras は mcp と oauth。
- gradio[mcp]：6.0.0〜6.27.0 は `mcp>=1.21.0,<2.0.0` を要求する。pydantic の実効の制約は、6.0〜6.1 が `>=2.11.10,<=2.12.4`（基本の依存による）、6.2.0 以降が `>=2.11.10,<=2.12.5`（mcp extra による。基本の依存は `>=2.0,<=3.0`）。5.50.0 は `mcp==1.10.1`。
- 固定の識別子：タグ gradio@6.27.0 → commit f153368503508b308b059c0986d4a0595312db70（gradio@6.26.0 → 6a2aef2e4e9aa492088f11f39dcc2e0460f44e3c）。wheel の SHA-256：gradio-6.27.0-py3-none-any.whl 6f4b9057c4a771283caa35a80dfdb3f599b5732108591fe9dcc32689cda17b68、gradio-6.26.0-py3-none-any.whl 54c5c4bfe7782e1773c2b7d7be128036df8b0dd6ca303c186ad6443280e1063b、mcp-1.30.0-py3-none-any.whl 666edb5009503e1047c9d60346a756f94b261f05cc2625f23d41c728ffc484d0。
- ソース（gradio@6.27.0）を読んだ限りのこと：gr.api の関数は mcp_server=True で MCP ツールになる（名前は `__name__`）。Streamable HTTP は `/gradio_api/mcp/`（stateless）で、旧 SSE `/gradio_api/mcp/sse` もコードに残る。resources と prompts は `gr.mcp.resource`・`gr.mcp.prompt`（5.43.0 で導入）。analytics は環境変数 GRADIO_ANALYTICS_ENABLED が文字列 "True" のとき、または未設定のときに有効になる。launch に analytics_enabled 引数はない。ツールの応答は `str(output)` の TextContent。run_history（6.27.0 でサーバ側の経路が追加された）は、トークン付きの要求を受けると HF Hub と通信する経路を登録する。vibe_mode・dev_mode・allowed_paths などは環境変数でも有効になる（Q93）。
- セキュリティ勧告：2026-02-27 公開の4件は <=6.5.1 または <6.7 が対象で、6.6.0・6.7 で修正済み。5.x の修正版はない（`gh api repos/gradio-app/gradio/security-advisories`）。
- Hugging Face Spaces：sdk_version は「All versions of Gradio are supported」、python_version は「Any valid Python 3.x or 3.x.x version. Defaults to 3.10.」（https://huggingface.co/docs/hub/spaces-config-reference）。参考値：最近更新された Gradio Space 100件のうち、sdk_version 6.27.0 で RUNNING のものが21件あった（Hub API、2026-09-17）。

### C-3 Python（読み取りのみ）

- 手元：arm64。既定の `python3` は gradio の要件（>=3.10）を満たさない。Homebrew の Python 3.14 系が1つある。uv・pyenv はない。Node.js は 24 系。
- Python の各系列（https://devguide.python.org/versions/、2026-05-27 更新）：3.14 はバグ修正中で EOL 2030-10、3.13 はバグ修正中で EOL 2029-10（通常のバグ修正は 3.13.16〔2026-10-06 予定〕で終了。PEP 719）、3.12 はセキュリティ修正のみで EOL 2028-10、3.11 は EOL 2027-10、3.10 は EOL 2026-10。3.15.0 は 2026-10-01 に初版の予定。
- 各系列の最新 patch：3.12.14（python.org の macOS インストーラはない）、3.13.15、3.14.7。Homebrew に python@3.12 3.12.14・python@3.13 3.13.15・python@3.14 3.14.7、uv 0.12.15 がある。
- unicodedata の版：3.10=13.0.0、3.11=14.0.0、3.12=15.0.0、3.13=15.1.0、3.14=16.0.0。v3.5.0 コーパスのテキストファイルに現れる文字は、13.0.0 と 16.0.0 で category・NFKC・NFC・casefold・east_asian_width がすべて同じだった（15.0・15.1 とは直接比べていない）。
- gradio[mcp]==6.27.0 の依存閉包（PyPI メタデータからの近似で約62〜63パッケージ）：C 拡張を含む13パッケージ（pydantic-core 2.41.5、numpy 2.5.3、pandas 3.0.5、pillow 12.3.0、orjson 3.12.0、audioop-lts 0.2.2〔3.13 以上〕、brotli 1.2.0、markupsafe 3.0.3、pyyaml 6.0.3、rpds-py 2026.6.3、cffi 2.1.1、cryptography 50.0.1、hf-xet 1.6.0）には、cp312・cp313・cp314 のいずれも macOS arm64 と manylinux x86_64 の wheel がある。Linux 側で最も厳しい要件は manylinux_2_27（numpy・pillow）。
- 参考値：公開 Gradio Space 8000件（最終更新 2026-08-30〜09-17 UTC、Hub API）が宣言する python_version は、3.12 系 2767件・3.13 系 672件・3.14 系 5件（宣言なし 3827件は既定の 3.10）。
- gradio の上流 CI は Python 3.10 でだけ試験している（test-python.yml）。公開用ビルドは 3.12（publish.yml）。3.14 についての上流の判断を示す記録は見つけていない（issue #12385 は起票者本人が約1分後に閉じたもので、判断の根拠にならない）。

### C-4 引き継ぐ未確認事項

- タグ v3.5.0 が過去に別のコミットを指したことがあるか（API で ref の変更履歴は取れない）。コミットの署名（GitHub API は verified=true だが、手元では独立に検証していない）。Pages と v3.5.0 の一致（確認したのは T1.html と LICENSE だけ）。
- Gradio の実際の動作（すべてコードを読んだうえでの推定）：gr.api だけの Blocks と mcp_server=True の組み合わせ、resources と prompts の登録、prompts/get の名前照合、Host ヘッダの扱い、ミドルウェアでの遮断、環境変数の無効化の効き目、import 時に外部へ通信しないか、ブラウザで `/` を開いたときの外部資源、ローカルに HF トークンが保存されている場合に MCP 内部のクライアントがそれを自己接続のヘッダに載せるか。
- Python 3.12・3.13・3.14 のそれぞれで、gradio 6.27.0 と mcp 1.30.0 が実際に動くか。依存閉包の実際の解決結果。
- Spaces の環境変数（SYSTEM・GRADIO_SERVER_NAME）、mcp extra が自動で入るか、patch 版まで指定できるか、ベースイメージの glibc。
- ライセンスの解釈はしていない（Q83）。
- 参考値（正規化と検索の試作・集計、Hub API の集計）は、限られた標本と代理の指標による。
- T4 英訳を著者が承認したかどうか（Q25）と、T07 の二本（Q23）。
