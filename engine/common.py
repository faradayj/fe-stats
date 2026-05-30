import os

# --- Shared Constants ---
STATS = ["HP", "Str", "Mag", "Skl", "Spd", "Lck", "Def", "Res"]

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
OUTPUT_REPORT = os.path.join(BASE_DIR, "average_stats_report.txt")
OUTPUT_JSON = os.path.join(BASE_DIR, "average_stats.json")
OUTPUT_JS_DATA = os.path.join(BASE_DIR, "average_stats_data.js")
