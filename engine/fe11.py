import os
from engine.common import STATS
from engine.parser import parse_html_tables, clean_value, parse_int, fetch_page

# --- Configurations & Constants ---
URLS = {
    "char_bases_default": "https://serenesforest.net/shadow-dragon/characters/base-stats/default/",
    "char_bases_absolute": "https://serenesforest.net/shadow-dragon/characters/base-stats/absolute/",
    "char_growths": "https://serenesforest.net/shadow-dragon/characters/growth-rates/base/",
    "class_bases": "https://serenesforest.net/shadow-dragon/classes/base-stats/",
    "class_growths": "https://serenesforest.net/shadow-dragon/classes/growth-rates/player/",
    "class_caps": "https://serenesforest.net/shadow-dragon/classes/maximum-stats/",
    "class_promotions": "https://serenesforest.net/shadow-dragon/classes/promotion-gains/"
}

FEMALE_CHARACTERS = {
    "Norne", "Shiida", "Lena", "Athena", "Maria", "Minerva", "Linde", "Midia",
    "Palla", "Catria", "Est", "Tiki", "Elice", "Nagi"
}

PROMOTED_CLASSES = {
    "Falcon Knight", "Dracoknight", "Paladin", "Sniper", "Swordmaster", 
    "Sage", "Bishop", "General", "Hero", "Warrior", "Horseman", "Berserker", "Sorcerer"
}

SPECIAL_CLASSES = {
    "Lord", "Thief", "Manakete", "Ballistician", "Chameleon"
}

BASE_CLASSES = {
    "Pegasus Knight", "Cavalier", "Archer", "Myrmidon", "Mage", "Cleric", "Curate",
    "Knight", "Mercenary", "Fighter", "Hunter", "Pirate", "Dark Mage"
}

CLASS_TO_GROWTH_GROUP = {
    "Lord": "Lord",
    "Pegasus Knight": "Pegasus Knight",
    "Falcon Knight": "Falcon Knight",
    "Dracoknight": "Dracoknight (M)",  # Dynamic override for female in helper
    "Cavalier": "Cavalier / Paladin",
    "Paladin": "Cavalier / Paladin",
    "Knight": "Knight / General",
    "General": "Knight / General",
    "Archer": "Archer / Sniper",
    "Sniper": "Archer / Sniper",
    "Mercenary": "Mercenary / Hero",
    "Hero": "Mercenary / Hero",
    "Myrmidon": "Myrmidon / Swordmaster",
    "Swordmaster": "Myrmidon / Swordmaster",
    "Fighter": "Fighter / Warrior",
    "Warrior": "Fighter / Warrior",
    "Hunter": "Hunter / Horseman",
    "Horseman": "Hunter / Horseman",
    "Pirate": "Pirate / Berserker",
    "Berserker": "Pirate / Berserker",
    "Dark Mage": "Dark Mage / Sorcerer",
    "Sorcerer": "Dark Mage / Sorcerer",
    "Mage": "Mage",
    "Sage": "Sage",
    "Curate": "Curate / Cleric",
    "Cleric": "Curate / Cleric",
    "Bishop": "Bishop",
    "Thief": "Thief",
    "Manakete": "Manakete",
    "Ballistician": "Ballistician",
    "Chameleon": "Chameleon"
}

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

SET_A_CLASSES = {
    "Cavalier", "Archer", "Myrmidon", "Mage", "Curate",
    "Paladin", "Dracoknight", "Sniper", "Swordmaster", "Sage", "Bishop"
}

SET_B_CLASSES = {
    "Knight", "Mercenary", "Fighter", "Hunter", "Pirate", "Dark Mage",
    "General", "Hero", "Warrior", "Horseman", "Berserker", "Sorcerer"
}

def get_base_class(promoted_class, is_female):
    if promoted_class == "Dracoknight":
        return "Pegasus Knight" if is_female else "Cavalier"
    if promoted_class == "Bishop":
        return "Cleric" if is_female else "Curate"
    return PROMOTION_MAP.get(promoted_class)

def load_fe11_data():
    raw = {}
    for name, url in URLS.items():
        raw[name] = fetch_page(f"fe11_{name}", url)

    # 1. Parse Class Bases
    class_bases = {}
    tables = parse_html_tables(raw["class_bases"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                cls_name = clean_value(row[0])
                if not cls_name or cls_name == "Class" or cls_name == "Class *":
                    continue
                cls_name = cls_name.split("*")[0].strip()
                class_bases[cls_name] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": parse_int(row[headers.index("Str")]),
                    "Mag": parse_int(row[headers.index("Mag")]),
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index("Lck")]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    # 2. Parse Class Growths
    class_growths = {}
    tables = parse_html_tables(raw["class_growths"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                cls_group = clean_value(row[0])
                if not cls_group or cls_group == "Class" or cls_group == "Class *":
                    continue
                cls_group = cls_group.split("*")[0].strip()
                class_growths[cls_group] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": parse_int(row[headers.index("Str")]),
                    "Mag": parse_int(row[headers.index("Mag")]),
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index("Lck")]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    # 3. Parse Class Maximum Stats
    class_caps = {}
    tables = parse_html_tables(raw["class_caps"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                cls_name = clean_value(row[0])
                if not cls_name or cls_name == "Class" or cls_name == "Class *":
                    continue
                cls_name = cls_name.split("*")[0].strip()
                class_caps[cls_name] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": parse_int(row[headers.index("Str")]),
                    "Mag": parse_int(row[headers.index("Mag")]),
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index("Lck")]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    # 4. Parse Class Promotion Gains
    promo_gains = {}
    tables = parse_html_tables(raw["class_promotions"])
    for table in tables:
        if len(table) > 1 and "Base class" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                base_cls = clean_value(row[headers.index("Base class")]).split("*")[0].strip()
                promo_cls = clean_value(row[headers.index("Promoted class")]).split("*")[0].strip()
                if not base_cls or base_cls == "Base class":
                    continue
                key = (base_cls, promo_cls)
                promo_gains[key] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": parse_int(row[headers.index("Str")]),
                    "Mag": parse_int(row[headers.index("Mag")]),
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index("Lck")]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    # 5. Parse Character Default Info (Class + Level)
    char_defaults = {}
    tables = parse_html_tables(raw["char_bases_default"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "Class" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0])
                if not name or name == "Name":
                    continue
                cls = clean_value(row[headers.index("Class")])
                lv = parse_int(row[headers.index("Lv")])
                if name not in char_defaults:
                    char_defaults[name] = {
                        "class": cls,
                        "lv": lv
                    }

    # 6. Parse Character Absolute Bases
    char_bases = {}
    tables = parse_html_tables(raw["char_bases_absolute"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "Lv" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0])
                if not name or name == "Name":
                    continue
                if name not in char_bases:
                    char_bases[name] = {
                        "lv": parse_int(row[headers.index("Lv")]),
                        "bases": {
                            "HP": parse_int(row[headers.index("HP")]),
                            "Str": parse_int(row[headers.index("Str")]),
                            "Mag": parse_int(row[headers.index("Mag")]),
                            "Skl": parse_int(row[headers.index("Skl")]),
                            "Spd": parse_int(row[headers.index("Spd")]),
                            "Lck": parse_int(row[headers.index("Lck")]),
                            "Def": parse_int(row[headers.index("Def")]),
                            "Res": parse_int(row[headers.index("Res")]),
                        }
                    }

    # 7. Parse Character Growths
    char_growths = {}
    tables = parse_html_tables(raw["char_growths"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0])
                if not name or name == "Name":
                    continue
                if name not in char_growths:
                    char_growths[name] = {
                        "HP": parse_int(row[headers.index("HP")]),
                        "Str": parse_int(row[headers.index("Str")]),
                        "Mag": parse_int(row[headers.index("Mag")]),
                        "Skl": parse_int(row[headers.index("Skl")]),
                        "Spd": parse_int(row[headers.index("Spd")]),
                        "Lck": parse_int(row[headers.index("Lck")]),
                        "Def": parse_int(row[headers.index("Def")]),
                        "Res": parse_int(row[headers.index("Res")]),
                    }

    database = {
        "characters": {},
        "classes": {
            "bases": class_bases,
            "growths": class_growths,
            "caps": class_caps,
            "promo_gains": promo_gains
        }
    }

    for name, data in char_bases.items():
        default_info = char_defaults.get(name)
        growths = char_growths.get(name)
        if not default_info:
            for d_name in char_defaults:
                if d_name in name or name in d_name:
                    default_info = char_defaults[d_name]
                    break
        if not growths:
            for g_name in char_growths:
                if g_name in name or name in g_name:
                    growths = char_growths[g_name]
                    break

        if default_info and growths:
            database["characters"][name] = {
                "name": name,
                "join_lv": default_info["lv"],
                "default_class": default_info["class"],
                "is_female": name in FEMALE_CHARACTERS,
                "absolute_bases": data["bases"],
                "base_growths": growths
            }

    return database


# --- Stat Calculation Engine ---
def get_caps_for_class(cls_name, caps_db):
    if cls_name in caps_db:
        return caps_db[cls_name]
    if cls_name in BASE_CLASSES or cls_name not in PROMOTED_CLASSES:
        return caps_db.get("Non-promoted", {s: 20 for s in STATS})
    return {s: 20 for s in STATS}

def get_class_growths(cls_name, growths_db, is_female=False):
    if cls_name == "Dracoknight" and is_female:
        group = "Dracoknight (F)"
    else:
        group = CLASS_TO_GROWTH_GROUP.get(cls_name)
        
    if group and group in growths_db:
        return growths_db[group]
    return {s: 0 for s in STATS}

def get_promo_gains(base_cls, promo_cls, promo_gains_db, class_bases_db):
    key = (base_cls, promo_cls)
    if key in promo_gains_db:
        return promo_gains_db[key]
    
    base_class_bases = class_bases_db.get(base_cls, {s: 0 for s in STATS})
    promo_class_bases = class_bases_db.get(promo_cls, {s: 0 for s in STATS})
    
    gains = {}
    for s in STATS:
        gains[s] = promo_class_bases[s] - base_class_bases[s]
    return gains

def calculate_fe11_avg_stats(char_data, target_class, db):
    is_female = char_data["is_female"]
    join_lv = char_data["join_lv"]
    abs_bases = char_data["absolute_bases"]
    base_growths = char_data["base_growths"]
    
    class_bases_db = db["classes"]["bases"]
    growths_db = db["classes"]["growths"]
    caps_db = db["classes"]["caps"]
    promo_gains_db = db["classes"]["promo_gains"]

    current_stats = {}
    history = []

    if target_class in SPECIAL_CLASSES:
        cls_bases = class_bases_db.get(target_class, {s: 0 for s in STATS})
        cls_caps = get_caps_for_class(target_class, caps_db)
        cls_growths = get_class_growths(target_class, growths_db, is_female)
        
        for s in STATS:
            val = abs_bases[s] + cls_bases[s]
            current_stats[s] = min(float(cls_caps[s]), float(max(0, val)))

        history.append((join_lv, target_class, current_stats.copy()))
        for lv in range(join_lv + 1, 31):
            for s in STATS:
                growth_rate = max(0, base_growths[s] + cls_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(cls_caps[s]), current_stats[s])
            history.append((lv, target_class, current_stats.copy()))
            
        return {
            "class_path": target_class,
            "final_class": target_class,
            "final_level": "30",
            "stats": current_stats,
            "history": history
        }

    elif target_class in PROMOTED_CLASSES:
        base_cls = get_base_class(target_class, is_female)
        if not base_cls:
            base_cls = "Cavalier"

        base_bases = class_bases_db.get(base_cls, {s: 0 for s in STATS})
        base_caps = get_caps_for_class(base_cls, caps_db)
        base_growths_cls = get_class_growths(base_cls, growths_db, is_female)

        for s in STATS:
            val = abs_bases[s] + base_bases[s]
            current_stats[s] = min(float(base_caps[s]), float(max(0, val)))

        is_already_promoted = char_data["default_class"] in PROMOTED_CLASSES
        
        if not is_already_promoted:
            history.append((join_lv, base_cls, current_stats.copy()))
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s] + base_growths_cls[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(base_caps[s]), current_stats[s])
                history.append((lv, base_cls, current_stats.copy()))
            
            gains = get_promo_gains(base_cls, target_class, promo_gains_db, class_bases_db)
            promo_caps = get_caps_for_class(target_class, caps_db)
            for s in STATS:
                current_stats[s] += gains[s]
                current_stats[s] = min(float(promo_caps[s]), current_stats[s])
            
            history.append(("20/1", target_class, current_stats.copy()))
            promo_growths_cls = get_class_growths(target_class, growths_db, is_female)
            for lv in range(2, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s] + promo_growths_cls[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(promo_caps[s]), current_stats[s])
                history.append((f"20/{lv}", target_class, current_stats.copy()))

            return {
                "class_path": f"{base_cls} -> {target_class}",
                "final_class": target_class,
                "final_level": "20/20",
                "stats": current_stats,
                "history": history
            }
        else:
            promo_bases = class_bases_db.get(target_class, {s: 0 for s in STATS})
            promo_caps = get_caps_for_class(target_class, caps_db)
            promo_growths_cls = get_class_growths(target_class, growths_db, is_female)

            for s in STATS:
                val = abs_bases[s] + promo_bases[s]
                current_stats[s] = min(float(promo_caps[s]), float(max(0, val)))

            history.append((join_lv, target_class, current_stats.copy()))
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s] + promo_growths_cls[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(promo_caps[s]), current_stats[s])
                history.append((lv, target_class, current_stats.copy()))

            return {
                "class_path": target_class,
                "final_class": target_class,
                "final_level": f"{join_lv} -> 20",
                "stats": current_stats,
                "history": history
            }

    else:
        base_bases = class_bases_db.get(target_class, {s: 0 for s in STATS})
        base_caps = get_caps_for_class(target_class, caps_db)
        base_growths_cls = get_class_growths(target_class, growths_db, is_female)

        for s in STATS:
            val = abs_bases[s] + base_bases[s]
            current_stats[s] = min(float(base_caps[s]), float(max(0, val)))

        history.append((join_lv, target_class, current_stats.copy()))
        for lv in range(join_lv + 1, 21):
            for s in STATS:
                growth_rate = max(0, base_growths[s] + base_growths_cls[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(base_caps[s]), current_stats[s])
            history.append((lv, target_class, current_stats.copy()))

        return {
            "class_path": target_class,
            "final_class": target_class,
            "final_level": "20",
            "stats": current_stats,
            "history": history
        }


# --- Reclass Availability Rules ---
def get_valid_classes_for_fe11_character(char_data):
    name = char_data["name"]
    is_female = char_data["is_female"]
    default_cls = char_data["default_class"]

    if name == "Marth":
        return ["Lord"]
    if default_cls == "Thief":
        return ["Thief"]
    if default_cls == "Manakete":
        return ["Manakete"]
    if default_cls == "Ballistician" or name in ("Beck", "Jake"):
        return ["Ballistician"]
    if default_cls == "Chameleon" or name == "Xane":
        return ["Chameleon"]

    if is_female:
        return [
            "Falcon Knight", "Dracoknight", "Paladin", "Sniper", "Swordmaster", "Sage", "Bishop",
            "Pegasus Knight", "Cavalier", "Archer", "Myrmidon", "Mage", "Cleric"
        ]
    else:
        # Determine set A vs set B based on initial class
        # Jagen (Paladin), Wendell (Sage), Boah (Bishop), Jeorge (Sniper), Arran (Paladin), Gotoh (Sage) are Set A
        # Astram (Hero), Samson (Hero), Horace (General), Lorenz (General), Ymir (Warrior), Etzel (Sorcerer) are Set B
        
        is_set_a = default_cls in SET_A_CLASSES
        
        if is_set_a:
            return [
                "Paladin", "Dracoknight", "Sniper", "Swordmaster", "Sage", "Bishop",
                "Cavalier", "Archer", "Myrmidon", "Mage", "Curate"
            ]
        else:
            return [
                "General", "Hero", "Warrior", "Horseman", "Berserker", "Sorcerer",
                "Knight", "Mercenary", "Fighter", "Hunter", "Pirate", "Dark Mage"
            ]

def get_fe11_direct_promotion_class(char_name, char_data):
    default_cls = char_data["default_class"]
    is_female = char_data["is_female"]
    
    if default_cls in PROMOTED_CLASSES or default_cls in SPECIAL_CLASSES:
        return default_cls
        
    if default_cls == "Pegasus Knight":
        return "Falcon Knight"
        
    for p_cls, b_cls in PROMOTION_MAP.items():
        if b_cls == default_cls:
            if default_cls == "Cavalier" and p_cls == "Dracoknight":
                continue
            return p_cls
            
    if default_cls == "Cleric" or default_cls == "Curate":
        return "Bishop"
        
    return default_cls
