import os
from engine.common import STATS
from engine.parser import parse_html_tables, clean_value, parse_int, fetch_page

# --- FE6 Configurations & Constants ---
URLS_FE6 = {
    "fe6_bases": "https://serenesforest.net/binding-blade/characters/base-stats/",
    "fe6_growths": "https://serenesforest.net/binding-blade/characters/growth-rates/",
    "fe6_caps": "https://serenesforest.net/binding-blade/classes/maximum-stats/",
    "fe6_promotions": "https://serenesforest.net/binding-blade/classes/promotion-gains/"
}

FE6_FEMALE_CHARACTERS = {
    "Elen", "Ellen", "Clarine", "Sue", "Wendy", "Fir", "Fir (HM)", "Tate", "Tate (HM)", 
    "Lalum", "Echidna", "Cath", "Cath (HM)", "Miredy", "Miredy (HM)", "Sofiya", "Sophia",
    "Igrene", "Fa", "Niime", "Juno", "Brunya", "Guinevere", "Lilina", "Thany", "Cecilia", "Dorothy"
}

FE6_MAGICAL_CLASSES = {
    "Mage", "Sage", "Shaman", "Druid", "Priest", "Cleric", "Bishop", "Troubadour", "Valkyria", "Valkyrie",
    "Mage (M)", "Mage (F)", "Sage (M)", "Sage (F)", "Shaman (M)", "Shaman (F)",
    "Druid (M)", "Druid (F)", "Priest (M)", "Priest (F)", "Bishop (M)", "Bishop (F)", "Valkyria"
}

FE6_SPECIAL_CLASSES = {"Thief", "Bard", "Dancer", "Mamkute", "Transporter", "King"}

FE6_PROMOTION_MAP = {
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

def get_fe6_gendered_class(cls_name, is_female):
    gender_suffix = " (F)" if is_female else " (M)"
    if cls_name == "Nomadic Trooper" or cls_name == "Nomad Trooper":
        return f"Nomad Trooper{gender_suffix}"
    if cls_name == "Cleric":
        return "Priest (F)"
    gender_distinguished = {
        "Mercenary", "Hero", "Myrmidon", "Swordmaster", "Cavalier", "Paladin",
        "Knight", "General", "Archer", "Sniper", "Nomad",
        "Wyvern Rider", "Wyvern Lord", "Mage", "Sage", "Shaman", "Druid", "Priest", "Bishop"
    }
    if cls_name in gender_distinguished:
        return cls_name + gender_suffix
    return cls_name

def get_valid_classes_for_fe6_character(char_data):
    base_cls = char_data["default_class"]
    if base_cls in FE6_SPECIAL_CLASSES:
        return [base_cls]
    promoted_cls = FE6_PROMOTION_MAP.get(base_cls)
    if not promoted_cls:
        return [base_cls]
    return [base_cls, promoted_cls]

def load_fe6_data():
    raw = {
        name: fetch_page(name, URLS_FE6[name])
        for name in ["fe6_bases", "fe6_growths", "fe6_caps", "fe6_promotions"]
    }

    # 1. Parse Class Caps
    class_caps = {}
    tables = parse_html_tables(raw["fe6_caps"])
    for table in tables:
        if len(table) > 1 and "S/M" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                cls_name = clean_value(row[0])
                if not cls_name or cls_name == "Class":
                    continue
                
                is_magical = cls_name in FE6_MAGICAL_CLASSES
                sm_val = parse_int(row[headers.index("S/M")])
                
                if "Non-promoted" in cls_name:
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
    tables = parse_html_tables(raw["fe6_promotions"])
    for table in tables:
        if len(table) > 1 and "S/M" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                base_cls = clean_value(row[0])
                promo_cls = clean_value(row[1])
                if not base_cls or base_cls == "Base Class":
                    continue
                
                is_magical = promo_cls in FE6_MAGICAL_CLASSES
                sm_val = parse_int(row[headers.index("S/M")])
                
                str_val = 0 if is_magical else sm_val
                mag_val = sm_val if is_magical else 0
                
                key = (base_cls, promo_cls)
                promo_gains[key] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": str_val,
                    "Mag": mag_val,
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": 0, # GBA promotions do not give Luck gains
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    # 3. Parse Character Bases
    characters = {}
    tables = parse_html_tables(raw["fe6_bases"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "Lv" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0])
                if not name or name == "Name":
                    continue
                
                # Check for Hard Mode duplicate name rows
                is_hm = False
                if "(HM)" in name or (len(row) > headers.index("Lv") + 1 and "Hard" in clean_value(row[headers.index("Lv") + 1])):
                    is_hm = True
                    
                cls_name = clean_value(row[headers.index("Class")])
                is_female = name in FE6_FEMALE_CHARACTERS
                is_magical = cls_name in FE6_MAGICAL_CLASSES
                
                sm_val = parse_int(row[headers.index("S/M")])
                str_val = 0 if is_magical else sm_val
                mag_val = sm_val if is_magical else 0
                
                db_name = f"{name} (HM)" if (is_hm and not name.endswith("(HM)")) else name
                
                characters[db_name] = {
                    "name": db_name,
                    "join_lv": parse_int(row[headers.index("Lv")]),
                    "default_class": cls_name,
                    "is_female": is_female,
                    "bases": {
                        "HP": parse_int(row[headers.index("HP")]),
                        "Str": str_val,
                        "Mag": mag_val,
                        "Skl": parse_int(row[headers.index("Skl")]),
                        "Spd": parse_int(row[headers.index("Spd")]),
                        "Lck": parse_int(row[headers.index("Lck")]),
                        "Def": parse_int(row[headers.index("Def")]),
                        "Res": parse_int(row[headers.index("Res")]),
                    }
                }

    # 4. Parse Character Growths
    tables = parse_html_tables(raw["fe6_growths"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "S/M" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0])
                if not name or name == "Name":
                    continue
                
                # Growth rates are shared for normal/HM profiles
                matching_chars = [c for c in characters if c == name or c == f"{name} (HM)"]
                if not matching_chars:
                    continue
                
                is_magical = characters[matching_chars[0]]["default_class"] in FE6_MAGICAL_CLASSES
                sm_val = parse_int(row[headers.index("S/M")])
                str_val = 0 if is_magical else sm_val
                mag_val = sm_val if is_magical else 0
                
                growths = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": str_val,
                    "Mag": mag_val,
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index("Lck")]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }
                
                for cname in matching_chars:
                    characters[cname]["growths"] = growths

    # Unify into standard structure
    database = {"characters": {}, "classes": {"caps": class_caps, "promo_gains": promo_gains}}
    for name, data in characters.items():
        if "growths" in data:
            database["characters"][name] = {
                "name": name,
                "join_lv": data["join_lv"],
                "default_class": data["default_class"],
                "is_female": data["is_female"],
                "absolute_bases": data["bases"],
                "base_growths": data["growths"]
            }
            
    return database


# --- FE6 Stat Calculation Engine ---
def is_fe6_promoted(cls_name):
    return cls_name in FE6_PROMOTION_MAP.values() or cls_name in {
        "Paladin", "Sage", "Bishop", "Valkyria", "Wyvern Lord", "General", "Sniper", "Warrior", "Berserker", "Hero", "Swordmaster", "Nomadic Trooper", "Nomad Trooper"
    }

def get_fe6_caps(cls_name, is_female, caps_db):
    gendered = get_fe6_gendered_class(cls_name, is_female)
    if gendered in caps_db:
        return caps_db[gendered]
    if cls_name in caps_db:
        return caps_db[cls_name]
    return caps_db.get("Non-promoted", {s: 20 for s in STATS})

def get_fe6_promo_gains(base_cls, promo_cls, is_female, promo_gains_db):
    gendered_base = get_fe6_gendered_class(base_cls, is_female)
    gendered_promo = get_fe6_gendered_class(promo_cls, is_female)
    
    key = (gendered_base, gendered_promo)
    if key in promo_gains_db:
        return promo_gains_db[key]
    key_plain = (base_cls, promo_cls)
    if key_plain in promo_gains_db:
        return promo_gains_db[key_plain]
    return {s: 0 for s in STATS}

def calculate_fe6_avg_stats(char_data, target_class, db):
    is_female = char_data["is_female"]
    join_lv = char_data["join_lv"]
    abs_bases = char_data["absolute_bases"]
    base_growths = char_data["base_growths"]
    
    caps_db = db["classes"]["caps"]
    promo_gains_db = db["classes"]["promo_gains"]

    current_stats = {}
    history = []

    if target_class in FE6_SPECIAL_CLASSES:
        cls_caps = get_fe6_caps(target_class, is_female, caps_db)
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

    elif is_fe6_promoted(target_class):
        is_already_promoted = is_fe6_promoted(char_data["default_class"])
        
        if not is_already_promoted:
            base_cls = char_data["default_class"]
            base_caps = get_fe6_caps(base_cls, is_female, caps_db)
            
            for s in STATS:
                current_stats[s] = float(max(0, abs_bases[s]))

            history.append((join_lv, base_cls, current_stats.copy()))
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(base_caps[s]), current_stats[s])
                history.append((lv, base_cls, current_stats.copy()))
            
            gains = get_fe6_promo_gains(base_cls, target_class, is_female, promo_gains_db)
            promo_caps = get_fe6_caps(target_class, is_female, caps_db)
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
            promo_caps = get_fe6_caps(target_class, is_female, caps_db)
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

    else:
        base_caps = get_fe6_caps(target_class, is_female, caps_db)
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

def get_fe6_direct_promotion_class(char_name, char_data):
    base_class = char_data["default_class"]
    return FE6_PROMOTION_MAP.get(base_class, base_class)
