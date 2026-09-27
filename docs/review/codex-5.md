# Codex 独立検査⑤（対象コミット `b072d88`）

| 項目 | 値 |
|---|---|
| 検査 | Codex（独立検査。指摘と差分案のみ。SPEC §10）。範囲は HTTP 併設（SPEC v2.5.1 §2.12） |
| 対象 | コミット `b072d88a2bb9f2f9d14672265fca3b29f1018fa2`（main。SPEC v2.5.1・CLAUDE.md v1.2） |
| 受領 | 2026-09-27（著者経由） |
| 正本 | SPEC v2.5.2（§2.12・§7 H03／H04・§12）・CLAUDE.md v1.3 |
| 反映 | ブランチ `http3`（merge の SHA は DECISIONS の「Codex⑤」の節と施工報告） |
| 規則の版 | HTTP-1.1.0 → **HTTP-1.2.0**・LIMITS-3.2.0 → **LIMITS-3.3.0** |

> **この記録について**：報告の本文は [codex-5-report.md](codex-5-report.md)（著者が配置。本文には手を入れていない）。
> 本書はそれに対する施工側の反映記録。

## 指摘と反映

| 指摘 | 重大度 | 採否 | 反映した箇所 | 実測・確かめ方（local・spaces の両モード） |
|---|---|---|---|---|
| F1 重複 JSON キーの孤立サロゲートで 500 | P2 | 採用 | `mekiki_reader/http_api.py` の `parse_body`：キーの重複（入れ子も）・値の型の誤りのエラー文を入力のキーを含まない固定文に。不正な名前は許可名の一覧だけを示す（従来どおり） | `test_h03_json_key_errors_are_fixed_and_utf8`：verify／check × JSON／Markdown × 直下／入れ子 × 上位／下位サロゲート（ペアの重複・単独の不正キーも）で 400・応答は厳格な UTF-8・入力のキーが出ない。後続の要求は 200 |
| F2 複数行の Accept／If-None-Match を最後の一行に潰す | P2 | 採用 | `http_api.joined`（同名の全行を順序どおりカンマ結合）を `app.py` の `_serve_api` で使う。`Host`・`Content-Length` の重複拒否は変えていない | `test_h04_repeated_accept_and_if_none_match_are_joined`：一行と二行で Content-Type・本文・ETag が一致（Markdown が先／後・`q=0`・ヘッダ名の大小・`*/*`）。現在の ETag が最初の行でも最後の行でも 304。別の表現の ETag では 304 にならない |
| F3 早期拒否に cache ヘッダが付かない | P3 | 採用 | `http_api.common_headers`（`no-store`・`Vary: Accept`・`nosniff`）を `_reply`（名前空間 `/api`・`/api/…` のとき）と `_send_api` で共有。h11 が Guard より前に返す応答は別と HTTP.md に明記 | `test_h04_early_rejections_carry_common_headers`（許可外 Host 400・未知経路 404〔GET／POST〕・`/api`・`/api/v2`・パス形 404・405・413・414。名前空間の外は付かない）・`test_h03_slow_body_and_busy_carry_common_headers`（408）・`test_h03_busy_503_carries_common_headers`（503） |
| F4 メソッドを大文字化して get／Post を受ける | P3 | 採用 | `app.py` の Guard：HTTP 併設の経路では `scope["method"]` をそのまま表と照合。MCP 側の `method`（大文字化）は変えていない | `test_h03_method_case_is_exact`：九経路で `get`・`Get`・`gET`・`post`・`Post`・`pOST` が 405・正しい `Allow`・共通ヘッダ。GET／POST は従来どおり |
| F5 空文字の説明の一般化・LIMITS の旧範囲 | P3 | 採用（文書） | `docs/rules/HTTP.md` §2：空文字の扱いを引数ごとに（`part`・`k` は省略時だけ既定、空文字は invalid_input）。`docs/rules/LIMITS.md` の要求本文の行に HTTP 併設を含めた。実装は変えていない（MCP と同じ） | `test_h01_empty_part_and_k_are_not_defaults`：`part=` は MCP の `part=""` と同じ JSON（invalid_input）、省略は MCP の省略と同じ（ok）。`k=` はツールの invalid_input（同じ入口の関数の結果と一致）で、MCP ではスキーマの isError。H01 に `part=""` の突合 |
| 長い query（範囲ごとの検算・差分案の末尾） | — | 採用（SPEC v2.5.2 の新設） | 要求行（経路＋問い合わせ）16 KiB＝414。HTTP 併設の名前空間だけ・Host の検査の直後・本文より先 | `test_h03_request_target_limit_is_414`：16,384／16,385 バイトが一括・分割とも 200／414。65,536 バイトは一括で 414、分割では h11 が先に 400。POST も本文より先に 414 |

## 規則12（CLAUDE.md v1.3）の当て込み

F1 は、値の側の孤立サロゲート検査がキーの側の経路を覆っていなかったことから起きた。CLAUDE.md に規則12を足し、
既知の入力の種類を九経路すべてに当てる試験 `test_h03_known_input_kinds_on_every_route` を置いた（両モード）。

| 種類 | 当てたもの | 結果 |
|---|---|---|
| 孤立サロゲート | 問い合わせの `%ED%A0%80`・本文の値 `\ud800`・本文のキー `\ud800` の重複 | 400 |
| 重複 | `Host` の重複・値の違う `Content-Length`・引数の重複・JSON キーの重複（`Accept` の重複は F2 の試験） | 400 |
| TE と CL の併記 | `Transfer-Encoding: chunked` と `Content-Length` | 400 |
| 巨大入力 | 本文 64 KiB＋1・要求行 16 KiB 超・値の上限超え（3,000字） | 413・414・400 |
| 不正な符号化 | `%G1`・`%FF%FE`・本文の非 UTF-8・生の非 ASCII のバイト | 400 |

九経路の結果の集合（local・spaces とも同じ）：GET の七経路は 400・414、`POST /api/v1/verify` は 400・413・414、
`POST /api/v1/check` は 200・400・413・414（200 は本文の値 `"%G1"`。JSON の中の `%` は文字どおりの入力で、
該当なしの `ok`）。5xx は0件、応答はすべて UTF-8 で読めた。

## 新しい試験が指摘を検出することの確認

追加した7つの試験（F1・F2・F3・F4・414・408 の共通ヘッダ・規則12の当て込み）を、修正前の `app.py`・
`mekiki_reader/http_api.py`（`b072d88`）に戻して local で走らせ、**7件とも失敗**することを確かめてから修正版に戻した。

## 試験

`.venv/bin/python -m pytest -q` → **530 passed**（2026-09-27・http3。HTTP の試験は両モードで 57 件）。
