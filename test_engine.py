"""Regression check: the engine must reproduce tests/snapshot.json. Run: python test_engine.py"""
import json
import os

from calculate_stats import calculate_game
from engine import GAMES
from engine.common import load_db

SNAPSHOT = os.path.join(os.path.dirname(__file__), "tests", "snapshot.json")
# Characters whose default promotion is not a class they can end in
NO_DIRECT = {("fe12", "Sheema")}  # joins as a General, which the female class pool does not contain


def diff(want, got, path):
    """Yield every place where `want` is not contained in `got` (extra keys in `got` are fine)."""
    if isinstance(want, dict):
        for key, value in want.items():
            if not isinstance(got, dict) or key not in got:
                yield f"{path}/{key}: missing"
            else:
                yield from diff(value, got[key], f"{path}/{key}")
    elif want != got:
        yield f"{path}: want {want!r}, got {got!r}"


def replay(segs):
    """Final stats from the exported segments, the way app.js replays them."""
    for _cls, _prefix, _first, rows, start, growths, caps in segs:
        stats = start
        for _ in range(rows - 1):
            stats = [min(c * 100, v + g) for v, g, c in zip(stats, growths, caps)]
    return [v / 100 for v in stats]


def check_exports(game, db):
    """The direct promotion must be a real class key, and segments must replay to the final stats."""
    rules = GAMES[game]
    for name, char in db["characters"].items():
        keys = rules.classes(char)
        if "My Unit" not in name and (game, name) not in NO_DIRECT and rules.direct(char) not in keys:
            yield f"{game}/{name}: direct class {rules.direct(char)!r} is not one of {keys}"
        for key in keys:
            calc = rules.calculate(char, key, db)
            if replay(calc["segs"]) != list(calc["stats"].values()):
                yield f"{game}/{name}/{key}: segments do not replay to the final stats"


def main():
    with open(SNAPSHOT, encoding="utf-8") as f:
        snapshot = json.load(f)
    problems = []
    for game, want in snapshot.items():
        db = load_db(game)
        problems += diff(want, calculate_game(game, db), game)
        problems += check_exports(game, db)
    for line in problems[:40]:
        print(line)
    assert not problems, f"{len(problems)} differences from snapshot"
    print("OK: engine matches snapshot")


if __name__ == "__main__":
    main()
