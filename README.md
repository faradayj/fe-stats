# FE Average Stats

Average stats for Fire Emblem characters (FE5 to FE12) in every class they can reach.

Live: https://faradayj.github.io/fe-stats/

## Run

Open `index.html` in a browser. After changing `data/` or `engine/`, rebuild the data:

    python calculate_stats.py

## Test

    python test_engine.py
    node tests/smoke_page.js .

## Files

- `data/`: game data, one file per game
- `engine/`: the stat engine, one file per game (see `engine/__init__.py` to add a game)
- `calculate_stats.py`: writes `average_stats_data.js`
- `index.html`, `style.css`, `app.js`: the page
- `tests/`: expected engine output and the page test
