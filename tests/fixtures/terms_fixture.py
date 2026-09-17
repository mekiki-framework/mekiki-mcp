"""T04 の match_via=term_map を確かめるための試験用の用語対応（著者承認済みではない）。"""

from mekiki_reader.terms import TermEntry

TEST_TERMS = (
    TermEntry(
        id="M90",
        forms_ja=("尊厳",),
        forms_en=("dignity",),
        sources=("THEORY_MAP.md（試験用。承認済みの出所ではない）",),
        approved_on="2026-09-18",
    ),
    TermEntry(
        id="M91",
        forms_ja=("仕様化費用",),
        forms_en=("specification cost", "Spec. cost"),
        sources=("papers/T1.md（試験用）",),
        approved_on="2026-09-18",
    ),
)
