import os
from engine.common import STATS
from engine.parser import parse_html_tables, clean_value, parse_int, fetch_page

# --- FE9 Configurations & Constants ---
URLS_FE9 = {
    "fe9_bases": "https://serenesforest.net/path-of-radiance/characters/base-stats/",
    "fe9_growths": "https://serenesforest.net/path-of-radiance/characters/growth-rates/",
    "fe9_caps": "https://serenesforest.net/path-of-radiance/classes/maximum-stats/",
    "fe9_promotions": "https://serenesforest.net/path-of-radiance/classes/promotion-gains/"
}

FE9_FEMALE_CHARACTERS = {
    "Titania", "Mia", "Ilyana", "Marcia", "Mist", "Lethe", "Nephenee", 
    "Jill", "Astrid", "Tanith", "Calill", "Lucia", "Elincia", "Ena", "Leanne"
}

FE9_SPECIAL_CLASSES = {
    "Beast tribe (Cat)", "Beast tribe (Tiger)", "Beast tribe (Lion)", 
    "Bird tribe (Hawk)", "Bird tribe (Raven)", "Bird tribe (Heron)", 
    "Dragon tribe (Red)", "Dragon tribe (White)", "Thief"
}

FE9_PROMOTION_MAP = {
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

def is_fe9_promoted(cls_name):
    promoted = {
        "Lord", "Hero", "Swordmaster", "Swordmaster (M)", "Swordmaster (F)", 
        "Halberdier", "Warrior", "Sniper", "General", "Paladin", "Paladin (M)", 
        "Paladin (F)", "Falcon Knight", "Wyvern Lord", "Wyvern Lord (M)", 
        "Wyvern Lord (F)", "Sage", "Bishop", "Valkyrie", "Assassin", "Assassin (M)", 
        "Berserker", "Princess Crimea"
    }
    return cls_name in promoted

def get_fe9_caps_key(cls_name, is_female, char_name=""):
    if char_name == "Ike" and cls_name == "Lord":
        return "Lord / Hero"
    if char_name == "Elincia":
        return "Princess Crimea"
    if char_name == "Tibarn":
        return "Bird tribe (Tibarn)"
    if char_name == "Naesala":
        return "Bird tribe (Naesala)"
    
    if cls_name in ("Ranger", "Myrmidon", "Soldier", "Fighter", "Archer", "Knight", 
                    "Sword Knight", "Lance Knight", "Axe Knight", "Thief", "Pegasus Knight", "Wyvern Rider"):
        return "Non-promoted physical"
    if cls_name == "Bow Knight":
        return "Horse Knight (F)" if is_female else "Non-promoted physical"
    if cls_name in ("Cleric", "Priest"):
        return "Priest / Cleric"
    
    if cls_name == "Swordmaster":
        return "Swordmaster (F)" if is_female else "Swordmaster (M)"
    if cls_name == "Paladin":
        return "Paladin (F)" if is_female else "Paladin (M)"
    if cls_name == "Wyvern Lord":
        return "Wyvern Lord (F)" if is_female else "Wyvern Lord (M)"
    if cls_name == "Assassin":
        return "Assassin (F)" if is_female else "Assassin (M)"
    
    if cls_name == "Beast tribe (Cat)":
        return "Beast tribe (Cat F)" if is_female else "Beast tribe (Cat M)"
    if cls_name == "Beast tribe (Tiger)":
        return "Beast tribe (Tiger)"
    if cls_name == "Beast tribe (Lion)":
        return "Lion" if char_name == "Giffca" else "Beast tribe (Lion)"
    if cls_name == "Bird tribe (Hawk)":
        return "Bird tribe (Hawk)"
    if cls_name == "Bird tribe (Raven)":
        return "Bird tribe (Raven)"
    if cls_name == "Bird tribe (Heron)":
        return "Bird tribe (Heron F)" if is_female else "Bird tribe (Heron M)"
    if cls_name == "Dragon tribe (Red)":
        return "Dragon tribe (Red F)" if is_female else "Dragon tribe (Red M)"
    if cls_name == "Dragon tribe (White)":
        return "Dragon tribe (White)"
        
    return cls_name

def get_fe9_promo_gains(base_cls, promo_cls, is_female, promo_gains_db):
    mapped_base = base_cls
    mapped_promo = promo_cls
    
    if base_cls == "Mage":
        mapped_base = "Mage (F)" if is_female else "Mage (M)"
        mapped_promo = "Sage (F)" if is_female else "Sage (M)"
    elif base_cls == "Myrmidon":
        mapped_base = "Myrmidon (F)" if is_female else "Myrmidon (M)"
        mapped_promo = "Swordmaster (F)" if is_female else "Swordmaster (M)"
    elif base_cls == "Soldier":
        mapped_base = "Soldier (F)" if is_female else "Soldier"
        mapped_promo = "Halberdier (F)" if is_female else "Halberdier"
    elif base_cls == "Wyvern Rider":
        mapped_base = "Wyvern Rider (F)" if is_female else "Wyvern Rider"
        mapped_promo = "Wyvern Lord (F)" if is_female else "Wyvern Lord"
    elif base_cls == "Priest":
        mapped_base = "Priest"
        mapped_promo = "Bishop (M)"
    elif base_cls == "Thief":
        mapped_base = "Thief"
        mapped_promo = "Assassin (M)"
    elif base_cls == "Sword Knight":
        mapped_base = "Sword Knight (M)"
        mapped_promo = "Paladin (M)"
    elif base_cls == "Lance Knight":
        mapped_base = "Lance Knight (M)"
        mapped_promo = "Paladin (M)"
    elif base_cls == "Axe Knight":
        mapped_base = "Axe Knight (M)"
        mapped_promo = "Paladin (M)"
    elif base_cls == "Bow Knight":
        mapped_base = "Bow Knight (F)" if is_female else "Bow Knight"
        mapped_promo = "Paladin (F)" if is_female else "Paladin"
        
    key = (mapped_base, mapped_promo)
    if key in promo_gains_db:
        return promo_gains_db[key]
    key_plain = (base_cls, promo_cls)
    if key_plain in promo_gains_db:
        return promo_gains_db[key_plain]
        
    return {s: 0 for s in STATS}

def get_valid_classes_for_fe9_character(char_data):
    base_cls = char_data["default_class"]
    name = char_data["name"]
    if base_cls in FE9_SPECIAL_CLASSES:
        if base_cls == "Thief":
            if name == "Sothe":
                return ["Thief"]
            else:
                return ["Thief", "Assassin"]
        return [base_cls]
    
    promoted_cls = FE9_PROMOTION_MAP.get(base_cls)
    if not promoted_cls:
        return [base_cls]
    return [base_cls, promoted_cls]

def get_fe9_direct_promotion_class(char_name, char_data):
    base_cls = char_data["default_class"]
    if char_name == "Volke":
        return "Assassin"
    if base_cls in FE9_SPECIAL_CLASSES:
        return base_cls
    return FE9_PROMOTION_MAP.get(base_cls, base_cls)

def load_fe9_data():
    import json, os
    from engine.common import BASE_DIR
    with open(os.path.join(BASE_DIR, 'data', 'fe9.json'), 'r', encoding='utf-8') as f:
        db = json.load(f)
    if 'classes' in db and 'promo_gains' in db['classes']:
        pg = db['classes']['promo_gains']
        db['classes']['promo_gains'] = {tuple(k.split(' -> ')) if ' -> ' in k else k: v for k, v in pg.items()}
    return db

def calculate_fe9_avg_stats(char_data, target_class, db):
    is_female = char_data["is_female"]
    join_lv = char_data["join_lv"]
    abs_bases = char_data["absolute_bases"]
    base_growths = char_data["base_growths"]
    char_name = char_data["name"]
    
    caps_db = db["classes"]["caps"]
    promo_gains_db = db["classes"]["promo_gains"]

    current_stats = {}
    history = []

    caps_key = get_fe9_caps_key(target_class, is_female, char_name)
    cls_caps = caps_db.get(caps_key, {s: 20 for s in STATS})

    if not is_fe9_promoted(target_class):
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

    elif is_fe9_promoted(target_class):
        is_already_promoted = is_fe9_promoted(char_data["default_class"])
        
        if not is_already_promoted:
            base_cls = char_data["default_class"]
            base_caps_key = get_fe9_caps_key(base_cls, is_female, char_name)
            base_caps = caps_db.get(base_caps_key, {s: 20 for s in STATS})
            
            for s in STATS:
                current_stats[s] = float(max(0, abs_bases[s]))

            history.append((join_lv, base_cls, current_stats.copy()))
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(base_caps[s]), current_stats[s])
                history.append((lv, base_cls, current_stats.copy()))
            
            gains = get_fe9_promo_gains(base_cls, target_class, is_female, promo_gains_db)
            promo_caps_key = get_fe9_caps_key(target_class, is_female, char_name)
            promo_caps = caps_db.get(promo_caps_key, {s: 20 for s in STATS})
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
            promo_caps_key = get_fe9_caps_key(target_class, is_female, char_name)
            promo_caps = caps_db.get(promo_caps_key, {s: 20 for s in STATS})
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
