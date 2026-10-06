#!/usr/bin/env python3
# SOURCE-SCHEMA ONLY: inspect metrics timestamp cadence. Do not read OI/ratio values.
import csv, io, json, urllib.request, zipfile
from datetime import datetime, timezone

SAMPLES=[
 ("XEMUSDT","2024-12-09"),
 ("REEFUSDT","2025-01-22"),
 ("AIAUSDT","2025-12-11"),
]

def fetch_zip(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabMetricsCadence/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read()

def parse_ts(s):
    s=s.strip()
    if not s: return None
    if s.isdigit():
        n=int(s)
        if n>10**14: n/=1000
        if n>10**11: n/=1000
        return int(n)
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d"):
        try: return int(datetime.strptime(s,fmt).replace(tzinfo=timezone.utc).timestamp()*1000)
        except Exception: pass
    return None

out=[]
for sym,day in SAMPLES:
    url=f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{day}.zip"
    raw=fetch_zip(url)
    z=zipfile.ZipFile(io.BytesIO(raw))
    name=z.namelist()[0]
    text=z.read(name).decode("utf-8-sig","replace")
    rows=list(csv.reader(io.StringIO(text)))
    timestamps=[]
    header=rows[0] if rows else []
    for row in rows[1:] if header and header[0].lower().startswith("create") else rows:
        if not row: continue
        t=parse_ts(row[0])
        if t is not None: timestamps.append(t)
    timestamps=sorted(set(timestamps))
    diffs=[b-a for a,b in zip(timestamps,timestamps[1:])]
    med=None
    if diffs:
        s=sorted(diffs); med=s[len(s)//2]
    out.append({
      "symbol":sym,"day":day,"header":header,
      "row_count":len(timestamps),
      "first_utc":datetime.fromtimestamp(timestamps[0]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z") if timestamps else None,
      "last_utc":datetime.fromtimestamp(timestamps[-1]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z") if timestamps else None,
      "median_interval_seconds":med/1000 if med is not None else None,
      "values_opened":False
    })
print("METRICS_CADENCE_SOURCE_BEGIN")
print(json.dumps(out,indent=2))
print("METRICS_CADENCE_SOURCE_END")
if not out or any(x["row_count"]<2 for x in out):
    raise SystemExit(2)

# trigger registered workflow
