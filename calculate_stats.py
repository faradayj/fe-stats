"""Regenerate average_stats_data.js from data/*.json. Run: python calculate_stats.py"""
import json

from engine import GAMES
from engine.common import OUTPUT_JS_DATA, load_db


def calculate_game(game, db):
    """Everything the page shows for one game: each character in every class they can reach."""
    rules = GAMES[game]
    results = {}
    for name, char in sorted(db["characters"].items()):
        classes = {}
        for key in rules.classes(char):
            classes[key] = calc = rules.calculate(char, key, db)
            calc["tier"] = rules.tier(calc["segs"][-1][0])
        results[name] = {
            "name": name,
            "join_lv": char["join_lv"],
            "default_class": char["default_class"],
            "is_female": char["is_female"],
            "absolute_bases": {s: char["absolute_bases"][s] for s in rules.NAMES},
            "base_growths": {s: char["base_growths"][s] for s in rules.NAMES},
            "special": char["default_class"] in rules.SPECIAL_CLASSES,
            "direct": rules.direct(char),
            "classes": classes,
        }
    return results


def main():
    data = {
        game: {
            "stats": rules.NAMES,
            "rank_all_classes": getattr(rules, "RANK_ALL_CLASSES", False),
            "characters": calculate_game(game, load_db(game)),
        }
        for game, rules in GAMES.items()
    }
    with open(OUTPUT_JS_DATA, "w", encoding="utf-8") as f:
        f.write("const AVERAGE_STATS_DATA = ")
        json.dump(data, f, separators=(",", ":"))
        f.write(";\n")
    print(f"Saved {OUTPUT_JS_DATA}: " + ", ".join(f"{g.upper()} {len(d['characters'])} units" for g, d in data.items()))


if __name__ == "__main__":
    main()
