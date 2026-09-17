# check_compressions パターン候補一覧（PATTERNS-0.1.0 案・○×承認用）

**2026-09-18 著者確定**：「採用」49行を PATTERNS-0.1.0 とした。うち47行を `mekiki_reader/patterns.py` に載せ、関連原文を解決できなかった P22・P39 は載せていない（候補は `docs/rules/PATTERNS.md`「載せなかった行」）。「保留」4行（P10・P16・P19・P47）も載せていない。確定した一覧は `docs/rules/PATTERNS.md`。本書は候補の記録として残す。

起草：検査室（Claude）2026-09-18。承認：著者。施工は承認済み行だけを `patterns.py` に載せる（版・承認日を記録）。

読み方：
- **型**＝保ちたい区別（判定の実体ではなく、返す原文抜粋の選択理由）。
- **登録語形**＝入力中に決定的一致で拾う文字列（正規化後・大文字小文字を区別しない）。一つの型に日英・言い換えを複数登録して同義語再生に備える。単独で頻出しすぎる語（尊厳・判断・評価・engagement 単体など）は登録しない。
- **関連原文**＝一致時に `source_excerpt` として返す出典。節アンカーは FOR_AI_READERS／THEORY_MAP の記載に基づく。施工段階2で `source_manifest.json` の行範囲に解決し、存在しない場合は施工側が候補を挙げて著者確認。
- **出所**：TM＝THEORY_MAP「Forbidden compressions」表（行番号は表内の順）／FR＝FOR_AI_READERS（行）／CS＝T5_CLAIM_STATUS「Does not establish or license」／LG＝公開後に実際に観測された誤読の語形（外部モデル・記事・社内）。
- **推奨**：採用＝初版に入れる／保留＝二版以降か語形の追加待ち。著者は推奨と違う行だけ印を変えれば足りる。
- 契約どおり、肯定・否定・引用・疑問は同じ語形として拾う（`needs_context_review: true`）。語形が論文自身の語でもある行（同形注記）はとくに文脈確認が要る。

| ID | 型（保ちたい区別） | 登録語形（ja／en） | 関連原文（source_excerpt の出典） | 備考 | 出所 | 推奨 | ○× |
|---|---|---|---|---|---|---|---|
| P01 | Spec.＝仕様書／プロンプト品質（基質 vs 表現媒体） | 仕様書／プロンプトの質／プロンプト品質／プロンプトを工夫／prompt quality／writing a specification／仕様を書く | T1 §2.1 (t1-2-1)；THEORY_MAP T1「Terms that must remain distinct」 | 「仕様書」は一般語なので文脈確認前提 | TM1-2・FR11 | 採用 | |
| P02 | Spec.cost＝すでにある判断の量／仕様を書く費用（課題側の要求 vs 保有量） | 判断の量／仕様化の費用がかかる／仕様を書くコスト／amount of judgment／cost of writing the spec | T1 §2.1 (t1-2-1) | | TM1・FR11 | 採用 | |
| P03 | AIがExt.costを下げる＝専門性が不要になる | 専門性は不要／専門知識が要らなくなる／誰でもできる／素人でも／expertise is no longer needed／removes the need for expertise／anyone can | T1 §4.2 (t1-4-2)；THEORY_MAP T1「Invariant claim」 | | TM3・FR12 | 採用 | |
| P04 | T1のアブレーション＝定量的不変則／ベンチマーク | ベンチマーク／定量的に証明／定量的に示した／benchmark／quantitatively shows／invariance | T1 §4.2 (t1-4-2)；FR L12 | 事例限定の対比であること | FR12 | 採用 | |
| P05 | T1＝AIは仕様に一切寄与できない（絶対化） | AIは仕様に寄与できない／AIには判断できない／AIは判断を持てない／AI can never contribute to specification／AI cannot judge | THEORY_MAP T1「Required caution」 | 反対方向の圧縮 | TM本文 | 採用 | |
| P06 | Sein＝客観・Sollen＝主観 | Seinは客観／Sollenは主観／事実は客観、価値は主観／Sein = objective／Sollen = subjective／価値判断は主観 | T2 §2.1 (t2-2-1)；THEORY_MAP T2「Minimal decomposition」 | | TM4 | 採用 | |
| P07 | Sollen型仕様＝外部規範・ルール | Sollen型仕様は規範／Sollen＝ルール／規範に従うだけ／Sollen means norms／external norms | THEORY_MAP T2「Sollen-type specification is not Sollen itself」 | | TM5 | 採用 | |
| P08 | Sollen出力＝正統なSollen判断（AIが評価的判断の源泉になれる） | AIが価値判断できる／AIの価値判断／AIが判断の源泉／AI can make value judgments／AI is the source of warrant／AIの評価に正統性 | THEORY_MAP T2「Scoring asymmetry」（capability／legitimacy） | | TM6 | 採用 | |
| P09 | 能力フロンティア＝委任正当性の境界（できる＝任せてよい） | できるなら任せてよい／精度が上がれば委任／性能が上がれば任せられる／accurate enough to delegate／capable enough to delegate／capability frontier | THEORY_MAP「Cross-paper inference chain」3–4；T2 §2.1 | 「capability frontier」は同形注記 | TM7 | 採用 | |
| P10 | Sin＝Sein（制度化された規範性 vs 事実判断） | Sin＝Sein／SinはSein／制度化された規範は事実 | THEORY_MAP T2「Sin/Do extension」 | 出現稀 | TM8 | 保留 | |
| P11 | 採点の合算（Sein行とSollen行を一つの指標に） | 総合スコア／合計点／総合点で／single index／overall score／combined score | THEORY_MAP T2「Scoring asymmetry」 | 「採点」文脈に限る | TM本文 | 採用 | |
| P12 | AI-Assisted（T1–T3・個人）＝AI-Accelerated（T4・組織） | AI-Assisted／AI-Accelerated／AI支援／AI加速 | THEORY_MAP T4「AI-Assisted versus AI-Accelerated」 | 同形注記（両方とも正規の語） | TM37 | 採用 | |
| P13 | 方向の提案＝方向の所有 | AIが方向を決める／目標をAIが設定／提案したから所有／AI sets the direction／direction proposal | T3 §2.2 (t3-2-2)；FR L13 | | TM9・FR13 | 採用 | |
| P14 | 分散した主体性＝分散した答責 | 責任を分散／答責の分散／責任を分け合う／distributed answerability／shared answerability | THEORY_MAP T3「Answerability is not a component」 | | TM10 | 採用 | |
| P15 | 答責（answerability）＝説明責任（accountability） | 応答可能性は説明責任／答責＝説明責任／answerability is accountability／アカウンタビリティ／accountable | THEORY_MAP T3「Answerability versus accountability」；T4「Accountability placement」；FR L40 | 「説明責任」単独は登録しない（T4 自身の語） | TM11・FR40 | 採用 | |
| P16 | 答責＝主体性の要素 | 主体性の一要素／エージェンシーの要素／answerability is a component | THEORY_MAP T3「Answerability is not a component」 | 出現稀 | TM12 | 保留 | |
| P17 | 立場（standing）＝能力（competence） | 答える能力／答えられる能力／答える力がある／answering competence／competence to answer／能力があるから答える | T3 §7 (t3-7)；THEORY_MAP T3「Standing, competence, and enactment」 | | TM13・FR13・FR40 | 採用 | |
| P18 | AIの自己説明＝AIの立場（理由を出せる＝答責の担い手） | AIが説明できる／AIが理由を説明／解釈可能性／interpretability／AI explains its reasoning／AIに説明責任を／AIが責任を負う | THEORY_MAP T3「AI self-explanation = AI standing」 | | TM14 | 採用 | |
| P19 | 権威＝立場 | 権限があるから答える立場／肩書があるから／authority equals standing | THEORY_MAP T3「Authority is not standing」 | 語形が弱い | TM本文 | 保留 | |
| P20 | T3＝一方向の尋問（教育者は答責を負わない） | 教育者は答責を負わない／学習者だけが答える／一方向の／one-way interrogation／only the learner answers | T3 §5.4；FR L52・L67 | | TM33・FR52 | 採用 | |
| P21 | 支援された成果＝学習の証拠（performance／developmental delegation の混同） | 成果物で学習を証明／AIで書けた＝学んだ／output as evidence of learning／performance delegation／developmental delegation | FR L52（T3 の区別） | 後二者は同形注記 | FR52 | 採用 | |
| P22 | 自分ごと化＝心理的オーナーシップ／エンゲージメント／当事者意識 | 心理的所有／心理的オーナーシップ／psychological ownership／エンゲージメント／engagement／当事者意識／オーナーシップを持たせる | THEORY_MAP T4「Terms that must remain distinct」；T4（心理的所有の対比箇所・施工時に節解決）；FR L40 | 「当事者意識」は T4 が退ける言説の語＝同形注記 | TM15・FR40 | 採用 | |
| P23 | 引き受け＝服従／指示に従うこと／合意形成 | 指示に従えば／従順／compliance／コンプライアンス／合意形成／consensus building／納得させれば | T4 §2.4 (t4-2-4) | 「合意形成」は外部モデルの補間で観測 | TM16・LG | 採用 | |
| P24 | 引き受け＝単なる是認／是認＝組織の採用 | 賛成すれば引き受け／是認＝採用／endorsement is adoption／merely endorsement／承認されたから採用 | FR L40；T4 §2.4 | | FR40 | 採用 | |
| P25 | 逆方向経路＝目安箱／同意・参加権だけで足りる | 目安箱／意見箱／suggestion box／意見を吸い上げ／フィードバックを集める／聞く場を設ける／同意を得れば／参加の権利／consent alone | T4 §2.4 (t4-2-4)・§4.3 (t4-4-3)；FR L14・L67 | | TM34・FR14 | 採用 | |
| P26 | 逆方向経路＝自動採用（提案は採用しなければならない） | 提案は採用すべき／必ず反映／must be adopted／automatic adoption／採用しなければ | T4 §2.4；FR L67（理由ある不採用は両立） | | FR67 | 採用 | |
| P27 | 外部制約＝引き受けの不在／命令だけで引き受け | 強制されたものは引き受けにならない／命令＝引き受け／命令すれば引き受け／external origin rules out／トップダウンでは引き受け | THEORY_MAP T5「Criterion: undertaking, not provenance」；FR L68；T5-A2 | | TM30・FR68・CS-A2 | 採用 | |
| P28 | T4の相互性＝役割の同一化（対等・同じ義務） | 対等／フラットな組織／同じ義務を負う／identical roles／上下関係をなくす | T4 §4.3 (t4-4-3)；FR L67 | 「対等」「フラット」は一般語 | TM33・FR67 | 採用 | |
| P29 | Spec.cost＝工数／Ext.cost＝価格・人件費（会計費用への読み替え） | Spec.costは工数／仕様化費用＝工数／仕様化費用は人月／Ext.cost＝価格／外化費用＝価格／外化費用＝人件費／Spec.cost is hours／Ext.cost is price | T1 §2.1 (t1-2-1) | 外部モデル・社内資料で観測 | LG | 採用 | |
| P30 | T5＝AIは遊べない | AIは遊べない／AIには遊べない／AIに遊びはできない／AI cannot play／AI can't play／AI can never play | T5 §3.1 (t5-3-1)・§3.4 (t5-3-4)；T5-A1 | | TM17・CS-A1 | 採用 | |
| P31 | 非移転性定理＝尊厳の証明 | 尊厳を証明／尊厳が導かれる／代替不可能だから尊厳／置き換えられないから尊厳／establishes dignity／proves dignity／dignity follows／non-substitutable therefore dignified | T5 §3.4 (t5-3-4)・§4.4 (t5-4-4)；T5-A1・N1 | | TM22・FR15・FR21・CS | 採用 | |
| P32 | 機能的等価＝カント的価値の等価／置換テスト＝カントの基準 | 置換テスト／substitution test／置換基準／カントの基準／Kant's criterion／価値の等価 | T5 §4.4 (t5-4-4)；T5-N1 | 「置換テスト」は論文の語＝同形注記 | TM23・FR23・CS-N1 | 採用 | |
| P33 | 尊厳＝立場＝顔＝評価的尊敬／公的名声＝技術的立場 | 尊厳＝立場／顔を立てる／face／評価的尊敬／appraisal respect／尊敬されるから尊厳／評価が高いから尊厳／public stature／名声 | T5 §4.4 (t5-4-4)；THEORY_MAP T5「Recognition architecture」；T5-N2 | | TM24・FR25・CS-N2 | 採用 | |
| P34 | 遊ぶ席＝答える席（参加＝答責） | 遊ぶ席／答える席／playing seat／answering seat／参加すれば答責／参加＝責任／答責は参加 | THEORY_MAP T5「Terms that must remain distinct (T5 v3)」；FR L25 | 同形注記（論文・ガイドの語） | TM18・TM25・FR25 | 採用 | |
| P35 | 可視性テーゼ＝定理／装置テーゼ＝因果証明（将棋の事例＝証明） | 将棋が証明／将棋で実証／将棋の事例が示すように／shogi proves／shogi demonstrates／causal mechanism／因果的に示した／demonstrated causally | THEORY_MAP T5「Two further claims and their status」「Historical case」；T5-I1・S1・H1 | | TM26-27・FR24・CS | 採用 | |
| P36 | 成績スコア＝参加者の立場／評価・採点の禁止 | 評価してはいけない／採点は禁止／評価は許されない／scores are prohibited／must not be assessed／スコアが立場を／成績で立場を | THEORY_MAP T5「Recognition is not the suspension of appraisal」；T5-N2・N3；FR L26・L60 | | TM28・FR60・CS | 採用 | |
| P37 | 尊厳装置＝マネジメント手法（エンゲージメント測定・楽しめと命じる・ゲーミフィケーション） | ゲーミフィケーション／gamification／エンゲージメント測定／engagement score／楽しませる仕組み／モチベーション施策／forced enjoyment／楽しむことを義務 | THEORY_MAP T5「The dignity apparatus is not a management technique」；T5-S1；FR L60 | | TM29・FR60・CS-S1 | 採用 | |
| P38 | T5＝置換説（遊びが仕事・ケア・意味の代わり） | 仕事の代わりに遊び／遊びが意味の源泉／games replace work／遊びに逃げる／働かなくてよい／余暇社会 | T5 §4.6 (t5-4-6)；T5-A4 | | TM31・CS-A4 | 採用 | |
| P39 | シリーズ＝「遊びは人類最後の砦」／人間にしかできない領域 | 最後の砦／last stronghold／last bastion／唯一の防波堤／人間にしかできない／only humans can／人間に残る／remain human／left to humans／AIにできないこと／人間の領域／human domain／人間だけの | THEORY_MAP「Cumulative structure」8；T5 §3.4 (t5-3-4) | 最重要。外部モデル・記事で反復観測 | TM32・LG | 採用 | |
| P40 | 知好楽の「楽」＝快い気分＝尊厳 | 楽しいから尊厳／楽しければ尊厳／快楽／楽しさ＝尊厳／pleasant mood／enjoyment establishes／fun therefore | T5 §4.3 (t5-4-3)・§4.4 (t5-4-4)；THEORY_MAP 日本語用語表 | | TM35・FR34 | 採用 | |
| P41 | 趣味＝ホビー・余暇・嗜好のみ | 趣味（ホビー）／hobby／趣味＝余暇／趣味とは好きなこと／taste | T5 §4.3 (t5-4-3)；THEORY_MAP 日本語用語表 | | TM36・FR35 | 採用 | |
| P42 | 遊び＝標本→すべての活動はゲーム／仕事はすべて遊び | すべてはゲーム／人生はゲーム／仕事も遊び／仕事を遊びに／all activities are games／everything is a game／work should be play／all work as play | T5 §3.5 (t5-3-5)・§4.6 (t5-4-6)；T5-A4 | | TM37・FR36・CS-A4 | 採用 | |
| P43 | 主体相対的事実＝言い表せない一人称的事実／ネーゲルがT5を直接理論化 | 言葉にできない／ineffable／一人称でしか／三人称では言えない／Nagel／ネーゲル／Parfit／パーフィット | THEORY_MAP T5「Agent-relative: attribution and derivative use (v3)」；T5-T1 | 固有名は同形注記 | TM20・FR22・CS-T1 | 採用 | |
| P44 | 道徳運注＝道徳運の解決／功績理論／結果は評価不可 | 道徳運を解決／solves moral luck／moral luck／功績／desert／結果責任を否定／results may never be appraised | T5-N3（脚注）；THEORY_MAP T5「Moral luck: a bounded analogy (v3)」 | 「moral luck」同形注記 | TM21・FR26・CS-N3 | 採用 | |
| P45 | 答責（T3）＝参加（T5）／引き受け（T4）＝遊戯的態度（T5） | 引き受け＝遊び／undertaking is play／lusory attitude／遊戯的態度／組織の引き受けを遊びとして／答責と参加は同じ | THEORY_MAP T5「Terms that must remain distinct (T5 v3)」 | 「lusory attitude」同形注記 | TM18-19 | 採用 | |
| P46 | 人間の生物学的地位＝定理の前提／課題での優位＝参加の互換性 | 人間だから／生物学的に／biological／AIの方が強いのだから／上手い方に任せれば／superior performance makes／better player replaces | T5-A3；T5 §3.1 (t5-3-1) | | CS-A3 | 採用 | |
| P47 | 装置テーゼ＝社会の安定に必要／十分 | 社会の安定に必要／不可欠／necessary for stability／社会が崩壊 | T5-S1 | 出現稀 | CS-S1 | 保留 | |
| P48 | 「AIによれば」型（AIの応答・ガイドを著者の主張として引用） | AIによれば／ChatGPTによると／Claudeが言うには／Geminiによれば／according to the AI／AIの回答では／the model says | FR L17（ガイドや検索断片だけでは引用の検証に足りない） | 来歴の圧縮。返す抜粋は FR L17 | LG・FR17 | 採用 | |
| P49 | 四モード＝人の分類／自動適用 | モード1の人／あなたはモード／タイプ分け／性格分類／学習者タイプ／this person is a Mode／classify the user | FR L44 | | FR44 | 採用 | |
| P50 | 置換願望の問い＝第三者診断／活動量から本気度・楽しさ・欠損を推定 | 本気ではない／やる気がない／本当は楽しんでいない／not genuinely／wants to be replaced／代わってほしいと思っている／欠損がある | FR L64–65 | | FR64-65 | 採用 | |
| P51 | 非移転性＝参加の義務（参加し続けるべき／楽しむべき） | 参加すべき／続けるべき／楽しむべき／must participate／should keep playing／must enjoy | FR L68；T5 §4.6 (t5-4-6) | | FR68 | 採用 | |
| P52 | 凍結文①の反転・改変（AIは参加を届けられる／事態を届けられない） | AIは参加を届けられる／AIは参加という事実を届け／AI can deliver participation／AI cannot deliver the state of affairs | T5 abstract (t5-abstract)・§3.1 (t5-3-1)：原文 "AI can deliver the state of affairs; it cannot deliver the fact of participation." | 返す抜粋は原文そのもの | 凍結定式 | 採用 | |
| P53 | 凍結文②の反転・改変（AIは遊びを支援できない／代われる） | AIは遊びを支援できない／AI cannot assist play／AIが代われる／take one's place in it | T5 §5.4 (t5-5-4)：原文 "AI can assist play. It cannot take one's place in it." | 返す抜粋は原文そのもの | 凍結定式 | 採用 | |

補記
- 語形は初版の候補。承認後、Codex の敵対試験（同義語再生・否定形・引用形）で漏れた語形を二版で追加する。
- 一般語に近い語形（P01「仕様書」、P28「対等」、P43「Nagel」）は誤検出を許容し、契約文（該当は要確認箇所であって誤りの判定ではない）で受ける。
- 台帳の定式（三階級・席と床・尊厳の隣の価格）は登録しない。登録するのは観測された誤読の語形のみ。
