"""Final refresh from the course Kalshi database before access ends (Oct 29, 2026, 11:59pm PT).

Steps (resumable, time-budgeted; rerun until it prints ALL DONE):
  1. Re-pull hourly_candles for 2026-10-26 (00:00-23:59 UTC), in 6-hour parts -> data/raw/_parts/candles_refresh/
     (Oct 27 onward is not needed for the project, decided Oct 28.)
  2. Re-pull market metadata for every slug (old + new) so newly settled markets get results -> data/raw/_parts/meta_refresh/
  3. Re-pull events, then rebuild data/raw/candles/candles-YYYY-MM-DD.parquet for Oct 26+, data/raw/markets.parquet, events.parquet

Usage (from notebooks/):  python refresh_from_db.py 150
"""
import datetime as dt, glob, os, sys, time
from kalshi_io import RAW, connect, sql
import pandas as pd

budget = float(sys.argv[1]) if len(sys.argv) > 1 else 150
t0 = time.time()
over = lambda: time.time() - t0 > budget
CR, MR = RAW / '_parts' / 'candles_refresh', RAW / '_parts' / 'meta_refresh'
CR.mkdir(parents=True, exist_ok=True); MR.mkdir(parents=True, exist_ok=True)
con = connect()
NUM = lambda df: df.assign(**{c: pd.to_numeric(df[c]) for c in df.columns if c.startswith(('yes_', 'price_')) or c in ('volume', 'open_interest')})

# 1 · candles
start = dt.datetime(2026, 10, 26, tzinfo=dt.timezone.utc)
stop = dt.datetime(2026, 10, 27, tzinfo=dt.timezone.utc)
a = start; pending = 0
while a < stop:
    b = a + dt.timedelta(hours=6); p = CR / f"part-{a:%Y-%m-%dT%H}.parquet"
    if not p.exists():
        if over(): pending += 1; a = b; continue
        df = NUM(sql(con, "select * from hourly_candles where end_time >= %s and end_time < %s", (a, b)))
        tmp = p.with_suffix('.tmp'); df.to_parquet(tmp, index=False); tmp.replace(p)
        print(f"candles {a:%m-%d %H}h rows={len(df):,}", flush=True)
    a = b
if pending or over(): print('candles: rerun to continue'); sys.exit()

# 2 · market metadata for every slug
old = pd.read_parquet(RAW / 'markets.parquet', columns=['slug']).slug
new = pd.concat([pd.read_parquet(f, columns=['market_slug']) for f in glob.glob(str(CR / 'part-*.parquet'))]).market_slug
slugs = sorted(set(old) | set(new)); B = 5000
Q = """SELECT slug,event_slug,ticker,title,status,result,market_type,start_date,end_date,observed_at,source_updated_at,synced_at,
 raw_payload->>'open_time' open_time, raw_payload->>'close_time' close_time,
 raw_payload->>'expected_expiration_time' expected_expiration_time, raw_payload->>'occurrence_datetime' occurrence_datetime,
 raw_payload->>'settlement_ts' settlement_ts, raw_payload->>'is_provisional' is_provisional,
 raw_payload->>'can_close_early' can_close_early, raw_payload->>'created_time' created_time,
 raw_payload->>'yes_sub_title' yes_sub_title, raw_payload->>'rules_primary' rules_primary
 FROM markets WHERE slug = ANY(%s)"""
for i in range(0, len(slugs), B):
    p = MR / f"markets-{i // B:04d}.parquet"
    if p.exists(): continue
    if over(): print(f'metadata: {sum(1 for j in range(0, len(slugs), B) if not (MR / f"markets-{j // B:04d}.parquet").exists())} batches left, rerun'); sys.exit()
    sql(con, Q, (slugs[i:i + B],)).to_parquet(p, index=False)
print('metadata batches complete', flush=True)

# 3 · events + rebuild consolidated files
m = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(MR / 'markets-*.parquet')))], ignore_index=True)
ev = sorted(set(m.event_slug.dropna()))
e = pd.concat([sql(con, "SELECT slug event_slug,ticker event_ticker,series_ticker,title event_title,category,mutually_exclusive FROM events WHERE slug=ANY(%s)", (ev[j:j + B],)) for j in range(0, len(ev), B)])
before = pd.read_parquet(RAW / 'markets.parquet', columns=['slug', 'status', 'result'])
m.to_parquet(RAW / 'markets.parquet', index=False, compression='zstd'); e.to_parquet(RAW / 'events.parquet', index=False, compression='zstd')
parts = sorted(glob.glob(str(CR / 'part-*.parquet')))
for day in sorted({os.path.basename(p)[5:15] for p in parts}):
    df = pd.concat([pd.read_parquet(p) for p in parts if os.path.basename(p)[5:15] == day], ignore_index=True)
    df.to_parquet(RAW / 'candles' / f'candles-{day}.parquet', index=False, compression='zstd')
    print(f'rebuilt candles-{day}: {len(df):,} rows')
j = before.merge(m[['slug', 'status', 'result']], on='slug', how='right', suffixes=('_old', ''))
print('markets now', len(m), '| newly finalized yes/no:', int(((j.status == 'finalized') & j.result.isin(['yes', 'no']) & ~((j.status_old == 'finalized') & j.result_old.isin(['yes', 'no']))).sum()))
print('ALL DONE')
