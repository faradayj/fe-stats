import os
from engine.common import STATS
from engine.parser import parse_html_tables, clean_value, parse_int, fetch_page

# --- FE10 Configurations & Constants ---
URLS_FE10 = {
    "fe10_bases": "https://serenesforest.net/radiant-dawn/characters/base-stats/",
    "fe10_growths": "https://serenesforest.net/radiant-dawn/characters/growth-rates/",
    "fe10_caps": "https://serenesforest.net/radiant-dawn/classes/maximum-stats/",
    "fe10_promotions": "https://serenesforest.net/radiant-dawn/classes/promotion-gains/"
}

FE10_FEMALE_CHARACTERS = {
    "Micaiah", "Laura", "Ilyana", "Meg", "Jill", "Fiona", "Vika", "Nailah",
    "Elincia", "Marcia", "Leanne", "Nephenee", "Heather", "Lucia", "Lethe",
    "Astrid", "Titania", "Mist", "Lyre", "Sigrun", "Tanith", "Sanaki", "Ena",
    "Mia", "Calill"
}

FE10_LAGUZ_CLASSES = {
    "Wolf", "Wolf Queen", "Cat", "Lion", "Lion King", "Tiger", "Hawk", "Hawk King", 
    "Raven", "Raven King", "Heron", "Red Dragon", "White Dragon", "Dragon Prince", "Dragon King"
}

FE10_PROMOTION_MAP = {
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

def is_fe10_promoted(cls_name):
    # This is a helper for general routing, but we will use the tier system instead
    return get_fe10_class_tier(cls_name) > 1

def get_fe10_class_tier(cls_name):
    tier1_classes = {
        "Light Mage", "Myrmidon", "Archer", "Fighter", "Priest", 
        "Thunder Mage", "Soldier", "Armor Sword", "Dracoknight", "Lance Knight"
    }
    if cls_name in tier1_classes:
        return 1
        
    tier2_classes = {
        "Light Sage", "Swordmaster", "Sniper", "Warrior", "Bishop", 
        "Thunder Sage", "Halberdier", "Sword General", "Lance General", "Axe General",
        "Dragonmaster", "Lance Paladin", "Axe Paladin", "Bow Paladin", "Blade Paladin",
        "Rogue", "Hero", "Wind Sage", "Fire Sage", "Dark Sage", "Cleric"
    }
    if cls_name in tier2_classes:
        return 2
        
    return 3

def get_fe10_caps_key(cls_name, is_female, char_name=""):
    if cls_name == "Arch Sage":
        if char_name in ("Ilyana",):
            return "Arch Sage (Thunder, F)"
        elif char_name in ("Calill",):
            return "Arch Sage (Fire, F)"
        elif char_name in ("Tormod", "Bastian"):
            if char_name == "Tormod" or char_name == "Bastian":
                return "Arch Sage (Fire, M)"
            return "Arch Sage (Wind)"
        elif char_name in ("Soren",):
            return "Arch Sage (Wind)"
        elif char_name == "Pelleas":
            return "Arch Sage (Dark)"
        return "Arch Sage (Wind)"
        
    if cls_name == "Marshall":
        if char_name == "Meg":
            return "Marshall (Sword, F)"
        elif char_name in ("Brom",):
            return "Marshall (Axe)"
        elif char_name in ("Tauroneo", "Gatrie"):
            return "Marshall (Lance)"
        return "Marshall (Lance)"
        
    if cls_name == "Gold Knight":
        if char_name in ("Kieran", "Titania"):
            return "Gold Knight (Axe, F)" if is_female else "Gold Knight (Axe, M)"
        # Makalov/Renning
        return "Gold Knight (Sword)"
        
    if cls_name == "Silver Knight":
        if char_name == "Astrid":
            return "Silver Knight (Bow, F)"
        # Fiona/Oscar/Geoffrey
        return f"Silver Knight (Lance, F)" if is_female else f"Silver Knight (Lance, M)"
        
    # Standard gender routing
    gendered_classes = {
        "Rogue", "Whisper", "Swordmaster", "Trueblade", "Halberdier", "Sentinel",
        "Priest", "Bishop", "Saint", "Armor Sword", "Sword General", "Dracoknight",
        "Dragonmaster", "Dragonlord", "Lance Knight", "Lance Paladin", "Axe Paladin",
        "Bow Paladin", "Thunder Mage", "Thunder Sage", "Fire Sage",
    }
    
    if cls_name in gendered_classes:
        return f"{cls_name} (F)" if is_female else f"{cls_name} (M)"
        
    # Laguz unique classes
    if cls_name == "Cat":
        return f"Cat (F)" if is_female else f"Cat (M)"
    if cls_name == "Raven":
        return f"Raven (F)" if is_female else f"Raven (M)"
    if cls_name == "Lion":
        if char_name == "Skrimir":
            return "Lion (Skrimir)"
        if char_name == "Giffca":
            return "Lion (Giffca)"
        return "Lion King"
    if cls_name == "Heron":
        if char_name == "Rafiel":
            return "Heron (Rafiel)"
        if char_name == "Reyson":
            return "Heron (Reyson)"
        return "Heron (Leanne)"
    if cls_name == "Red Dragon":
        return f"Red Dragon (F)" if is_female else f"Red Dragon (M)"
        
    return cls_name

def get_fe10_class_type(cls_name, is_female, char_name=""):
    is_magical = cls_name in (
        "Light Sage", "Wind Sage", "Fire Sage", "Thunder Sage", "Dark Sage",
        "Bishop", "Cleric"
    )
    if is_magical:
        return "Female Magical" if is_female else "Male Magical"
    else:
        return "Female Physical" if is_female else "Male Physical"

def get_fe10_promo_gains(base_cls, promo_cls, is_female, promo_gains_db):
    suffix = "(female)" if is_female else "(male)"
    key_gender = (f"{base_cls} {suffix}", f"{promo_cls} {suffix}")
    if key_gender in promo_gains_db:
        return promo_gains_db[key_gender]
    key_plain = (base_cls, promo_cls)
    if key_plain in promo_gains_db:
        return promo_gains_db[key_plain]
    for (b, p), gains in promo_gains_db.items():
        if base_cls in b and promo_cls in p:
            return gains
    return {s: 0 for s in STATS}

def get_valid_classes_for_fe10_character(char_data):
    base_cls = char_data["default_class"]
    if base_cls in FE10_LAGUZ_CLASSES:
        return [base_cls]
        
    tier = get_fe10_class_tier(base_cls)
    classes = [base_cls]
    
    current = base_cls
    while current in FE10_PROMOTION_MAP:
        promoted = FE10_PROMOTION_MAP[current]
        classes.append(promoted)
        current = promoted
        
    return classes

def get_fe10_direct_promotion_class(char_name, char_data):
    base_cls = char_data["default_class"]
    if base_cls in FE10_LAGUZ_CLASSES:
        return base_cls
    promoted = FE10_PROMOTION_MAP.get(base_cls, base_cls)
    # If starting class is Tier 1, go directly to Tier 3 for direct promo comparison!
    if get_fe10_class_tier(base_cls) == 1:
        tier2 = promoted
        tier3 = FE10_PROMOTION_MAP.get(tier2, tier2)
        return tier3
    return promoted

def load_fe10_data():
    raw = {
        name: fetch_page(name, URLS_FE10[name])
        for name in ["fe10_bases", "fe10_growths", "fe10_caps", "fe10_promotions"]
    }

    # 1. Parse Class Caps
    class_caps = {}
    tables = parse_html_tables(raw["fe10_caps"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                cls_name = clean_value(row[0]).strip()
                if not cls_name or cls_name == "Class":
                    continue
                
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

    # 2. Parse Promotion Gains
    promo_gains = {}
    tables = parse_html_tables(raw["fe10_promotions"])
    # We only parse the first table which has stat gains
    table = tables[0]
    if len(table) > 1 and "HP" in table[0] and "Promotion" in table[0]:
        headers = [clean_value(h) for h in table[0]]
        for row in table[1:]:
            if len(row) < len(headers):
                continue
            base_cls = clean_value(row[0]).strip()
            promo_cls = clean_value(row[1]).strip()
            if not base_cls or base_cls == "Class" or base_cls == "Base Class":
                continue
            
            gains = {
                "HP": parse_int(row[headers.index("HP")]),
                "Str": parse_int(row[headers.index("Str")]),
                "Mag": parse_int(row[headers.index("Mag")]),
                "Skl": parse_int(row[headers.index("Skl")]),
                "Spd": parse_int(row[headers.index("Spd")]),
                "Lck": 0,
                "Def": parse_int(row[headers.index("Def")]),
                "Res": parse_int(row[headers.index("Res")]),
            }
            
            # Map standard categories
            if "Male Physical" in base_cls:
                promo_gains["Male Physical"] = gains
            elif "Female Physical" in base_cls:
                promo_gains["Female Physical"] = gains
            elif "Male Magical" in base_cls:
                promo_gains["Male Magical"] = gains
            elif "Female Magical" in base_cls:
                promo_gains["Female Magical"] = gains
            else:
                # Specific class specific promotion
                # Clean class names
                b_clean = base_cls.replace("(male)", "").replace("(female)", "").strip()
                p_clean = promo_cls.replace("(male)", "").replace("(female)", "").strip()
                promo_gains[(b_clean, p_clean)] = gains

    # 3. Parse Character Bases
    characters = {}
    tables = parse_html_tables(raw["fe10_bases"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "Lv" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0]).replace("*", "").strip()
                if not name or name == "Name":
                    continue
                
                cls_name = clean_value(row[headers.index("Class")]).replace("*", "").strip()
                is_female = name in FE10_FEMALE_CHARACTERS
                
                characters[name] = {
                    "name": name,
                    "join_lv": parse_int(row[headers.index("Lv")]),
                    "default_class": cls_name,
                    "is_female": is_female,
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

    # 4. Parse Character Growths
    tables = parse_html_tables(raw["fe10_growths"])
    growths = {}
    for table in tables:
        if len(table) > 1 and "HP" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            lck_header = "Lck" if "Lck" in headers else "Luck"
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0]).replace("*", "").strip()
                if not name or name == "Name":
                    continue
                
                growths[name] = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": parse_int(row[headers.index("Str")]),
                    "Mag": parse_int(row[headers.index("Mag")]),
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index(lck_header)]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Res": parse_int(row[headers.index("Res")]),
                }

    for name in list(characters.keys()):
        if name in growths:
            characters[name]["growths"] = growths[name]
            characters[name]["absolute_bases"] = characters[name]["bases"]
            characters[name]["base_growths"] = characters[name]["growths"]
        else:
            del characters[name]
            
    return {
        "characters": characters,
        "classes": {
            "caps": class_caps,
            "promo_gains": promo_gains
        }
    }

def calculate_fe10_avg_stats(char_data, target_class, db):
    is_female = char_data["is_female"]
    join_lv = char_data["join_lv"]
    abs_bases = char_data["absolute_bases"]
    base_growths = char_data["base_growths"]
    char_name = char_data["name"]
    base_class = char_data["default_class"]
    
    caps_db = db["classes"]["caps"]
    promo_gains_db = db["classes"]["promo_gains"]

    current_stats = {s: float(max(0, abs_bases[s])) for s in STATS}
    history = []

    # Laguz units routing
    if base_class in FE10_LAGUZ_CLASSES:
        history.append((join_lv, base_class, current_stats.copy()))
        caps_key = get_fe10_caps_key(base_class, is_female, char_name)
        cls_caps = caps_db.get(caps_key, {s: 40 for s in STATS})
        
        for lv in range(join_lv + 1, 41):
            for s in STATS:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(cls_caps[s]), current_stats[s])
            history.append((lv, base_class, current_stats.copy()))
            
        return {
            "class_path": base_class,
            "final_class": base_class,
            "final_level": "40",
            "stats": current_stats,
            "history": history
        }

    # Beorc multi-tier simulation
    char_start_tier = get_fe10_class_tier(base_class)
    target_tier = get_fe10_class_tier(target_class)

    # Validate that target class is reachable from base class
    valid_classes = get_valid_classes_for_fe10_character(char_data)
    if target_class not in valid_classes:
        raise ValueError(f"{target_class} is not a valid class for {char_name} (starts as {base_class})")

    # Trace classes in the promotion chain dynamically based on starting tier
    class_t1 = None
    class_t2 = None
    class_t3 = None
    
    valid_classes = get_valid_classes_for_fe10_character(char_data)
    if char_start_tier == 1:
        class_t1 = valid_classes[0]
        if len(valid_classes) > 1:
            class_t2 = valid_classes[1]
        if len(valid_classes) > 2:
            class_t3 = valid_classes[2]
    elif char_start_tier == 2:
        class_t2 = valid_classes[0]
        if len(valid_classes) > 1:
            class_t3 = valid_classes[1]
    elif char_start_tier == 3:
        class_t3 = valid_classes[0]

    # LEVELING ENGINE
    if target_tier == 1:
        # Just Tier 1 from join_lv to 20
        history.append((join_lv, class_t1, current_stats.copy()))
        t1_caps_key = get_fe10_caps_key(class_t1, is_female, char_name)
        t1_caps = caps_db.get(t1_caps_key, {s: 20 for s in STATS})
        
        for lv in range(join_lv + 1, 21):
            for s in STATS:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(t1_caps[s]), current_stats[s])
            history.append((lv, class_t1, current_stats.copy()))
            
        return {
            "class_path": class_t1,
            "final_class": class_t1,
            "final_level": "20",
            "stats": current_stats,
            "history": history
        }

    elif target_tier == 2:
        if char_start_tier == 1:
            # Level class_t1 from join_lv to 20
            history.append((join_lv, class_t1, current_stats.copy()))
            t1_caps_key = get_fe10_caps_key(class_t1, is_female, char_name)
            t1_caps = caps_db.get(t1_caps_key, {s: 20 for s in STATS})
            
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t1_caps[s]), current_stats[s])
                history.append((lv, class_t1, current_stats.copy()))
                
            # Promote class_t1 -> class_t2
            gains = get_fe10_promo_gains(class_t1, class_t2, is_female, promo_gains_db)
            t2_caps_key = get_fe10_caps_key(class_t2, is_female, char_name)
            t2_caps = caps_db.get(t2_caps_key, {s: 30 for s in STATS})
            for s in STATS:
                current_stats[s] += gains[s]
                current_stats[s] = min(float(t2_caps[s]), current_stats[s])
            history.append(("20/1", class_t2, current_stats.copy()))
            
            # Level class_t2 from 2 to 20
            for lv in range(2, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t2_caps[s]), current_stats[s])
                history.append((f"20/{lv}", class_t2, current_stats.copy()))
                
            return {
                "class_path": f"{class_t1} -> {class_t2}",
                "final_class": class_t2,
                "final_level": "20/20",
                "stats": current_stats,
                "history": history
            }
        else:
            # Starts as Tier 2, just level class_t2 from join_lv to 20
            history.append((join_lv, class_t2, current_stats.copy()))
            t2_caps_key = get_fe10_caps_key(class_t2, is_female, char_name)
            t2_caps = caps_db.get(t2_caps_key, {s: 30 for s in STATS})
            
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t2_caps[s]), current_stats[s])
                history.append((lv, class_t2, current_stats.copy()))
                
            return {
                "class_path": class_t2,
                "final_class": class_t2,
                "final_level": "20",
                "stats": current_stats,
                "history": history
            }

    elif target_tier == 3:
        if char_start_tier == 1:
            # 1. Level class_t1 from join_lv to 20
            history.append((join_lv, class_t1, current_stats.copy()))
            t1_caps_key = get_fe10_caps_key(class_t1, is_female, char_name)
            t1_caps = caps_db.get(t1_caps_key, {s: 20 for s in STATS})
            
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t1_caps[s]), current_stats[s])
                history.append((lv, class_t1, current_stats.copy()))
                
            # 2. Promote class_t1 -> class_t2
            gains12 = get_fe10_promo_gains(class_t1, class_t2, is_female, promo_gains_db)
            t2_caps_key = get_fe10_caps_key(class_t2, is_female, char_name)
            t2_caps = caps_db.get(t2_caps_key, {s: 30 for s in STATS})
            for s in STATS:
                current_stats[s] += gains12[s]
                current_stats[s] = min(float(t2_caps[s]), current_stats[s])
            history.append(("20/1", class_t2, current_stats.copy()))
            
            # 3. Level class_t2 from 2 to 20
            for lv in range(2, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t2_caps[s]), current_stats[s])
                history.append((f"20/{lv}", class_t2, current_stats.copy()))
                
            # 4. Promote class_t2 -> class_t3 (Standard Tier 2 -> 3 Gains)
            class_type = get_fe10_class_type(class_t2, is_female, char_name)
            gains23 = promo_gains_db.get(class_type, {s: 0 for s in STATS})
            t3_caps_key = get_fe10_caps_key(class_t3, is_female, char_name)
            t3_caps = caps_db.get(t3_caps_key, {s: 40 for s in STATS})
            for s in STATS:
                current_stats[s] += gains23[s]
                current_stats[s] = min(float(t3_caps[s]), current_stats[s])
            history.append(("20/20/1", class_t3, current_stats.copy()))
            
            # 5. Level class_t3 from 2 to 20
            for lv in range(2, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t3_caps[s]), current_stats[s])
                history.append((f"20/20/{lv}", class_t3, current_stats.copy()))
                
            return {
                "class_path": f"{class_t1} -> {class_t2} -> {class_t3}",
                "final_class": class_t3,
                "final_level": "20/20/20",
                "stats": current_stats,
                "history": history
            }
            
        elif char_start_tier == 2:
            # 1. Level class_t2 from join_lv to 20
            history.append((join_lv, class_t2, current_stats.copy()))
            t2_caps_key = get_fe10_caps_key(class_t2, is_female, char_name)
            t2_caps = caps_db.get(t2_caps_key, {s: 30 for s in STATS})
            
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t2_caps[s]), current_stats[s])
                history.append((lv, class_t2, current_stats.copy()))
                
            # 2. Promote class_t2 -> class_t3
            class_type = get_fe10_class_type(class_t2, is_female, char_name)
            gains23 = promo_gains_db.get(class_type, {s: 0 for s in STATS})
            t3_caps_key = get_fe10_caps_key(class_t3, is_female, char_name)
            t3_caps = caps_db.get(t3_caps_key, {s: 40 for s in STATS})
            for s in STATS:
                current_stats[s] += gains23[s]
                current_stats[s] = min(float(t3_caps[s]), current_stats[s])
            history.append(("20/1", class_t3, current_stats.copy()))
            
            # 3. Level class_t3 from 2 to 20
            for lv in range(2, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t3_caps[s]), current_stats[s])
                history.append((f"20/{lv}", class_t3, current_stats.copy()))
                
            return {
                "class_path": f"{class_t2} -> {class_t3}",
                "final_class": class_t3,
                "final_level": "20/20",
                "stats": current_stats,
                "history": history
            }
            
        else:
            # Starts as Tier 3, just level class_t3 from join_lv to 20
            history.append((join_lv, class_t3, current_stats.copy()))
            t3_caps_key = get_fe10_caps_key(class_t3, is_female, char_name)
            t3_caps = caps_db.get(t3_caps_key, {s: 40 for s in STATS})
            
            for lv in range(join_lv + 1, 21):
                for s in STATS:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(t3_caps[s]), current_stats[s])
                history.append((lv, class_t3, current_stats.copy()))
                
            return {
                "class_path": class_t3,
                "final_class": class_t3,
                "final_level": "20",
                "stats": current_stats,
                "history": history
            }

    raise ValueError(f"Could not calculate stats for class tier target: {target_class}")
