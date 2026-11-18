from engine.common import STATS, final_level, simulate, stages, suffix

NAMES = STATS

SPECIAL_CLASSES = LAGUZ_CLASSES = {
    "Wolf", "Wolf Queen", "Cat", "Lion", "Lion King", "Tiger", "Hawk", "Hawk King",
    "Raven", "Raven King", "Heron", "Red Dragon", "White Dragon", "Dragon Prince", "Dragon King"
}

PROMOTION_MAP = {
    # Tier 1 -> Tier 2
    "Light Mage": "Light Sage",
    "Myrmidon": "Swordmaster",
    "Archer": "Sniper",
    "Fighter": "Warrior",
    "Priest": "Bishop",
    "Thunder Mage": "Thunder Sage",
    "Soldier": "Halberdier",
    "Armor Sword": "Sword General",
    "Dracoknight": "Dragonmaster",
    "Lance Knight": "Lance Paladin",

    # Tier 2 -> Tier 3
    "Light Sage": "Light Priestess",
    "Swordmaster": "Trueblade",
    "Sniper": "Marksman",
    "Warrior": "Reaver",
    "Bishop": "Saint",
    "Thunder Sage": "Arch Sage",
    "Halberdier": "Sentinel",
    "Sword General": "Marshall",
    "Lance General": "Marshall",
    "Axe General": "Marshall",
    "Dragonmaster": "Dragonlord",
    "Lance Paladin": "Silver Knight",
    "Axe Paladin": "Gold Knight",
    "Bow Paladin": "Silver Knight",
    "Blade Paladin": "Gold Knight",
    "Rogue": "Whisper",
    "Hero": "Vanguard",
    "Wind Sage": "Arch Sage",
    "Fire Sage": "Arch Sage",
    "Dark Sage": "Arch Sage",

    # Mist Cleric -> Valkyrie (treated as Tier 2 -> Tier 3)
    "Cleric": "Valkyrie",
}

TIER1_CLASSES = {
    "Light Mage", "Myrmidon", "Archer", "Fighter", "Priest",
    "Thunder Mage", "Soldier", "Armor Sword", "Dracoknight", "Lance Knight"
}
TIER2_CLASSES = {
    "Light Sage", "Swordmaster", "Sniper", "Warrior", "Bishop",
    "Thunder Sage", "Halberdier", "Sword General", "Lance General", "Axe General",
    "Dragonmaster", "Lance Paladin", "Axe Paladin", "Bow Paladin", "Blade Paladin",
    "Rogue", "Hero", "Wind Sage", "Fire Sage", "Dark Sage", "Cleric"
}
MAGICAL_TIER2 = {"Light Sage", "Wind Sage", "Fire Sage", "Thunder Sage", "Dark Sage", "Bishop", "Cleric"}

GENDERED_CAPS = {
    "Rogue", "Whisper", "Swordmaster", "Trueblade", "Halberdier", "Sentinel",
    "Priest", "Bishop", "Saint", "Armor Sword", "Sword General", "Dracoknight",
    "Dragonmaster", "Dragonlord", "Lance Knight", "Lance Paladin", "Axe Paladin",
    "Bow Paladin", "Thunder Mage", "Thunder Sage", "Fire Sage", "Cat", "Raven", "Red Dragon",
}
# Caps rows that depend on the character: {class: ({character: row}, row for everyone else)}
CHARACTER_CAPS = {
    "Arch Sage": ({
        "Ilyana": "Arch Sage (Thunder, F)", "Calill": "Arch Sage (Fire, F)", "Tormod": "Arch Sage (Fire, M)",
        "Bastian": "Arch Sage (Fire, M)", "Pelleas": "Arch Sage (Dark)",
    }, "Arch Sage (Wind)"),
    "Marshall": ({"Meg": "Marshall (Sword, F)", "Brom": "Marshall (Axe)"}, "Marshall (Lance)"),
    "Lion": ({"Skrimir": "Lion (Skrimir)", "Giffca": "Lion (Giffca)"}, "Lion King"),
    "Heron": ({"Rafiel": "Heron (Rafiel)", "Reyson": "Heron (Reyson)"}, "Heron (Leanne)"),
}


def tier_of(cls):
    return 1 if cls in TIER1_CLASSES else 2 if cls in TIER2_CLASSES else 3


def tier(cls):
    return "special" if cls in LAGUZ_CLASSES else "" if tier_of(cls) == 1 else "promo"


def caps_key(cls, char):
    name, is_female = char["name"], char["is_female"]
    if cls in CHARACTER_CAPS:
        by_name, default = CHARACTER_CAPS[cls]
        return by_name.get(name, default)
    if cls == "Gold Knight":
        return f"Gold Knight (Axe, {'F' if is_female else 'M'})" if name in ("Kieran", "Titania") else "Gold Knight (Sword)"
    if cls == "Silver Knight":
        return "Silver Knight (Bow, F)" if name == "Astrid" else f"Silver Knight (Lance, {'F' if is_female else 'M'})"
    return cls + suffix(is_female) if cls in GENDERED_CAPS else cls


def classes(char):
    chain = [char["default_class"]]
    while chain[-1] in PROMOTION_MAP:
        chain.append(PROMOTION_MAP[chain[-1]])
    return chain


def direct(char):
    """Tier 3 for units starting in tier 1, otherwise the next promotion."""
    chain = classes(char)
    return chain[min(len(chain) - 1, 2 if tier_of(chain[0]) == 1 else 1)]


def calculate(char, target, db):
    is_female = char["is_female"]
    gains_db = db["classes"]["promo_gains"]

    def gains(prev, cls):
        if tier_of(cls) == 3:
            # Every tier 2 -> 3 promotion shares one row per gender and physical/magical type
            return gains_db[f"{'Female' if is_female else 'Male'} {'Magical' if prev in MAGICAL_TIER2 else 'Physical'}"]
        gender = "(female)" if is_female else "(male)"
        for key in ((f"{prev} {gender}", f"{cls} {gender}"), (prev, cls)):
            if key in gains_db:
                return gains_db[key]
        # shortcut: first row whose names contain both classes, replace with exact keys if a wrong match shows up
        return next(row for pair, row in gains_db.items() if isinstance(pair, tuple) and prev in pair[0] and cls in pair[1])

    chain = classes(char)
    path = chain[:chain.index(target) + 1]
    maxes = [40] if chain[0] in LAGUZ_CLASSES else [20] * len(path)
    stage_list = stages(
        path, char["join_lv"], maxes,
        growths=lambda cls: char["base_growths"],
        caps=lambda cls: db["classes"]["caps"][caps_key(cls, char)],
        gains=gains,
    )
    return simulate(NAMES, char["absolute_bases"], stage_list, final_level(char["join_lv"], maxes))
