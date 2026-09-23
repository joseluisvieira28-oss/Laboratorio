#!/usr/bin/env python3
"""DCV-001 mark-price coverage diagnostic — timestamps only, no price values."""
from __future__ import annotations
import csv, io, json, urllib.request, zipfile
from datetime import datetime, timezone, timedelta

BASE="https://data.binance.vision/data/futures/um/monthly/markPriceKlines/BTCUSDT/1h"
UA="Crypto-Lab-DCV001-MarkCoverageDiag/0.1"

def req(url):
    r=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(r,timeout=60) as x:
        return x.read()

def to_ms(v):
    x=float(v)
    if x>1e14:return int(x/1000)
    if x>1e11:return int(x)
    return int(x*1000)

ts=[]
for y in (2021,2022,2023):
    for m in range(1,13):
        ym=f"{y:04d}-{m:02d}"
        url=f"{BASE}/BTCUSDT-1h-{ym}.zip"
        raw=req(url)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=[n for n in z.namelist() if n.endswith(".csv")]
            rows=[r for r in csv.reader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))) if r]
        body=rows
        try: to_ms(rows[0][0])
        except Exception: body=rows[1:]
        ts.extend(to_ms(r[0]) for r in body)

ts=sorted(set(ts))
start=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
end=int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp()*1000)
hour=3600000
expected=list(range(start,end,hour))
present=set(ts)
missing=[x for x in expected if x not in present]

runs=[]
if missing:
    a=missing[0]; prev=missing[0]
    for x in missing[1:]:
        if x==prev+hour:
            prev=x
        else:
            runs.append((a,prev))
            a=prev=x
    runs.append((a,prev))

fmt=lambda ms: datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")
out={
  "lab_id":"DCV-001",
  "diagnostic":"MARK_1H_TIMESTAMP_COVERAGE_SOURCE_ONLY",
  "economic_values_reported":False,
  "outcomes_opened":False,
  "present_unique_hours":len(ts),
  "expected_hours":len(expected),
  "missing_hours":len(missing),
  "first_present_utc":fmt(ts[0]),
  "last_present_utc":fmt(ts[-1]),
  "missing_run_count":len(runs),
  "missing_runs":[
      {"start_utc":fmt(a),"end_utc":fmt(b),"hours":int((b-a)//hour+1)}
      for a,b in runs
  ],
  "internal_missing_hours_after_first_present":sum(1 for x in missing if x>=ts[0]),
  "protected_2025_accessed":False,
  "protected_2026_accessed":False,
}
print(json.dumps(out,sort_keys=True))
