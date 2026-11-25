"""FE11 (Shadow Dragon) and FE12 (New Mystery): same reclass rules, different class pools."""
from engine import common
from engine.common import STATS, final_level, simulate, stages, suffix

NAMES = STATS

SPECIAL_CLASSES = {"Lord", "Thief", "Dancer", "Chameleon", "Manakete", "Ballistician"}
RANK_ALL_CLASSES = True  # leaderboard ranks every reclass option, not just the default promotion

# promoted class -> the class it promotes from
PROMOTION_MAP = {
    "Falcon Knight": "Pegasus Knight",
    "Dracoknight": "Pegasus Knight",
    "Paladin": "Cavalier",
    "Sniper": "Archer",
    "Swordmaster": "Myrmidon",
    "Sage": "Mage",
    "Bishop": "Curate",
    "General": "Knight",
    "Hero": "Mercenary",
    "Warrior": "Fighter",
    "Horseman": "Hunter",
    "Berserker": "Pirate",
    "Sorcerer": "Dark Mage"
}

FEMALE_CLASSES = [
    "Falcon Knight", "Dracoknight", "Paladin", "Sniper", "Swordmaster", "Sage", "Bishop",
    "Pegasus Knight", "Cavalier", "Archer", "Myrmidon", "Mage", "Cleric"
]
# FE11 men are split into two reclass sets by their starting class
FE11_SET_A = [
    "Paladin", "Dracoknight", "Sniper", "Swordmaster", "Sage", "Bishop",
    "Cavalier", "Archer", "Myrmidon", "Mage", "Curate"
]
FE11_SET_B = [
    "General", "Hero", "Warrior", "Horseman", "Berserker", "Sorcerer",
    "Knight", "Mercenary", "Fighter", "Hunter", "Pirate", "Dark Mage"
]
FE12_MALE_CLASSES = [
    "Paladin", "Sniper", "Swordmaster", "Sage", "Bishop", "Dracoknight",
    "General", "Hero", "Warrior", "Horseman", "Berserker", "Sorcerer",
    "Cavalier", "Archer", "Myrmidon", "Mage", "Curate",
    "Knight", "Mercenary", "Fighter", "Hunter", "Pirate", "Dark Mage", "Barbarian"
]
FLIERS = {"Pegasus Knight", "Falcon Knight", "Dracoknight"}


def tier(cls):
    return common.tier(cls, SPECIAL_CLASSES, PROMOTION_MAP)


def fixed_class(char):
    """The only class of a unit that cannot reclass, else None."""
    if char["name"] == "Beck":
        return "Ballistician"
    return char["default_class"] if char["default_class"] in SPECIAL_CLASSES else None


def classes_fe11(char):
    if fixed_class(char):
        return [fixed_class(char)]
    if char["is_female"]:
        return FEMALE_CLASSES
    return FE11_SET_A if char["default_class"] in FE11_SET_A else FE11_SET_B


def classes_fe12(char):
    if fixed_class(char):
        return [fixed_class(char)]
    if char["name"] == "Sheema":
        return ["General"] + FEMALE_CLASSES  # the one woman who joins as a General
    return FEMALE_CLASSES if char["is_female"] else FE12_MALE_CLASSES


def direct(char):
    base = fixed_class(char) or char["default_class"]
    if base in PROMOTION_MAP or base in SPECIAL_CLASSES:
        return base
    if base == "Pegasus Knight":
        return "Falcon Knight"
    if base in ("Cleric", "Curate"):
        return "Bishop"
    return next((promoted for promoted, b in PROMOTION_MAP.items() if b == base), base)


def base_class(promoted, is_female):
    if promoted == "Dracoknight":
        return "Pegasus Knight" if is_female else "Cavalier"
    if promoted == "Bishop":
        return "Cleric" if is_female else "Curate"
    return PROMOTION_MAP[promoted]


def calculate(char, target, db):
    is_female = char["is_female"]
    table = db["classes"]

    def growths(cls):
        return {s: char["base_growths"][s] + class_growths(cls)[s] for s in NAMES}

    def class_growths(cls):
        rows = table["growths"]
        for key in (cls + suffix(is_female), cls):
            if key in rows:
                return rows[key]
        for key, row in rows.items():
            if cls in key.split(" / "):
                return row
        assert cls in FLIERS, f"no growth group for {cls}"
        return rows["Peg / Falco / Draco Knight"]  # FE12's one group not named after its classes

    def caps(cls):
        return table["caps"][cls if cls in table["caps"] else "Non-promoted"]

    def gains(prev, cls):
        if (prev, cls) in table["promo_gains"]:
            return table["promo_gains"][(prev, cls)]
        return {s: table["bases"][cls][s] - table["bases"][prev][s] for s in NAMES}

    pre_promoted = target in PROMOTION_MAP and char["default_class"] in PROMOTION_MAP
    if target in PROMOTION_MAP and not pre_promoted:
        path = [base_class(target, is_female), target]
    else:
        path = [target]
    maxes = [30] if target in SPECIAL_CLASSES else [20] * len(path)
    bases = {s: char["absolute_bases"][s] + table["bases"][path[0]][s] for s in NAMES}
    stage_list = stages(path, char["join_lv"], maxes, growths, caps, gains)
    return simulate(NAMES, bases, stage_list, final_level(char["join_lv"], maxes, pre_promoted))
