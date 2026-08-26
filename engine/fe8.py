import os
import re
from engine.common import STATS
from engine.parser import parse_html_tables, clean_value, parse_int, fetch_page

# --- FE8 Configurations & Constants ---
URLS_FE8 = {
    "fe8_bases": "https://serenesforest.net/the-sacred-stones/characters/base-stats/",
    "fe8_growths": "https://serenesforest.net/the-sacred-stones/characters/growth-rates/",
    "fe8_caps": "https://serenesforest.net/the-sacred-stones/classes/maximum-stats/",
    "fe8_promotions": "https://serenesforest.net/the-sacred-stones/classes/promotion-gains/"
}

FE8_FEMALE_CHARACTERS = {
    "Eirika", "Vanessa", "Neimi", "Lute", "Natasha", "Amelia", "Tana", "Marisa", "L'Arachel", 
    "Myrrh", "Syrene", "Ismaire", "Selena"
}

FE8_MAGICAL_CLASSES = {
    "Mage", "Sage", "Monk", "Priest", "Cleric", "Bishop", "Shaman", "Druid", "Summoner", "Pupil", 
    "Troubadour", "Valkyrie", "Mage Knight", "Necromancer", "Necromancer (Lyon)", "Pupil (1)", "Pupil (2)", "Pupil (3)"
}

FE8_PROMOTION_TREE = {
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

def clean_fe8_char_name(name):
    name = clean_value(name)
    name = re.sub(r"L[^a-zA-Z]?Arachel", "L'Arachel", name)
    name = name.replace("Knolls", "Knoll's").replace("Ewans", "Ewan's").replace("Lyons", "Lyon's")
    name = name.replace("’", "'").replace("`", "'")
    return name

def is_fe8_magical_class(cls_name):
    base_name = cls_name.split("(")[0].strip()
    if base_name in FE8_MAGICAL_CLASSES:
        return True
    if any(m in cls_name for m in ["Sage", "Bishop", "Druid", "Summoner", "Valkyrie", "Mage Knight", "Necromancer", "Pupil"]):
        return True
    return False

def load_fe8_data():
    import json, os
    from engine.common import BASE_DIR
    with open(os.path.join(BASE_DIR, 'data', 'fe8.json'), 'r', encoding='utf-8') as f:
        db = json.load(f)
    if 'classes' in db and 'promo_gains' in db['classes']:
        pg = db['classes']['promo_gains']
        db['classes']['promo_gains'] = {tuple(k.split(' -> ')) if ' -> ' in k else k: v for k, v in pg.items()}
    return db

def get_fe8_caps(cls_name, is_female, caps_db):
    if cls_name in caps_db:
        return caps_db[cls_name]
    gender_suffix = " (F)" if is_female else " (M)"
    if f"{cls_name}{gender_suffix}" in caps_db:
        return caps_db[f"{cls_name}{gender_suffix}"]
    clean_name = cls_name.split("(")[0].strip()
    if clean_name in caps_db:
        return caps_db[clean_name]
    if f"{clean_name}{gender_suffix}" in caps_db:
        return caps_db[f"{clean_name}{gender_suffix}"]
    return {
        "HP": 60, "Str": 20, "Mag": 20, "Skl": 20, "Spd": 20, "Lck": 30, "Def": 20, "Res": 20
    }

def get_fe8_promo_gains(base_cls, promo_cls, promo_gains_db):
    key = (base_cls, promo_cls)
    if key in promo_gains_db:
        return promo_gains_db[key]
    clean_promo = promo_cls.split("(")[0].strip()
    key2 = (base_cls, clean_promo)
    if key2 in promo_gains_db:
        return promo_gains_db[key2]
    clean_base = base_cls.split("(")[0].strip()
    key3 = (clean_base, clean_promo)
    if key3 in promo_gains_db:
        return promo_gains_db[key3]
    if clean_base == "Pupil" and clean_promo == "Shaman":
        if ("Pupil", "Shaman (M)") in promo_gains_db:
            return promo_gains_db[("Pupil", "Shaman (M)")]
    return {s: 0 for s in STATS}

def is_fe8_promoted(cls_name):
    base_name = cls_name.split("(")[0].strip()
    if base_name in ["Lord", "Dancer", "Manakete", "Journeyman", "Recruit", "Pupil", "Journeyman (2)", "Recruit (2)", "Pupil (2)"]:
        return False
    if base_name in ["Cavalier", "Knight", "Thief", "Mercenary", "Myrmidon", "Archer", "Wyvern Rider", "Pegasus Knight", "Mage", "Shaman", "Priest", "Monk", "Cleric", "Troubadour", "Fighter", "Pirate"]:
        return False
    return True

def get_fe8_valid_classes_and_paths(char_name, default_class, is_female):
    if char_name == "Myrrh" or default_class == "Manakete":
        return [["Manakete"]]
    if char_name == "Tethys" or default_class == "Dancer":
        return [["Dancer"]]
    
    gender_suffix = " (F)" if is_female else " (M)"
    if default_class in ["Paladin", "Sniper", "Berserker", "Sage", "Rogue", "Great Knight", "Falcoknight", "Hero", "Bishop", "Swordmaster", "Mage Knight", "Wyvern Lord", "Wyvern Knight", "General", "Necromancer"]:
        if default_class in ["Necromancer", "Rogue"]:
            return [[default_class]]
        if default_class == "Falcoknight":
            return [["Falcoknight"]]
        return [[f"{default_class}{gender_suffix}"]]
    
    start_class = default_class
    if default_class in ["Cavalier", "Knight", "Myrmidon", "Archer", "Mage"]:
        start_class = f"{default_class}{gender_suffix}"
    elif default_class == "Lord":
        if "Eirika" in char_name:
            start_class = "Lord (Eirika)"
        else:
            start_class = "Lord (Ephraim)"
            
    paths = []
    def build_paths(current_path):
        cls = current_path[-1]
        promotions = FE8_PROMOTION_TREE.get(cls, [])
        if not promotions:
            paths.append(current_path)
            return
        paths.append(current_path)
        for promo in promotions:
            build_paths(current_path + [promo])
            
    build_paths([start_class])
    return paths

def calculate_fe8_avg_stats(char_data, path, db):
    is_female = char_data["is_female"]
    join_lv = char_data["join_lv"]
    abs_bases = char_data["absolute_bases"]
    base_growths = char_data["base_growths"]
    
    caps_db = db["classes"]["caps"]
    promo_gains_db = db["classes"]["promo_gains"]

    current_stats = {s: float(abs_bases[s]) for s in STATS}
    history = []

    is_trainee = char_data["default_class"] in ["Journeyman", "Recruit", "Pupil"]

    if is_trainee:
        t1_class = path[0]
        t1_caps = get_fe8_caps(t1_class, is_female, caps_db)
        
        for s in STATS:
            current_stats[s] = min(float(t1_caps[s]), current_stats[s])
        history.append((join_lv, t1_class, current_stats.copy()))
        
        for lv in range(join_lv + 1, 11):
            for s in STATS:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(t1_caps[s]), current_stats[s])
            history.append((lv, t1_class, current_stats.copy()))
            
        if len(path) > 1:
            t2_class = path[1]
            t2_caps = get_fe8_caps(t2_class, is_female, caps_db)
            gains = get_fe8_promo_gains(t1_class, t2_class, promo_gains_db)
            
            for s in STATS:
                current_stats[s] += gains[s]
                current_stats[s] = min(float(t2_caps[s]), current_stats[s])
            history.append(("10/1", t2_class, current_stats.copy()))
            
            for lv in range(2, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t2_caps[s]), current_stats[s])
                history.append((f"10/{lv}", t2_class, current_stats.copy()))
                
            if len(path) > 2:
                t3_class = path[2]
                t3_caps = get_fe8_caps(t3_class, is_female, caps_db)
                gains2 = get_fe8_promo_gains(t2_class, t3_class, promo_gains_db)
                
                for s in STATS:
                    current_stats[s] += gains2[s]
                    current_stats[s] = min(float(t3_caps[s]), current_stats[s])
                history.append(("10/20/1", t3_class, current_stats.copy()))
                
                for lv in range(2, 21):
                    for s in STATS:
                        growth_rate = max(0, base_growths[s])
                        current_stats[s] += growth_rate / 100.0
                        current_stats[s] = min(float(t3_caps[s]), current_stats[s])
                    history.append((f"10/20/{lv}", t3_class, current_stats.copy()))
                    
                return {
                    "class_path": " -> ".join(path),
                    "final_class": t3_class,
                    "final_level": "10/20/20",
                    "stats": current_stats,
                    "history": history
                }
            else:
                return {
                    "class_path": " -> ".join(path),
                    "final_class": t2_class,
                    "final_level": "10/20",
                    "stats": current_stats,
                    "history": history
                }
        else:
            return {
                "class_path": t1_class,
                "final_class": t1_class,
                "final_level": "10",
                "stats": current_stats,
                "history": history
            }
            
    else:
        start_class = path[0]
        is_already_promoted = is_fe8_promoted(char_data["default_class"])
        
        if not is_already_promoted:
            t1_caps = get_fe8_caps(start_class, is_female, caps_db)
            for s in STATS:
                current_stats[s] = min(float(t1_caps[s]), current_stats[s])
            history.append((join_lv, start_class, current_stats.copy()))
            
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t1_caps[s]), current_stats[s])
                history.append((lv, start_class, current_stats.copy()))
                
            if len(path) > 1:
                promo_class = path[1]
                promo_caps = get_fe8_caps(promo_class, is_female, caps_db)
                gains = get_fe8_promo_gains(start_class, promo_class, promo_gains_db)
                
                for s in STATS:
                    current_stats[s] += gains[s]
                    current_stats[s] = min(float(promo_caps[s]), current_stats[s])
                history.append(("20/1", promo_class, current_stats.copy()))
                
                for lv in range(2, 21):
                    for s in STATS:
                        growth_rate = max(0, base_growths[s])
                        current_stats[s] += growth_rate / 100.0
                        current_stats[s] = min(float(promo_caps[s]), current_stats[s])
                    history.append((f"20/{lv}", promo_class, current_stats.copy()))
                    
                return {
                    "class_path": " -> ".join(path),
                    "final_class": promo_class,
                    "final_level": "20/20",
                    "stats": current_stats,
                    "history": history
                }
            else:
                return {
                    "class_path": start_class,
                    "final_class": start_class,
                    "final_level": "20",
                    "stats": current_stats,
                    "history": history
                }
                
        else:
            promo_caps = get_fe8_caps(start_class, is_female, caps_db)
            for s in STATS:
                current_stats[s] = min(float(promo_caps[s]), current_stats[s])
            history.append((join_lv, start_class, current_stats.copy()))
            
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(promo_caps[s]), current_stats[s])
                history.append((lv, start_class, current_stats.copy()))
                
            return {
                "class_path": start_class,
                "final_class": start_class,
                "final_level": f"{join_lv} -> 20",
                "stats": current_stats,
                "history": history
            }

def get_fe8_direct_promotion_class(char_name, char_data):
    base_class = char_data["default_class"]
    
    if is_fe8_promoted(base_class) or base_class in ["Manakete", "Dancer"]:
        return base_class
        
    if char_name == "Ross":
        return "Warrior (via Fighter)"
    if char_name == "Amelia":
        return "General (F) (via Knight (F))"
    if char_name == "Ewan":
        return "Sage (M) (via Mage (M))"
        
    gender_suffix = " (F)" if char_data["is_female"] else " (M)"
    
    if base_class == "Lord":
        if "Eirika" in char_name:
            return "Great Lord (Eirika)"
        else:
            return "Great Lord (Ephraim)"
            
    mapping = {
        "Cavalier": "Paladin",
        "Knight": "General",
        "Thief": "Rogue",
        "Mercenary": "Hero",
        "Myrmidon": "Swordmaster",
        "Archer": "Sniper",
        "Wyvern Rider": "Wyvern Lord",
        "Pegasus Knight": "Falcoknight",
        "Mage": "Sage",
        "Shaman": "Druid",
        "Priest": "Bishop",
        "Monk": "Bishop",
        "Cleric": "Bishop",
        "Troubadour": "Valkyrie",
        "Fighter": "Warrior",
        "Pirate": "Berserker"
    }
    
    promo = mapping.get(base_class)
    if not promo:
        return base_class
        
    if promo in ["Paladin", "General", "Hero", "Swordmaster", "Sniper", "Wyvern Lord", "Sage", "Druid", "Bishop"]:
        return f"{promo}{gender_suffix}"
    return promo

def get_fe8_class_keys(char_name, char_data):
    default_class = char_data["default_class"]
    is_female = char_data["is_female"]
    paths = get_fe8_valid_classes_and_paths(char_name, default_class, is_female)
    
    final_class_to_paths = {}
    for p in paths:
        final_class = p[-1]
        if final_class not in final_class_to_paths:
            final_class_to_paths[final_class] = []
        final_class_to_paths[final_class].append(p)
        
    path_to_key = {}
    for final_class, path_list in final_class_to_paths.items():
        if len(path_list) == 1:
            path_to_key[tuple(path_list[0])] = final_class
        else:
            for p in path_list:
                if len(p) < 2:
                    path_to_key[tuple(p)] = final_class
                else:
                    promo_via = p[1].split("(")[0].strip()
                    path_to_key[tuple(p)] = f"{final_class} (via {promo_via})"
                    
    return path_to_key
