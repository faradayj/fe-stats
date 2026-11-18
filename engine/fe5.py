from engine import common
from engine.common import STATS_FE5, final_level, promote_path, simulate, stages, suffix

NAMES = STATS_FE5

# Universal caps: HP 80, others 20
CAPS = {s: 80 if s == "HP" else 20 for s in STATS_FE5}

PROMOTED_CLASSES = {
    "Prince", "Paladin", "Forrest Knight", "Duke Knight", "Great Knight",
    "General", "Mercenary", "Swordmaster", "Sniper", "Bow Knight",
    "Warrior", "Pegasus Knight", "Dragon Knight", "High Priest", "Sage",
    "Mage Knight", "Dark Mage", "Thief Fighter", "Dancer"
}

PROMOTION_MAP = {
    "Lord": "Prince",
    "Social Knight": "Paladin",
    "Troubadour": "Paladin",
    "Free Knight": "Forrest Knight",
    "Lance Knight": "Duke Knight",
    "Axe Knight": "Great Knight",
    "Axe Armour": "General",
    "Axe Fighter": "Mercenary",
    "Swordfighter": "Swordmaster",
    "Bow Fighter": "Sniper",
    "Arch Knight": "Bow Knight",
    "Mountain Thief": "Warrior",
    "Pegasus Rider": "Pegasus Knight",
    "Dragon Rider": "Dragon Knight",
    "Priest": "High Priest",
    "Sister": "Sage",
    "Bard": "Sage",
    "Mage": "Sage",
    "Loputo Mage": "Dark Mage",
    "Thief": "Thief Fighter",
}

SPECIAL_CLASSES = {"Thief", "Dancer", "Bard"}


def tier(cls):
    return common.tier(cls, {"Dancer"}, PROMOTED_CLASSES)


LARA_PATHS = {
    "Dancer": ["Thief", "Dancer"],
    "Thief Fighter (via Dancer)": ["Thief", "Dancer", "Thief Fighter"],
}


def direct(char):
    if char["name"] == "Machua":
        return "Mercenary"
    if char["name"] == "Miranda":
        return "Mage Knight"
    base = char["default_class"]
    return PROMOTION_MAP.get(base, base)


def classes(char):
    base = char["default_class"]
    if char["name"] == "Lara":
        return ["Thief", "Thief Fighter", "Dancer", "Thief Fighter (via Dancer)"]
    if base in PROMOTED_CLASSES or direct(char) == base:
        return [base]
    return [base, direct(char)]


def calculate(char, target, db):
    gains_db = db["classes"]["promo_gains"]

    def gains(prev, cls):
        # Sniper is the one class with a row per gender
        return gains_db[(prev, cls)] if (prev, cls) in gains_db else gains_db[(prev, cls + suffix(char["is_female"]))]

    lara_path = LARA_PATHS.get(target) if char["name"] == "Lara" else None
    path, pre_promoted = (lara_path, False) if lara_path else promote_path(char, target, PROMOTED_CLASSES.__contains__)
    maxes = [20] * len(path)
    stage_list = stages(
        path, char["join_lv"], maxes,
        growths=lambda cls: char["base_growths"],
        caps=lambda cls: CAPS,
        gains=gains,
    )
    if lara_path:
        stage_list[0][3] = 19  # existing behaviour: Lara leaves Thief one level early on the Dancer paths
    return simulate(NAMES, char["absolute_bases"], stage_list, final_level(char["join_lv"], maxes, pre_promoted))
