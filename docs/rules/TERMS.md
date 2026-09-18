# TERMS — 用語対応表

| 項目 | 値 |
|---|---|
| 規則ID・版 | TERMS-0.1.1（30項目。0.1.0 から M02 の日本語形を外した）。表 `790e1240…7be0` |
| 状態 | 確定（著者承認 2026-09-18。Q52・Q53。0.1.1 も同日の著者確定） |
| 実装 | `mekiki_reader/terms.py`（`TERMS`・`SOURCES`・`build_term_index`）・`mekiki_reader/tools.py`（`_term_prepass`・`_expansions`） |
| 出所の検索 | `scripts/find_term_sources.py --terms`（TERMS-SRC-1.0.0。同梱データだけを読む） |

## 規則

- 載せるのは著者が承認した項目だけ。範囲はコーパスが自ら示す対訳と表記揺れに限る（概念レベルの対応は入れない。SPEC §11）。
- 項目の形：id（`M` と数字）・forms_ja・forms_en・sources（コーパス内の出所）・approved_on。起動時に形を確かめ、不正なら起動しない。
- 表の正準 JSON（`{"version", "entries"[id・forms_ja・forms_en・sources・approved_on]}`・sort_keys・ensure_ascii=False・区切りなし）の SHA-256 は `790e124094aeca1ccd3cf72823e9acbd70a897057b12d357eece26486e467be0`。`terms.table_sha256()` が import 時に照合し、違えば起動しない（Q49・Codex① P2-7）。
- 語形は日英あわせて二つ以上。片側だけの行も置ける（0.1.1 で M02 を英語の表記揺れだけの行にしたため。日本語クエリからは当たらず、英語の表記揺れを束ねる働きだけを持つ）。
- 索引：各語形を SEARCH の畳み込み（1.0.0 から不変）にかけ、語形 → 項目 id の表を作る（TERMS-0.1.1 では語形78個、項目どうしの重複なし）。
- 検索での使い方（SEARCH-1.1.0）：
  1. 前処理：畳み込んだクエリの中から、語形（空白や記号を含むものも）を長い順・左から拾い、一つの断片として取り出す。
  2. 断片が語形と一致すれば、その項目の他の語形でも照合する。一致の経路は `match_via` に `term_map:<id>` として記録する（直接の一致は `query`）。
  3. 順位では、語の種類数の次に直接一致を優先する（SEARCH）。
- 一致は語句上の対応であって、意味の一致ではない（limitations に明記）。

## 出所の探し方（TERMS-SRC-1.0.0）

A：T4 本文の「日本語（…英語…）」表記。B：英訳 manifest の unit ごとの ja↔en 共起（訳注を除く）。C：訳注の本文。D：ガイド（THEORY_MAP・FOR_AI_READERS・SOURCE_INDEX・llms.txt）の同じ行。E：読解試験の同じ設問の日英。F：THEORY_MAP の「Japanese public wording」節で「literal translation」と明記された行と、その英語側（題なら冒頭の T5 の英題の行、文なら同節の英語の原文の行）。どれにも当たらない項目は、各語形の出現箇所だけを記す。

## 表（TERMS-0.1.1・承認 2026-09-18）

| ID | 日本語 | 英語（表記揺れを含む） | 出所（機械的な検索・TERMS-SRC-1.0.0） | 候補表の出所（参考） |
|---|---|---|---|---|
| M01 | 仕様／専門性の基質 | specification / Spec. | T4 本文の対訳表記 papers/T4.md:61；T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:61↔T4.en.md:220）；訳注 translations/T4.en.md:227（tn-05） | T4「専門性の基質（specification）」；THEORY_MAP T1 Terms |
| M02 | （なし） | specification cost / Spec.cost / Spec. cost | 英語の表記揺れだけの行（0.1.1 で日本語形「仕様化費用」を外した。同梱ファイルに一度も現れないため）；英語形の出現 papers/T1.md:14・papers/T1.md:20・papers/T1.md:40 ほか | T1（"Spec. cost" 2件・"specification cost" 63件）；T4 |
| M03 | 外化／外化費用 | externalization / externalisation / Ext.cost / externalization cost | T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:19↔T4.en.md:30・T4.md:41↔T4.en.md:126 ほか） | T1（英綴り externalisation）；T2〜T4（米綴り）；THEORY_MAP T1 |
| M04 | 事実／事実認識 | Sein / Sein-type | T4 本文の対訳表記 papers/T4.md:61・papers/T4.md:104・papers/T4.md:116 ほか；T4↔T4.en の manifest 対応で共起 4/7 unit（T4.md:61↔T4.en.md:220・T4.md:104↔T4.en.md:386 ほか） | T4「事実（Sein）」「事実認識（Sein）」 |
| M05 | 価値判断 | Sollen / Sollen-type | T4 本文の対訳表記 papers/T4.md:61・papers/T4.md:69・papers/T4.md:116 ほか；T4↔T4.en の manifest 対応で共起 4/8 unit（T4.md:61↔T4.en.md:220・T4.md:69↔T4.en.md:258 ほか） | T4「価値判断（Sollen）」 |
| M06 | 応答可能性／答える立場 | answerability | T4 本文の対訳表記 papers/T4.md:19・papers/T4.md:21・papers/T4.md:45 ほか；T4↔T4.en の manifest 対応で共起 17/20 unit（T4.md:19↔T4.en.md:30・T4.md:21↔T4.en.md:45 ほか）；ガイドの同じ行 SOURCE_INDEX.md:182；読解試験の日英設問 R06 | T4「応答可能性（answerability）」「答える立場（answerability）」 |
| M07 | 説明責任 | accountability | T4 本文の対訳表記 papers/T4.md:77；T4↔T4.en の manifest 対応で共起 8/9 unit（T4.md:19↔T4.en.md:30・T4.md:45↔T4.en.md:150 ほか） | T4「説明責任（accountability）」 |
| M08 | 引き受け | undertaking | T4↔T4.en の manifest 対応で共起 33/36 unit（T4.md:19↔T4.en.md:30・T4.md:29↔T4.en.md:70 ほか）；ガイドの同じ行 THEORY_MAP.md:134 | T4.en（訳語）；THEORY_MAP T4 Terms；FR L40 |
| M09 | 自分ごと化 | jibungoto-ka | T4↔T4.en の manifest 対応で共起 22/22 unit（T4.md:19↔T4.en.md:30・T4.md:21↔T4.en.md:45 ほか）；訳注 translations/T4.en.md:37（tn-01）；ガイドの同じ行 THEORY_MAP.md:12・THEORY_MAP.md:133 | THEORY_MAP T4 Terms；T4.en |
| M10 | 心理的所有 | psychological ownership | T4 本文の対訳表記 papers/T4.md:228；T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:228↔T4.en.md:907） | T4「心理的所有（psychological ownership）」 |
| M11 | 責任の空隙 | responsibility gap | T4 本文の対訳表記 papers/T4.md:144；T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:144↔T4.en.md:558） | T4「責任の空隙（responsibility gap）」 |
| M12 | 多くの手の問題 | the problem of many hands / many hands | T4 本文の対訳表記 papers/T4.md:144；T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:144↔T4.en.md:558） | T4「多くの手の問題（the problem of many hands）」 |
| M13 | 自惚れ | self-conceit | T4 本文の対訳表記 papers/T4.md:164；T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:85↔T4.en.md:340・T4.md:138↔T4.en.md:529 ほか） | T4「自惚れ（self-conceit）」 |
| M14 | 直接服薬確認療法 | DOTS | T4 本文の対訳表記 papers/T4.md:53；T4↔T4.en の manifest 対応で共起 1/1 unit（T4.md:53↔T4.en.md:182） | T4「直接服薬確認療法（DOTS）」 |
| M15 | 参加 | participation | T4↔T4.en の manifest 対応で共起 4/6 unit（T4.md:19↔T4.en.md:30・T4.md:29↔T4.en.md:70 ほか）；読解試験の日英設問 R06・R07・R08；THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13・THEORY_MAP.md:253↔256 | THEORY_MAP 日本語用語表（遊び／play の説明文）；T5 邦題「参加の非移転性」 |
| M16 | 非移転性 | non-transferability / non-transferable | 読解試験の日英設問 R01；THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13 | THEORY_MAP「Japanese public wording」（邦題） |
| M17 | 尊厳 | dignity | ガイドの同じ行 THEORY_MAP.md:238・SOURCE_INDEX.md:33；読解試験の日英設問 R01・R03・R05・R16；THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13 | THEORY_MAP 邦題「尊厳の可視性」 |
| M18 | 可視性 | visibility | THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:251↔13 | THEORY_MAP 邦題「尊厳の可視性」 |
| M19 | 明晰な没入 | lucid absorption | ガイドの同じ行 THEORY_MAP.md:238 | THEORY_MAP 日本語用語表（知好楽の「楽」） |
| M20 | 遊び | play | ガイドの同じ行 THEORY_MAP.md:240・FOR_AI_READERS.md:36・llms.txt:13；読解試験の日英設問 R03 | THEORY_MAP 日本語用語表；FR L36 |
| M21 | 趣味 | shumi | 訳注 translations/T4.en.md:826（tn-16）；ガイドの同じ行 THEORY_MAP.md:239・FOR_AI_READERS.md:35・SOURCE_INDEX.md:36 ほか；読解試験の日英設問 R17 | THEORY_MAP 日本語用語表；FR L35 |
| M22 | 知好楽の「楽」 | delight | ガイドの同じ行 FOR_AI_READERS.md:34；読解試験の日英設問 R16 | FR L34 |
| M24 | 正統性 | legitimacy | T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:49↔T4.en.md:166・T4.md:51↔T4.en.md:175 ほか） | T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:49↔T4.en.md:166・T4.md:51↔175・T4.md:55↔189・T4.md:85↔340） |
| M25 | 立場 | standing | T4↔T4.en の manifest 対応で共起 10/12 unit（T4.md:29↔T4.en.md:70・T4.md:45↔T4.en.md:150 ほか） | T4↔T4.en の manifest 対応で共起 10/12 unit（T4.md:29↔T4.en.md:70・T4.md:45↔150・T4.md:75↔289・T4.md:77↔296 ほか） |
| M26 | 能力 | ability / capacities | T4↔T4.en の manifest 対応で共起 3/3 unit（T4.md:75↔T4.en.md:289・T4.md:150↔T4.en.md:581 ほか）；読解試験の日英設問 R01 | 出所なし（「能力」を含む3 unit で competence・capability は 0/3。英訳は ability・capacities で 3/3：T4.md:75↔T4.en.md:289・T4.md:150↔581・T4.md:162↔635） |
| M27 | 逆方向 | reverse pathway / reverse | T4↔T4.en の manifest 対応で共起 2/2 unit（T4.md:19↔T4.en.md:30・T4.md:132↔T4.en.md:508）；読解試験の日英設問 R11 | 出所なし（「逆方向経路」「逆方向の経路」は原文に0件。原文の表記は「逆方向」で、同じ unit の英訳に reverse・pathway：T4.md:19↔T4.en.md:30・T4.md:132↔508） |
| M28 | 承認 | endorsement / endorse / approval | T4↔T4.en の manifest 対応で共起 2/5 unit（T4.md:69↔T4.en.md:258・T4.md:192↔T4.en.md:760）；訳注 translations/T4.en.md:303（tn-07） | 機械的には manifest 共起 1/5 unit（T4.md:192↔T4.en.md:760）と tn-07（T4.en.md:303）。ただし tn-07 は「承認」を対象に応じて endorsement／adoption・approval と訳し分け、自動的には recognition としないと述べる。「承認」を含む5 unit は endorse 系・approval で 5/5 |
| M30 | 相互性 | reciprocity / reciprocal | T4↔T4.en の manifest 対応で共起 8/8 unit（T4.md:19↔T4.en.md:30・T4.md:45↔T4.en.md:150 ほか）；読解試験の日英設問 R10 | T4↔T4.en の manifest 対応で共起 8/8 unit（T4.md:19↔T4.en.md:30・T4.md:45↔150・T4.md:79↔311・T4.md:85↔340 ほか） |
| M31 | 主体性 | agency | ガイドの同じ行 SOURCE_INDEX.md:27 | SOURCE_INDEX.md:27 の話題ラベル「T3の主体性・選抜ではない分析 / agency, not diagnosis」 |
| M32 | 事態 | state of affairs | THEORY_MAP の日本語公開表記の節（直訳の行↔英語の行） THEORY_MAP.md:253↔256 | THEORY_MAP「Japanese public wording」（短形・長形） |

## 注記

- M02：日本語形「仕様化費用」は同梱ファイルに一度も現れないため、0.1.1（2026-09-18・著者確定）で外した。英語側の表記揺れ（specification cost・Spec. cost・Spec.cost）だけを登録する。日本語クエリからは当たらない。
- M28：「承認」は recognition として登録しない（訳注 tn-07 が、承認を対象に応じて endorsement・adoption/approval と訳し分け、自動的には recognition としないと述べるため）。
- 候補の M23（委任）・M29（是認）は削除した（同梱ファイルに日本語形が現れない）。
- B の共起は、同じ unit に日本語と英語の語形がそろって現れることを示すだけで、語どうしの訳の対応を一つずつ確かめたものではない。
