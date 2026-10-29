"""Pull markets + events metadata for every slug in the candle parts; resumable, time-budgeted."""
from kalshi_io import *
import glob, sys
budget=float(sys.argv[1]) if len(sys.argv)>1 else 150
OUT=RAW/"meta"; OUT.mkdir(exist_ok=True); t0=time.time()
sl=OUT/"slugs.parquet"
if not sl.exists():
    s=set()
    for f in glob.glob(str(RAW/'candles'/'part-*.parquet')): s|=set(pd.read_parquet(f,columns=['market_slug']).market_slug)
    pd.DataFrame({'slug':sorted(s)}).to_parquet(sl,index=False)
slugs=pd.read_parquet(sl).slug.tolist(); B=5000; con=connect()
Q="""SELECT slug,event_slug,ticker,title,status,result,market_type,start_date,end_date,observed_at,source_updated_at,synced_at,
 raw_payload->>'open_time' open_time, raw_payload->>'close_time' close_time,
 raw_payload->>'expected_expiration_time' expected_expiration_time, raw_payload->>'occurrence_datetime' occurrence_datetime,
 raw_payload->>'settlement_ts' settlement_ts, raw_payload->>'is_provisional' is_provisional,
 raw_payload->>'can_close_early' can_close_early, raw_payload->>'created_time' created_time,
 raw_payload->>'yes_sub_title' yes_sub_title, raw_payload->>'rules_primary' rules_primary
 FROM markets WHERE slug = ANY(%s)"""
for i in range(0,len(slugs),B):
    p=OUT/f"markets-{i//B:04d}.parquet"
    if p.exists(): continue
    if time.time()-t0>budget: break
    df=sql(con,Q,(slugs[i:i+B],)); df.to_parquet(p,index=False)
left=sum(1 for i in range(0,len(slugs),B) if not (OUT/f"markets-{i//B:04d}.parquet").exists())
print("market batches left:",left, "of", -(-len(slugs)//B), f"{time.time()-t0:.0f}s")
if left==0 and not (OUT/"events.parquet").exists():
    ev=sorted(set(pd.concat([pd.read_parquet(f,columns=['event_slug']) for f in glob.glob(str(OUT/'markets-*.parquet'))]).event_slug.dropna()))
    parts=[sql(con,"SELECT slug event_slug,ticker event_ticker,series_ticker,title event_title,category,mutually_exclusive FROM events WHERE slug=ANY(%s)",(ev[j:j+B],)) for j in range(0,len(ev),B)]
    pd.concat(parts).to_parquet(OUT/"events.parquet",index=False); print("events",len(ev))
