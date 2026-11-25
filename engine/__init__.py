"""Per-game rules. Every entry of GAMES provides:

NAMES                     stat names, in display order
classes(char)             class keys the character can end in
calculate(char, key, db)  average stats for one class key (see common.simulate)
direct(char)              class key of the character's default promotion
tier(cls)                 "special", "promo" or "" for a class
SPECIAL_CLASSES           starting classes the sidebar's "special" filter shows
RANK_ALL_CLASSES          optional, default False: the leaderboard ranks every final-class path of
                          every character instead of only their default promotion
"""
from types import SimpleNamespace

from engine import fe5, fe6, fe7, fe8, fe9, fe10, fe11_12


def _ds(classes):
    return SimpleNamespace(**{**vars(fe11_12), "classes": classes})


GAMES = {
    "fe5": fe5,
    "fe6": fe6,
    "fe7": fe7,
    "fe8": fe8,
    "fe9": fe9,
    "fe10": fe10,
    "fe11": _ds(fe11_12.classes_fe11),
    "fe12": _ds(fe11_12.classes_fe12),
}
