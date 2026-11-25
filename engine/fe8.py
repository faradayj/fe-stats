from engine.common import STATS, final_level, simulate, stages, suffix

NAMES = STATS

PROMOTION_TREE = {
    "Lord (Eirika)": ["Great Lord (Eirika)"],
    "Lord (Ephraim)": ["Great Lord (Ephraim)"],
    "Cavalier (M)": ["Paladin (M)", "Great Knight (M)"],
    "Cavalier (F)": ["Paladin (F)", "Great Knight (F)"],
    "Knight (M)": ["General (M)", "Great Knight (M)"],
    "Knight (F)": ["General (F)", "Great Knight (F)"],
    "Thief": ["Rogue", "Assassin (M)"],
    "Mercenary": ["Hero (M)", "Ranger (M)"],
    "Myrmidon (M)": ["Swordmaster (M)", "Assassin (M)"],
    "Myrmidon (F)": ["Swordmaster (F)", "Assassin (F)"],
    "Archer (M)": ["Sniper (M)", "Ranger (M)"],
    "Archer (F)": ["Sniper (F)", "Ranger (F)"],
    "Wyvern Rider": ["Wyvern Lord (M)", "Wyvern Knight (M)"],
    "Pegasus Knight": ["Falcoknight", "Wyvern Knight (F)"],
    "Mage (M)": ["Sage (M)", "Mage Knight (M)"],
    "Mage (F)": ["Sage (F)", "Mage Knight (F)"],
    "Shaman": ["Druid (M)", "Summoner (M)"],
    "Priest": ["Bishop (M)", "Sage (M)"],
    "Monk": ["Bishop (M)", "Sage (M)"],
    "Cleric": ["Bishop (F)", "Valkyrie"],
    "Troubadour": ["Valkyrie", "Mage Knight (F)"],
    "Fighter": ["Warrior", "Hero (M)"],
    "Pirate": ["Berserker", "Warrior"],
    "Journeyman": ["Fighter", "Pirate", "Journeyman (2)"],
    "Recruit": ["Cavalier (F)", "Knight (F)", "Recruit (2)"],
    "Pupil": ["Mage (M)", "Shaman", "Pupil (2)"],
    "Journeyman (2)": ["Hero (M)", "Journeyman (3)"],
    "Recruit (2)": ["Paladin (F)", "Recruit (3)"],
    "Pupil (2)": ["Sage (M)", "Pupil (3)"],
}

SPECIAL_CLASSES = {"Dancer", "Manakete"}
RANK_ALL_CLASSES = True  # leaderboard ranks every path to a final class, not just the default promotion
TRAINEES = {"Journeyman", "Recruit", "Pupil"}
UNPROMOTED = TRAINEES | {
    "Lord", "Dancer", "Manakete", "Cavalier", "Knight", "Thief", "Mercenary", "Myrmidon", "Archer",
    "Wyvern Rider", "Pegasus Knight", "Mage", "Shaman", "Priest", "Monk", "Cleric", "Troubadour", "Fighter", "Pirate"
}
GENDERED_STARTS = {"Cavalier", "Knight", "Myrmidon", "Archer", "Mage"}
GENDERED_PROMOTED = {
    "Paladin", "Sniper", "Berserker", "Sage", "Great Knight", "Hero", "Bishop", "Swordmaster",
    "Mage Knight", "Wyvern Lord", "Wyvern Knight", "General"
}
DEFAULT_CAPS = {"HP": 60, "Str": 20, "Mag": 20, "Skl": 20, "Spd": 20, "Lck": 30, "Def": 20, "Res": 20}


def plain(cls):
    return cls.split("(")[0].strip()


def tier(cls):
    return "special" if cls in SPECIAL_CLASSES else "" if plain(cls) in UNPROMOTED else "promo"


def start_class(char):
    cls = char["default_class"]
    if cls == "Lord":
        return "Lord (Eirika)" if "Eirika" in char["name"] else "Lord (Ephraim)"
    return cls + suffix(char["is_female"]) if cls in GENDERED_STARTS | GENDERED_PROMOTED else cls


def class_keys(char):
    """{class key: path}; a final class reachable several ways gets a "(via X)" key per path."""
    paths = []

    def build(path):
        paths.append(path)
        for promo in PROMOTION_TREE.get(path[-1], []):
            build(path + [promo])

    build([start_class(char)])
    finals = [p[-1] for p in paths]
    paths.sort(key=lambda p: finals.index(p[-1]))  # keep paths to the same final class together
    return {
        f"{p[-1]} (via {plain(p[1])})" if finals.count(p[-1]) > 1 and len(p) > 1 else p[-1]: p
        for p in paths
    }


def classes(char):
    return list(class_keys(char))


def direct(char):
    """Key of the default promotion line: the first option at every branch."""
    path = [start_class(char)]
    if char["name"] == "Amelia":
        path += ["Knight (F)"]
    while path[-1] in PROMOTION_TREE:
        path.append(PROMOTION_TREE[path[-1]][0])
    return next(key for key, p in class_keys(char).items() if p == path)


def calculate(char, key, db):
    is_female = char["is_female"]
    caps_db = db["classes"]["caps"]
    gains_db = db["classes"]["promo_gains"]

    def caps(cls):
        for name in (cls, cls + suffix(is_female), plain(cls), plain(cls) + suffix(is_female)):
            if name in caps_db:
                return caps_db[name]
        return DEFAULT_CAPS  # unpromoted classes have no row in the caps table

    def gains(prev, cls):
        for pair in ((prev, cls), (prev, plain(cls)), (plain(prev), plain(cls))):
            if pair in gains_db:
                return gains_db[pair]
        if (plain(prev), plain(cls)) == ("Pupil", "Shaman"):
            return gains_db[("Pupil", "Shaman (M)")]
        raise KeyError(f"no FE8 promotion gains for {prev} -> {cls}")

    path = class_keys(char)[key]
    base = char["default_class"]
    maxes = ([10, 20, 20] if base in TRAINEES else [20, 20])[:len(path)]
    stage_list = stages(path, char["join_lv"], maxes, lambda cls: char["base_growths"], caps, gains)
    return simulate(NAMES, char["absolute_bases"], stage_list, final_level(char["join_lv"], maxes, base not in UNPROMOTED))
