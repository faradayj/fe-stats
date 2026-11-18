from engine import common
from engine.common import STATS, final_level, promote_path, simulate, stages, suffix

NAMES = STATS

SPECIAL_CLASSES = {
    "Beast tribe (Cat)", "Beast tribe (Tiger)", "Beast tribe (Lion)",
    "Bird tribe (Hawk)", "Bird tribe (Raven)", "Bird tribe (Heron)",
    "Dragon tribe (Red)", "Dragon tribe (White)", "Thief"
}

PROMOTION_MAP = {
    "Ranger": "Lord",
    "Myrmidon": "Swordmaster",
    "Soldier": "Halberdier",
    "Fighter": "Warrior",
    "Archer": "Sniper",
    "Knight": "General",
    "Sword Knight": "Paladin",
    "Lance Knight": "Paladin",
    "Axe Knight": "Paladin",
    "Bow Knight": "Paladin",
    "Pegasus Knight": "Falcon Knight",
    "Wyvern Rider": "Wyvern Lord",
    "Mage": "Sage",
    "Priest": "Bishop",
    "Cleric": "Valkyrie",
    "Thief": "Assassin"
}

PROMOTED_CLASSES = set(PROMOTION_MAP.values()) | {"Hero", "Berserker", "Princess Crimea"}

CHARACTER_CAPS = {"Elincia": "Princess Crimea", "Tibarn": "Bird tribe (Tibarn)", "Naesala": "Bird tribe (Naesala)"}
UNPROMOTED_PHYSICAL = {
    "Ranger", "Myrmidon", "Soldier", "Fighter", "Archer", "Knight",
    "Sword Knight", "Lance Knight", "Axe Knight", "Thief", "Pegasus Knight", "Wyvern Rider"
}
GENDERED_CAPS = {"Swordmaster", "Paladin", "Wyvern Lord", "Assassin"}
# Caps rows named "<tribe> (<kind> F)" / "<tribe> (<kind> M)"
GENDERED_LAGUZ = {"Beast tribe (Cat)", "Bird tribe (Heron)", "Dragon tribe (Red)"}

# Promotion-gain rows: (base key, promoted key) per gender, where they differ from the plain class names
GAIN_KEYS = {
    "Mage": (("Mage (M)", "Sage (M)"), ("Mage (F)", "Sage (F)")),
    "Myrmidon": (("Myrmidon (M)", "Swordmaster (M)"), ("Myrmidon (F)", "Swordmaster (F)")),
    "Soldier": (("Soldier", "Halberdier"), ("Soldier (F)", "Halberdier (F)")),
    "Wyvern Rider": (("Wyvern Rider", "Wyvern Lord"), ("Wyvern Rider (F)", "Wyvern Lord (F)")),
    "Priest": (("Priest", "Bishop (M)"),) * 2,
    "Thief": (("Thief", "Assassin (M)"),) * 2,
    "Sword Knight": (("Sword Knight (M)", "Paladin (M)"),) * 2,
    "Lance Knight": (("Lance Knight (M)", "Paladin (M)"),) * 2,
    "Axe Knight": (("Axe Knight (M)", "Paladin (M)"),) * 2,
    "Bow Knight": (("Bow Knight", "Paladin"), ("Bow Knight (F)", "Paladin (F)")),
}


def caps_key(cls, char):
    name, is_female = char["name"], char["is_female"]
    if name == "Ike" and cls == "Lord":
        return "Lord / Hero"
    if name in CHARACTER_CAPS:
        return CHARACTER_CAPS[name]
    if cls in UNPROMOTED_PHYSICAL or (cls == "Bow Knight" and not is_female):
        return "Non-promoted physical"
    if cls == "Bow Knight":
        return "Horse Knight (F)"
    if cls in ("Cleric", "Priest"):
        return "Priest / Cleric"
    if cls in GENDERED_CAPS:
        return cls + suffix(is_female)
    if cls in GENDERED_LAGUZ:
        return f"{cls[:-1]} {'F' if is_female else 'M'})"
    if cls == "Beast tribe (Lion)" and name == "Giffca":
        return "Lion"
    return cls


def tier(cls):
    return common.tier(cls, SPECIAL_CLASSES, PROMOTED_CLASSES)


def direct(char):
    base = char["default_class"]
    if char["name"] == "Volke":
        return "Assassin"
    if base in SPECIAL_CLASSES:
        return base
    return PROMOTION_MAP.get(base, base)


def classes(char):
    base = char["default_class"]
    if base == "Thief":
        return ["Thief"] if char["name"] == "Sothe" else ["Thief", "Assassin"]
    if base in SPECIAL_CLASSES or base not in PROMOTION_MAP:
        return [base]
    return [base, PROMOTION_MAP[base]]


def calculate(char, target, db):
    gains_db = db["classes"]["promo_gains"]

    def gains(prev, cls):
        key = GAIN_KEYS.get(prev, ((prev, cls),) * 2)[char["is_female"]]
        return gains_db[key] if key in gains_db else gains_db[(prev, cls)]

    path, pre_promoted = promote_path(char, target, PROMOTED_CLASSES.__contains__)
    maxes = [20] * len(path)
    stage_list = stages(
        path, char["join_lv"], maxes,
        growths=lambda cls: char["base_growths"],
        caps=lambda cls: db["classes"]["caps"][caps_key(cls, char)],
        gains=gains,
    )
    return simulate(NAMES, char["absolute_bases"], stage_list, final_level(char["join_lv"], maxes, pre_promoted))
