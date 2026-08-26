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
    import json, os
    from engine.common import BASE_DIR
    with open(os.path.join(BASE_DIR, 'data', 'fe5.json'), 'r', encoding='utf-8') as f:
        db = json.load(f)
    if 'classes' in db and 'promo_gains' in db['classes']:
        pg = db['classes']['promo_gains']
        db['classes']['promo_gains'] = {tuple(k.split(' -> ')) if ' -> ' in k else k: v for k, v in pg.items()}
    return db
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
