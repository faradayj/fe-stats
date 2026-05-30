import os
from engine.parser import parse_html_tables, clean_value, parse_int, fetch_page

# --- FE5 Configurations & Constants ---
URLS_FE5 = {
    "fe5_bases": "https://serenesforest.net/thracia-776/characters/base-stats/",
    "fe5_growths": "https://serenesforest.net/thracia-776/characters/growth-rates/",
    "fe5_promotions": "https://serenesforest.net/thracia-776/classes/promotion-gains/"
}

STATS_FE5 = ["HP", "Str", "Mag", "Skl", "Spd", "Lck", "Def", "Bld", "Mov"]

FE5_PROMOTED_CLASSES = {
    "Prince", "Paladin", "Forrest Knight", "Duke Knight", "Great Knight", 
    "General", "Mercenary", "Swordmaster", "Sniper", "Bow Knight", 
    "Warrior", "Pegasus Knight", "Dragon Knight", "High Priest", "Sage", 
    "Mage Knight", "Dark Mage", "Thief Fighter", "Dancer"
}

FE5_PROMOTION_MAP = {
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

def get_fe5_direct_promotion_class(char_name, char_data):
    if char_name == "Machua":
        return "Mercenary"
    if char_name == "Miranda":
        return "Mage Knight"
    base_class = char_data["default_class"]
    return FE5_PROMOTION_MAP.get(base_class, base_class)

def get_valid_classes_for_fe5_character(char_name, char_data):
    base_cls = char_data["default_class"]
    if char_name == "Lara":
        return ["Thief", "Thief Fighter", "Dancer", "Thief Fighter (via Dancer)"]
    if base_cls in FE5_PROMOTED_CLASSES:
        return [base_cls]
    promoted_cls = get_fe5_direct_promotion_class(char_name, char_data)
    if not promoted_cls or promoted_cls == base_cls:
        return [base_cls]
    return [base_cls, promoted_cls]

def load_fe5_data():
    raw = {
        name: fetch_page(name, URLS_FE5[name])
        for name in ["fe5_bases", "fe5_growths", "fe5_promotions"]
    }

    # 1. Parse Promotion Gains
    promo_gains = {}
    tables = parse_html_tables(raw["fe5_promotions"])
    for table in tables:
        if len(table) > 1 and "Str" in table[0] and "Mag" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                base_cls = clean_value(row[0])
                promo_cls = clean_value(row[1])
                if not base_cls or base_cls == "Class" or base_cls == "Base Class":
                    continue
                
                # Column mappings
                str_val = parse_int(row[headers.index("Str")])
                mag_val = parse_int(row[headers.index("Mag")])
                skl_val = parse_int(row[headers.index("Skl")])
                spd_val = parse_int(row[headers.index("Spd")])
                def_val = parse_int(row[headers.index("Def")])
                bld_val = parse_int(row[headers.index("Con")]) if "Con" in headers else 0
                mov_val = parse_int(row[headers.index("Mov")]) if "Mov" in headers else 0
                
                key = (base_cls, promo_cls)
                promo_gains[key] = {
                    "HP": 0,
                    "Str": str_val,
                    "Mag": mag_val,
                    "Skl": skl_val,
                    "Spd": spd_val,
                    "Lck": 0,
                    "Def": def_val,
                    "Bld": bld_val,
                    "Mov": mov_val,
                }

    # 2. Parse Character Bases
    characters = {}
    tables = parse_html_tables(raw["fe5_bases"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "Lv" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[headers.index("Name")])
                if not name or name == "Name":
                    continue
                
                cls_name = clean_value(row[headers.index("Class")])
                
                characters[name] = {
                    "name": name,
                    "join_lv": parse_int(row[headers.index("Lv")]),
                    "default_class": cls_name,
                    "is_female": name in {"Evayle", "Tania", "Lara", "Karin", "Nanna", "Selphina", "Olwen", "Mareeta", "Tina", "Eda", "Linoan", "Sara", "Miranda", "Misha", "Amalda"},
                    "bases": {
                        "HP": parse_int(row[headers.index("HP")]),
                        "Str": parse_int(row[headers.index("Str")]),
                        "Mag": parse_int(row[headers.index("Mag")]),
                        "Skl": parse_int(row[headers.index("Skl")]),
                        "Spd": parse_int(row[headers.index("Spd")]),
                        "Lck": parse_int(row[headers.index("Lck")]),
                        "Def": parse_int(row[headers.index("Def")]),
                        "Bld": parse_int(row[headers.index("Bld")]),
                        "Mov": parse_int(row[headers.index("Mov")]),
                    }
                }

    # 3. Parse Character Growths
    tables = parse_html_tables(raw["fe5_growths"])
    for table in tables:
        if len(table) > 1 and "HP" in table[0] and "Str" in table[0]:
            headers = [clean_value(h) for h in table[0]]
            for row in table[1:]:
                if len(row) < len(headers):
                    continue
                name = clean_value(row[0])
                if not name or name == "Character" or name == "Name":
                    continue
                
                if name == "Leaf":
                    db_name = "Leaf"
                elif name == "Fin":
                    db_name = "Fin"
                elif name == "Othin":
                    db_name = "Othin"
                elif name == "Halvan":
                    db_name = "Halvan"
                else:
                    db_name = name
                
                # Match character in database
                matching = [c for c in characters if c.lower() == db_name.lower() or db_name.lower() in c.lower()]
                if not matching:
                    continue
                
                growths = {
                    "HP": parse_int(row[headers.index("HP")]),
                    "Str": parse_int(row[headers.index("Str")]),
                    "Mag": parse_int(row[headers.index("Mag")]),
                    "Skl": parse_int(row[headers.index("Skl")]),
                    "Spd": parse_int(row[headers.index("Spd")]),
                    "Lck": parse_int(row[headers.index("Lck")]),
                    "Def": parse_int(row[headers.index("Def")]),
                    "Bld": parse_int(row[headers.index("Bld")]),
                    "Mov": parse_int(row[headers.index("Mov")]),
                }
                
                for cname in matching:
                    characters[cname]["growths"] = growths

    # Unify into standard structure
    database = {"characters": {}, "classes": {"caps": {}, "promo_gains": promo_gains}}
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


# --- FE5 Stat Calculation Engine ---
def is_fe5_promoted(cls_name):
    return cls_name in FE5_PROMOTED_CLASSES

def calculate_fe5_avg_stats(char_data, target_class, db):
    char_name = char_data["name"]
    join_lv = char_data["join_lv"]
    abs_bases = char_data["absolute_bases"]
    base_growths = char_data["base_growths"]
    promo_gains_db = db["classes"]["promo_gains"]

    # Universal Caps: HP 80, others 20
    caps = {s: 80 if s == "HP" else 20 for s in STATS_FE5}

    current_stats = {}
    history = []

    # 1. Base Class Level Up
    for s in STATS_FE5:
        current_stats[s] = float(max(0, abs_bases[s]))

    base_class = char_data["default_class"]
    
    # Handle already promoted joiners
    if is_fe5_promoted(base_class):
        history.append((join_lv, base_class, current_stats.copy()))
        for lv in range(join_lv + 1, 21):
            for s in STATS_FE5:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(caps[s]), current_stats[s])
            history.append((lv, base_class, current_stats.copy()))
        return {
            "class_path": base_class,
            "final_class": base_class,
            "final_level": f"{join_lv} -> 20",
            "stats": current_stats,
            "history": history
        }

    # Standard progression
    if target_class == base_class:
        # No promotion, just level up base class to 20
        history.append((join_lv, base_class, current_stats.copy()))
        for lv in range(join_lv + 1, 21):
            for s in STATS_FE5:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(caps[s]), current_stats[s])
            history.append((lv, base_class, current_stats.copy()))
        return {
            "class_path": base_class,
            "final_class": base_class,
            "final_level": "20",
            "stats": current_stats,
            "history": history
        }

    # Handle Lara's special Dancer options
    if char_name == "Lara" and target_class == "Dancer":
        # Thief -> Dancer
        history.append((join_lv, "Thief", current_stats.copy()))
        for lv in range(join_lv + 1, 20):  # Assume reclass/promote at level 20 or 10. Let's do 20 to be consistent with others.
            for s in STATS_FE5:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(caps[s]), current_stats[s])
            history.append((lv, "Thief", current_stats.copy()))
        
        # Reclass to Dancer
        gains = promo_gains_db.get(("Thief", "Dancer"), {s: 0 for s in STATS_FE5})
        for s in STATS_FE5:
            current_stats[s] += gains[s]
            current_stats[s] = max(0.0, min(float(caps[s]), current_stats[s]))
        history.append(("Promotion", "Dancer", current_stats.copy()))

        # Level up Dancer 1 to 20
        for lv in range(1, 21):
            if lv > 1:
                for s in STATS_FE5:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(caps[s]), current_stats[s])
            history.append((f"20/{lv}", "Dancer", current_stats.copy()))
        return {
            "class_path": "Thief -> Dancer",
            "final_class": "Dancer",
            "final_level": "20/20",
            "stats": current_stats,
            "history": history
        }

    if char_name == "Lara" and target_class == "Thief Fighter (via Dancer)":
        # Thief -> Dancer -> Thief Fighter
        history.append((join_lv, "Thief", current_stats.copy()))
        for lv in range(join_lv + 1, 20):
            for s in STATS_FE5:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(caps[s]), current_stats[s])
            history.append((lv, "Thief", current_stats.copy()))

        # Reclass to Dancer
        gains1 = promo_gains_db.get(("Thief", "Dancer"), {s: 0 for s in STATS_FE5})
        for s in STATS_FE5:
            current_stats[s] += gains1[s]
            current_stats[s] = max(0.0, min(float(caps[s]), current_stats[s]))
        history.append(("Promotion", "Dancer", current_stats.copy()))

        # Level up Dancer from 1 to 20
        for lv in range(2, 21):
            for s in STATS_FE5:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(caps[s]), current_stats[s])
            history.append((f"20/{lv}", "Dancer", current_stats.copy()))

        # Promote Dancer -> Thief Fighter
        gains2 = promo_gains_db.get(("Dancer", "Thief Fighter"), {s: 0 for s in STATS_FE5})
        for s in STATS_FE5:
            current_stats[s] += gains2[s]
            current_stats[s] = max(0.0, min(float(caps[s]), current_stats[s]))
        history.append(("Promotion", "Thief Fighter", current_stats.copy()))

        # Level up Thief Fighter from 1 to 20
        for lv in range(1, 21):
            if lv > 1:
                for s in STATS_FE5:
                    growth_rate = max(0, base_growths[s])
                    current_stats[s] += growth_rate / 100.0
                    current_stats[s] = min(float(caps[s]), current_stats[s])
            history.append((f"20/20/{lv}", "Thief Fighter", current_stats.copy()))
        return {
            "class_path": "Thief -> Dancer -> Thief Fighter",
            "final_class": "Thief Fighter",
            "final_level": "20/20/20",
            "stats": current_stats,
            "history": history
        }

    # Standard single promotion (e.g. Lord -> Prince, Thief -> Thief Fighter)
    history.append((join_lv, base_class, current_stats.copy()))
    for lv in range(join_lv + 1, 21):
        for s in STATS_FE5:
            growth_rate = max(0, base_growths[s])
            current_stats[s] += growth_rate / 100.0
            current_stats[s] = min(float(caps[s]), current_stats[s])
        history.append((lv, base_class, current_stats.copy()))

    # Promotion gains
    gains = promo_gains_db.get((base_class, target_class), {s: 0 for s in STATS_FE5})
    for s in STATS_FE5:
        current_stats[s] += gains[s]
        current_stats[s] = min(float(caps[s]), current_stats[s])
    history.append(("Promotion", target_class, current_stats.copy()))

    # Promoted class level up
    for lv in range(1, 21):
        if lv > 1:
            for s in STATS_FE5:
                growth_rate = max(0, base_growths[s])
                current_stats[s] += growth_rate / 100.0
                current_stats[s] = min(float(caps[s]), current_stats[s])
        history.append((f"20/{lv}", target_class, current_stats.copy()))

    return {
        "class_path": f"{base_class} -> {target_class}",
        "final_class": target_class,
        "final_level": "20/20",
        "stats": current_stats,
        "history": history
    }
