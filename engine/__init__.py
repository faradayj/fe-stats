from engine.common import STATS, BASE_DIR, CACHE_DIR, OUTPUT_REPORT, OUTPUT_JSON, OUTPUT_JS_DATA
from engine.fe5 import (
    load_fe5_data,
    calculate_fe5_avg_stats,
    get_valid_classes_for_fe5_character,
    get_fe5_direct_promotion_class
)
from engine.fe6 import (
    load_fe6_data,
    calculate_fe6_avg_stats,
    get_valid_classes_for_fe6_character,
    get_fe6_direct_promotion_class
)
from engine.fe7 import (
    load_fe7_data,
    calculate_fe7_avg_stats,
    get_valid_classes_for_fe7_character,
    get_fe7_direct_promotion_class
)
from engine.fe8 import (
    load_fe8_data,
    calculate_fe8_avg_stats,
    get_fe8_class_keys,
    get_fe8_direct_promotion_class
)
from engine.fe9 import (
    load_fe9_data,
    calculate_fe9_avg_stats,
    get_valid_classes_for_fe9_character,
    get_fe9_direct_promotion_class
)
from engine.fe10 import (
    load_fe10_data,
    calculate_fe10_avg_stats,
    get_valid_classes_for_fe10_character,
    get_fe10_direct_promotion_class
)
from engine.fe11 import (
    load_fe11_data,
    calculate_fe11_avg_stats,
    get_valid_classes_for_fe11_character,
    get_fe11_direct_promotion_class
)
from engine.fe12 import (
    load_fe12_data,
    calculate_fe12_avg_stats,
    get_valid_classes_for_character,
    get_direct_promotion_class
)
from engine.report import generate_report

__all__ = [
    "STATS", "BASE_DIR", "CACHE_DIR", "OUTPUT_REPORT", "OUTPUT_JSON", "OUTPUT_JS_DATA",
    "load_fe5_data", "calculate_fe5_avg_stats", "get_valid_classes_for_fe5_character", "get_fe5_direct_promotion_class",
    "load_fe6_data", "calculate_fe6_avg_stats", "get_valid_classes_for_fe6_character", "get_fe6_direct_promotion_class",
    "load_fe7_data", "calculate_fe7_avg_stats", "get_valid_classes_for_fe7_character", "get_fe7_direct_promotion_class",
    "load_fe8_data", "calculate_fe8_avg_stats", "get_fe8_class_keys", "get_fe8_direct_promotion_class",
    "load_fe9_data", "calculate_fe9_avg_stats", "get_valid_classes_for_fe9_character", "get_fe9_direct_promotion_class",
    "load_fe10_data", "calculate_fe10_avg_stats", "get_valid_classes_for_fe10_character", "get_fe10_direct_promotion_class",
    "load_fe11_data", "calculate_fe11_avg_stats", "get_valid_classes_for_fe11_character", "get_fe11_direct_promotion_class",
    "load_fe12_data", "calculate_fe12_avg_stats", "get_valid_classes_for_character", "get_direct_promotion_class",
    "generate_report",
    
    # High-level unified API
    "load_game_data",
    "calculate_avg_stats",
    "get_valid_classes",
    "get_direct_promo_class"
]

def load_game_data(game_key):
    """Loads database for a given game ('fe5', 'fe6', 'fe7', 'fe8', 'fe9', 'fe10', 'fe11', 'fe12')."""
    if game_key == "fe5":
        return load_fe5_data()
    elif game_key == "fe6":
        return load_fe6_data()
    elif game_key == "fe7":
        return load_fe7_data()
    elif game_key == "fe8":
        return load_fe8_data()
    elif game_key == "fe9":
        return load_fe9_data()
    elif game_key == "fe10":
        return load_fe10_data()
    elif game_key == "fe11":
        return load_fe11_data()
    elif game_key == "fe12":
        return load_fe12_data()
    raise ValueError(f"Unknown game: {game_key}")

def calculate_avg_stats(game_key, char_data, cls_or_path, db):
    """Calculates average stats for a character in a specific target class or path."""
    if game_key == "fe5":
        return calculate_fe5_avg_stats(char_data, cls_or_path, db)
    elif game_key == "fe6":
        return calculate_fe6_avg_stats(char_data, cls_or_path, db)
    elif game_key == "fe7":
        return calculate_fe7_avg_stats(char_data, cls_or_path, db)
    elif game_key == "fe8":
        return calculate_fe8_avg_stats(char_data, cls_or_path, db)
    elif game_key == "fe9":
        return calculate_fe9_avg_stats(char_data, cls_or_path, db)
    elif game_key == "fe10":
        return calculate_fe10_avg_stats(char_data, cls_or_path, db)
    elif game_key == "fe11":
        return calculate_fe11_avg_stats(char_data, cls_or_path, db)
    elif game_key == "fe12":
        return calculate_fe12_avg_stats(char_data, cls_or_path, db)
    raise ValueError(f"Unknown game: {game_key}")

def get_valid_classes(game_key, char_name, char_data):
    """Returns the list of valid class options for a character."""
    if game_key == "fe5":
        return get_valid_classes_for_fe5_character(char_name, char_data)
    elif game_key == "fe6":
        return get_valid_classes_for_fe6_character(char_data)
    elif game_key == "fe7":
        return get_valid_classes_for_fe7_character(char_data)
    elif game_key == "fe8":
        path_to_key = get_fe8_class_keys(char_name, char_data)
        return list(path_to_key.values())
    elif game_key == "fe9":
        return get_valid_classes_for_fe9_character(char_data)
    elif game_key == "fe10":
        return get_valid_classes_for_fe10_character(char_data)
    elif game_key == "fe11":
        return get_valid_classes_for_fe11_character(char_data)
    elif game_key == "fe12":
        return get_valid_classes_for_character(char_data)
    raise ValueError(f"Unknown game: {game_key}")

def get_direct_promo_class(game_key, char_name, char_data):
    """Returns the default/direct promotion class for a character in a given game."""
    if game_key == "fe5":
        return get_fe5_direct_promotion_class(char_name, char_data)
    elif game_key == "fe6":
        return get_fe6_direct_promotion_class(char_name, char_data)
    elif game_key == "fe7":
        return get_fe7_direct_promotion_class(char_name, char_data)
    elif game_key == "fe8":
        return get_fe8_direct_promotion_class(char_name, char_data)
    elif game_key == "fe9":
        return get_fe9_direct_promotion_class(char_name, char_data)
    elif game_key == "fe10":
        return get_fe10_direct_promotion_class(char_name, char_data)
    elif game_key == "fe11":
        return get_fe11_direct_promotion_class(char_name, char_data)
    elif game_key == "fe12":
        return get_direct_promotion_class(char_name, char_data)
    raise ValueError(f"Unknown game: {game_key}")

