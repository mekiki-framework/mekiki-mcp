# stage0_facts.md — 段階0で確認した現物（2026-09-17〜18 JST）

版：DECISIONS.md 付録C から分離（2026-09-18）。段階0時点の記録で、以後の変更は DECISIONS.md に記す。回答票で変わった点：LICENSE と CITATION.md は同梱する（Q06・Q07。CITATION.md の値は施工段階1の取得時に記録）。

## C-1 同梱許可ファイル（commit 67480613108cf72c29d5691e3d7a6c7e6553eb9b）

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
| LICENSE（Q06＝C で同梱） | 18657 | da6ab6cc8f333d7e89a99812866df8f24374d47c | 9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411 |

同梱しないもの：README.md・MAINTENANCE.md・metadata.json・translations/T4.en.meta.json（Q08）・`papers/*.html`・mekiki-framework-t1-t5.md・`tools/*`・`index.*`・sitemap.xml・robots.txt・404.html・.nojekyll・mekiki-framework-t1-t3.md・mekiki-framework-t1-t4.md。

## C-2 Gradio（読み取りのみ。インストールも実行もしていない。日付は UTC）

- PyPI：gradio の最新は 6.27.0（2026-09-11）。直近は 6.26.0（08-24）・6.25.0（08-19）・6.24.0（08-12）・6.23.1（08-11）。5.x の最終安定版は 5.50.0（2025-11-21）。7.x はない。extras は mcp と oauth。
- gradio[mcp]：6.0.0〜6.27.0 は `mcp>=1.21.0,<2.0.0` を要求する。pydantic の実効の制約は、6.0〜6.1 が `>=2.11.10,<=2.12.4`（基本の依存による）、6.2.0 以降が `>=2.11.10,<=2.12.5`（mcp extra による。基本の依存は `>=2.0,<=3.0`）。5.50.0 は `mcp==1.10.1`。
- 固定の識別子：タグ gradio@6.27.0 → commit f153368503508b308b059c0986d4a0595312db70（gradio@6.26.0 → 6a2aef2e4e9aa492088f11f39dcc2e0460f44e3c）。wheel の SHA-256：gradio-6.27.0-py3-none-any.whl 6f4b9057c4a771283caa35a80dfdb3f599b5732108591fe9dcc32689cda17b68、gradio-6.26.0-py3-none-any.whl 54c5c4bfe7782e1773c2b7d7be128036df8b0dd6ca303c186ad6443280e1063b、mcp-1.30.0-py3-none-any.whl 666edb5009503e1047c9d60346a756f94b261f05cc2625f23d41c728ffc484d0。
- ソース（gradio@6.27.0）を読んだ限りのこと：gr.api の関数は mcp_server=True で MCP ツールになる（名前は `__name__`）。Streamable HTTP は `/gradio_api/mcp/`（stateless）で、旧 SSE `/gradio_api/mcp/sse` もコードに残る。resources と prompts は `gr.mcp.resource`・`gr.mcp.prompt`（5.43.0 で導入）。analytics は環境変数 GRADIO_ANALYTICS_ENABLED が文字列 "True" のとき、または未設定のときに有効になる。launch に analytics_enabled 引数はない。ツールの応答は `str(output)` の TextContent。run_history（6.27.0 でサーバ側の経路が追加された）は、トークン付きの要求を受けると HF Hub と通信する経路を登録する。vibe_mode・dev_mode・allowed_paths などは環境変数でも有効になる（Q93）。
- セキュリティ勧告：2026-02-27 公開の4件は <=6.5.1 または <6.7 が対象で、6.6.0・6.7 で修正済み。5.x の修正版はない（`gh api repos/gradio-app/gradio/security-advisories`）。
- Hugging Face Spaces：sdk_version は「All versions of Gradio are supported」、python_version は「Any valid Python 3.x or 3.x.x version. Defaults to 3.10.」（https://huggingface.co/docs/hub/spaces-config-reference）。参考値：最近更新された Gradio Space 100件のうち、sdk_version 6.27.0 で RUNNING のものが21件あった（Hub API、2026-09-17）。

## C-3 Python（読み取りのみ）

- 手元：arm64。既定の `python3` は gradio の要件（>=3.10）を満たさない。Homebrew の Python 3.14 系が1つある。uv・pyenv はない。Node.js は 24 系。
- Python の各系列（https://devguide.python.org/versions/、2026-05-27 更新）：3.14 はバグ修正中で EOL 2030-10、3.13 はバグ修正中で EOL 2029-10（通常のバグ修正は 3.13.16〔2026-10-06 予定〕で終了。PEP 719）、3.12 はセキュリティ修正のみで EOL 2028-10、3.11 は EOL 2027-10、3.10 は EOL 2026-10。3.15.0 は 2026-10-01 に初版の予定。
- 各系列の最新 patch：3.12.14（python.org の macOS インストーラはない）、3.13.15、3.14.7。Homebrew に python@3.12 3.12.14・python@3.13 3.13.15・python@3.14 3.14.7、uv 0.12.15 がある。
- unicodedata の版：3.10=13.0.0、3.11=14.0.0、3.12=15.0.0、3.13=15.1.0、3.14=16.0.0。v3.5.0 コーパスのテキストファイルに現れる文字は、13.0.0 と 16.0.0 で category・NFKC・NFC・casefold・east_asian_width がすべて同じだった（15.0・15.1 とは直接比べていない）。
- gradio[mcp]==6.27.0 の依存閉包（PyPI メタデータからの近似で約62〜63パッケージ）：C 拡張を含む13パッケージ（pydantic-core 2.41.5、numpy 2.5.3、pandas 3.0.5、pillow 12.3.0、orjson 3.12.0、audioop-lts 0.2.2〔3.13 以上〕、brotli 1.2.0、markupsafe 3.0.3、pyyaml 6.0.3、rpds-py 2026.6.3、cffi 2.1.1、cryptography 50.0.1、hf-xet 1.6.0）には、cp312・cp313・cp314 のいずれも macOS arm64 と manylinux x86_64 の wheel がある。Linux 側で最も厳しい要件は manylinux_2_27（numpy・pillow）。
- 参考値：公開 Gradio Space 8000件（最終更新 2026-08-30〜09-17 UTC、Hub API）が宣言する python_version は、3.12 系 2767件・3.13 系 672件・3.14 系 5件（宣言なし 3827件は既定の 3.10）。
- gradio の上流 CI は Python 3.10 でだけ試験している（test-python.yml）。公開用ビルドは 3.12（publish.yml）。3.14 についての上流の判断を示す記録は見つけていない（issue #12385 は起票者本人が約1分後に閉じたもので、判断の根拠にならない）。

## C-4 引き継ぐ未確認事項

- タグ v3.5.0 が過去に別のコミットを指したことがあるか（API で ref の変更履歴は取れない）。コミットの署名（GitHub API は verified=true だが、手元では独立に検証していない）。Pages と v3.5.0 の一致（確認したのは T1.html と LICENSE だけ）。
- Gradio の実際の動作（すべてコードを読んだうえでの推定）：gr.api だけの Blocks と mcp_server=True の組み合わせ、resources と prompts の登録、prompts/get の名前照合、Host ヘッダの扱い、ミドルウェアでの遮断、環境変数の無効化の効き目、import 時に外部へ通信しないか、ブラウザで `/` を開いたときの外部資源、ローカルに HF トークンが保存されている場合に MCP 内部のクライアントがそれを自己接続のヘッダに載せるか。
- Python 3.12・3.13・3.14 のそれぞれで、gradio 6.27.0 と mcp 1.30.0 が実際に動くか。依存閉包の実際の解決結果。
- Spaces の環境変数（SYSTEM・GRADIO_SERVER_NAME）、mcp extra が自動で入るか、patch 版まで指定できるか、ベースイメージの glibc。
- ライセンスの解釈はしていない（Q83）。
- 参考値（正規化と検索の試作・集計、Hub API の集計）は、限られた標本と代理の指標による。
- T4 英訳を著者が承認したかどうか（Q25）と、T07 の二本（Q23）。
