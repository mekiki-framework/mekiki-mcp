"""check_compressions の圧縮候補パターン（PATTERNS・docs/rules/PATTERNS.md）。

載せるのは著者が承認した、版番号つきの語形だけ（CLAUDE.md 絶対規則9・SPEC §5.6）。承認前は空で起動する。
候補は docs/candidates/patterns_candidates_v0.md（未承認）で、ここには載せない。
試験用のパターンは tests/fixtures/ にあり、テストが内部引数でだけ注入する。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Iterable

from .corpus import is_blank
from .schema import SOURCE_KIND_BY_PATH

PATTERNS_VERSION = "PATTERNS-0.1.1"
APPROVED_ON = "2026-09-18"
MATCH_RULE = "PATTERNS-MATCH-1.0.0"
RELATED_KINDS = frozenset({"paper_md", "theory_map", "reading_guide"})

_ID_RE = re.compile(r"^P[0-9A-Z-]{1,16}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


@dataclass(frozen=True)
class RelatedSource:
    """一致時に source_excerpt として返す原文の位置（同梱ファイル・1 始まり・終端を含む）。"""

    path: str
    line_start: int
    line_end: int
    anchor: str | None = None  # 論文の節 id（論文以外は None）
    char_start: int | None = None  # 1行の中の文字位置（凍結文など、文そのものを返す場合）
    char_end: int | None = None


@dataclass(frozen=True)
class Pattern:
    id: str
    version: str
    surface_forms: tuple[str, ...]
    related_sources: tuple[RelatedSource, ...]
    approved_on: str
    match_rule: str = MATCH_RULE


# 著者承認済みのパターン（PATTERNS-0.1.1・承認 2026-09-18・docs/rules/PATTERNS.md）。
# 候補は docs/candidates/patterns_candidates_v0.md、関連原文の解決は scripts/build_patterns.py。
PATTERNS: tuple[Pattern, ...] = (
    Pattern(
        id='P01',
        version=PATTERNS_VERSION,
        surface_forms=(
            '仕様書',
            'プロンプトの質',
            'プロンプト品質',
            'プロンプトを工夫',
            'prompt quality',
            'writing a specification',
            '仕様を書く',
        ),
        related_sources=(
            RelatedSource('papers/T1.md', 48, 63, 't1-2-1'),
            RelatedSource('THEORY_MAP.md', 37, 43, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P02',
        version=PATTERNS_VERSION,
        surface_forms=(
            '判断の量',
            '仕様化の費用がかかる',
            '仕様を書くコスト',
            'amount of judgment',
            'cost of writing the spec',
        ),
        related_sources=(
            RelatedSource('papers/T1.md', 48, 63, 't1-2-1'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P03',
        version=PATTERNS_VERSION,
        surface_forms=(
            '専門性は不要',
            '専門知識が要らなくなる',
            '誰でもできる',
            '素人でも',
            'expertise is no longer needed',
            'removes the need for expertise',
            'anyone can',
        ),
        related_sources=(
            RelatedSource('papers/T1.md', 161, 194, 't1-4-2'),
            RelatedSource('THEORY_MAP.md', 44, 47, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P04',
        version=PATTERNS_VERSION,
        surface_forms=(
            'ベンチマーク',
            '定量的に証明',
            '定量的に示した',
            'benchmark',
            'quantitatively shows',
            'invariance',
        ),
        related_sources=(
            RelatedSource('papers/T1.md', 161, 194, 't1-4-2'),
            RelatedSource('FOR_AI_READERS.md', 12, 12, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P05',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIは仕様に寄与できない',
            'AIには判断できない',
            'AIは判断を持てない',
            'AI can never contribute to specification',
            'AI cannot judge',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 48, 51, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P06',
        version=PATTERNS_VERSION,
        surface_forms=(
            'Seinは客観',
            'Sollenは主観',
            '事実は客観、価値は主観',
            'Sein = objective',
            'Sollen = subjective',
            '価値判断は主観',
        ),
        related_sources=(
            RelatedSource('papers/T2.md', 35, 38, 't2-2-1'),
            RelatedSource('THEORY_MAP.md', 54, 59, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P07',
        version=PATTERNS_VERSION,
        surface_forms=(
            'Sollen型仕様は規範',
            'Sollen＝ルール',
            '規範に従うだけ',
            'Sollen means norms',
            'external norms',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 60, 63, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P08',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIが価値判断できる',
            'AIの価値判断',
            'AIが判断の源泉',
            'AI can make value judgments',
            'AI is the source of warrant',
            'AIの評価に正統性',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 64, 72, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P09',
        version=PATTERNS_VERSION,
        surface_forms=(
            'できるなら任せてよい',
            '精度が上がれば委任',
            '性能が上がれば任せられる',
            'accurate enough to delegate',
            'capable enough to delegate',
            'capability frontier',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 264, 265, None),
            RelatedSource('papers/T2.md', 35, 38, 't2-2-1'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P11',
        version=PATTERNS_VERSION,
        surface_forms=(
            '総合スコア',
            '合計点',
            '総合点で',
            'single index',
            'overall score',
            'combined score',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 64, 72, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P12',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AI-Assisted',
            'AI-Accelerated',
            'AI支援',
            'AI加速',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 153, 156, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P13',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIが方向を決める',
            '目標をAIが設定',
            '提案したから所有',
            'AI sets the direction',
            'direction proposal',
        ),
        related_sources=(
            RelatedSource('papers/T3.md', 39, 42, 't3-2-2'),
            RelatedSource('FOR_AI_READERS.md', 13, 13, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P14',
        version=PATTERNS_VERSION,
        surface_forms=(
            '責任を分散',
            '答責の分散',
            '責任を分け合う',
            'distributed answerability',
            'shared answerability',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 96, 101, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P15',
        version=PATTERNS_VERSION,
        surface_forms=(
            '応答可能性は説明責任',
            '答責＝説明責任',
            'answerability is accountability',
            'アカウンタビリティ',
            'accountable',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 102, 108, None),
            RelatedSource('THEORY_MAP.md', 149, 152, None),
            RelatedSource('FOR_AI_READERS.md', 40, 40, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P17',
        version=PATTERNS_VERSION,
        surface_forms=(
            '答える能力',
            '答えられる能力',
            '答える力がある',
            'answering competence',
            'competence to answer',
            '能力があるから答える',
        ),
        related_sources=(
            RelatedSource('papers/T3.md', 160, 163, 't3-7'),
            RelatedSource('THEORY_MAP.md', 109, 118, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P18',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIが説明できる',
            'AIが理由を説明',
            '解釈可能性',
            'interpretability',
            'AI explains its reasoning',
            'AIに説明責任を',
            'AIが責任を負う',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 290, 290, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P20',
        version=PATTERNS_VERSION,
        surface_forms=(
            '教育者は答責を負わない',
            '学習者だけが答える',
            '一方向の',
            'one-way interrogation',
            'only the learner answers',
        ),
        related_sources=(
            RelatedSource('papers/T3.md', 148, 155, 't3-5-4'),
            RelatedSource('FOR_AI_READERS.md', 52, 52, None),
            RelatedSource('FOR_AI_READERS.md', 67, 67, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P21',
        version=PATTERNS_VERSION,
        surface_forms=(
            '成果物で学習を証明',
            'AIで書けた＝学んだ',
            'output as evidence of learning',
            'performance delegation',
            'developmental delegation',
        ),
        related_sources=(
            RelatedSource('FOR_AI_READERS.md', 52, 52, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P22',
        version=PATTERNS_VERSION,
        surface_forms=(
            '心理的所有',
            '心理的オーナーシップ',
            'psychological ownership',
            'エンゲージメント',
            'engagement',
            '当事者意識',
            'オーナーシップを持たせる',
        ),
        related_sources=(
            RelatedSource('papers/T4.md', 65, 72, 't4-2-3'),
            RelatedSource('THEORY_MAP.md', 133, 133, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P23',
        version=PATTERNS_VERSION,
        surface_forms=(
            '指示に従えば',
            '従順',
            'compliance',
            'コンプライアンス',
            '合意形成',
            'consensus building',
            '納得させれば',
        ),
        related_sources=(
            RelatedSource('papers/T4.md', 73, 97, 't4-2-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P24',
        version=PATTERNS_VERSION,
        surface_forms=(
            '賛成すれば引き受け',
            '是認＝採用',
            'endorsement is adoption',
            'merely endorsement',
            '承認されたから採用',
        ),
        related_sources=(
            RelatedSource('FOR_AI_READERS.md', 40, 40, None),
            RelatedSource('papers/T4.md', 73, 97, 't4-2-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P25',
        version=PATTERNS_VERSION,
        surface_forms=(
            '目安箱',
            '意見箱',
            'suggestion box',
            '意見を吸い上げ',
            'フィードバックを集める',
            '聞く場を設ける',
            '同意を得れば',
            '参加の権利',
            'consent alone',
        ),
        related_sources=(
            RelatedSource('papers/T4.md', 73, 97, 't4-2-4'),
            RelatedSource('papers/T4.md', 128, 145, 't4-4-3'),
            RelatedSource('FOR_AI_READERS.md', 14, 14, None),
            RelatedSource('FOR_AI_READERS.md', 67, 67, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P26',
        version=PATTERNS_VERSION,
        surface_forms=(
            '提案は採用すべき',
            '必ず反映',
            'must be adopted',
            'automatic adoption',
            '採用しなければ',
        ),
        related_sources=(
            RelatedSource('papers/T4.md', 73, 97, 't4-2-4'),
            RelatedSource('FOR_AI_READERS.md', 67, 67, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P27',
        version=PATTERNS_VERSION,
        surface_forms=(
            '強制されたものは引き受けにならない',
            '命令＝引き受け',
            '命令すれば引き受け',
            'external origin rules out',
            'トップダウンでは引き受け',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 171, 176, None),
            RelatedSource('FOR_AI_READERS.md', 68, 68, None),
            RelatedSource('papers/T5.md', 93, 93, 't5-3-2'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P28',
        version=PATTERNS_VERSION,
        surface_forms=(
            '対等',
            'フラットな組織',
            '同じ義務を負う',
            'identical roles',
            '上下関係をなくす',
        ),
        related_sources=(
            RelatedSource('papers/T4.md', 128, 145, 't4-4-3'),
            RelatedSource('FOR_AI_READERS.md', 67, 67, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P29',
        version=PATTERNS_VERSION,
        surface_forms=(
            'Spec.costは工数',
            '仕様化費用＝工数',
            '仕様化費用は人月',
            'Ext.cost＝価格',
            '外化費用＝価格',
            '外化費用＝人件費',
            'Spec.cost is hours',
            'Ext.cost is price',
        ),
        related_sources=(
            RelatedSource('papers/T1.md', 48, 63, 't1-2-1'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P30',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIは遊べない',
            'AIには遊べない',
            'AIに遊びはできない',
            'AI cannot play',
            "AI can't play",
            'AI can never play',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 77, 88, 't5-3-1'),
            RelatedSource('papers/T5.md', 107, 120, 't5-3-4'),
            RelatedSource('papers/T5.md', 79, 79, 't5-3-1'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P31',
        version=PATTERNS_VERSION,
        surface_forms=(
            '尊厳を証明',
            '尊厳が導かれる',
            '代替不可能だから尊厳',
            '置き換えられないから尊厳',
            'establishes dignity',
            'proves dignity',
            'dignity follows',
            'non-substitutable therefore dignified',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 107, 120, 't5-3-4'),
            RelatedSource('papers/T5.md', 165, 182, 't5-4-4'),
            RelatedSource('papers/T5.md', 79, 79, 't5-3-1'),
            RelatedSource('papers/T5.md', 171, 171, 't5-4-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P32',
        version=PATTERNS_VERSION,
        surface_forms=(
            '置換テスト',
            'substitution test',
            '置換基準',
            'カントの基準',
            "Kant's criterion",
            '価値の等価',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 165, 182, 't5-4-4'),
            RelatedSource('papers/T5.md', 171, 171, 't5-4-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P33',
        version=PATTERNS_VERSION,
        surface_forms=(
            '尊厳＝立場',
            '顔を立てる',
            'face',
            '評価的尊敬',
            'appraisal respect',
            '尊敬されるから尊厳',
            '評価が高いから尊厳',
            'public stature',
            '名声',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 165, 182, 't5-4-4'),
            RelatedSource('THEORY_MAP.md', 192, 204, None),
            RelatedSource('papers/T5.md', 175, 175, 't5-4-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P34',
        version=PATTERNS_VERSION,
        surface_forms=(
            '遊ぶ席',
            '答える席',
            'playing seat',
            'answering seat',
            '参加すれば答責',
            '参加＝責任',
            '答責は参加',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 220, 231, None),
            RelatedSource('FOR_AI_READERS.md', 25, 25, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P35',
        version=PATTERNS_VERSION,
        surface_forms=(
            '将棋が証明',
            '将棋で実証',
            '将棋の事例が示すように',
            'shogi proves',
            'shogi demonstrates',
            'causal mechanism',
            '因果的に示した',
            'demonstrated causally',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 209, 215, None),
            RelatedSource('papers/T5.md', 181, 181, 't5-4-4'),
            RelatedSource('papers/T5.md', 181, 181, 't5-4-4'),
            RelatedSource('papers/T5.md', 181, 181, 't5-4-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P36',
        version=PATTERNS_VERSION,
        surface_forms=(
            '評価してはいけない',
            '採点は禁止',
            '評価は許されない',
            'scores are prohibited',
            'must not be assessed',
            'スコアが立場を',
            '成績で立場を',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 227, 227, None),
            RelatedSource('papers/T5.md', 175, 175, 't5-4-4'),
            RelatedSource('papers/T5.md', 175, 175, 't5-4-4'),
            RelatedSource('FOR_AI_READERS.md', 26, 26, None),
            RelatedSource('FOR_AI_READERS.md', 60, 60, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P37',
        version=PATTERNS_VERSION,
        surface_forms=(
            'ゲーミフィケーション',
            'gamification',
            'エンゲージメント測定',
            'engagement score',
            '楽しませる仕組み',
            'モチベーション施策',
            'forced enjoyment',
            '楽しむことを義務',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 229, 229, None),
            RelatedSource('papers/T5.md', 181, 181, 't5-4-4'),
            RelatedSource('FOR_AI_READERS.md', 60, 60, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P38',
        version=PATTERNS_VERSION,
        surface_forms=(
            '仕事の代わりに遊び',
            '遊びが意味の源泉',
            'games replace work',
            '遊びに逃げる',
            '働かなくてよい',
            '余暇社会',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 191, 194, 't5-4-6'),
            RelatedSource('papers/T5.md', 179, 179, 't5-4-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P39',
        version=PATTERNS_VERSION,
        surface_forms=(
            '最後の砦',
            'last stronghold',
            'last bastion',
            '唯一の防波堤',
            '人間にしかできない',
            'only humans can',
            '人間に残る',
            'remain human',
            'left to humans',
            'AIにできないこと',
            '人間の領域',
            'human domain',
            '人間だけの',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 269, 269, None),
            RelatedSource('papers/T5.md', 107, 120, 't5-3-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P40',
        version=PATTERNS_VERSION,
        surface_forms=(
            '楽しいから尊厳',
            '楽しければ尊厳',
            '快楽',
            '楽しさ＝尊厳',
            'pleasant mood',
            'enjoyment establishes',
            'fun therefore',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 149, 164, 't5-4-3'),
            RelatedSource('papers/T5.md', 165, 182, 't5-4-4'),
            RelatedSource('THEORY_MAP.md', 232, 244, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P41',
        version=PATTERNS_VERSION,
        surface_forms=(
            '趣味（ホビー）',
            'hobby',
            '趣味＝余暇',
            '趣味とは好きなこと',
            'taste',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 149, 164, 't5-4-3'),
            RelatedSource('THEORY_MAP.md', 232, 244, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P42',
        version=PATTERNS_VERSION,
        surface_forms=(
            'すべてはゲーム',
            '人生はゲーム',
            '仕事も遊び',
            '仕事を遊びに',
            'all activities are games',
            'everything is a game',
            'work should be play',
            'all work as play',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 121, 126, 't5-3-5'),
            RelatedSource('papers/T5.md', 191, 194, 't5-4-6'),
            RelatedSource('papers/T5.md', 179, 179, 't5-4-4'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P43',
        version=PATTERNS_VERSION,
        surface_forms=(
            '言葉にできない',
            'ineffable',
            '一人称でしか',
            '三人称では言えない',
            'Nagel',
            'ネーゲル',
            'Parfit',
            'パーフィット',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 167, 170, None),
            RelatedSource('papers/T5.md', 81, 81, 't5-3-1'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P44',
        version=PATTERNS_VERSION,
        surface_forms=(
            '道徳運を解決',
            'solves moral luck',
            'moral luck',
            '功績',
            'desert',
            '結果責任を否定',
            'results may never be appraised',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 175, 175, 't5-4-4'),
            RelatedSource('THEORY_MAP.md', 205, 208, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P45',
        version=PATTERNS_VERSION,
        surface_forms=(
            '引き受け＝遊び',
            'undertaking is play',
            'lusory attitude',
            '遊戯的態度',
            '組織の引き受けを遊びとして',
            '答責と参加は同じ',
        ),
        related_sources=(
            RelatedSource('THEORY_MAP.md', 220, 231, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P46',
        version=PATTERNS_VERSION,
        surface_forms=(
            '人間だから',
            '生物学的に',
            'biological',
            'AIの方が強いのだから',
            '上手い方に任せれば',
            'superior performance makes',
            'better player replaces',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 103, 103, 't5-3-3'),
            RelatedSource('papers/T5.md', 77, 88, 't5-3-1'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P48',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIによれば',
            'ChatGPTによると',
            'Claudeが言うには',
            'Geminiによれば',
            'according to the AI',
            'AIの回答では',
            'the model says',
        ),
        related_sources=(
            RelatedSource('FOR_AI_READERS.md', 17, 17, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P49',
        version=PATTERNS_VERSION,
        surface_forms=(
            'モード1の人',
            'あなたはモード',
            'タイプ分け',
            '性格分類',
            '学習者タイプ',
            'this person is a Mode',
            'classify the user',
        ),
        related_sources=(
            RelatedSource('FOR_AI_READERS.md', 44, 44, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P50',
        version=PATTERNS_VERSION,
        surface_forms=(
            '本気ではない',
            'やる気がない',
            '本当は楽しんでいない',
            'not genuinely',
            'wants to be replaced',
            '代わってほしいと思っている',
            '欠損がある',
        ),
        related_sources=(
            RelatedSource('FOR_AI_READERS.md', 64, 65, None),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P51',
        version=PATTERNS_VERSION,
        surface_forms=(
            '参加すべき',
            '続けるべき',
            '楽しむべき',
            'must participate',
            'should keep playing',
            'must enjoy',
        ),
        related_sources=(
            RelatedSource('FOR_AI_READERS.md', 68, 68, None),
            RelatedSource('papers/T5.md', 191, 194, 't5-4-6'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P52',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIは参加を届けられる',
            'AIは参加という事実を届け',
            'AI can deliver participation',
            'AI cannot deliver the state of affairs',
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 13, 13, 't5-abstract', char_start=616, char_end=697),
            RelatedSource('papers/T5.md', 77, 88, 't5-3-1'),
        ),
        approved_on=APPROVED_ON,
    ),
    Pattern(
        id='P53',
        version=PATTERNS_VERSION,
        surface_forms=(
            'AIは遊びを支援できない',
            'AI cannot assist play',
            'AIが代われる',
            "take one's place in it",
        ),
        related_sources=(
            RelatedSource('papers/T5.md', 223, 223, 't5-5-4', char_start=0, char_end=53),
        ),
        approved_on=APPROVED_ON,
    ),
)


def validate_patterns(corpus, patterns: Iterable[Pattern]) -> tuple[Pattern, ...]:
    """パターンの形と関連原文の実在を検査する。不正なら ValueError。"""
    seen: set[str] = set()
    out = []
    for p in patterns:
        if not isinstance(p, Pattern) or not _ID_RE.match(p.id) or p.id in seen:
            raise ValueError(f"invalid or duplicate pattern id: {getattr(p, 'id', p)!r}")
        if p.match_rule != MATCH_RULE or not p.version or not _DATE_RE.match(p.approved_on or ""):
            raise ValueError(f"{p.id}: match_rule/version/approved_on")
        if not p.surface_forms or any(not isinstance(f, str) or is_blank(f) for f in p.surface_forms):
            raise ValueError(f"{p.id}: surface_forms")
        if not p.related_sources:
            raise ValueError(f"{p.id}: related_sources")
        for rs in p.related_sources:
            if SOURCE_KIND_BY_PATH.get(rs.path) not in RELATED_KINDS:
                raise ValueError(f"{p.id}: related source kind for {rs.path}")
            lines = corpus.lines.get(rs.path)
            if lines is None or not (1 <= rs.line_start <= rs.line_end <= len(lines)):
                raise ValueError(f"{p.id}: related source {rs.path}:{rs.line_start}-{rs.line_end}")
            if (rs.char_start is None) != (rs.char_end is None):
                raise ValueError(f"{p.id}: char_start と char_end はそろって指定する")
            if rs.char_start is not None:
                if rs.line_start != rs.line_end:
                    raise ValueError(f"{p.id}: 文字位置の指定は1行のときだけ")
                if not (0 <= rs.char_start < rs.char_end <= len(lines[rs.line_start - 1])):
                    raise ValueError(f"{p.id}: 文字位置 {rs.char_start}-{rs.char_end} が行の外")
            paper = next((x for x in corpus.papers.values() if x.path == rs.path), None)
            if paper is not None:
                sec = paper.section(rs.anchor) if rs.anchor else None
                if sec is None or not (sec.line_start <= rs.line_start and rs.line_end <= sec.line_end):
                    raise ValueError(f"{p.id}: anchor {rs.anchor!r} does not contain the lines")
            elif rs.anchor is not None:
                raise ValueError(f"{p.id}: anchor is only for papers")
        seen.add(p.id)
        out.append(p)
    return tuple(sorted(out, key=lambda p: p.id))


def table_rows() -> list[dict]:
    """表の正準形（Pattern の全欄）。SHA-256 の対象（Q49・Codex① P2-7）。

    `asdict` で作るので、欄を足したら自動的に正準形に入り、ハッシュが変わって気づける。
    この二つは `scripts/build_patterns.py --write` が書き換える範囲の外に置く（消えないように）。
    """
    return [asdict(p) for p in PATTERNS]


def table_sha256() -> str:
    raw = json.dumps({"version": PATTERNS_VERSION, "patterns": table_rows()},
                     sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# 表の正準 JSON の SHA-256（Q49）。表を変えたら版を上げ、この値と docs/rules/PATTERNS.md を更新する。
PATTERNS_TABLE_SHA256 = "92666827a79b31b55c0fa1b424f7be9e4891b97fab044d316b2622ec1a3a304b"
if table_sha256() != PATTERNS_TABLE_SHA256:  # pragma: no cover - 表と定数の食い違いは import 時に止める
    raise RuntimeError(f"PATTERNS table hash mismatch: {table_sha256()}")
