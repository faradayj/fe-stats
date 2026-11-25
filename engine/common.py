import json
import os

STATS = ["HP", "Str", "Mag", "Skl", "Spd", "Lck", "Def", "Res"]
STATS_FE5 = ["HP", "Str", "Mag", "Skl", "Spd", "Lck", "Def", "Bld", "Mov"]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_JS_DATA = os.path.join(BASE_DIR, "average_stats_data.js")


def load_db(game):
    """Load data/<game>.json; "A -> B" promotion-gain keys become (A, B) tuples."""
    with open(os.path.join(BASE_DIR, "data", f"{game}.json"), encoding="utf-8") as f:
        db = json.load(f)
    gains = db["classes"]["promo_gains"]
    db["classes"]["promo_gains"] = {tuple(k.split(" -> ")) if " -> " in k else k: v for k, v in gains.items()}
    return db


def suffix(is_female):
    return " (F)" if is_female else " (M)"


def tier(cls, special, promoted):
    """Badge and filter group of a class: "special", "promo" or "" (unpromoted)."""
    return "special" if cls in special else "promo" if cls in promoted else ""


def promote_path(char, target, is_promoted):
    """(path, pre_promoted) for games with one promotion: train the default class to 20, then promote."""
    base = char["default_class"]
    if is_promoted(target) and not is_promoted(base):
        return [base, target], False
    return [target], is_promoted(target)


def final_level(join_lv, maxes, pre_promoted=False):
    if len(maxes) > 1:
        return "/".join(map(str, maxes))
    return f"{join_lv} -> {maxes[0]}" if pre_promoted else str(maxes[0])


def stages(path, join_lv, maxes, growths, caps, gains):
    """One [cls, label_prefix, first_lv, last_lv, growths, caps, gains] per class in `path`.

    growths(cls) and caps(cls) return {stat: value}. gains(prev, cls) returns the promotion
    gains, or None for no gains. Class i is trained to level maxes[i].
    """
    out, prefix = [], ""
    for i, (cls, last) in enumerate(zip(path, maxes)):
        out.append([cls, prefix, 1 if i else join_lv, last, growths(cls), caps(cls), gains(path[i - 1], cls) if i else None])
        prefix += f"{last}/"
    return out


def simulate(names, bases, stage_list, level):
    """Average stats along a class path, in exact hundredths of a point (all game data is integer).

    Each segment is [cls, label_prefix, first_lv, rows, start, growths, caps]: `start` is in
    hundredths, and each later row adds `growths` hundredths up to `caps` points.
    """
    stats = [max(0, bases[s]) * 100 for s in names]
    segs = []
    for cls, prefix, first, last, growths, caps, gains in stage_list:
        cap = [caps[s] * 100 for s in names]
        grow = [max(0, growths[s]) for s in names]
        gain = [gains[s] * 100 if gains else 0 for s in names]
        stats = [max(0, min(c, v + g)) for v, c, g in zip(stats, cap, gain)]
        rows = max(1, last - first + 1)
        segs.append([cls, prefix, first, rows, stats, grow, [caps[s] for s in names]])
        for _ in range(rows - 1):
            stats = [min(c, v + g) for v, c, g in zip(stats, cap, grow)]
    return {
        "class_path": " -> ".join(stage[0] for stage in stage_list),
        "final_level": level,
        "stats": {s: v / 100 for s, v in zip(names, stats)},
        "segs": segs,
    }
