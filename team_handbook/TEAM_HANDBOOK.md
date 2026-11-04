# STATS 414 Team Handbook

**Living document.** Last updated: November 4, 2026 · Team: Juan Cortes-Aguiar, Ravikiran Madichetty, Ashish Singh

This handbook explains everything the project does, technically and practically, so any of us can present it, defend it in Q&A, rerun it, or extend it. It is updated whenever the work changes; the [change log](#12-change-log) at the bottom lists what changed and when. If something here disagrees with the code, the code is right and this document needs fixing; say so in the team chat.

**Contents**
1. [Project at a glance](#1-project-at-a-glance)
2. [Course requirements and how we meet them](#2-course-requirements-and-how-we-meet-them)
3. [Prediction markets in ten minutes](#3-prediction-markets-in-ten-minutes)
4. [Our data](#4-our-data)
5. [Working in the repository](#5-working-in-the-repository)
6. [Midterm: "Almost Certain?" step by step](#6-midterm-almost-certain-step-by-step)
7. [Midterm results and how to talk about them](#7-midterm-results-and-how-to-talk-about-them)
8. [Statistics and ML reference](#8-statistics-and-ml-reference)
9. [Lecture map](#9-lecture-map)
10. [Glossary](#10-glossary)
11. [Decisions and open questions](#11-decisions-and-open-questions)
12. [Change log](#12-change-log)

---

## 1. Project at a glance

| | Midterm: "The 99-Cent Question" |
| --- | --- |
| Question | Do Kalshi YES contracts first seen at a 90–99¢ ask win as often as their price says, and can market features predict which favorites lose better than the price? |
| Categories | All |
| Methods | EDA, calibration, elastic-net logistic regression, random forest, XGBoost, chronological validation, event bootstrap |
| Deliverable | 15-minute presentation including Q&A |
| Due | Wed Oct 28, 2026 (in class) |
| Status | Presented |

**Final:** on Nov 4 Prof. Cheng replaced the original final topic (informed trading on long shots, "Who Knew?") with a new assignment. The old final plan, its order-book data and its scripts were removed from the project.

The project plan with dates lives in the shared doc *STATS 414 Project Plan*; the repository is `github.com/SunLite9/414-Project-99` (public; no raw data or credentials).

## 2. Course requirements and how we meet them

From the syllabus (Prof. Guang Cheng, TA Hengzhi He):

- **Grading:** quizzes 20%, midterm presentation 20%, final presentation 30%, final report 30%. Presentations and reports are graded by **ranking** against other teams, so clarity and novelty matter, not only correctness.
- **Data:** "strictly required to use the prediction market data." We use the course's Kalshi database.
- **Midterm:** basic analysis of prediction-market data with predictive-AI algorithms, 15 minutes per team including Q&A. Ours covers calibration, three model families from Weeks 3–4 and honest validation.
- **Final:** changed by Prof. Cheng on Nov 4; this handbook will cover it once the new assignment is set.
- **Course rules we follow:** never try to identify a person behind a wallet; never put the database password in a shared file or on GitHub; the course data is not redistributed outside the class.

## 3. Prediction markets in ten minutes

- **Contract.** A yes/no question with a deadline ("Will CPI exceed 3.8% for 2026?"). A **YES** share pays $1 if the answer is yes and $0 otherwise; a **NO** share is the reverse. YES + NO always pays exactly $1.
- **Price = probability.** If you believe the event has probability *p* and a YES share costs *c*, your expected profit is *p* − *c*. Buyers push the price up when *p* > *c*, so the price settles near the crowd's probability. Fees, thin markets and risk aversion bend it, so a price is an estimate, not a fact.
- **Order book.** Traders post **bids** (offers to buy YES) and **asks** (offers to sell YES). The **spread** is ask − bid; the **midpoint** is (bid + ask)/2. A **taker** trades against an existing order; a **maker** posts one and waits. A large order "walks the book" and moves the price.
- **Events and ladders.** An event groups related markets, for example one market per strike price ("gas above $3.10, $3.20, …"). Markets in one event share a cause, so they are **not independent observations**. This is why we resample whole events in our bootstraps.
- **Resolution.** Kalshi resolves markets itself under its rulebook.

## 4. Our data

### 4.1 Sources

| Source | What it holds | Access |
| --- | --- | --- |
| Kalshi course database (PostgreSQL) | `markets`, `events`, `hourly_candles` | Read-only login from Prof. Cheng; **window ends Oct 29, 2026, 11:59pm PT** |

Credentials live only in a local `.env` file (git-ignored). Never paste them into a notebook.

### 4.2 What we downloaded (in the repo under `data/raw/`)

| File | Rows | What it is |
| --- | --- | --- |
| `candles/candles-YYYY-MM-DD.parquet` (20 files) | 7,173,620 | Every hourly candle for every market, Oct 8–27 UTC |
| `markets.parquet` | 839,613 | Metadata for every market with a candle: result, status, open/close times, scheduled event time, rules text |
| `events.parquet` | 67,261 | Event title, series, **category** |

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
6. **Access ended** Oct 29, 2026, 11:59pm PT; the raw data stays on Ashish's Mac and is not in the repo.

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
git clone https://github.com/SunLite9/414-Project-99.git && cd 414-Project-99
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
- **Where Claude works:** the Project folder on Ashish's Mac (`Documents/STATS_414/Project`) holds the working copy and the local-only raw data (`data/raw/`: candles and market metadata). The repo is the shared source of truth.
- **New lecture slides** go into `Documents/STATS_414/lectures` and are summarized in [section 9](#9-lecture-map).

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

## 8. Statistics and ML reference

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

## 9. Lecture map

| Week | Topic | Project use |
| --- | --- | --- |
| 1 (Sep 30) | ML pipeline, bias–variance, validation and cross-validation, OLS, PCA | Pipelines, time-based validation. *The Week 1 PDF on Ashish's Mac is stored only in iCloud and could not be read yet; open it once in Finder to download it.* |
| 2 (Oct 7) | Prediction markets (guest lecture, Yurii Nosov) | Market mechanics, data quirks |
| 3 (Oct 14) | Regularization, lasso, ridge, elastic net, tuning, logistic regression | Elastic-net model, validation tuning |
| 4 (Oct 21) | Outlier detection: Isolation Forest, Online IF, Random Cut Forest, forests/XGBoost, PU learning | Midterm tree models |
| 5 (Oct 28) | Midterm presentations | — |
| 6 (Nov 4) | Agentic AI: reasoning, planning, ReAct/CodeAct, AgentBeats | — |
| 7 (Nov 18) | Agents: tool use and memory | — |
| 8 (Nov 25) | Table-reasoning agent and error localization (guest); Quiz 2 | — |
| 9 (Dec 2) | Final presentations | — |

New slides are added here as they arrive in `STATS_414/lectures`.

## 10. Glossary

**Ask / bid:** lowest price to buy YES / highest price to sell it. **Midpoint:** (bid + ask)/2. **Spread:** ask − bid. **Candle:** one hour's summary (open, high, low, close of bid, ask and trade price, plus volume and open interest). **Open interest:** contracts outstanding. **Event:** a group of related markets. **Ladder:** an event with one market per threshold. **Favorite / long shot:** a contract priced near $1 / near $0. **Resolution / settlement:** the official answer and payout. **Brier score:** mean squared error of probabilities. **Ablation:** removing a feature group to see what it adds. **Leakage (modeling):** using information not available at prediction time. **CFTC:** the US regulator of event contracts.

## 11. Decisions and open questions

| Date | Decision |
| --- | --- |
| Oct 26 | Everyone works on every step |
| Oct 26 | Notebooks for code |
| Oct 27 | Full-population rebuild of the midterm replaces the 25% sample in the presentation |
| Oct 27 | UCLA style guide adopted for all slides and plots |
| Oct 28 | Deck retitled "The 99-Cent Question: How Accurate Are Kalshi's Odds?" |
| Oct 28 | Public repo `414-Project-99` created with fresh history, no credentials, no raw data |
| Nov 4 | Prof. Cheng changed the final; old final plan, order books and scripts removed |

Open:
- The new final assignment: scope, data and deadlines once Prof. Cheng posts them.

## 12. Change log

| Date | Change |
| --- | --- |
| 2026-11-04 | Final changed by Prof. Cheng: removed the "Who Knew?" plan (old section 8), order books, the Oct 28 refresh files and the order-book/refresh scripts; sections renumbered |
| 2026-10-28 | Public repo `414-Project-99` created (fresh history, credentials read from `.env`, raw data excluded) |
| 2026-10-28 | Deck retitled; slide 3 caveat and slide 12 "next" line removed |
| 2026-10-28 | Database refresh done: Oct 26 re-pulled (unchanged), outcomes refreshed (+7,977 settled markets) into `markets_2026-10-28.parquet`; Oct 27 not needed |
| 2026-10-28 | Deck finalized: backup slides removed, Thank You slide added (13 slides) |
| 2026-10-27 | Midterm deck rebuilt around EDA: notebook 03 (landscape, prices, spreads, full-range calibration), 12 main slides timed to about 10:20; model slides merged; section 7.1 added |
| 2026-10-27 | Order-book push to GitHub paused after Oct 1–10; remaining steps listed in section 12 |
| 2026-10-27 | Order books downloaded (583 hours, events + snapshots, verified) and copied to the Mac; `pull_orderbook.py`, `unpack_ob.py`, `refresh_from_db.py` added |
| 2026-10-27 | Handbook created: course requirements, data, repo workflow, full midterm methodology and results, final plan, references |
