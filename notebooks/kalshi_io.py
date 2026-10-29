"""Shared helpers for reading the course Kalshi data. Credentials come from ../.env (never committed)."""
import os, io, time, hashlib
from pathlib import Path
import pandas as pd, psycopg2, requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

def load_env(path=ROOT / ".env"):
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip())
load_env()

def connect():
    con = psycopg2.connect(os.environ["KALSHI_DB_URL"], connect_timeout=15)
    con.set_session(readonly=True)
    return con

def sql(con, q, params=None):
    with con.cursor() as cur:
        cur.execute(q, params)
        cols = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)

def get_s3(name, timeout=180):
    r = requests.get(f"{os.environ['KALSHI_S3_BASE']}/{name}",
                     auth=(os.environ["KALSHI_USER"], os.environ["KALSHI_PASSWORD"]), timeout=timeout)
    return r

def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()
