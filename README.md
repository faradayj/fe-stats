# FE Average Stats

Average stats for Fire Emblem characters (FE5 to FE12) in every class they can reach, shown on a static page: reclass table, comparison chart, level-by-level simulator and a BST leaderboard per class.

## Layout

- `data/feN.json`: source data per game (character bases and growths, class caps and promotion gains). These never change.
- `engine/`: the stat engine. `common.py` holds the one simulator; each `feN.py` only describes that game's rules (class paths, caps and gains lookups). `engine/__init__.py` lists the games.
- `calculate_stats.py`: runs the engine and writes `average_stats_data.js`.
- `index.html`, `style.css`, `app.js`: the page. It only displays `average_stats_data.js`; it holds no game rules.

## Use

```
python calculate_stats.py     # regenerate average_stats_data.js after changing data or rules
python test_engine.py         # engine must reproduce tests/snapshot.json
node tests/smoke_page.js .    # drives every game, character, class, tab and filter of app.js
```

Open `index.html` directly in a browser; there is no build step. Python needs only the standard library.

If a rule change is meant to alter numbers, `test_engine.py` lists every changed value. Check the list, then update `tests/snapshot.json`.

## Adding a game

1. Add `data/feN.json` in the same shape as the existing files.
2. Add `engine/feN.py` with `NAMES`, `SPECIAL_CLASSES`, `classes`, `calculate`, `direct` and `tier` (see the docstring in `engine/__init__.py`), and register it in `GAMES`.
3. Add the game to `GAME_SETTINGS` in `app.js` and to the `game-selector` dropdown in `index.html`.

The scraper that produced the data files was removed once the data was complete. It is in git history: `git show 87b0f3f:engine/parser.py`.
