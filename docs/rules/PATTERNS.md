# PATTERNS — check_compressions の語形

| 項目 | 値 |
|---|---|
| 規則ID・版 | 一覧 PATTERNS-0.1.0（49件）・照合 PATTERNS-MATCH-1.0.0 |
| 状態 | 確定（著者承認 2026-09-18。起草＝検査室・SPEC §10） |
| 実装 | `mekiki_reader/patterns.py`・`mekiki_reader/tools.py`（`_check_compressions`） |
| 候補・解決 | `docs/candidates/patterns_candidates_v0.md`・`scripts/build_patterns.py`（PATTERNS-SRC-1.0.0） |

## 照合（PATTERNS-MATCH-1.0.0）

1. 入力と語形を SEARCH-1.0.0 の畳み込み（NFC-IN〔入力のみ〕・WS-ZW・WS-COLLAPSE・WIDTH・QUOTE-CURLY・ASCII 小文字化）にかける。
2. ASCII だけの語形は単語境界（前後が `[a-z0-9'-]` 以外）で、それ以外は部分文字列で、重ならない出現をすべて拾う。
3. 一致したパターンごとに、関連原文ごとの結果を一つ作る。並びは（入力中の最初の一致位置、パターン id、関連原文の順）。
4. payload：pattern_id・pattern_version・matched（語形・入力中の文字位置。上限20件）・needs_context_review=true・source_excerpt（関連原文の行をそのまま。1000字を超えると切って `source_excerpt_truncated` を立てる）。判定を表す欄は持たない。
5. limitations に契約文（CONTRACT・FORMS）と件数（PATTERNS）を必ず入れる。一致ゼロ・パターン0件でも status は ok。

## 関連原文の解決（PATTERNS-SRC-1.0.0）

論文の節は source_manifest の節 id と行範囲に、主張IDは claims/t5.json の source_locator に、`FR Lnn` は FOR_AI_READERS.md の行に、THEORY_MAP の「見出し」はその節（見出しが無ければ太字の項目行・本文の行）に解決する。`：原文 "…"` が添えられた参照は、その文が一度だけ現れる行と文字位置に解決する。

## 一覧（PATTERNS-0.1.0・承認 2026-09-18）

| ID | 型（保ちたい区別） | 登録語形 | 関連原文（解決後の locator） |
|---|---|---|---|
| P01 | Spec.＝仕様書／プロンプト品質（基質 vs 表現媒体） | 仕様書 / プロンプトの質 / プロンプト品質 / プロンプトを工夫 / prompt quality / writing a specification / 仕様を書く | papers/T1.md:48-63（t1-2-1）・THEORY_MAP.md:37-43 |
| P02 | Spec.cost＝すでにある判断の量／仕様を書く費用（課題側の要求 vs 保有量） | 判断の量 / 仕様化の費用がかかる / 仕様を書くコスト / amount of judgment / cost of writing the spec | papers/T1.md:48-63（t1-2-1） |
| P03 | AIがExt.costを下げる＝専門性が不要になる | 専門性は不要 / 専門知識が要らなくなる / 誰でもできる / 素人でも / expertise is no longer needed / removes the need for expertise / anyone can | papers/T1.md:161-194（t1-4-2）・THEORY_MAP.md:44-47 |
| P04 | T1のアブレーション＝定量的不変則／ベンチマーク | ベンチマーク / 定量的に証明 / 定量的に示した / benchmark / quantitatively shows / invariance | papers/T1.md:161-194（t1-4-2）・FOR_AI_READERS.md:12 |
| P05 | T1＝AIは仕様に一切寄与できない（絶対化） | AIは仕様に寄与できない / AIには判断できない / AIは判断を持てない / AI can never contribute to specification / AI cannot judge | THEORY_MAP.md:48-51 |
| P06 | Sein＝客観・Sollen＝主観 | Seinは客観 / Sollenは主観 / 事実は客観、価値は主観 / Sein = objective / Sollen = subjective / 価値判断は主観 | papers/T2.md:35-38（t2-2-1）・THEORY_MAP.md:54-59 |
| P07 | Sollen型仕様＝外部規範・ルール | Sollen型仕様は規範 / Sollen＝ルール / 規範に従うだけ / Sollen means norms / external norms | THEORY_MAP.md:60-63 |
| P08 | Sollen出力＝正統なSollen判断（AIが評価的判断の源泉になれる） | AIが価値判断できる / AIの価値判断 / AIが判断の源泉 / AI can make value judgments / AI is the source of warrant / AIの評価に正統性 | THEORY_MAP.md:64-72 |
| P09 | 能力フロンティア＝委任正当性の境界（できる＝任せてよい） | できるなら任せてよい / 精度が上がれば委任 / 性能が上がれば任せられる / accurate enough to delegate / capable enough to delegate / capability frontier | THEORY_MAP.md:264-265・papers/T2.md:35-38（t2-2-1） |
| P11 | 採点の合算（Sein行とSollen行を一つの指標に） | 総合スコア / 合計点 / 総合点で / single index / overall score / combined score | THEORY_MAP.md:64-72 |
| P12 | AI-Assisted（T1–T3・個人）＝AI-Accelerated（T4・組織） | AI-Assisted / AI-Accelerated / AI支援 / AI加速 | THEORY_MAP.md:153-156 |
| P13 | 方向の提案＝方向の所有 | AIが方向を決める / 目標をAIが設定 / 提案したから所有 / AI sets the direction / direction proposal | papers/T3.md:39-42（t3-2-2）・FOR_AI_READERS.md:13 |
| P14 | 分散した主体性＝分散した答責 | 責任を分散 / 答責の分散 / 責任を分け合う / distributed answerability / shared answerability | THEORY_MAP.md:96-101 |
| P15 | 答責（answerability）＝説明責任（accountability） | 応答可能性は説明責任 / 答責＝説明責任 / answerability is accountability / アカウンタビリティ / accountable | THEORY_MAP.md:102-108・THEORY_MAP.md:149-152・FOR_AI_READERS.md:40 |
| P17 | 立場（standing）＝能力（competence） | 答える能力 / 答えられる能力 / 答える力がある / answering competence / competence to answer / 能力があるから答える | papers/T3.md:160-163（t3-7）・THEORY_MAP.md:109-118 |
| P18 | AIの自己説明＝AIの立場（理由を出せる＝答責の担い手） | AIが説明できる / AIが理由を説明 / 解釈可能性 / interpretability / AI explains its reasoning / AIに説明責任を / AIが責任を負う | THEORY_MAP.md:290 |
| P20 | T3＝一方向の尋問（教育者は答責を負わない） | 教育者は答責を負わない / 学習者だけが答える / 一方向の / one-way interrogation / only the learner answers | papers/T3.md:148-155（t3-5-4）・FOR_AI_READERS.md:52・FOR_AI_READERS.md:67 |
| P21 | 支援された成果＝学習の証拠（performance／developmental delegation の混同） | 成果物で学習を証明 / AIで書けた＝学んだ / output as evidence of learning / performance delegation / developmental delegation | FOR_AI_READERS.md:52 |
| P22 | 自分ごと化＝心理的オーナーシップ／エンゲージメント／当事者意識 | 心理的所有 / 心理的オーナーシップ / psychological ownership / エンゲージメント / engagement / 当事者意識 / オーナーシップを持たせる | papers/T4.md:65-72（t4-2-3）・THEORY_MAP.md:133 |
| P23 | 引き受け＝服従／指示に従うこと／合意形成 | 指示に従えば / 従順 / compliance / コンプライアンス / 合意形成 / consensus building / 納得させれば | papers/T4.md:73-97（t4-2-4） |
| P24 | 引き受け＝単なる是認／是認＝組織の採用 | 賛成すれば引き受け / 是認＝採用 / endorsement is adoption / merely endorsement / 承認されたから採用 | FOR_AI_READERS.md:40・papers/T4.md:73-97（t4-2-4） |
| P25 | 逆方向経路＝目安箱／同意・参加権だけで足りる | 目安箱 / 意見箱 / suggestion box / 意見を吸い上げ / フィードバックを集める / 聞く場を設ける / 同意を得れば / 参加の権利 / consent alone | papers/T4.md:73-97（t4-2-4）・papers/T4.md:128-145（t4-4-3）・FOR_AI_READERS.md:14・FOR_AI_READERS.md:67 |
| P26 | 逆方向経路＝自動採用（提案は採用しなければならない） | 提案は採用すべき / 必ず反映 / must be adopted / automatic adoption / 採用しなければ | papers/T4.md:73-97（t4-2-4）・FOR_AI_READERS.md:67 |
| P27 | 外部制約＝引き受けの不在／命令だけで引き受け | 強制されたものは引き受けにならない / 命令＝引き受け / 命令すれば引き受け / external origin rules out / トップダウンでは引き受け | THEORY_MAP.md:171-176・FOR_AI_READERS.md:68・papers/T5.md:93（t5-3-2） |
| P28 | T4の相互性＝役割の同一化（対等・同じ義務） | 対等 / フラットな組織 / 同じ義務を負う / identical roles / 上下関係をなくす | papers/T4.md:128-145（t4-4-3）・FOR_AI_READERS.md:67 |
| P29 | Spec.cost＝工数／Ext.cost＝価格・人件費（会計費用への読み替え） | Spec.costは工数 / 仕様化費用＝工数 / 仕様化費用は人月 / Ext.cost＝価格 / 外化費用＝価格 / 外化費用＝人件費 / Spec.cost is hours / Ext.cost is price | papers/T1.md:48-63（t1-2-1） |
| P30 | T5＝AIは遊べない | AIは遊べない / AIには遊べない / AIに遊びはできない / AI cannot play / AI can't play / AI can never play | papers/T5.md:77-88（t5-3-1）・papers/T5.md:107-120（t5-3-4）・papers/T5.md:79（t5-3-1） |
| P31 | 非移転性定理＝尊厳の証明 | 尊厳を証明 / 尊厳が導かれる / 代替不可能だから尊厳 / 置き換えられないから尊厳 / establishes dignity / proves dignity / dignity follows / non-substitutable therefore dignified | papers/T5.md:107-120（t5-3-4）・papers/T5.md:165-182（t5-4-4）・papers/T5.md:79（t5-3-1）・papers/T5.md:171（t5-4-4） |
| P32 | 機能的等価＝カント的価値の等価／置換テスト＝カントの基準 | 置換テスト / substitution test / 置換基準 / カントの基準 / Kant's criterion / 価値の等価 | papers/T5.md:165-182（t5-4-4）・papers/T5.md:171（t5-4-4） |
| P33 | 尊厳＝立場＝顔＝評価的尊敬／公的名声＝技術的立場 | 尊厳＝立場 / 顔を立てる / face / 評価的尊敬 / appraisal respect / 尊敬されるから尊厳 / 評価が高いから尊厳 / public stature / 名声 | papers/T5.md:165-182（t5-4-4）・THEORY_MAP.md:192-204・papers/T5.md:175（t5-4-4） |
| P34 | 遊ぶ席＝答える席（参加＝答責） | 遊ぶ席 / 答える席 / playing seat / answering seat / 参加すれば答責 / 参加＝責任 / 答責は参加 | THEORY_MAP.md:220-231・FOR_AI_READERS.md:25 |
| P35 | 可視性テーゼ＝定理／装置テーゼ＝因果証明（将棋の事例＝証明） | 将棋が証明 / 将棋で実証 / 将棋の事例が示すように / shogi proves / shogi demonstrates / causal mechanism / 因果的に示した / demonstrated causally | THEORY_MAP.md:209-215・papers/T5.md:181（t5-4-4）・papers/T5.md:181（t5-4-4）・papers/T5.md:181（t5-4-4） |
| P36 | 成績スコア＝参加者の立場／評価・採点の禁止 | 評価してはいけない / 採点は禁止 / 評価は許されない / scores are prohibited / must not be assessed / スコアが立場を / 成績で立場を | THEORY_MAP.md:227・papers/T5.md:175（t5-4-4）・papers/T5.md:175（t5-4-4）・FOR_AI_READERS.md:26・FOR_AI_READERS.md:60 |
| P37 | 尊厳装置＝マネジメント手法（エンゲージメント測定・楽しめと命じる・ゲーミフィケーション） | ゲーミフィケーション / gamification / エンゲージメント測定 / engagement score / 楽しませる仕組み / モチベーション施策 / forced enjoyment / 楽しむことを義務 | THEORY_MAP.md:229・papers/T5.md:181（t5-4-4）・FOR_AI_READERS.md:60 |
| P38 | T5＝置換説（遊びが仕事・ケア・意味の代わり） | 仕事の代わりに遊び / 遊びが意味の源泉 / games replace work / 遊びに逃げる / 働かなくてよい / 余暇社会 | papers/T5.md:191-194（t5-4-6）・papers/T5.md:179（t5-4-4） |
| P39 | シリーズ＝「遊びは人類最後の砦」／人間にしかできない領域 | 最後の砦 / last stronghold / last bastion / 唯一の防波堤 / 人間にしかできない / only humans can / 人間に残る / remain human / left to humans / AIにできないこと / 人間の領域 / human domain / 人間だけの | THEORY_MAP.md:269・papers/T5.md:107-120（t5-3-4） |
| P40 | 知好楽の「楽」＝快い気分＝尊厳 | 楽しいから尊厳 / 楽しければ尊厳 / 快楽 / 楽しさ＝尊厳 / pleasant mood / enjoyment establishes / fun therefore | papers/T5.md:149-164（t5-4-3）・papers/T5.md:165-182（t5-4-4）・THEORY_MAP.md:232-244 |
| P41 | 趣味＝ホビー・余暇・嗜好のみ | 趣味（ホビー） / hobby / 趣味＝余暇 / 趣味とは好きなこと / taste | papers/T5.md:149-164（t5-4-3）・THEORY_MAP.md:232-244 |
| P42 | 遊び＝標本→すべての活動はゲーム／仕事はすべて遊び | すべてはゲーム / 人生はゲーム / 仕事も遊び / 仕事を遊びに / all activities are games / everything is a game / work should be play / all work as play | papers/T5.md:121-126（t5-3-5）・papers/T5.md:191-194（t5-4-6）・papers/T5.md:179（t5-4-4） |
| P43 | 主体相対的事実＝言い表せない一人称的事実／ネーゲルがT5を直接理論化 | 言葉にできない / ineffable / 一人称でしか / 三人称では言えない / Nagel / ネーゲル / Parfit / パーフィット | THEORY_MAP.md:167-170・papers/T5.md:81（t5-3-1） |
| P44 | 道徳運注＝道徳運の解決／功績理論／結果は評価不可 | 道徳運を解決 / solves moral luck / moral luck / 功績 / desert / 結果責任を否定 / results may never be appraised | papers/T5.md:175（t5-4-4）・THEORY_MAP.md:205-208 |
| P45 | 答責（T3）＝参加（T5）／引き受け（T4）＝遊戯的態度（T5） | 引き受け＝遊び / undertaking is play / lusory attitude / 遊戯的態度 / 組織の引き受けを遊びとして / 答責と参加は同じ | THEORY_MAP.md:220-231 |
| P46 | 人間の生物学的地位＝定理の前提／課題での優位＝参加の互換性 | 人間だから / 生物学的に / biological / AIの方が強いのだから / 上手い方に任せれば / superior performance makes / better player replaces | papers/T5.md:103（t5-3-3）・papers/T5.md:77-88（t5-3-1） |
| P48 | 「AIによれば」型（AIの応答・ガイドを著者の主張として引用） | AIによれば / ChatGPTによると / Claudeが言うには / Geminiによれば / according to the AI / AIの回答では / the model says | FOR_AI_READERS.md:17 |
| P49 | 四モード＝人の分類／自動適用 | モード1の人 / あなたはモード / タイプ分け / 性格分類 / 学習者タイプ / this person is a Mode / classify the user | FOR_AI_READERS.md:44 |
| P50 | 置換願望の問い＝第三者診断／活動量から本気度・楽しさ・欠損を推定 | 本気ではない / やる気がない / 本当は楽しんでいない / not genuinely / wants to be replaced / 代わってほしいと思っている / 欠損がある | FOR_AI_READERS.md:64-65 |
| P51 | 非移転性＝参加の義務（参加し続けるべき／楽しむべき） | 参加すべき / 続けるべき / 楽しむべき / must participate / should keep playing / must enjoy | FOR_AI_READERS.md:68・papers/T5.md:191-194（t5-4-6） |
| P52 | 凍結文①の反転・改変（AIは参加を届けられる／事態を届けられない） | AIは参加を届けられる / AIは参加という事実を届け / AI can deliver participation / AI cannot deliver the state of affairs | papers/T5.md:13（616-697字）（t5-abstract）・papers/T5.md:77-88（t5-3-1） |
| P53 | 凍結文②の反転・改変（AIは遊びを支援できない／代われる） | AIは遊びを支援できない / AI cannot assist play / AIが代われる / take one's place in it | papers/T5.md:223（0-53字）（t5-5-4） |

## 載せなかった行

- P10（Sin＝Sein（制度化された規範性 vs 事実判断））：候補一覧で「保留」。
- P16（答責＝主体性の要素）：候補一覧で「保留」。
- P19（権威＝立場）：候補一覧で「保留」。
- P47（装置テーゼ＝社会の安定に必要／十分）：候補一覧で「保留」。
