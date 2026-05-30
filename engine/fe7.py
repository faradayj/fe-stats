import os
from engine.common import STATS
from engine.parser import parse_html_tables, clean_value, parse_int, fetch_page

# --- FE7 Configurations & Constants ---
URLS_FE7 = {
    "fe7_bases": "https://serenesforest.net/blazing-sword/characters/base-stats/",
    "fe7_growths": "https://serenesforest.net/blazing-sword/characters/growth-rates/",
    "fe7_caps": "https://serenesforest.net/blazing-sword/classes/maximum-stats/",
    "fe7_promotions": "https://serenesforest.net/blazing-sword/classes/promotion-gains/"
}

FE7_FEMALE_CHARACTERS = {
    "Lyn", "Florina", "Serra", "Rebecca", "Priscilla", "Fiora", "Ninian", "Isadora", 
    "Farina", "Louise", "Nino", "Vaida", "Vaida HM", "Karla"
}

FE7_MAGICAL_CLASSES = {
    "Mage", "Sage", "Monk", "Priest", "Cleric", "Bishop", "Shaman", "Druid", "Troubadour", 
    "Valkyrie", "Archsage"
}

FE7_SPECIAL_CLASSES = {"Dancer", "Bard", "Transporter", "Archsage"}

FE7_PROMOTION_MAP = {
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

def get_fe7_gendered_class(cls_name, is_female):
    gender_suffix = " (F)" if is_female else " (M)"
    if cls_name in ["Paladin", "General", "Hero", "Swordmaster", "Sniper", "Nomad Trooper", "Nmd Trooper", "Wyvern Lord", "Sage", "Bishop", "Druid"]:
        return f"{cls_name}{gender_suffix}"
    return cls_name

def get_valid_classes_for_fe7_character(char_data):
    base_cls = char_data["default_class"]
    if base_cls in FE7_SPECIAL_CLASSES:
        return [base_cls]
    if base_cls == "Lord":
        name = char_data["name"]
        if "Lyn" in name:
            return ["Lord", "Blade Lord"]
        elif "Eliwood" in name:
            return ["Lord", "Knight Lord"]
        elif "Hector" in name:
            return ["Lord", "Great Lord"]
    promoted_cls = FE7_PROMOTION_MAP.get(base_cls)
    if not promoted_cls:
        return [base_cls]
    return [base_cls, promoted_cls]

def load_fe7_data():
    raw = {
        name: fetch_page(name, URLS_FE7[name])
        for name in ["fe7_bases", "fe7_growths", "fe7_caps", "fe7_promotions"]
    }

    # 1. Parse Class Caps
    class_caps = {}
    tables = parse_html_tables(raw["fe7_caps"])
    for table in tables:
        if len(table) > 1 and "S/M" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                cls_name = clean_value(row[0])
                if not cls_name or cls_name == "Class":
                    continue
                
                is_magical = cls_name in FE7_MAGICAL_CLASSES or "Sage" in cls_name or "Bishop" in cls_name or "Druid" in cls_name or "Valkyrie" in cls_name or "Archsage" in cls_name
                sm_val = parse_int(row[headers.index("S/M")])
                
                if cls_name == "Non-promoted":
                    str_val = sm_val
                    mag_val = sm_val
                else:
                    str_val = 0 if is_magical else sm_val
                    mag_val = sm_val if is_magical else 0
                
                class_caps[cls_name] = {
                    "HP": 60,
                    "Str": str_val,
                    "Mag": mag_val,
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": 30,
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    # 2. Parse Promotion Gains
    promo_gains = {}
    tables = parse_html_tables(raw["fe7_promotions"])
    for table in tables:
        if len(table) > 1 and "Def" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                promo_cls = clean_value(row[0])
                if not promo_cls or promo_cls == "Class":
                    continue
                
                is_magical = promo_cls in FE7_MAGICAL_CLASSES or "Sage" in promo_cls or "Bishop" in promo_cls or "Druid" in promo_cls or "Valkyrie" in promo_cls or "Archsage" in promo_cls
                sm_val = parse_int(row[headers.index("S/M")])
                
                str_val = 0 if is_magical else sm_val
                mag_val = sm_val if is_magical else 0
                
                promo_gains[promo_cls] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": str_val,
                    "Mag": mag_val,
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": 0,
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    # 3. Parse Character Bases
    char_bases = {}
    tables = parse_html_tables(raw["fe7_bases"])
    table = tables[1]  # Eliwood/Hector main story bases
    headers = [clean_value(h) for h in table[0]]
    for row in table[1:]:
        if len(row) < len(headers):
            continue
        name = clean_value(row[0])
        if not name or name in ["Name", "Class"]:
            continue
        
        is_female = name in FE7_FEMALE_CHARACTERS or name.split(" HM")[0].strip() in FE7_FEMALE_CHARACTERS
        cls_name = clean_value(row[headers.index("Class")])
        is_magical = cls_name in FE7_MAGICAL_CLASSES
        sm_val = parse_int(row[headers.index("S/M")])
        
        char_bases[name] = {
            "name": name,
            "default_class": cls_name,
            "join_lv": parse_int(row[headers.index("Lv")]),
            "is_female": is_female,
            "bases": {
                "HP": parse_int(row[headers.index("HP")]),
                "Str": 0 if is_magical else sm_val,
                "Mag": sm_val if is_magical else 0,
                "Skl": parse_int(row[headers.index("Skl")]),
                "Spd": parse_int(row[headers.index("Spd")]),
                "Lck": parse_int(row[headers.index("Lck")]),
                "Def": parse_int(row[headers.index("Def")]),
                "Res": parse_int(row[headers.index("Res")]),
            }
        }

    # 4. Parse Character Growths
    char_growths = {}
    tables = parse_html_tables(raw["fe7_growths"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "S/M" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0])
                if not name or name == "Name":
                    continue
                
                is_magical = False
                base_info = char_bases.get(name)
                if not base_info:
                    base_info = char_bases.get(f"{name} HM")
                if base_info:
                    is_magical = base_info["default_class"] in FE7_MAGICAL_CLASSES
                
                sm_val = parse_int(row[headers.index("S/M")])
                char_growths[name] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": 0 if is_magical else sm_val,
                    "Mag": sm_val if is_magical else 0,
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index("Lck")]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    database = {
        "characters": {},
        "classes": {
            "caps": class_caps,
            "promo_gains": promo_gains
        }
    }
    
    for name, data in char_bases.items():
        base_name = name.split(" HM")[0].strip()
        growths = char_growths.get(base_name)
        if not growths:
            if base_name in ["Nils", "Ninian"]:
                growths = char_growths.get("Nils/Ninian")
        
        if not growths:
            continue
            
        database["characters"][name] = {
            "name": name,
            "join_lv": data["join_lv"],
            "default_class": data["default_class"],
            "is_female": data["is_female"],
            "absolute_bases": data["bases"],
            "base_growths": growths
        }
        
    return database

# --- FE7 Stat Calculation Engine ---
def is_fe7_promoted(cls_name):
    return cls_name in FE7_PROMOTION_MAP.values() or cls_name in {
        "Blade Lord", "Knight Lord", "Great Lord", "Paladin", "Sage", "Bishop", "Valkyrie", "Wyvern Lord", "General", "Sniper", "Warrior", "Berserker", "Hero", "Swordmaster", "Nomad Trooper", "Nmd Trooper", "Falcon Knight", "Falcoknight", "Assassin"
    }

def get_fe7_caps(cls_name, is_female, caps_db):
    gendered = get_fe7_gendered_class(cls_name, is_female)
    if gendered in caps_db:
        return caps_db[gendered]
    if cls_name in caps_db:
        return caps_db[cls_name]
    return caps_db.get("Non-promoted", {s: 20 for s in STATS})

def get_fe7_promo_gains(target_class, is_female, promo_gains_db):
    gendered = get_fe7_gendered_class(target_class, is_female)
    if gendered in promo_gains_db:
        return promo_gains_db[gendered]
    if target_class in promo_gains_db:
        return promo_gains_db[target_class]
    if target_class == "Falcon Knight" and "Falcoknight" in promo_gains_db:
        return promo_gains_db["Falcoknight"]
    if target_class == "Nomad Trooper" and "Nmd Trooper" in promo_gains_db:
        return promo_gains_db["Nmd Trooper"]
    if target_class == "Nomad Trooper (F)" and "Nmd Trooper (F)" in promo_gains_db:
        return promo_gains_db["Nmd Trooper (F)"]
    if target_class == "Nomad Trooper (M)" and "Nmd Trooper (M)" in promo_gains_db:
        return promo_gains_db["Nmd Trooper (M)"]
    return {s: 0 for s in STATS}

def get_fe7_direct_promotion_class(char_name, char_data):
    base_class = char_data["default_class"]
    if base_class == "Lord":
        if "Lyn" in char_name:
            return "Blade Lord"
        elif "Eliwood" in char_name:
            return "Knight Lord"
        elif "Hector" in char_name:
            return "Great Lord"
    return FE7_PROMOTION_MAP.get(base_class, base_class)

def calculate_fe7_avg_stats(char_data, target_class, db):
    is_female = char_data["is_female"]
    join_lv = char_data["join_lv"]
    abs_bases = char_data["absolute_bases"]
    base_growths = char_data["base_growths"]
    
    caps_db = db["classes"]["caps"]
    promo_gains_db = db["classes"]["promo_gains"]

    current_stats = {}
    history = []

    # Case 1: Special Class (No Promotion)
    if target_class in FE7_SPECIAL_CLASSES:
        cls_caps = get_fe7_caps(target_class, is_female, caps_db)
        
        for s in STATS:
            current_stats[s] = float(max(0, abs_bases[s]))

        history.append((join_lv, target_class, current_stats.copy()))
        for lv in range(join_lv + 1, 21):
            for s in STATS:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(cls_caps[s]), current_stats[s])
            history.append((lv, target_class, current_stats.copy()))
            
        return {
            "class_path": target_class,
            "final_class": target_class,
            "final_level": "20",
            "stats": current_stats,
            "history": history
        }

    # Case 2: Promoted Class
    elif is_fe7_promoted(target_class):
        is_already_promoted = is_fe7_promoted(char_data["default_class"])
        
        if not is_already_promoted:
            base_cls = char_data["default_class"]
            base_caps = get_fe7_caps(base_cls, is_female, caps_db)
            
            for s in STATS:
                current_stats[s] = float(max(0, abs_bases[s]))

            history.append((join_lv, base_cls, current_stats.copy()))
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(base_caps[s]), current_stats[s])
                history.append((lv, base_cls, current_stats.copy()))
            
            # Apply Promotion Gains
            gains = get_fe7_promo_gains(target_class, is_female, promo_gains_db)
            promo_caps = get_fe7_caps(target_class, is_female, caps_db)
            for s in STATS:
                current_stats[s] += gains[s]
                current_stats[s] = min(float(promo_caps[s]), current_stats[s])
            
            history.append(("20/1", target_class, current_stats.copy()))
            for lv in range(2, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
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
            promo_caps = get_fe7_caps(target_class, is_female, caps_db)
            for s in STATS:
                current_stats[s] = float(max(0, abs_bases[s]))

            history.append((join_lv, target_class, current_stats.copy()))
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
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

    # Case 3: Base Class (Level 20 unpromoted)
    else:
        base_caps = get_fe7_caps(target_class, is_female, caps_db)
        for s in STATS:
            current_stats[s] = float(max(0, abs_bases[s]))

        history.append((join_lv, target_class, current_stats.copy()))
        for lv in range(join_lv + 1, 21):
            for s in STATS:
                growth_rate = max(0, base_growths[s])
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
