"""Download every available Kalshi order-book hour (events-* deltas and snap-* snapshots). Resumable.

Credentials come from ../.env (KALSHI_S3_BASE, KALSHI_USER, KALSHI_PASSWORD); never hard-code them.
Usage (from notebooks/):  python pull_orderbook.py ../data/raw/orderbook
"""
import datetime as dt, json, os, sys
from concurrent.futures import ThreadPoolExecutor
import requests
import kalshi_io  # loads ../.env into os.environ

OUT = sys.argv[1]
BASE = os.environ['KALSHI_S3_BASE']
AUTH = (os.environ['KALSHI_USER'], os.environ['KALSHI_PASSWORD'])
os.makedirs(OUT, exist_ok=True)
hours = [dt.datetime(2026, 9, 28) + dt.timedelta(hours=i) for i in range(24 * 32)]


def get(name):
    p = os.path.join(OUT, name)
    if os.path.exists(p):
        return name, 'cached', os.path.getsize(p)
    err = ''
    for _ in range(3):
        try:
            r = requests.get(f"{BASE}/{name}", auth=AUTH, timeout=180)
            if r.status_code == 403:          # hour not published
                return name, 'absent', 0
            r.raise_for_status()
            tmp = p + '.tmp'
            with open(tmp, 'wb') as f:
                f.write(r.content)
            os.replace(tmp, p)
            return name, 'ok', len(r.content)
        except Exception as e:  # retry transient network errors
            err = str(e)
    return name, 'error: ' + err[:80], 0


names = [f"{k}-{h:%Y-%m-%dT%H}.parquet" for h in hours for k in ("events", "snap")]
with ThreadPoolExecutor(12) as ex:
    res = list(ex.map(get, names))
got = [r for r in res if r[1] in ('ok', 'cached')]
bad = [r for r in res if r[1].startswith('error')]
json.dump({'checked_hours': len(hours), 'files': len(got), 'bytes': sum(r[2] for r in got), 'errors': bad},
          open(os.path.join(OUT, '_download_report.json'), 'w'), indent=1)
print('files', len(got), 'GB', round(sum(r[2] for r in got) / 1e9, 2), 'errors', len(bad))
