#!/usr/bin/env python3
import csv, io, json, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
START=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2025,12,31,23,tzinfo=timezone.utc).timestamp()*1000)

def months():
    y,m=2021,1
    while (y,m)<=(2025,12):
        yield y,m
        m+=1
        if m==13:y+=1;m=1

ts=set()
for y,m in months():
    ym=f"{y:04d}-{m:02d}"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/SOLUSDT/1h/SOLUSDT-1h-{ym}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CoverageProbe/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r: body=r.read()
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        text=zf.read(zf.namelist()[0]).decode("utf-8-sig")
    for q in csv.reader(io.StringIO(text)):
        if not q: continue
        try:t=int(q[0])
        except ValueError:continue
        if t>10**14:t//=1000
        if START<=t<=END: ts.add(t)

expected=range(START,END+1,3600000)
missing=[t for t in expected if t not in ts]
ranges=[]
if missing:
    a=p=missing[0]
    for t in missing[1:]:
        if t==p+3600000:
            p=t
        else:
            ranges.append((a,p))
            a=p=t
    ranges.append((a,p))

fmt=lambda t: datetime.fromtimestamp(t/1000,tz=timezone.utc).isoformat()
out={
  "probe":"SOLUSDT_1H_COVERAGE_GAP_PROBE_V0.1",
  "economic_outcomes_opened":False,
  "first_available":fmt(min(ts)) if ts else None,
  "last_available":fmt(max(ts)) if ts else None,
  "present_hours":len(ts),
  "missing_hours":len(missing),
  "missing_ranges":[{"start":fmt(a),"end":fmt(b),"hours":((b-a)//3600000)+1} for a,b in ranges],
}
path=EVID/"SOLUSDT_1H_COVERAGE_GAP_PROBE_V0.1.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
