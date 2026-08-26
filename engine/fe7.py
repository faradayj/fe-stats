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
    import json, os
    from engine.common import BASE_DIR
    with open(os.path.join(BASE_DIR, 'data', 'fe7.json'), 'r', encoding='utf-8') as f:
        db = json.load(f)
    if 'classes' in db and 'promo_gains' in db['classes']:
        pg = db['classes']['promo_gains']
        db['classes']['promo_gains'] = {tuple(k.split(' -> ')) if ' -> ' in k else k: v for k, v in pg.items()}
    return db
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
