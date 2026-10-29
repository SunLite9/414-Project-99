# %% [markdown]
# # 01 · Build the full-population entry dataset
# STATS 414 midterm, "Almost Certain?". Turns the raw Kalshi hourly candles (all markets, Oct 8–27 2026)
# and market metadata into one row per market: the first observed high-confidence YES quote.
#
# Inputs: `data/raw/candles/candles-YYYY-MM-DD.parquet` (one file per UTC day), `data/raw/markets.parquet`, `data/raw/events.parquet`.
# They were pulled with `pull_candles.py` / `pull_meta.py` before course database access ended (Oct 29, 2026).
# Output: `data/processed/midterm_entries.parquet` (+ `.csv`) and `results/midterm/funnel.csv`.

# %%
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
RAW, PROC, RES = ROOT/'data/raw', ROOT/'data/processed', ROOT/'results/midterm'
PROC.mkdir(parents=True, exist_ok=True); RES.mkdir(parents=True, exist_ok=True)
VAL_START, TEST_START = pd.Timestamp('2026-10-15', tz='UTC'), pd.Timestamp('2026-10-20', tz='UTC')
funnel = []
def stage(name, df, unit='markets'):
    n_m = df['market_slug'].nunique() if 'market_slug' in df else len(df)
    funnel.append({'stage': name, 'rows': len(df), 'markets': n_m}); print(f'{name:<60} rows={len(df):>10,} markets={n_m:>8,}')

# %% [markdown]
# ## Market metadata and labels
# Keep binary markets with a final `yes`/`no` result. `close_time` is the *actual* close (settlement follows it by a
# median of 3 minutes), so it is used only to require that an entry precedes the close, never as a feature.
# The scheduled `occurrence_datetime` is used for the time-to-event feature.

# %%
mcols = ['slug','event_slug','title','status','result','close_time','occurrence_datetime','open_time','settlement_ts']
meta = pd.read_parquet(RAW/'markets.parquet', columns=mcols)
for c in ['close_time','occurrence_datetime','open_time','settlement_ts']:
    meta[c] = pd.to_datetime(meta[c], utc=True, errors='coerce', format='mixed')
events = pd.read_parquet(RAW/'events.parquet')
meta = meta.merge(events[['event_slug','category','event_title','series_ticker']], on='event_slug', how='left')
meta['category'] = meta['category'].fillna('Unknown')
meta['event_size'] = meta.groupby('event_slug')['slug'].transform('size')   # markets of this event that have candles in our Oct 8-27 pull (a proxy for event size)
labeled = meta[meta.status.eq('finalized') & meta.result.isin(['yes','no'])].rename(columns={'slug':'market_slug'})
labeled['y_win'] = labeled.result.eq('yes').astype(int)
print(f'markets with candles: {len(meta):,}   finalized yes/no: {len(labeled):,}')

# %% [markdown]
# ## Candles → quotes
# Read every 6-hour part, keep only labeled markets and hours before the market closed.

# %%
ccols = ['market_slug','end_time','observed_at','yes_bid_close','yes_ask_close','volume','open_interest']
keep = set(labeled.market_slug); close = labeled.set_index('market_slug')['close_time']
parts = []
for f in sorted(glob.glob(str(RAW/'candles/candles-*.parquet'))):
    p = pd.read_parquet(f, columns=ccols)
    p = p[p.market_slug.isin(keep)]
    if len(p): parts.append(p)
c = pd.concat(parts, ignore_index=True); del parts
c['market_slug'] = c['market_slug'].astype('category')
stage('Hourly candles for finalized yes/no markets', c)
c = c.drop_duplicates(['market_slug','end_time'], keep='last')
c = c[c.end_time.values < close.reindex(c.market_slug.astype(str)).values]
stage('Candle ends before the market closed', c)
c['mid'] = (c.yes_bid_close + c.yes_ask_close) / 2
c['spread'] = c.yes_ask_close - c.yes_bid_close
c['quote_ok'] = (c.yes_bid_close > 0) & (c.yes_bid_close <= c.yes_ask_close) & (c.yes_ask_close < 1)

# %% [markdown]
# ## Entry rule
# First observed candle with ask 90–99¢, midpoint ≥ 90¢ and spread ≤ 5¢ (a high ask over a low bid is not consensus).

# %%
hi = c[c.quote_ok & c.yes_ask_close.between(0.90, 0.99)]
stage('Valid two-sided quote with ask 90–99¢', hi)
hi = hi[(hi.mid >= 0.90) & (hi.spread <= 0.05)]
stage('Midpoint ≥ 90¢ and spread ≤ 5¢', hi)
entries = hi.sort_values(['market_slug','end_time']).groupby('market_slug', observed=True).head(1).copy()
entries['market_slug'] = entries.market_slug.astype(str)
stage('First observed eligible quote per market', entries)

# %% [markdown]
# ## Trailing features (only information from before the entry candle)
# Within the 6 hours before entry: the most recent valid quote's midpoint, total recorded volume, and how many hourly
# candles exist (gaps are common, so "previous row" is never assumed to be "previous hour").

# %%
c['market_slug'] = c.market_slug.astype(str)
w = c[c.market_slug.isin(set(entries.market_slug))].merge(entries[['market_slug','end_time']].rename(columns={'end_time':'t0'}), on='market_slug')
w = w[(w.end_time < w.t0) & (w.end_time >= w.t0 - pd.Timedelta(hours=6))]
prev_q = w[w.quote_ok].sort_values('end_time').groupby('market_slug').tail(1).set_index('market_slug')
agg = w.groupby('market_slug').agg(prior_candles_6h=('end_time','size'), volume_prev_6h=('volume','sum'))
entries = entries.set_index('market_slug')
entries['prev_mid'] = prev_q['mid']
entries['hours_since_prev_quote'] = (entries.end_time - prev_q['end_time']).dt.total_seconds() / 3600
entries = entries.join(agg)
entries[['prior_candles_6h','volume_prev_6h']] = entries[['prior_candles_6h','volume_prev_6h']].fillna(0)
entries = entries.reset_index()
del c, w

# %%
d = entries.merge(labeled[['market_slug','event_slug','title','category','event_title','series_ticker','event_size','y_win',
                           'close_time','occurrence_datetime','open_time','settlement_ts']], on='market_slug', how='left')
d = d.rename(columns={'end_time':'entry_time','yes_bid_close':'bid','yes_ask_close':'ask','mid':'midpoint'})
d['mid_change_6h'] = d.midpoint - d.prev_mid                      # NaN when no earlier quote in 6h
d['fresh_cross'] = (d.prev_mid < 0.90).astype(float).where(d.prev_mid.notna())
d['log_volume'] = np.log1p(d.volume.clip(lower=0)); d['volume_missing'] = d.volume.isna().astype(int)
d['log_open_interest'] = np.log1p(d.open_interest.clip(lower=0))
d['log_volume_prev_6h'] = np.log1p(d.volume_prev_6h.clip(lower=0))
d['hours_to_event'] = (d.occurrence_datetime - d.entry_time).dt.total_seconds() / 3600   # scheduled, known in advance
d['hours_since_open'] = (d.entry_time - d.open_time).dt.total_seconds() / 3600
d['log_event_size'] = np.log1p(d.event_size)
d['collection_lag_h'] = (d.observed_at - d.entry_time).dt.total_seconds() / 3600
d['observed_after_close'] = (d.observed_at >= d.close_time).astype(int)
top = ['Sports','Economics','Financials','Commodities','Crypto','Climate and Weather','Elections','Politics','Entertainment']
d['category_group'] = np.where(d.category.isin(top), d.category, 'Other')
d['price_band'] = pd.cut(d.ask, [0.895, 0.949, 0.979, 0.991], labels=['90–94¢','95–97¢','98–99¢']).astype(str)

# %% [markdown]
# ## Chronological splits with event separation and label purging
# Train: entries before Oct 15 · validation: Oct 15–19 · test: Oct 20 onward (UTC), the same cut-offs as the team's
# first version. An event whose markets fall in two splits is dropped, and a training (validation) market is dropped if it
# settled after the validation (test) start, because its label was not yet known at that cut-off.

# %%
d['split'] = np.select([d.entry_time < VAL_START, d.entry_time < TEST_START], ['train','validation'], 'test')
n_split = d.groupby('event_slug').split.nunique()
d = d[d.event_slug.map(n_split).eq(1)]
stage('Remove events spanning two splits', d)
late = ((d.split == 'train') & (d.settlement_ts >= VAL_START)) | ((d.split == 'validation') & (d.settlement_ts >= TEST_START))
d = d[~late].copy()
stage('Purge labels settled after their split cut-off', d)
print(d.groupby('split').agg(markets=('market_slug','size'), events=('event_slug','nunique'), losses=('y_win', lambda s: int((1-s).sum()))))

# %%
d.to_parquet(PROC/'midterm_entries.parquet', index=False)
d.drop(columns=['title','event_title']).to_csv(PROC/'midterm_entries.csv', index=False)
pd.DataFrame(funnel).to_csv(RES/'funnel.csv', index=False)
print('saved', len(d), 'entries')
