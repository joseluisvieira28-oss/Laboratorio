#!/usr/bin/env python3
"""DCV-001 metrics timestamp duplication diagnostic — source structure only."""
from __future__ import annotations
import csv, io, json, urllib.request, zipfile
from collections import Counter
from datetime import datetime, timezone

BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
DAYS=("2021-01-01","2021-01-03","2021-01-22","2021-06-15")
UA="Crypto-Lab-DCV001-Metrics-Diag/0.1"

def req(url):
    r=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(r,timeout=60) as x:
        return x.read()

def to_ms(v):
    v=v.strip()
    try:
        x=float(v)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except ValueError: pass
    dt=datetime.fromisoformat(v.replace("Z","+00:00"))
    if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp()*1000)

out={"lab_id":"DCV-001","diagnostic":"METRICS_TIMESTAMP_DUPLICATION_SOURCE_ONLY",
     "economic_values_reported":False,"outcomes_opened":False,"days":[]}
for d in DAYS:
    url=f"{BASE}/BTCUSDT-metrics-{d}.zip"
    raw=req(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.endswith(".csv")]
        text=z.read(names[0]).decode("utf-8-sig")
    rows=[r for r in csv.reader(io.StringIO(text)) if r]
    h=[x.strip() for x in rows[0]]
    ti=h.index("create_time")
    si=h.index("symbol")
    body=rows[1:]
    ts=[to_ms(r[ti]) for r in body]
    c=Counter(ts)
    dup={k:v for k,v in c.items() if v>1}
    final=max(ts)
    # Structural-only equality check: compare whole raw CSV row bytes after redacting economic fields.
    # We intentionally do NOT reveal any economic field values.
    same_final=[r for r in body if to_ms(r[ti])==final]
    out["days"].append({
        "day":d,
        "header":h,
        "row_count":len(body),
        "unique_create_time_count":len(c),
        "duplicate_create_time_count":sum(v-1 for v in c.values() if v>1),
        "duplicate_timestamp_group_count":len(dup),
        "max_duplicate_multiplicity":max(c.values()),
        "final_create_time_multiplicity":len(same_final),
        "all_symbols_btcusdt":all(r[si].strip()=="BTCUSDT" for r in body),
        "duplicate_groups_exact_row_identical":all(
            len({tuple(r) for r in body if to_ms(r[ti])==t})==1
            for t,v in c.items() if v>1
        ),
        "conflicting_duplicate_group_count":sum(
            1 for t,v in c.items()
            if v>1 and len({tuple(r) for r in body if to_ms(r[ti])==t})>1
        ),
        "economic_values_reported":False,
    })
print(json.dumps(out,sort_keys=True))
