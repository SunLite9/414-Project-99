# %% [markdown]
# # 03 · Exploratory data analysis of the Kalshi data
# STATS 414 midterm. Before modeling favorites, look at everything we downloaded: what Kalshi trades, what prices,
# spreads and volume look like, and whether prices are calibrated across the whole 1–99¢ range.
#
# Inputs: `data/raw/candles/*.parquet` (7.17M hourly candles, Oct 8–27 2026), `data/raw/markets.parquet`, `data/raw/events.parquet`.
# Outputs: `results/midterm/eda_*.csv`, `results/midterm/eda_summary.json`, figures in `results/midterm/figures/eda_*.png`.

# %%
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
RAW, RES = ROOT/'data/raw', ROOT/'results/midterm'; FIG = RES/'figures'; FIG.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT/'style_guide')); import ucla_style as us; us.apply()
summary = {}

# %% [markdown]
# ## Load
# Market metadata gives each market its event, category and final result. Categories come from the event.

# %%
meta = pd.read_parquet(RAW/'markets.parquet', columns=['slug', 'event_slug', 'status', 'result', 'close_time', 'open_time'])
ev = pd.read_parquet(RAW/'events.parquet', columns=['event_slug', 'category'])
meta = meta.merge(ev, on='event_slug', how='left')
meta['category'] = meta.category.fillna('Unknown')
for c in ['close_time', 'open_time']: meta[c] = pd.to_datetime(meta[c], utc=True, errors='coerce', format='mixed')
# Read one day-file at a time and keep only compact pieces (the Mac has about 3 GB of memory).
cols = ['market_slug', 'end_time', 'yes_bid_close', 'yes_ask_close', 'volume']
vol_parts, quote_parts, cand_parts = [], [], []
n_candles = n_zero_vol = 0
for f in sorted(glob.glob(str(RAW/'candles/candles-*.parquet'))):
    d = pd.read_parquet(f, columns=cols)
    if d.empty: continue                       # days with no candles (Oct 12-14, 19)
    d['end_time'] = pd.to_datetime(d.end_time, utc=True)
    n_candles += len(d); n_zero_vol += int((d.volume.fillna(0) == 0).sum())
    vol_parts.append(d.groupby('market_slug').volume.sum())
    ok = (d.yes_bid_close > 0) & (d.yes_bid_close <= d.yes_ask_close) & (d.yes_ask_close < 1)
    d = d[ok]
    mid = ((d.yes_bid_close + d.yes_ask_close) / 2).astype('float32'); spr = (d.yes_ask_close - d.yes_bid_close).astype('float32')
    quote_parts.append(pd.DataFrame({'mid': mid.values, 'spread': spr.values, 'traded': (d.volume.fillna(0) > 0).values}))
    k = spr.values <= 0.05   # candidate first quotes for the calibration check
    cand_parts.append(pd.DataFrame({'market_slug': d.market_slug.values[k], 'end_time': d.end_time.dt.tz_convert(None).values[k],
                                    'mid': mid.values[k], 'ask': d.yes_ask_close.values[k]}))
    del d
vol = pd.concat(vol_parts).groupby(level=0).sum().rename('volume')
q = pd.concat(quote_parts, ignore_index=True); cand = pd.concat(cand_parts, ignore_index=True); del quote_parts, cand_parts, vol_parts
summary['candles'] = n_candles; summary['markets'] = int(meta.slug.nunique()); summary['events'] = int(meta.event_slug.nunique())
print(f"{n_candles:,} candles · {summary['markets']:,} markets · {summary['events']:,} events · {len(q):,} valid quotes")

# %% [markdown]
# ## 1 · What does Kalshi trade?
# Markets and contracts traded (sum of hourly volume) by event category.

# %%
m = meta.set_index('slug').join(vol, how='left'); m['volume'] = m.volume.fillna(0)
top = ['Sports', 'Crypto', 'Financials', 'Economics', 'Commodities', 'Climate and Weather', 'Elections', 'Politics', 'Entertainment', 'Science and Technology', 'Mentions', 'Companies']
m['cat'] = np.where(m.category.isin(top), m.category, 'Other')
land = m.groupby('cat').agg(markets=('event_slug', 'size'), events=('event_slug', 'nunique'), volume=('volume', 'sum'))
land['market_share'] = land.markets / land.markets.sum(); land['volume_share'] = land.volume / land.volume.sum()
land = land.sort_values('volume', ascending=False); land.to_csv(RES/'eda_landscape.csv')
v = np.sort(m.volume.values)[::-1]
summary['top1pct_market_volume_share'] = float(v[:max(1, len(v) // 100)].sum() / v.sum())
summary['markets_with_zero_volume'] = float((m.volume == 0).mean())
summary['candles_with_zero_volume'] = n_zero_vol / n_candles
summary['markets_per_event_median'] = float(m.groupby('event_slug').size().median())
land.round(4)

# %%
cc = land.sort_values('volume_share')
fig, ax = us.figure((6.2, 4.3)); y = np.arange(len(cc))
ax.barh(y + 0.2, cc.volume_share * 100, 0.38, color=us.PRIMARY, label='Contracts traded')
ax.barh(y - 0.2, cc.market_share * 100, 0.38, color=us.REFERENCE, label='Markets listed')
for i, (_, r) in enumerate(cc.iterrows()):
    us.label(ax, r.volume_share * 100 + 0.8, i + 0.2, f'{r.volume_share*100:.0f}%' if r.volume_share >= 0.01 else f'{r.volume_share*100:.1f}%', ha='left', va='center', fontsize=9.5)
ax.set_yticks(y, cc.index); ax.grid(axis='y', visible=False); ax.grid(axis='x', color=us.GRAY_10)
ax.set_xlabel('Share of all markets / contracts traded, Oct 8–27 (%)'); ax.set_xlim(0, cc[['volume_share', 'market_share']].max().max() * 100 + 8)
ax.legend(loc='lower right')
us.save(fig, FIG/'eda_landscape.png')

# %% [markdown]
# ## 2 · Prices, spreads and liquidity
# A valid two-sided quote has 0 < bid ≤ ask < 1. Midpoint = (bid + ask)/2, spread = ask − bid.

# %%
summary['valid_quote_share'] = float(len(q) / n_candles)
summary['quotes_below_10c'] = float((q.mid < 0.10).mean()); summary['quotes_above_90c'] = float((q.mid > 0.90).mean())
summary['median_spread'] = float(q.spread.median())
bins = np.round(np.arange(0, 1.0001, 0.05), 2)
q['bin'] = pd.cut(q.mid, bins, include_lowest=True)
liq = q.groupby('bin', observed=True).agg(quotes=('mid', 'size'), median_spread=('spread', 'median'),
                                           traded=('traded', 'mean')).reset_index()
liq['center'] = [b.mid for b in liq.bin]; liq.drop(columns='bin').to_csv(RES/'eda_liquidity_by_price.csv', index=False)

fig, (a1, a2) = us.figure((9.0, 3.6), ncols=2)
a1.bar(liq.center * 100, liq.quotes / liq.quotes.sum() * 100, width=4.2, color=us.PRIMARY)
a1.set_xlabel('Quoted midpoint (¢)'); a1.set_ylabel('Share of hourly quotes (%)'); a1.set_xlim(0, 100)
a2.plot(liq.center * 100, liq.median_spread * 100, color=us.PRIMARY, marker='o', ms=5)
a2.set_xlabel('Quoted midpoint (¢)'); a2.set_ylabel('Median bid–ask spread (¢)'); a2.set_xlim(0, 100); a2.set_ylim(0, None)
fig.tight_layout(w_pad=3)
us.save(fig, FIG/'eda_prices_spreads.png')
liq.drop(columns='bin').round(4)

# %% [markdown]
# ## 3 · Are prices calibrated across the whole range?
# One observation per finalized yes/no market: its first valid quote with spread ≤ 5¢ that ends before the market closed
# (the same quality rule as the favorites study). Win rate vs quoted midpoint, with 95% Wilson intervals.

# %%
lab = meta[meta.status.eq('finalized') & meta.result.isin(['yes', 'no'])].rename(columns={'slug': 'market_slug'})[['market_slug', 'result', 'close_time', 'category']]
qq = cand.merge(lab, on='market_slug')
qq = qq[qq.end_time < qq.close_time.dt.tz_convert(None)]   # candle end times kept as naive UTC
first = qq.sort_values('end_time').groupby('market_slug').head(1).copy()
first['y'] = first.result.eq('yes').astype(int)
edges = [0, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98, 1.0]
first['b'] = pd.cut(first.mid, edges, include_lowest=True)
def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z*z/n; ctr = (p + z*z/(2*n)) / den; hw = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den; return ctr - hw, ctr + hw
cal = first.groupby('b', observed=True).agg(n=('y', 'size'), wins=('y', 'sum'), mid=('mid', 'mean')).reset_index()
cal['win_rate'] = cal.wins / cal.n; cal[['lo', 'hi']] = [wilson(k, n) for k, n in zip(cal.wins, cal.n)]
cal['gap'] = cal.win_rate - cal.mid; cal['bin'] = cal.b.astype(str); cal.drop(columns='b').to_csv(RES/'eda_calibration_full_range.csv', index=False)
summary['calibration_markets'] = int(len(first))
summary['mean_abs_calibration_gap'] = float(np.average(cal.gap.abs(), weights=cal.n))
# Plot the gap (win rate − price) so small biases are visible; on a plain calibration plot every point sits on the diagonal.
fig, ax = us.figure((5.6, 4.1))
cal['gap_lo'] = cal.lo - cal.mid; cal['gap_hi'] = cal.hi - cal.mid
col = [us.ATTENTION if h < 0 else (us.PRIMARY if l > 0 else us.REFERENCE) for l, h in zip(cal.gap_lo, cal.gap_hi)]
ax.axhline(0, color=us.GRAY_80, lw=1.2)
ax.errorbar(cal.mid * 100, cal.gap * 100, yerr=[(cal.gap - cal.gap_lo) * 100, (cal.gap_hi - cal.gap) * 100], fmt='none', ecolor=us.DARK, lw=1.2)
ax.scatter(cal.mid * 100, cal.gap * 100, c=col, s=55, zorder=3, edgecolors=us.DARK, linewidths=0.6)
ax.set(xlim=(0, 100), xlabel='Quoted midpoint at first quote (¢)', ylabel='Win rate minus price (percentage points)')
ax.text(2, ax.get_ylim()[1] * 0.92, 'won more often than priced', fontsize=9.5, color=us.GRAY_60)
ax.text(2, ax.get_ylim()[0] * 0.92, 'won less often than priced', fontsize=9.5, color=us.GRAY_60, va='bottom')
ax.grid(axis='x', color=us.GRAY_10)
us.save(fig, FIG/'eda_calibration_full_range.png')
cal.drop(columns='b').round(4)

# %% [markdown]
# ## 4 · Long shots: how many 1–10¢ contracts won? (sets up the final project)
# Counts by the four course categories, using the mapping in the team handbook.

# %%
course = {'Politics': 'Politics', 'Elections': 'Politics', 'Science and Technology': 'Technology', 'Companies': 'Technology',
          'Entertainment': 'Entertainment', 'Economics': 'Economy', 'Financials': 'Economy'}
ls = first[(first.ask >= 0.01) & (first.ask <= 0.10)].copy()
ls['course_cat'] = ls.category.map(course).fillna('Other categories')
lst = ls.groupby('course_cat').agg(long_shots=('y', 'size'), won=('y', 'sum')); lst['win_rate'] = lst.won / lst.long_shots
lst.to_csv(RES/'eda_longshots_by_course_category.csv')
summary['long_shots_total'] = int(len(ls)); summary['long_shot_winners'] = int(ls.y.sum())
summary['long_shot_winners_in_course_categories'] = int(ls[ls.course_cat != 'Other categories'].y.sum())
lst

# %%
(RES/'eda_summary.json').write_text(json.dumps(summary, indent=2)); summary
