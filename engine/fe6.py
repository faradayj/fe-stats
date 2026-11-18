from engine import common
from engine.common import STATS, final_level, promote_path, simulate, stages, suffix

NAMES = STATS

SPECIAL_CLASSES = {"Thief", "Bard", "Dancer", "Mamkute", "Transporter", "King"}

PROMOTION_MAP = {
    "Lord": "Master Lord",
    "Mercenary": "Hero",
    "Myrmidon": "Swordmaster",
    "Cavalier": "Paladin",
    "Knight": "General",
    "Fighter": "Warrior",
    "Bandit": "Berserker",
    "Brigand": "Berserker",
    "Pirate": "Berserker",
    "Archer": "Sniper",
    "Nomad": "Nomadic Trooper",
    "Pegasus Knight": "Falcon Knight",
    "Wyvern Rider": "Wyvern Lord",
    "Mage": "Sage",
    "Shaman": "Druid",
    "Priest": "Bishop",
    "Cleric": "Bishop",
    "Troubadour": "Valkyria"
}

PROMOTED_CLASSES = set(PROMOTION_MAP.values()) | {"Nomad Trooper"}

GENDERED_CLASSES = {
    "Mercenary", "Hero", "Myrmidon", "Swordmaster", "Cavalier", "Paladin",
    "Knight", "General", "Archer", "Sniper", "Nomad",
    "Wyvern Rider", "Wyvern Lord", "Mage", "Sage", "Shaman", "Druid", "Priest", "Bishop"
}


def gendered(cls, is_female):
    if cls in ("Nomadic Trooper", "Nomad Trooper"):
        return "Nomad Trooper" + suffix(is_female)
    if cls == "Cleric":
        return "Priest (F)"
    return cls + suffix(is_female) if cls in GENDERED_CLASSES else cls


def tier(cls):
    return common.tier(cls, SPECIAL_CLASSES, PROMOTED_CLASSES)


def direct(char):
    base = char["default_class"]
    return PROMOTION_MAP.get(base, base)


def classes(char):
    base = char["default_class"]
    if base in SPECIAL_CLASSES or base not in PROMOTION_MAP:
        return [base]
    return [base, PROMOTION_MAP[base]]


def calculate(char, target, db):
    is_female = char["is_female"]
    caps_db = db["classes"]["caps"]
    gains_db = db["classes"]["promo_gains"]

    def caps(cls):
        for key in (gendered(cls, is_female), cls):
            if key in caps_db:
                return caps_db[key]
        return caps_db["Non-promoted"]

    def gains(prev, cls):
        prev = "Brigand" if prev == "Bandit" else prev  # the gains table knows the class only as Brigand
        key = (gendered(prev, is_female), gendered(cls, is_female))
        return gains_db[key] if key in gains_db else gains_db[(prev, cls)]

    path, pre_promoted = promote_path(char, target, PROMOTED_CLASSES.__contains__)
    maxes = [20] * len(path)
    stage_list = stages(path, char["join_lv"], maxes, lambda cls: char["base_growths"], caps, gains)
    return simulate(NAMES, char["absolute_bases"], stage_list, final_level(char["join_lv"], maxes, pre_promoted))
