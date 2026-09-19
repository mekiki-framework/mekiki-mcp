# Codex 独立検査②（対象コミット `41fa3f9`）

| 項目 | 値 |
|---|---|
| 検査 | Codex（独立検査。指摘と差分案のみ。SPEC §10） |
| 対象 | コミット `41fa3f9`（Codex① の反映と CORS の遮断を merge した時点） |
| 受領 | 2026-09-18（著者経由） |
| 反映 | ブランチ `codex3` → コミット `d448021`（merge `e18ffea`） |
| 試験 | `.venv/bin/python -m pytest -q` → 398 passed（反映時点） |

> **この記録について**：**報告の本文は [codex-2-report.md](codex-2-report.md)**（著者が配置。ローカルの絶対パスは
> 施工側でリポジトリ相対に置換した。本文には手を入れていない）。本書はそれに対する施工側の反映記録で、
> 2026-09-18 に `DECISIONS.md` の「Codex②」の節と、`codex-1.md` 冒頭の検算メモをここへ移した。

## 前回（Codex①）の10件の検算

**Codex② による検算の結果（対象 `41fa3f9`）**：①②③⑦⑧⑨ は修正済み、④（queue の待機・未回収結果）と
⑥（S03 の書き換え先・停止処理・自己接続判定）は**一部残存**、⑤（キャッシュ）は制限は入ったが**並行での退行あり**、
⑩ は SEARCH・PROMPTS の旧記述が**残存**。いずれも `codex3`（Codex② の反映）で直した、と記録した（Codex③ の再検算で、④⑥ に残存、⑩ に別の不一致が見つかった。下の「残っていた3点」の訂正を見る）。

前回の対応表（`codex-1.md`）に①の行が無かったのも、この検算で指摘された（`codex-1.md` の「P1-1」として追加済み）。

## 指摘と反映

報告の本文は `docs/review/codex-2-report.md`（著者が配置。施工側は絶対パス17箇所をリポジトリ相対に置換しただけ）。
反映はブランチ `codex3`。前回10件の検算では ①②③⑦⑧⑨ が修正済み、④⑥ が一部残存、⑤ に退行、⑩ が一部残存と判定された。

| 指摘 | 採否 | 反映した箇所 | 実測・確かめ方 |
|---|---|---|---|
| 1. queue の待機要求・未回収結果が無制限 | 採用 | `app.py`：受付8とは別に**待機の上限64**（超過は 503・`_QUEUE_STATE` に記録）。Gradio の待ち行列は 72（＝8＋64。断るのはこちらの層）。回収されない結果は**件数64・4 MiB・120秒**で捨てる掃除を5秒ごとに回す（`sweep_results`・`start_sweeper`） | `resources/read` 同時 24/32/64/80 が全て ok（待機の最大26・拒否0）。結果を回収しない join 12本 → 掃除が1セッション破棄。`test_s01_queue_waiting_is_capped`（受付0・待機0 で 6/6 が 503）・`test_s01_uncollected_results_are_dropped`・`test_sweep_results_drops_by_count_size_and_age` |
| 2. LRU が並行呼び出しで KeyError | 採用（差分案どおり） | `tools.py`：自前の dict＋move_to_end をやめ `functools.lru_cache(maxsize=512)` に | `test_word_pattern_cache_is_safe_under_interleaving`：旧実装の割込み順を再現して KeyError を示し、今の実装は8スレッドで壊れず上限も守ることを確認 |
| 3. 本文到着10秒がチャンクごとにリセットされる | 採用 | `app.py`：受信ループ**全体で一つの期限**（`loop.time()` の締切。残り時間で `wait_for`） | 1バイトずつ 1.25 秒間隔で送ると 10.3 秒で切られる。`test_s01_slow_body_is_cut` |
| 4. S03 の監査の穴（書き換え先・相対パス・停止処理・自己接続判定） | 採用（差分案どおり） | `server_launcher.py`：rename 等は**元・先・dir_fd** を記録し相対パスを解決。**`data/` 宛ての書き換えは遮断**。自己接続の免除は**実際に bind した宛先**と自ポートに限る（`::1` を一律免除しない）。陽性対照のフラグは `finally` で戻し、**停止処理の後**に監査を保存。子プロセス・`sendmsg`・別の IPv6・`data/` への rename を陽性対照に追加 | `test_s03_no_outbound_traffic`：6つの対照がすべて blocked、`data/` への rename は**何も起きない**（`rename_did_nothing`）。配信中のリポジトリ書き換え0件 |
| 5. `[::1]x80` を受理する | 採用 | `app.py`：括弧の後は空か `:<ポート>` だけ | `test_s01_host_variants` に `[::1]x80` を追加（400） |
| 6. 生成器が規則一覧のハッシュを更新しない | 採用（一覧から外す案） | `docs/rules/README.md` から重複ハッシュを外し、値は個別の規則文書にだけ置く。生成器は `--write` の最後に**文書整合試験まで走らせる** | `test_rule_documents_match_the_tables` が「一覧にハッシュを写さない」ことも検査。`build_patterns.py --write` の末尾で 1 passed |
| 7. README・記録に実装より強い記述 | 採用 | README：CORS は「別オリジンのページに許可ヘッダを返さない」に、CL の重複は HTTP 層の担当と明記、`check_compressions` の20件は**1結果あたりの一致位置**（最悪 99 結果・183 KiB を LIMITS に実測記録）、起動時の一時書き込みの実態（filelock の `probe-source`・`probe-link`）、**遮断経路の一覧**を追加。橋渡しは prompts 6件で**再検収**。`docs/rules/SEARCH.md`「初版は空」・`PROMPTS.md`「日本語のみ」を現物に。`codex-1.md` の「10件すべて反映」を④⑥残存・⑤退行ありに、DECISIONS の「原本未受領」を配置済みに直し、対応表に前回①の行を追加 | `pytest -q` → 398 passed。橋渡しの再検収：tools 7・resources 12・prompts 6・`four_modes_en` の文面 |

**残っていた3点（前回の④⑥⑩）**：④は上の1で、⑥は4で、⑩は7で塞いだ、とこの時点では記録した。**Codex③（対象 `40b2777`・本文 [codex-3-report.md](codex-3-report.md)）の再検算で訂正**：1（queue・未回収結果）は受付8・待機64・待ち行列72は維持されていたが、保持処理に残存と退行があった（本文の受信が受付枠より前・LRU で追い出したセッションのイベント ID の残存・期限の基準がセッションを最初に見た時刻・大きさを `repr` の文字数で数えていた）。4（S03）は、相対パスの open と記述子を宛先にした操作を取りこぼしていた。7（記述）は旧指摘は是正済みだが、上限値の過大記述（check_compressions の「最悪約184 KiB」）が新たにあった。⑩は旧 SEARCH・PROMPTS の記述は是正済みで、別の不一致（版運用の境界。あわせて NORM の規則8に実装が合っていない点＝Codex③ 10）があった。したがって「すべて解消」ではない。反映は `DECISIONS.md` の「Codex③」の節。

**この反映で分かったこと（記録として）**：陽性対照で `data/` への rename を試したところ、監査が**記録するだけで止めていなかった**ため実際にファイルが1件でき、`data/` の余剰として起動が拒まれた。ファイルはすぐ取り除き（`data/` の差分0・18本で起動を確認）、フックを**遮断する**側に直した。試験用の起動器に限った出来事で、`app.py` は `data/` に書かない。
