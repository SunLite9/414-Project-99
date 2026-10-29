# STATS 414 project: Almost Certain? → Who Knew?

Team: Juan Cortes-Aguiar, Ravikiran Madichetty, Ashish Singh. Course: STATS 414, Fall 2026 (Prof. Guang Cheng).

**Start here:** [Team handbook](team_handbook/TEAM_HANDBOOK.md) (what we do and why, in full) · [Style guide](style_guide/STYLE_GUIDE.md) (UCLA look for slides and plots)

- **Midterm (Oct 28):** do Kalshi YES contracts first seen at a 90–99¢ ask win as often as their price says, and can market features predict which favorites lose better than the price itself?
- **Final (Dec 2 / report Dec 11):** the other tail. Among 1–10¢ long shots that won, did prices or volume move before the news (informed trading) in Politics, Technology, Entertainment and Economy markets?

## Midterm at a glance

| | |
| --- | --- |
| Data | Every hourly candle in the course Kalshi database, Oct 8–27 2026 (7.17M rows, 839,613 markets) |
| EDA | Sports is 76% of volume; top 1% of markets carry 82%; prices calibrated within 0.5 points on average, with a favorite–long-shot bias at the extremes |
| Study population | 10,351 favorites (first quote with ask 90–99¢, midpoint ≥ 90¢, spread ≤ 5¢), 513 losses |
| Splits | Train before Oct 15 · validation Oct 15–19 · test Oct 20+ (entries fall on Oct 9–11, 15–18, 20–25 because of data gaps); events never span splits |
| Models | Quoted price (baseline), price-only logistic, elastic-net logistic, random forest, XGBoost, each with and without volume, tuned on validation |
| Main result | The quoted price had the best test Brier score (0.04624); no model beat it, and volume added nothing |
| Calibration | Test favorites lost 4.96% of the time vs 5.40% implied by price |
| Exception | Economics favorites (mostly AAA gas-price ladders) lost 0.5% vs 3.5% implied; event-bootstrap 95% CI of the gap [−3.4, −2.6] pts, stable across periods |
| Economics | Buying every test favorite at the ask: 95.0% won, −$19.61 on 2,299 contracts before fees |

Slides: [`slides/midterm/Almost_Certain_Midterm.pptx`](slides/midterm/Almost_Certain_Midterm.pptx) (PDF alongside; speaker notes in the deck).

## Repository layout

```
team_handbook/TEAM_HANDBOOK.md  full technical and practical guide to the project (living document)
style_guide/                    STYLE_GUIDE.md, ucla_style.py (plot helper), deck_theme.json
notebooks/
  01_build_dataset.ipynb   raw candles + metadata -> one entry per market (data/processed/midterm_entries.*)
  02_midterm_models.ipynb  models, validation, bootstrap, figures -> results/midterm/
  03_midterm_eda.ipynb     exploratory analysis of all 7.17M candles -> results/midterm/eda_*
  *.py                     plain-script sources of the notebooks (py2nb.py converts them)
  pull_candles.py, pull_meta.py, kalshi_io.py   how the raw data was pulled (needs .env; access ended Oct 29)
data/raw/  (not in this repo: course data; rebuilt by the pull scripts)
  candles/candles-YYYY-MM-DD.parquet   hourly_candles, every market, one file per UTC day
  markets.parquet, events.parquet      market/event metadata incl. result, close time, category, rules text
data/processed/midterm_entries.*       the 10,351-row midterm study table
results/midterm/                       metrics, bootstrap intervals, tables and figures
slides/midterm/                        deck (+ build_deck.js that generates it from the figures)
access_kalshi2.ipynb, insider_demo*, lab_database_walkthrough*   Juan's first look + course demos
COURSE_MATERIALS_README.md             the guest lecture's README
```

## Reproduce

```bash
pip install -r requirements.txt
cd notebooks
jupyter nbconvert --to notebook --execute --inplace 01_build_dataset.ipynb   # ~1 min
jupyter nbconvert --to notebook --execute --inplace 02_midterm_models.ipynb  # ~30 s
jupyter nbconvert --to notebook --execute --inplace 03_midterm_eda.ipynb     # ~10 s
node ../slides/midterm/build_deck.js                                          # optional: rebuild the deck (needs pptxgenjs)
```

**Raw data is not included.** The course Kalshi data may not be redistributed, so `data/raw/` is not in this repository. Class members can rebuild it with `notebooks/pull_candles.py`, `pull_meta.py` and `pull_orderbook.py` (credentials in a local `.env`, see `.env.example`) while course access is open. `data/processed/midterm_entries.*` and `results/` are included, so notebook 02 and the slides run without it.

## Data notes and limits

- The candle table has gaps: no candles on Oct 12–14 or 19, and only 1–4 hours on Oct 15 and 18. An entry is the first *observed* qualifying quote, not necessarily the first ever.
- Median candle was stored 2.5 h after its hour and 49.5% after the market closed (backfilled), so this is a retrospective study, not a live backtest.
- `close_time` in the metadata is the actual close (settlement follows in a median of 3 minutes), so it is never a feature; time-to-event uses the scheduled `occurrence_datetime`.
- Economic figures assume one contract at the displayed ask, held to settlement, before fees; order-book depth and fills are unknown.
- Course data: raw Kalshi data is not published here. Credentials live only in a local `.env` (git-ignored); copy `.env.example` and fill it in. No usernames, passwords or private hosts are committed.

The team's first version (25% sample, 2,530 favorites) is in the separate `414-project-99-cents` repository; its numbers reproduce exactly and this version extends it to the full data, adds tuned regularization (Week 3), gradient boosting (Week 4), timing/momentum/category features and event-level confidence intervals.
