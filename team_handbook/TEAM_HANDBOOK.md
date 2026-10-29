# STATS 414 Team Handbook

**Living document.** Last updated: October 27, 2026 (afternoon) · Team: Juan Cortes-Aguiar, Ravikiran Madichetty, Ashish Singh

This handbook explains everything the project does, technically and practically, so any of us can present it, defend it in Q&A, rerun it, or extend it. It is updated whenever the work changes; the [change log](#13-change-log) at the bottom lists what changed and when. If something here disagrees with the code, the code is right and this document needs fixing; say so in the team chat.

**Contents**
1. [Project at a glance](#1-project-at-a-glance)
2. [Course requirements and how we meet them](#2-course-requirements-and-how-we-meet-them)
3. [Prediction markets in ten minutes](#3-prediction-markets-in-ten-minutes)
4. [Our data](#4-our-data)
5. [Working in the repository](#5-working-in-the-repository)
6. [Midterm: "Almost Certain?" step by step](#6-midterm-almost-certain-step-by-step)
7. [Midterm results and how to talk about them](#7-midterm-results-and-how-to-talk-about-them)
8. [Final: "Who Knew?" plan and methods](#8-final-who-knew-plan-and-methods)
9. [Statistics and ML reference](#9-statistics-and-ml-reference)
10. [Lecture map](#10-lecture-map)
11. [Glossary](#11-glossary)
12. [Decisions and open questions](#12-decisions-and-open-questions)
13. [Change log](#13-change-log)

---

## 1. Project at a glance

| | Midterm: "Almost Certain?" | Final: "Who Knew?" |
| --- | --- | --- |
| Question | Do Kalshi YES contracts first seen at a 90–99¢ ask win as often as their price says, and can market features predict which favorites lose better than the price? | Among 1–10¢ long shots that won, did prices or volume move before the news became public (informed trading)? |
| Categories | All | Politics, Technology, Entertainment, Economy (required by the syllabus) |
| Methods | Calibration, elastic-net logistic regression, random forest, XGBoost, chronological validation, event bootstrap | Information leakage score, Isolation Forest, Random Cut Forest, synthetic-injection evaluation, PU learning on confirmed insider wallets, an AI agent for news timestamps |
| Deliverable | 15-minute presentation including Q&A | 15-minute presentation; report of at least 10 pages with source code |
| Due | Wed Oct 28, 2026 (in class) | Presentation Wed Dec 2; report Fri Dec 11, 5pm |
| Status | Analysis and slides done; rehearsal pending | Planning; data pull on Oct 28 morning |

The project plan with dates lives in the shared doc *STATS 414 Project Plan*; the repository is `github.com/SunLite9/414-Project` (private).

## 2. Course requirements and how we meet them

From the syllabus (Prof. Guang Cheng, TA Hengzhi He):

- **Grading:** quizzes 20%, midterm presentation 20%, final presentation 30%, final report 30%. Presentations and reports are graded by **ranking** against other teams, so clarity and novelty matter, not only correctness.
- **Data:** "strictly required to use the prediction market data." We use the course's Kalshi database (and Polymarket lab data for the final's check against confirmed cases).
- **Midterm:** basic analysis of prediction-market data with predictive-AI algorithms, 15 minutes per team including Q&A. Ours covers calibration, three model families from Weeks 3–4 and honest validation.
- **Final:** insider or informed-trader detection in Politics, Technology, Entertainment and Economy markets. Ours detects information leakage before public news on long-shot winners.
- **Final report:** at least 10 pages plus source code, due Dec 11 at 5pm. Strong projects may be turned into a conference submission, so we write it in LaTeX with a conference-style template.
- **Course rules we follow:** never try to identify a person behind a wallet; never put the database password in a shared file or on GitHub; the course data is not redistributed outside the class.

## 3. Prediction markets in ten minutes

- **Contract.** A yes/no question with a deadline ("Will CPI exceed 3.8% for 2026?"). A **YES** share pays $1 if the answer is yes and $0 otherwise; a **NO** share is the reverse. YES + NO always pays exactly $1.
- **Price = probability.** If you believe the event has probability *p* and a YES share costs *c*, your expected profit is *p* − *c*. Buyers push the price up when *p* > *c*, so the price settles near the crowd's probability. Fees, thin markets and risk aversion bend it, so a price is an estimate, not a fact.
- **Order book.** Traders post **bids** (offers to buy YES) and **asks** (offers to sell YES). The **spread** is ask − bid; the **midpoint** is (bid + ask)/2. A **taker** trades against an existing order; a **maker** posts one and waits. A large order "walks the book" and moves the price.
- **Events and ladders.** An event groups related markets, for example one market per strike price ("gas above $3.10, $3.20, …"). Markets in one event share a cause, so they are **not independent observations**. This is why we resample whole events in our bootstraps.
- **Resolution.** Kalshi resolves markets itself under its rulebook. Polymarket uses the UMA oracle with proposals, a dispute window and bonds.
- **Kalshi vs Polymarket.** Kalshi is a US exchange regulated by the CFTC; traders are ID-verified but **trades are anonymous in public data**. Polymarket settles on the Polygon blockchain; every trade shows a **wallet** (pseudonymized in the lab's data) but no identity. So wallet-level insider detection is only possible on Polymarket; on Kalshi we work at the market level.
- **Insiders in the news.** Confirmed or charged cases include the Maduro-raid market (a US Army soldier charged by DOJ/CFTC in 2026), US strikes on Iran, Google search markets, and Kalshi's own February 2026 penalties against a MrBeast video editor and a former California candidate. Labels are few and biased toward the people who got caught.

## 4. Our data

### 4.1 Sources

| Source | What it holds | Access |
| --- | --- | --- |
| Kalshi course database (PostgreSQL) | `markets`, `events`, `hourly_candles` | Read-only login from Prof. Cheng; **window ends Oct 29, 2026, 11:59pm PT** |
| Kalshi order-book files (CloudFront) | Per UTC hour: `events-*.parquet` (every order-book level change: `ts_ms, asset_id, market, side, price, size`) and `snap-*.parquet` (full book at the start of the hour: `bids`, `asks` lists) | Same login. **Downloaded Oct 27:** all 583 hours, Oct 1 17:00 to Oct 25 23:00 UTC, no gaps, 1,166 files, 1.73 GB. On Ashish's Mac in `data/raw/orderbook/` (too large for Git) |
| Polymarket lab data (guest lecture) | Market catalog, resolutions, hourly order books since May 30, per-wallet trades through Oct 5 | Catalog needs the lab password; files are public |
| Polymarket confirmed-insider labels | `wallet_features.csv`: 55,952 wallets, 19 confirmed insiders (lab list of 36) | Course materials, `lectures/Week 2/notebooks/data` |

Credentials live only in a local `.env` file (git-ignored). Never paste them into a notebook.

### 4.2 What we downloaded (in the repo under `data/raw/`)

| File | Rows | What it is |
| --- | --- | --- |
| `candles/candles-YYYY-MM-DD.parquet` (20 files) | 7,173,620 | Every hourly candle for every market, Oct 8–27 UTC |
| `markets.parquet` | 839,613 | Metadata for every market with a candle: result, status, open/close times, scheduled event time, rules text |
| `events.parquet` | 67,261 | Event title, series, **category** |
| `markets_2026-10-28.parquet`, `events_2026-10-28.parquet` | 839,613 / 67,261 | Same markets refreshed on Oct 28: 7,977 more now have a final yes/no (522,732 in all). Use these for the final; the midterm used the Oct 27 snapshot (`markets.parquet`) |

Key columns:

- **Candles:** `market_slug`, `end_time` (end of the hour), `observed_at` (when the row was stored), `yes_bid_close`, `yes_ask_close`, `price_close` (last trade), `volume` (contracts traded that hour), `open_interest`.
- **Markets:** `status` (finalized, active, …), `result` (yes, no, scalar, blank), `close_time` (**actual** close), `occurrence_datetime` (**scheduled** event time), `open_time`, `settlement_ts`, `rules_primary`.
- **Events:** `category` (Sports, Economics, Financials, Elections, Politics, Entertainment, Science and Technology, Companies, Crypto, Commodities, Climate and Weather, Mentions, …).

### 4.3 Data quirks you must know

1. **Gaps.** The candle table has no rows for Oct 12, 13, 14 or 19, and only 1–4 hours on Oct 15 and 18 (figure `coverage_by_day.png`). So "first observed" is not "first ever".
2. **Backfill.** The median candle was stored 2.5 hours after its hour, and 49.5% of our entry candles were stored after the market had closed. The data is fine for looking back, but it is not what a trader could have seen live.
3. **`close_time` is the actual close.** Settlement follows it by a median of 3 minutes. Using it as a feature would leak the answer, so we only use it to require entries before the close; time-to-event uses the scheduled `occurrence_datetime`.
4. **Status values.** Of 839,613 markets, 514,755 are finalized with a yes/no result; 3,420 finalized markets are "scalar" and excluded.
5. **Server timeout.** The database cancels any query after 2 minutes, so whole-table counts fail; we pulled in 6-hour chunks.
6. **Final database refresh (Oct 28):** `notebooks/refresh_from_db.py` re-pulled Oct 26 (unchanged: 199,680 rows, already complete) and refreshed every market's outcome. Oct 27 is partial and not needed (team decision Oct 28). Database access ends Oct 29, 11:59pm PT.
8. **Order books:** a book at time T = the hour's snapshot, then every delta up to T in file order (several changes can share a millisecond). `size = 0` removes a level. One hour holds millions of rows (Oct 20 00:00 UTC: 3.48M changes over 7,455 books).
7. **Polymarket lab quirks** (from the guest lecture): status flags are never updated (filter on dates), catalog prices are stale (check `synced_at`), some order-book snapshots are stale, and not every market's book is recorded.

## 5. Working in the repository

### 5.1 Layout

```
README.md                      project summary and how to reproduce
style_guide/                   STYLE_GUIDE.md, ucla_style.py (plots), deck_theme.json (slides)
team_handbook/                 this handbook
notebooks/
  01_build_dataset.ipynb       raw data -> one row per market (midterm study table)
  02_midterm_models.ipynb      models, validation, bootstrap, figures
  03_midterm_eda.ipynb         exploratory analysis of all 7.17M candles (landscape, prices, spreads, calibration)
  *.py                         the same notebooks as plain scripts ("# %%" cells); edit these, then run py2nb.py
  pull_candles.py, pull_meta.py, kalshi_io.py   how raw data was pulled (needs .env)
data/raw/                      downloaded data (see 4.2)
data/processed/                midterm_entries.parquet / .csv (10,351 rows)
results/midterm/               metric tables (.csv), summary.json, figures/
slides/midterm/                Almost_Certain_Midterm.pptx (+ PDF) and build_deck.js that generates it
```

### 5.2 Setup and running

```bash
git clone git@github.com:SunLite9/414-Project.git && cd 414-Project
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd notebooks
jupyter nbconvert --to notebook --execute --inplace 01_build_dataset.ipynb    # about 1 minute
jupyter nbconvert --to notebook --execute --inplace 02_midterm_models.ipynb   # about 30 seconds
```

To regenerate the deck after changing figures: `npm install pptxgenjs`, then `node slides/midterm/build_deck.js` from the repo root.

Re-runs can differ in the 6th–8th decimal place because multithreaded tree models add numbers in a different order; nothing on the slides changes.

### 5.3 How we work

- **Branching:** everyone pushes to `main`. Run `git pull` before you start and before you push; write commit messages that say what changed and why.
- **Notebooks:** edit the `.py` source, then `python py2nb.py 02_midterm_models.py 02_midterm_models.ipynb` and execute. This keeps diffs readable.
- **Plots and slides** follow `style_guide/STYLE_GUIDE.md` (UCLA colors, Arial). Plots must call `ucla_style.apply()`.
- **Where Claude works:** the Project folder on Ashish's Mac (`Documents/STATS_414/Project`) holds the working copy and the large local-only files (raw 6-hour parts, order books). The repo is the shared source of truth.
- **New lecture slides** go into `Documents/STATS_414/lectures` and are summarized in [section 10](#10-lecture-map).

## 6. Midterm: "Almost Certain?" step by step

### 6.1 Why this question

Buying contracts at 95–99¢ looks like easy money: they almost always win. But at 99¢ one loss cancels 99 wins (profit per contract = outcome − price paid). The real question is whether the **price is accurate**, and whether anything else we observe predicts the rare losses better than the price does.

### 6.2 Building the study table (notebook 01)

| Step | Rule | Markets left |
| --- | --- | --- |
| 1 | Finalized markets with a yes/no result that have candles | 514,755 |
| 2 | Keep candles whose hour ends **before** the market's actual close | 224,712 |
| 3 | Valid two-sided quote (0 < bid ≤ ask < 1) with ask between 90¢ and 99¢ | 45,540 |
| 4 | Midpoint ≥ 90¢ and spread ≤ 5¢ (a 99¢ ask over a 40¢ bid is not consensus) | 10,898 |
| 5 | Keep the **first** such candle per market (the "entry") | 10,898 |
| 6 | Drop events whose markets fall in two different splits | 10,554 |
| 7 | Drop training markets settled on or after Oct 15 and validation markets settled on or after Oct 20 (label not yet known at the cut-off) | **10,351** |

Label: `y_win = 1` if the result is yes. 513 of the 10,351 lost.

### 6.3 Features (all known at the entry hour)

| Feature | Definition | Why |
| --- | --- | --- |
| `midpoint` | (bid + ask)/2 | The market's probability; the baseline |
| `spread` | ask − bid | Uncertainty and trading friction |
| `log_open_interest` | log(1 + open interest) | Contracts outstanding |
| `log_volume`, `volume_missing` | log(1 + contracts traded in the entry hour), missing flag | The main hypothesis (does volume help?) |
| `log_volume_prev_6h` | log(1 + volume summed over the 6 hours before entry) | Recent participation |
| `slog_hours_to_event` | sign(h)·log(1 + \|h\|), h = scheduled event time − entry time, clipped to [−72, 336] hours | Favorites far from the event face more uncertainty |
| `log_hours_since_open` | log(1 + hours since the market opened) | Market age |
| `mid_change_6h_f`, `has_prior_quote` | midpoint − most recent valid midpoint in the prior 6 h (0 if none), and a flag for whether one existed | Momentum into the entry |
| `fresh_cross_f` | 1 if that earlier midpoint was below 90¢ | Did the market just become a favorite? |
| `prior_candles_6h` | number of candles in the prior 6 h | Activity, and a gap indicator |
| `log_event_size` | log(1 + number of the event's markets with candles in our Oct 8–27 pull) | Ladders vs single markets. Caveat: counts markets seen during the whole window, a mild look-ahead |
| `category_group` | Event category (top 9, others as "Other"), one-hot encoded | Pricing may differ by market type |

Numeric features are median-imputed and standardized; both steps are fitted on training data only (inside a scikit-learn `Pipeline`).

### 6.4 Splits

| Split | Entry dates (UTC) | Markets | Events | Losses |
| --- | --- | --- | --- | --- |
| Train | before Oct 15 (data: Oct 9–11) | 4,358 | 2,131 | 179 |
| Validation | Oct 15–19 (data: Oct 15–18) | 3,694 | 1,724 | 220 |
| Test | Oct 20 onward (data: Oct 20–25) | 2,299 | 1,063 | 114 |

These are the same cut-offs as the team's first version (chosen for coverage before any model was fitted). Splitting by time imitates a forecaster who only knows the past; splitting at random would leak information between related markets.

### 6.5 Models and tuning (notebook 02)

| Model | What it is | Grid searched (validation Brier) | Chosen |
| --- | --- | --- | --- |
| Quoted midpoint | The price itself as the win probability | none | — |
| Training win rate | Same probability for everyone | none | — |
| Price-only logistic | Logistic regression on midpoint (essentially unpenalized, C = 10⁶) | none | — |
| Elastic-net logistic | Logistic regression with penalty λ[α·\|β\|₁ + (1−α)/2·\|β\|²₂]; C = 1/λ, L1 share α | C ∈ {0.01, 0.1, 1, 10}, α ∈ {0, 0.5, 1} | C = 0.01, α = 0.5 |
| Random forest | 300 trees | depth ∈ {4, 8}, min leaf ∈ {20, 50} | depth 4 (leaf 20 without volume, 50 with) |
| XGBoost | Gradient-boosted trees, 200 rounds, subsample 0.8, colsample 0.8, min child weight 5 | depth ∈ {2, 3}, learning rate ∈ {0.03, 0.1} | depth 2, rate 0.03 |

Each fitted family is run twice, **with and without the volume features**, so the difference isolates what volume adds (an "ablation"). Procedure: fit on train → choose hyperparameters by validation Brier → refit the chosen setting on train + validation → score the test period **once**.

### 6.6 Evaluation

- **Brier score** (main metric): mean of (p − y)², lower is better. It rewards calibrated probabilities, which is what matters for pricing.
- **Log loss:** −mean[y log p + (1−y) log(1−p)]; punishes confident mistakes heavily.
- **AUC:** the chance a random winner gets a higher probability than a random loser (0.5 = no skill).
- **Loss average precision:** treats losses as the positive class and ranks by 1 − p; compare with the loss rate (about 5%), which is what random ranking scores.
- **Accuracy is not used**: "always predict win" is 95% accurate and useless.
- **Event bootstrap** (1,000 draws): resample whole events with replacement, recompute Brier(model) − Brier(price), and take the 2.5th and 97.5th percentiles as a 95% interval. Resampling events instead of markets respects the dependence inside ladders.
- **Wilson intervals** for win rates in calibration bins (better than ±1.96·√(p(1−p)/n) when p is near 1).
- **Economics:** gross result per contract = y − ask, assuming one contract bought at the displayed ask and held to settlement, before fees. It is an illustration, not a backtest (no order-book depth, no fills, no fees).

## 7. Midterm results and how to talk about them

### 7.1 Exploratory analysis (notebook 03, slides 3–6)

The midterm is meant to be data analysis and EDA first, so the deck opens with four exploration slides on all the data before the favorites study.

| Finding | Number | Where |
| --- | --- | --- |
| Coverage | 7.17M hourly candles, 839,613 markets, 67,261 events; days missing (Oct 12–14, 19) | slide 3 |
| What trades | Sports = 76% of contracts traded from 37% of markets; Crypto 17% from 38% | slide 4, `eda_landscape.csv` |
| Concentration | Top 1% of markets = 82% of volume; 72% of markets never traded; 89% of hourly candles have zero volume | slide 4, `eda_summary.json` |
| Course categories | Politics, Economics, Tech, Entertainment each under 0.4% of volume | slide 4 |
| Where prices sit | 77% of candles have a valid two-sided quote; 21% of quotes below 10¢, 5.5% above 90¢ | slide 5 |
| Spreads | Median 4¢; 1–2¢ near 0¢ and 100¢; widest (10¢) near 50¢ | slide 5, `eda_liquidity_by_price.csv` |
| Calibration, full range | 129,866 markets (first quote with spread ≤ 5¢); average gap 0.5 points | slide 6, `eda_calibration_full_range.csv` |
| Favorite–long-shot bias | Under 2¢: won 0.8% vs 1.6% priced; 2–5¢: 2.5% vs 3.5%; 95–100¢ favorites won about 1 point more than priced | slide 6 |

The calibration intervals are Wilson intervals per bin; markets in one event are related, so they are somewhat optimistic.

### 7.2 Favorites and models (notebooks 01–02, slides 7–11)

| Result | Number | Where |
| --- | --- | --- |
| Calibration | Test favorites lost 4.96% vs 5.40% implied (validation 5.96% vs 5.17%; train 4.11% vs 5.61%) | slide 6, `calibration.csv` |
| Best predictor | Quoted midpoint, test Brier 0.04624 (also best on validation, 0.05490) | slide 9, `model_scores.csv` |
| Closest model | Elastic net 0.04629; difference +0.00005, 95% CI [−0.00015, +0.00025] | `bootstrap_comparisons.csv` |
| Volume ablation | Brier changes ≤ 0.0001 in every family; all intervals include 0 | slide 9 |
| What the elastic net kept | midpoint, spread, open interest, event size; every volume, timing and category coefficient shrunk to 0 | `elastic_net_coefficients.csv` |
| Category exception | Economics lost 0.5% vs 3.5% implied; gap −3.1 points, CI [−3.4, −2.6]; 1, 3, 3 losses in train/validation/test; mostly AAA gas-price ladders | slide 7, `loss_by_category.csv` |
| Financials | 7.3% vs 4.8% implied, CI [−2.4, +8.4], not significant | slide 7 |
| Timing | Loss rates track the price from 1 h to 3 days out; lower than implied once the event has started or is under 1 h away | slide 8 |
| Economics of buying all | Test: 95.0% won, −$19.61 on 2,299 contracts (−0.85¢ each); validation −2.16¢; train +0.25¢ | slide 10 |
| Model filter | Margin chosen on validation (3¢) selected 0 test contracts | `strategy_illustration.csv` |

**Talking points.** The price is a strong forecaster; our models could not beat it, and the regularized model told us why by shrinking everything but price to zero. That is a real finding about market efficiency, not a failure. The forest and XGBoost fit training data better but lost on test: bias–variance in action.

**Likely questions and answers.**
- *Why not accuracy?* 95% of favorites win, so "always yes" scores 95% and finds no losses. Brier measures probability quality.
- *Why split by date?* A random split would put markets from the same event (and same day's news) on both sides and overstate skill.
- *Is the Economics finding a free lunch?* It held in all three periods, but it is mostly one market family (AAA gas prices), we did not model fees or depth, and gas prices settle on public data that sharp traders may already use. It is a lead, not a strategy.
- *Why did the elastic net choose such a strong penalty?* Validation Brier preferred it: extra features added noise, not signal.
- *What about the 25% sample version?* It reproduces exactly; the full data quadruples the losses and tightens every interval.
- *Can you trade this?* No: the data was backfilled, and we cannot see depth, fills or fees.

## 8. Final: "Who Knew?" plan and methods

### 8.1 Population

YES contracts whose first valid quote has an ask of 1–10¢, one entry per market, in the four required categories:

| Course category | Kalshi categories |
| --- | --- |
| Politics | Politics, Elections |
| Technology | Science and Technology, Companies |
| Entertainment | Entertainment |
| Economy | Economics, Financials |

Long shots that **won** are the cases; long shots that lost are the comparison group.

**Sample-size warning (from notebook 03):** with the first-quote rule, only **35** long shots priced 1–10¢ won in the four course categories during Oct 8–27 (Economy 20, Politics 8, Technology 6, Entertainment 1), out of 1,218 long-shot winners overall. Ways to get enough cases: widen to 1–15¢ or use every crossing below 10¢ rather than the first quote; use the order books back to Oct 1; add the Polymarket confirmed-insider events; and treat the other categories as a larger comparison set. Sports, Crypto, Weather and Mentions serve only as comparison or placebo groups.

### 8.2 When did the news break?

For each winning long shot we need the time the outcome became public:
- **Scheduled releases** (CPI, Fed decisions, gas-price prints): official calendars, so the time is exact.
- **Unscheduled news:** the earliest report in GDELT (a free global news index, 15-minute updates) or found by an **AI agent** that searches news archives and returns a timestamp with its source. This is where the course's agents half (Weeks 6–8: reasoning, tool use, memory) comes in.
- Every timestamp records its source and a confidence level; we check a sample by hand.

### 8.3 Measures

- **Information leakage score** for each market: ILS = (p_before_news − p_open)/(p_resolution − p_open). It is the share of the total price move that happened before the news. ILS near 0 means the market learned at the announcement; near 1 means the price got there before the public knew (see "Per-Market Information Leakage and Order-Flow Skill", arXiv 2605.02287).
- **Pre-news features** from hourly candles: volume relative to the market's own baseline, price drift, change in open interest, spread; from order books where available: buy/sell imbalance and depth.

### 8.4 Detectors

- **Isolation Forest** (Week 4): random axis-parallel cuts; points isolated in few cuts are anomalous. Score s(x) = 2^(−E[h(x)]/c(n)).
- **Random Cut Forest** (Week 4): a streaming version that scores each new hour by how much it disrupts the tree ("CoDisp"), suited to price series within a market. **Online Isolation Forest** is the alternative.
- **Baseline to beat:** rank by the largest volume spike. If the forest does not beat it, we say so (the guest lecture's demo found the simple "biggest spender" ranking beat Isolation Forest on confirmed insiders).

### 8.5 Evaluation without many labels

- **Synthetic injection:** plant fake informed buying (a burst of long-shot buying hours before resolution) into real markets and measure how many plants each detector recovers (recall at k).
- **Winners vs losers:** do winning long shots score higher than losing ones?
- **Scheduled vs unscheduled news:** scheduled releases should show little leakage; a detector that flags them heavily is picking up noise.
- **Polymarket check:** run the same features on the confirmed insider events (Iran strikes, Maduro) and on the lab's confirmed wallets, using **PU learning** (positive–unlabeled: few known positives, everything else unlabeled) as in the Week 4 lecture.

### 8.6 Deliverables

Final presentation (Dec 2, same slide system), and a report of at least 10 pages in LaTeX: introduction, data, methods, results, limitations, and an appendix with code pointers.

## 9. Statistics and ML reference

| Concept | One-line meaning | Where we use it |
| --- | --- | --- |
| Bias–variance trade-off | Flexible models fit noise (low bias, high variance) | Forest/XGBoost beat others on train, lost on test |
| Regularization | Penalize coefficient size to reduce variance | Elastic net; C = 0.01 shrank most coefficients to 0 |
| Lasso / ridge / elastic net | L1 (sparse) / L2 (shrink) / mix | α = 0.5 chosen |
| Hyperparameter tuning | Choose settings on data not used for fitting | Validation Brier |
| Logistic regression | log(p/(1−p)) = β₀ + βᵀx; odds and log-odds | Price-only and elastic-net models |
| Random forest | Average of decorrelated trees on bootstrap samples | Midterm model family |
| Gradient boosting (XGBoost) | Trees added one at a time to fix earlier errors | Midterm model family |
| Calibration | Predicted probability = observed frequency | Slide 6 |
| Bootstrap | Resample data to measure variability | Event-level intervals |
| Anomaly detection | Find points that are "few and different" | Final (Isolation Forest, RCF) |
| PU learning | Learn from positives + unlabeled data | Final Polymarket check |

## 10. Lecture map

| Week | Topic | Project use |
| --- | --- | --- |
| 1 (Sep 30) | ML pipeline, bias–variance, validation and cross-validation, OLS, PCA | Pipelines, time-based validation. *The Week 1 PDF on Ashish's Mac is stored only in iCloud and could not be read yet; open it once in Finder to download it.* |
| 2 (Oct 7) | Prediction markets (guest lecture, Yurii Nosov) | Market mechanics, data quirks, insider cases, Isolation Forest demo |
| 3 (Oct 14) | Regularization, lasso, ridge, elastic net, tuning, logistic regression | Elastic-net model, validation tuning |
| 4 (Oct 21) | Outlier detection: Isolation Forest, Online IF, Random Cut Forest, forests/XGBoost, PU learning | Midterm tree models; final detectors |
| 5 (Oct 28) | Midterm presentations | — |
| 6 (Nov 4) | Agentic AI: reasoning, planning, ReAct/CodeAct, AgentBeats | News-timestamp agent design |
| 7 (Nov 18) | Agents: tool use and memory | Agent implementation |
| 8 (Nov 25) | Table-reasoning agent and error localization (guest); Quiz 2 | Agent evaluation ideas |
| 9 (Dec 2) | Final presentations | — |

New slides are added here as they arrive in `STATS_414/lectures`.

## 11. Glossary

**Ask / bid:** lowest price to buy YES / highest price to sell it. **Midpoint:** (bid + ask)/2. **Spread:** ask − bid. **Candle:** one hour's summary (open, high, low, close of bid, ask and trade price, plus volume and open interest). **Open interest:** contracts outstanding. **Event:** a group of related markets. **Ladder:** an event with one market per threshold. **Favorite / long shot:** a contract priced near $1 / near $0. **Resolution / settlement:** the official answer and payout. **Brier score:** mean squared error of probabilities. **Ablation:** removing a feature group to see what it adds. **Leakage (modeling):** using information not available at prediction time. **Information leakage (markets):** prices moving before the news is public. **PU learning:** positive–unlabeled classification. **CFTC:** the US regulator of event contracts.

## 12. Decisions and open questions

| Date | Decision |
| --- | --- |
| Oct 26 | Midterm "Almost Certain?" and final "Who Knew?" are connected; everyone works on every step |
| Oct 26 | Repo private; notebooks for code; LaTeX conference template for the report |
| Oct 26 | Category mapping in 8.1 and the 1–10¢ long-shot cutoff accepted |
| Oct 26 | News-timestamp agent and Polymarket check are in scope |
| Oct 27 | Full-population rebuild of the midterm replaces the 25% sample in the presentation |
| Oct 27 | UCLA style guide adopted for all slides and plots |

Open:
- Who presents which midterm slides (decide after rehearsal). Deck: 12 content slides plus a Thank You slide (no backup slides), about 10:20 of talk, leaving about 4:40 for questions.
- Final: only 35 long-shot winners in the course categories under the first-quote rule (37 with the Oct 28 outcome refresh: Economy 20, Politics 10, Technology 6, Entertainment 1); choose how to widen the sample in week 1.
- **Order books on GitHub:** Oct 1–10 (446 files) are pushed. Oct 11–25 (720 files, about 1.1 GB) are still to push, in commits of about 150 MB or less (a 374 MB push was dropped). Paused Oct 27 at Ashish's request. The full set is on Ashish's Mac in `data/raw/orderbook/`.
- Optional cleanup on the Mac: `data/raw/_obtar/` (1.7 GB of copy pieces) and `data/raw/_to_delete/`.

## 13. Change log

| Date | Change |
| --- | --- |
| 2026-10-28 | Database refresh done: Oct 26 re-pulled (unchanged), outcomes refreshed (+7,977 settled markets) into `markets_2026-10-28.parquet`; Oct 27 not needed |
| 2026-10-28 | Deck finalized: backup slides removed, Thank You slide added (13 slides) |
| 2026-10-27 | Midterm deck rebuilt around EDA: notebook 03 (landscape, prices, spreads, full-range calibration), 12 main slides timed to about 10:20; model slides merged; section 7.1 added |
| 2026-10-27 | Order-book push to GitHub paused after Oct 1–10; remaining steps listed in section 12 |
| 2026-10-27 | Order books downloaded (583 hours, events + snapshots, verified) and copied to the Mac; `pull_orderbook.py`, `unpack_ob.py`, `refresh_from_db.py` added |
| 2026-10-27 | Handbook created: course requirements, data, repo workflow, full midterm methodology and results, final plan, references |
