#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — FUNDING MARK GAP PROBE V0.1

SOURCE-ONLY. ZERO economic outcomes.
Examines three frozen funding timestamps where the funding record markPrice is
empty and the monthly 1h markPriceKline map lacks the exact hour.
"""
from __future__ import annotations
import csv, io, json, hashlib, urllib.request, urllib.parse, zipfile
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
HOST="https://www.binance.com"
HOUR=3_600_000

CASES=[
    {"symbol":"ETHUSDT","ts":1664668800000,"date":"2022-10-02","month":"2022-10"},
    {"symbol":"SOLUSDT","ts":1625097600000,"date":"2021-07-01","month":"2021-07"},
    {"symbol":"BNBUSDT","ts":1625097600000,"date":"2021-07-01","month":"2021-07"},
]

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-MarkGapProbe/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:
        return r.read(),getattr(r,"status",200)

def parse_mark_zip(body):
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        names=zf.namelist()
        if len(names)!=1:
            raise RuntimeError(f"unexpected zip members {names}")
        text=zf.read(names[0]).decode("utf-8-sig")
    rows={}
    for q in csv.reader(io.StringIO(text)):
        if not q: continue
        try:t=int(q[0])
        except ValueError:continue
        if t>10**14:t//=1000
        rows[t]={
            "open":float(q[1]),"high":float(q[2]),"low":float(q[3]),"close":float(q[4]),
        }
    return rows

def funding_probe(symbol,ts):
    qs=urllib.parse.urlencode({
        "symbol":symbol,
        "startTime":ts-2000,
        "endTime":ts+2000,
        "limit":10,
    })
    url=HOST+"/fapi/v1/fundingRate?"+qs
    raw,status=get(url)
    arr=json.loads(raw.decode())
    return {
        "url":url,"status":status,"sha256":hashlib.sha256(raw).hexdigest(),
        "records":arr,
    }

out={
    "lab":"BTC-CONVEX-TREND-CAPTURE-001",
    "probe":"FUNDING_MARK_GAP_PROBE_V0.1",
    "role":"SOURCE_ONLY_NO_ECONOMIC_OUTCOMES",
    "cases":[],
}
for c in CASES:
    s=c["symbol"]; ts=c["ts"]
    monthly_url=f"https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{s}/1h/{s}-1h-{c['month']}.zip"
    daily_url=f"https://data.binance.vision/data/futures/um/daily/markPriceKlines/{s}/1h/{s}-1h-{c['date']}.zip"

    rec={"symbol":s,"target_ts":ts,"target_iso":datetime.fromtimestamp(ts/1000,tz=timezone.utc).isoformat()}
    try:
        mb,ms=get(monthly_url); mr=parse_mark_zip(mb)
        rec["monthly"]={
            "url":monthly_url,"status":ms,"sha256":hashlib.sha256(mb).hexdigest(),
            "row_count":len(mr),"target_present":ts in mr,
            "target":mr.get(ts),
            "neighbor_hours":{
                str(t):mr.get(t) for t in [ts-2*HOUR,ts-HOUR,ts,ts+HOUR,ts+2*HOUR]
            },
        }
    except Exception as e:
        rec["monthly"]={"url":monthly_url,"error":repr(e)}

    try:
        db,ds=get(daily_url); dr=parse_mark_zip(db)
        rec["daily"]={
            "url":daily_url,"status":ds,"sha256":hashlib.sha256(db).hexdigest(),
            "row_count":len(dr),"target_present":ts in dr,
            "target":dr.get(ts),
            "neighbor_hours":{
                str(t):dr.get(t) for t in [ts-HOUR,ts,ts+HOUR]
            },
        }
    except Exception as e:
        rec["daily"]={"url":daily_url,"error":repr(e)}

    try:
        rec["funding"]=funding_probe(s,ts)
    except Exception as e:
        rec["funding"]={"error":repr(e)}

    rec["daily_can_resolve_exact_gap"]=bool(rec.get("daily",{}).get("target_present"))
    out["cases"].append(rec)

out["all_daily_exact_resolutions"]=all(x["daily_can_resolve_exact_gap"] for x in out["cases"])
p=EVID/"FUNDING_MARK_GAP_PROBE_V0.1.json"
p.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps({
    "probe":out["probe"],
    "all_daily_exact_resolutions":out["all_daily_exact_resolutions"],
    "cases":[{
        "symbol":x["symbol"],
        "target_iso":x["target_iso"],
        "monthly_target_present":x.get("monthly",{}).get("target_present"),
        "daily_target_present":x.get("daily",{}).get("target_present"),
        "daily_target":x.get("daily",{}).get("target"),
        "funding_records":x.get("funding",{}).get("records"),
        "monthly_error":x.get("monthly",{}).get("error"),
        "daily_error":x.get("daily",{}).get("error"),
        "funding_error":x.get("funding",{}).get("error"),
    } for x in out["cases"]]
},indent=2))
print("WROTE",p)
if not out["all_daily_exact_resolutions"]:
    raise SystemExit("SOURCE_BLOCKED: one or more daily markPrice gaps unresolved")
