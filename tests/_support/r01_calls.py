"""R01（再現性）で使う固定の呼び出し。別プロセスからも同じ関数を呼ぶ。"""

from __future__ import annotations

import sys

from mekiki_reader import corpus as C
from mekiki_reader import schema as S
from mekiki_reader import tools as T

CALLS = (
    ("list_papers", ()),
    ("get_section", ("T4", "t4-2-4")),
    ("get_section", ("T4", "paper-t4", "en")),
    ("get_section", ("T1", "t1-2-9")),
    ("search_passages", ("answerability", None, 20)),
    ("search_passages", ("アドヒアランス 自分ごと化 zzqxjvw", None, 20)),
    ("get_claim_record", ("T5-N3",)),
    ("get_claim_record", (None, "dignity")),
    ("get_claim_record", ("T2-A1",)),
    ("verify_quote", ("従業員が遭遇から結晶化させた向きを、正式な検討の回路に入れ",)),
    ("verify_quote", ("the author's r",)),
    ("verify_quote", ("AI can deliver the fact of participation.",)),
    ("check_compressions", ("AIは遊べない",)),
    ("get_reading_guide", ("all",)),
)


def outputs(reader: T.Reader) -> list[str]:
    return [S.to_json(getattr(T, name)(reader, *args)) for name, args in CALLS]


if __name__ == "__main__":
    for line in outputs(T.Reader(C.load_corpus())):
        sys.stdout.write(line + "\n")
