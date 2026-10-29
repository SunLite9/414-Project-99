"""Pull hourly_candles in 6-hour parts; resumable; stops after a time budget (seconds, argv[1])."""
from kalshi_io import *
import datetime as dt, sys
budget=float(sys.argv[1]) if len(sys.argv)>1 else 150
OUT=RAW/"candles"; con=connect(); t0=time.time()
start=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc); end=dt.datetime(2026,10,27,6,tzinfo=dt.timezone.utc)
a=start; done=0
while a<end:
    b=a+dt.timedelta(hours=6); p=OUT/f"part-{a:%Y-%m-%dT%H}.parquet"
    if not p.exists():
        if time.time()-t0>budget: break
        t=time.time()
        df=sql(con,"select * from hourly_candles where end_time >= %s and end_time < %s",(a,b))
        for c in df.columns:
            if c.startswith(('yes_','price_')) or c in ('volume','open_interest'): df[c]=pd.to_numeric(df[c])
        tmp=p.with_suffix(".tmp"); df.to_parquet(tmp,index=False); tmp.rename(p)
        print(f"{a:%m-%d %H}h rows={len(df):,} {time.time()-t:.0f}s",flush=True)
    else: done+=1
    a=b
left=sum(1 for i in range(int((end-start)/dt.timedelta(hours=6))) if not (OUT/f"part-{start+dt.timedelta(hours=6*i):%Y-%m-%dT%H}.parquet").exists())
print("remaining parts:",left)
