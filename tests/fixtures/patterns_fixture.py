"""T11 用の試験パターン（著者承認済みではない。テストが Reader の内部引数でだけ注入する）。"""

from mekiki_reader.patterns import Pattern, RelatedSource

TEST_PATTERNS = (
    Pattern(
        id="P-T01",
        version="TEST-1",
        surface_forms=("AIは遊べない", "AI cannot play"),
        related_sources=(RelatedSource("papers/T5.md", 223, 223, "t5-5-4"),),
        approved_on="2026-09-18",
    ),
    Pattern(
        id="P-T02",
        version="TEST-1",
        surface_forms=("最後の砦", "last stronghold"),
        related_sources=(
            RelatedSource("papers/T5.md", 13, 13, "t5-abstract"),
            RelatedSource("FOR_AI_READERS.md", 71, 71),
        ),
        approved_on="2026-09-18",
    ),
)

# 肯定・否定・引用・疑問（SPEC §5.6・T11）。どれも同じ語形を含む。
FORM_CASES = (
    ("affirmative", "AIは遊べない。"),
    ("negative", "AIは遊べないわけではない。"),
    ("quotation", "「AIは遊べない」と書く人がいる。"),
    ("question", "AIは遊べないのか？"),
    ("affirmative-en", "Some say AI cannot play."),
    ("negative-en", "It is not true that AI cannot play."),
    ("quotation-en", "The slogan \"AI cannot play\" circulates."),
    ("question-en", "Is it the case that AI cannot play?"),
)
