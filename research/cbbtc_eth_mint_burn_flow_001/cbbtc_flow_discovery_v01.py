#!/usr/bin/env python3
from __future__ import annotations

import hashlib, io, json, random, urllib.request, zipfile
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec=60

HERE=Path("research/cbbtc_eth_mint_burn_flow_001")
SAMPLE=HERE/"DISCOVERY_FLOW_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
ROWS=HERE/"DISCOVERY_FLOW_PREDICTOR_SAMPLE_ROWS_V0.1.json"
OUT=HERE/"FLOW_DISCOVERY_RESULT_V0.1.json"

sample=json.loads(SAMPLE.read_text())
rows_obj=json.loads(ROWS.read_text())

if sample.get("classification")!="FLOW_PREDICTOR_SAMPLE_PASS":
    raise SystemExit("FLOW_PREDICTOR_SAMPLE_NOT_PASS")
if sample.get("market_returns_opened") is not False:
    raise SystemExit("SAMPLE_BOUNDARY_ALREADY_OPEN")

BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d"
MONTHS=[f"2025-{m:02d}" for m in range(7,13)]

def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read()

def ms_or_us_to_date(v:int)->str:
    # Binance public archives may use millisecond or microsecond timestamps.
    sec=(v/1_000_000) if v>100_000_000_000_000 else (v/1_000)
    return datetime.fromtimestamp(sec,tz=timezone.utc).date().isoformat()

prices={}
archives=[]
for ym in MONTHS:
    name=f"BTCUSDT-1d-{ym}.zip"
    url=f"{BASE}/{name}"
    checksum_url=url+".CHECKSUM"
    blob=fetch(url)
    checksum_blob=fetch(checksum_url).decode().strip()
    expected=checksum_blob.split()[0].lower()
    got=hashlib.sha256(blob).hexdigest().lower()
    if expected!=got:
        raise SystemExit(f"CHECKSUM_MISMATCH:{ym}:{expected}:{got}")
    archives.append({"month":ym,"filename":name,"sha256":got,"checksum_verified":True})
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=z.namelist()
        if len(names)!=1:
            raise SystemExit(f"ZIP_FILE_COUNT:{ym}:{len(names)}")
        raw=z.read(names[0]).decode().strip().splitlines()
        for line in raw:
            cols=line.split(",")
            if len(cols)<6:
                raise SystemExit(f"BAD_KLINE_ROW:{ym}")
            day=ms_or_us_to_date(int(cols[0]))
            if not day.startswith("2025-"):
                raise SystemExit(f"NON_2025_PRICE_OPENED:{day}")
            open_px=Decimal(cols[1])
            if open_px<=0:
                raise SystemExit(f"NONPOSITIVE_OPEN:{day}")
            if day in prices:
                raise SystemExit(f"DUPLICATE_DAY:{day}")
            prices[day]=open_px

# Require complete 2025 H2 daily source.
d=date(2025,7,1)
while d<=date(2025,12,31):
    if d.isoformat() not in prices:
        raise SystemExit("MISSING_PRICE_DAY:"+d.isoformat())
    d+=timedelta(days=1)

events=rows_obj.get("events",[])
if len(events)!=sample.get("transition_event_count"):
    raise SystemExit("EVENT_COUNT_MISMATCH")

def plus(day:str,n:int)->str:
    return (date.fromisoformat(day)+timedelta(days=n)).isoformat()

result_rows=[]
for i,e in enumerate(events):
    t=e["utc_day"]
    if t>"2025-12-29":
        # Predictor evidence remains preserved, but 2026 price access is forbidden.
        continue
    entry_day=plus(t,1)
    exit_day=plus(t,2)
    if entry_day not in prices or exit_day not in prices:
        raise SystemExit("PRIMARY_PRICE_MISSING:"+t)
    entry=prices[entry_day]
    exitp=prices[exit_day]
    raw=(exitp-entry)/entry
    if e["state"]=="POSITIVE_EXTREME":
        signed=raw
    elif e["state"]=="NEGATIVE_EXTREME":
        signed=-raw
    else:
        raise SystemExit("NON_EXTREME_EVENT:"+t)

    sec=None
    if t<="2025-12-27":
        sec_day=plus(t,4)
        if sec_day not in prices:
            raise SystemExit("SECONDARY_PRICE_MISSING:"+t)
        sec_raw=(prices[sec_day]-entry)/entry
        sec=sec_raw if e["state"]=="POSITIVE_EXTREME" else -sec_raw

    result_rows.append({
      "event_index":i,
      "event_day":t,
      "state":e["state"],
      "entry_day":entry_day,
      "exit_day":exit_day,
      "entry_open":format(entry,"f"),
      "exit_open":format(exitp,"f"),
      "raw_return_24h":format(raw,"f"),
      "signed_return_24h":format(signed,"f"),
      "signed_return_72h_diagnostic":None if sec is None else format(sec,"f")
    })

neg=[Decimal(r["signed_return_24h"]) for r in result_rows if r["state"]=="NEGATIVE_EXTREME"]
pos=[Decimal(r["signed_return_24h"]) for r in result_rows if r["state"]=="POSITIVE_EXTREME"]
vals=[Decimal(r["signed_return_24h"]) for r in result_rows]

def mean(xs):
    return sum(xs,Decimal(0))/Decimal(len(xs))

if len(vals)<20 or len(neg)<6 or len(pos)<6:
    classification="DISCOVERY_OUTCOME_INSUFFICIENT_SAMPLE"
    lo=hi=None
else:
    rng=random.Random(20260926)
    boots=[]
    n=len(vals)
    for _ in range(10_000):
        boots.append(mean([vals[rng.randrange(n)] for __ in range(n)]))
    boots.sort()
    lo=boots[max(0,int(0.025*len(boots))-1)]
    hi=boots[min(len(boots)-1,int(0.975*len(boots))-1)]
    passed=mean(vals)>0 and lo>0 and mean(neg)>0 and mean(pos)>0
    classification="FLOW_DISCOVERY_PASS" if passed else "FLOW_DISCOVERY_FAIL"

secondary=[Decimal(r["signed_return_72h_diagnostic"]) for r in result_rows if r["signed_return_72h_diagnostic"] is not None]

out={
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"FLOW_DISCOVERY_V0.1",
  "classification":classification,
  "price_source":{
    "provider":"Binance public historical Spot data",
    "instrument":"BTCUSDT",
    "interval":"1d",
    "months":archives,
    "opened_years":[2025]
  },
  "primary_horizon_hours":24,
  "event_count":len(result_rows),
  "negative_extreme_event_count":len(neg),
  "positive_extreme_event_count":len(pos),
  "pooled_mean_signed_return_24h":None if not vals else format(mean(vals),"f"),
  "negative_mean_signed_return_24h":None if not neg else format(mean(neg),"f"),
  "positive_mean_signed_return_24h":None if not pos else format(mean(pos),"f"),
  "bootstrap":{
    "seed":20260926,
    "resamples":10000,
    "percentile_95_lower":None if lo is None else format(lo,"f"),
    "percentile_95_upper":None if hi is None else format(hi,"f")
  },
  "secondary_72h_diagnostic":{
    "valid_count":len(secondary),
    "mean_signed_return":None if not secondary else format(mean(secondary),"f"),
    "can_rescue_primary":False
  },
  "rows":result_rows,
  "market_returns_opened":True,
  "pnl_opened":False,
  "protected_2026_opened":False,
  "mutation":False,
  "promotion_credit":0
}

OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in out.items() if k!="rows"},indent=2,sort_keys=True))
