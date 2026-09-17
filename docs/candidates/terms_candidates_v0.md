# 用語対応表 候補一覧（TERMS-0.1.0 案・○×承認用）

起草：検査室（Claude）2026-09-18。承認：著者。施工は承認済み行だけを `mekiki_reader/terms.py` に載せる（版・承認日を記録）。
範囲：**コーパスが自ら示す対訳と表記揺れに限る**（SPEC §11。概念レベルの対応は入れない）。各行に出所（コーパス内の位置）が要る。「要確認」の行は、施工段階2で Claude Code が T4・T4.en・ガイド類を機械的に検索して出所の行を埋め、見つからない行は落とす。著者の確認は、出所が埋まった後の一回で足りる。
用途：`search_passages` で日本語クエリが英語論文（T1〜T3・T5）に、英語クエリが T4 に届くようにする。一致には `match_via: term_map:<id>` を必ず付ける。

| ID | 日本語 | 英語（表記揺れを含む） | 出所（コーパス内） | 備考 | 推奨 | ○× |
|---|---|---|---|---|---|---|
| M01 | 仕様／専門性の基質 | specification / Spec. | T4「専門性の基質（specification）」；THEORY_MAP T1 Terms | | 採用 | |
| M02 | 仕様化費用 | specification cost / Spec.cost / Spec. cost | T1（"Spec. cost" 2件・"specification cost" 63件）；T4 | 「Spec.cost」「Spec. cost」の揺れを含める | 採用 | |
| M03 | 外化／外化費用 | externalization / externalisation / Ext.cost / externalization cost | T1（英綴り externalisation）；T2〜T4（米綴り）；THEORY_MAP T1 | 英米綴りの両方 | 採用 | |
| M04 | 事実（Sein）／事実認識 | Sein / Sein-type | T4「事実（Sein）」「事実認識（Sein）」 | | 採用 | |
| M05 | 価値判断（Sollen） | Sollen / Sollen-type | T4「価値判断（Sollen）」 | | 採用 | |
| M06 | 応答可能性／答える立場 | answerability | T4「応答可能性（answerability）」「答える立場（answerability）」 | 「答責」はコーパス外の訳語のため入れない | 採用 | |
| M07 | 説明責任 | accountability | T4「説明責任（accountability）」 | | 採用 | |
| M08 | 引き受け | undertaking | T4.en（訳語）；THEORY_MAP T4 Terms；FR L40 | 出所は T4.en の訳注または manifest 対応で確認 | 採用 | |
| M09 | 自分ごと化 | jibungoto-ka | THEORY_MAP T4 Terms；T4.en | | 採用 | |
| M10 | 心理的所有 | psychological ownership | T4「心理的所有（psychological ownership）」 | | 採用 | |
| M11 | 責任の空隙 | responsibility gap | T4「責任の空隙（responsibility gap）」 | | 採用 | |
| M12 | 多くの手の問題 | the problem of many hands / many hands | T4「多くの手の問題（the problem of many hands）」 | | 採用 | |
| M13 | 自惚れ | self-conceit | T4「自惚れ（self-conceit）」 | | 採用 | |
| M14 | 直接服薬確認療法 | DOTS | T4「直接服薬確認療法（DOTS）」 | 事例語 | 採用 | |
| M15 | 参加 | participation | THEORY_MAP 日本語用語表（遊び／play の説明文）；T5 邦題「参加の非移転性」 | | 採用 | |
| M16 | 非移転性 | non-transferability / non-transferable | THEORY_MAP「Japanese public wording」（邦題） | | 採用 | |
| M17 | 尊厳 | dignity | THEORY_MAP 邦題「尊厳の可視性」 | | 採用 | |
| M18 | 可視性 | visibility | THEORY_MAP 邦題「尊厳の可視性」 | | 採用 | |
| M19 | 明晰な没入 | lucid absorption | THEORY_MAP 日本語用語表（知好楽の「楽」） | | 採用 | |
| M20 | 遊び | play | THEORY_MAP 日本語用語表；FR L36 | 「play」は display 等を含む部分一致を避け単語境界で | 採用 | |
| M21 | 趣味 | shumi | THEORY_MAP 日本語用語表；FR L35 | | 採用 | |
| M22 | 知好楽の「楽」 | delight | FR L34 | | 採用 | |
| M23 | 委任 | delegation | 出所なし（「委任」は同梱の md・txt に0件） | | 要確認 | |
| M24 | 正統性 | legitimacy | T4↔T4.en の manifest 対応で共起 4/4 unit（T4.md:49↔T4.en.md:166・T4.md:51↔175・T4.md:55↔189・T4.md:85↔340） | | 要確認 | |
| M25 | 立場 | standing | T4↔T4.en の manifest 対応で共起 10/12 unit（T4.md:29↔T4.en.md:70・T4.md:45↔150・T4.md:75↔289・T4.md:77↔296 ほか） | | 要確認 | |
| M26 | 能力 | competence / capability | 出所なし（「能力」を含む3 unit で competence・capability は 0/3。英訳は ability・capacities で 3/3：T4.md:75↔T4.en.md:289・T4.md:150↔581・T4.md:162↔635） | | 要確認 | |
| M27 | 逆方向経路／逆方向の経路 | reverse pathway | 出所なし（「逆方向経路」「逆方向の経路」は原文に0件。原文の表記は「逆方向」で、同じ unit の英訳に reverse・pathway：T4.md:19↔T4.en.md:30・T4.md:132↔508） | | 要確認 | |
| M28 | 承認 | recognition | 機械的には manifest 共起 1/5 unit（T4.md:192↔T4.en.md:760）と tn-07（T4.en.md:303）。ただし tn-07 は「承認」を対象に応じて endorsement／adoption・approval と訳し分け、自動的には recognition としないと述べる。「承認」を含む5 unit は endorse 系・approval で 5/5 | 「承認」は endorsement の訳でもありうる | 要確認 | |
| M29 | 是認 | endorsement | 出所なし（「是認」は同梱の md・txt に0件。英訳の endorse 系は原文の「承認」に対応：M28 の欄） | | 要確認 | |
| M30 | 相互性 | reciprocity / reciprocal | T4↔T4.en の manifest 対応で共起 8/8 unit（T4.md:19↔T4.en.md:30・T4.md:45↔150・T4.md:79↔311・T4.md:85↔340 ほか） | | 要確認 | |
| M31 | 主体性 | agency | SOURCE_INDEX.md:27 の話題ラベル「T3の主体性・選抜ではない分析 / agency, not diagnosis」 | | 要確認 | |
| M32 | 事態 | state of affairs | THEORY_MAP「Japanese public wording」（短形・長形） | 凍結文の対訳 | 採用 | |

補記
- M23〜M31 の出所欄は、施工段階2（2026-09-18）に `scripts/find_term_sources.py`（TERMS-SRC-1.0.0）で機械的に検索して埋めた。判定は候補表の語形による（A：T4 本文の対訳表記、B：manifest の unit ごとの ja↔en 共起、C：訳注、D：ガイドの同じ行）。「出所なし」の行と M28 の注記は、語形の見直しか削除を著者が判断する。表は terms.py にまだ載せていない。
- M23〜M31 は T4.en の manifest（sourceUnits の ja↔en 対応）で機械的に確かめられる。訳注（TN01〜TN16）由来の対応は出所欄に「TN」と明記する。
- 同一の日本語に複数の英語（M26・M28）が対応する場合は分けて登録し、`match_via` で区別する。
