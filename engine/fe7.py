from engine import common
from engine.common import STATS, final_level, promote_path, simulate, stages, suffix

NAMES = STATS

SPECIAL_CLASSES = {"Dancer", "Bard", "Transporter", "Archsage"}

PROMOTION_MAP = {
    "Cavalier": "Paladin",
    "Knight": "General",
    "Mercenary": "Hero",
    "Myrmidon": "Swordmaster",
    "Thief": "Assassin",
    "Archer": "Sniper",
    "Nomad": "Nmd Trooper",
    "Pegasus Knight": "Falcoknight",
    "Wyvern Rider": "Wyvern Lord",
    "Mage": "Sage",
    "Monk": "Bishop",
    "Priest": "Bishop",
    "Cleric": "Bishop",
    "Shaman": "Druid",
    "Fighter": "Warrior",
    "Pirate": "Berserker",
    "Troubadour": "Valkyrie"
}

LORD_PROMOTIONS = {"Lyn": "Blade Lord", "Eliwood": "Knight Lord", "Hector": "Great Lord"}

PROMOTED_CLASSES = set(PROMOTION_MAP.values()) | set(LORD_PROMOTIONS.values())

GENDERED_CLASSES = {
    "Paladin", "General", "Hero", "Swordmaster", "Sniper", "Nmd Trooper", "Wyvern Lord", "Sage", "Bishop", "Druid"
}


def tier(cls):
    return common.tier(cls, SPECIAL_CLASSES, PROMOTED_CLASSES)


def direct(char):
    base = char["default_class"]
    if base == "Lord":
        for lord, promoted in LORD_PROMOTIONS.items():
            if lord in char["name"]:
                return promoted
    return PROMOTION_MAP.get(base, base)


def classes(char):
    base = char["default_class"]
    if base in SPECIAL_CLASSES or direct(char) == base:
        return [base]
    return [base, direct(char)]


def calculate(char, target, db):
    is_female = char["is_female"]
    caps_db = db["classes"]["caps"]
    gains_db = db["classes"]["promo_gains"]

    def lookup(table, cls, default=None):
        for key in (cls + suffix(is_female) if cls in GENDERED_CLASSES else cls, cls):
            if key in table:
                return table[key]
        return table[default or cls]

    path, pre_promoted = promote_path(char, target, PROMOTED_CLASSES.__contains__)
    maxes = [20] * len(path)
    stage_list = stages(
        path, char["join_lv"], maxes,
        growths=lambda cls: char["base_growths"],
        caps=lambda cls: lookup(caps_db, cls, "Non-promoted"),
        gains=lambda prev, cls: lookup(gains_db, cls),  # FE7 gains are keyed by promoted class only
    )
    return simulate(NAMES, char["absolute_bases"], stage_list, final_level(char["join_lv"], maxes, pre_promoted))
