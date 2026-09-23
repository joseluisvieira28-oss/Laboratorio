#!/usr/bin/env python3
"""ARQ-002 source-only diagnostics for incomplete Binance metrics days."""
from __future__ import annotations
import csv,hashlib,io,json,re,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
DAYS=("2024-02-16","2024-10-28")
UA="Crypto-Lab-ARQ002-MetricsGapDiag/0.1"

def req(u):
    r=urllib.request.Request(u,headers={"User-Agent":UA})
    with urllib.request.urlopen(r,timeout=90) as x:return x.read()
def to_ms(v):
    s=v.strip()
    try:
        x=float(s)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except:pass
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
    return int(d.timestamp()*1000)
def iso(x):return datetime.fromtimestamp(x/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")

out={"lab_id":"ARQ-002-CSP-001","diagnostic":"METRICS_GAP_SOURCE_ONLY","days":[],"economic_values_reported":False,"outcomes_opened":False}
for ds in DAYS:
    url=f"{BASE}/BTCUSDT-metrics-{ds}.zip"
    raw=req(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.endswith(".csv")]
        txt=z.read(names[0]).decode("utf-8-sig")
    rows=[r for r in csv.reader(io.StringIO(txt)) if r]
    h=[x.strip() for x in rows[0]]
    ti=h.index("create_time")
    body=rows[1:]
    ts=sorted(set(to_ms(r[ti]) for r in body))
    lo=to_ms(ds+"T00:00:00Z")
    exp=[lo+i*300000 for i in range(288)]
    missing=[x for x in exp if x not in set(ts)]
    runs=[]
    if missing:
        start=prev=missing[0]
        for x in missing[1:]:
            if x==prev+300000: prev=x
            else:
                runs.append((start,prev))
                start=prev=x
        runs.append((start,prev))
    out["days"].append({
        "date":ds,"raw_rows":len(body),"unique_timestamps":len(ts),
        "first_timestamp_utc":iso(ts[0]),"last_timestamp_utc":iso(ts[-1]),
        "missing_count":len(missing),
        "missing_runs":[{"start_utc":iso(a),"end_utc":iso(b),"slots":int((b-a)/300000)+1} for a,b in runs],
        "timestamps_exact_5m_grid":all((x-lo)%300000==0 for x in ts),
        "duplicate_timestamp_rows":len(body)-len(ts),
        "economic_values_reported":False
    })
print(json.dumps(out,sort_keys=True))
