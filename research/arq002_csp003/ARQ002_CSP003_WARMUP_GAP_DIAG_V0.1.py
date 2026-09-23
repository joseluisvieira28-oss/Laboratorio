#!/usr/bin/env python3
import csv,io,json,urllib.request,zipfile
from datetime import datetime,timezone
BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2021-12-31.zip"
UTC=timezone.utc
req=urllib.request.Request(BASE,headers={"User-Agent":"Crypto-Lab-ARQ002-CSP003-WarmupGap/0.1"})
with urllib.request.urlopen(req,timeout=90) as x: raw=x.read()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    n=[n for n in z.namelist() if n.endswith(".csv")][0]
    rows=[r for r in csv.reader(io.StringIO(z.read(n).decode("utf-8-sig"))) if r]
h=[x.strip() for x in rows[0]];ti=h.index("create_time")
def ms(v):
    s=v.strip()
    try:
        x=float(s)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except:pass
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:d=d.replace(tzinfo=UTC)
    return int(d.timestamp()*1000)
def iso(t):return datetime.fromtimestamp(t/1000,tz=UTC).isoformat().replace("+00:00","Z")
obs={ms(r[ti]) for r in rows[1:]}
lo=int(datetime(2021,12,31,tzinfo=UTC).timestamp()*1000)
exp={lo+i*300000 for i in range(288)}
missing=sorted(exp-obs)
out={"lab_id":"ARQ-002-CSP-003","diagnostic":"WARMUP_METRICS_GAP_SOURCE_ONLY",
     "observed_slots":len(obs),"missing_slots":[iso(x) for x in missing],
     "missing_count":len(missing),"economic_values_opened":False,"outcomes_opened":False}
print(json.dumps(out,sort_keys=True))
