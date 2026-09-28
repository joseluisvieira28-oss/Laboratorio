#!/usr/bin/env python3
from __future__ import annotations

import hashlib, io, json, random, urllib.request, zipfile
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec=60

ART=Path("artifacts/cbbtc_forward")
CENSUS=ART/"CBBTC_FORWARD_CENSUS_RECEIPT_V0.1.json"
DAILY=ART/"CBBTC_FORWARD_DAILY_FLOW_V0.1.json"
EVENTS_OUT=ART/"CBBTC_FORWARD_EVENT_LEDGER_V0.1.json"
STATUS_OUT=ART/"CBBTC_FORWARD_STATUS_V0.1.json"
RESULT_OUT=ART/"CBBTC_FORWARD_RESULT_V0.1.json"

Q10_NUM=-18316281339
Q10_DEN=1601692985627
Q90_NUM=35266522085
Q90_DEN=1057456895899

FIRST_EVENT_DAY="2026-09-30"
MIN_TOTAL=20
MIN_EACH=6

if not CENSUS.exists():
    raise SystemExit("FORWARD_CENSUS_RECEIPT_MISSING")
census=json.loads(CENSUS.read_text())
if census.get("classification")=="FORWARD_WAITING_BOUNDARY":
    status={
      "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
      "stage":"FORWARD_POST_H1_V0.1",
      "classification":"FORWARD_WAITING_BOUNDARY",
      "market_returns_opened":False,
      "pnl_opened":False,
      "promotion_credit":0
    }
    STATUS_OUT.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps(status,indent=2,sort_keys=True))
    raise SystemExit(0)

if census.get("classification")!="FORWARD_PREDICTOR_CENSUS_PASS":
    raise SystemExit("FORWARD_PREDICTOR_CENSUS_NOT_PASS")
if not DAILY.exists():
    raise SystemExit("FORWARD_DAILY_FLOW_MISSING")

days=json.loads(DAILY.read_text()).get("days",[])
if not days or days[0].get("utc_day")!="2026-09-29":
    raise SystemExit("FORWARD_BOUNDARY_DAY_MISMATCH")

def classify(row):
    prior=int(row["prior_supply_raw"])
    net=int(row["net_mint_minus_burn_raw"])
    if prior<=0:
        raise SystemExit("INVALID_PRIOR_SUPPLY:"+row["utc_day"])
    if net*Q10_DEN <= Q10_NUM*prior:
        return "NEGATIVE_EXTREME"
    if net*Q90_DEN >= Q90_NUM*prior:
        return "POSITIVE_EXTREME"
    return "NEUTRAL"

states={r["utc_day"]:classify(r) for r in days}
ordered=[r["utc_day"] for r in days]
events=[]
for i,day in enumerate(ordered):
    if day<FIRST_EVENT_DAY:
        continue
    prev_day=(date.fromisoformat(day)-timedelta(days=1)).isoformat()
    if prev_day not in states:
        raise SystemExit("MISSING_PREDECESSOR:"+day)
    st=states[day]
    prev=states[prev_day]
    if st=="NEGATIVE_EXTREME" and prev!="NEGATIVE_EXTREME":
        events.append({"event_day":day,"state":st})
    elif st=="POSITIVE_EXTREME" and prev!="POSITIVE_EXTREME":
        events.append({"event_day":day,"state":st})

neg=[e for e in events if e["state"]=="NEGATIVE_EXTREME"]
pos=[e for e in events if e["state"]=="POSITIVE_EXTREME"]
sample_ready=len(events)>=MIN_TOTAL and len(neg)>=MIN_EACH and len(pos)>=MIN_EACH

ART.mkdir(parents=True,exist_ok=True)
EVENTS_OUT.write_text(json.dumps({
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"FORWARD_EVENT_LEDGER_V0.1",
  "prospective_anchor_day":"2026-09-29",
  "first_event_eligible_day":FIRST_EVENT_DAY,
  "thresholds":{
    "q10":{"numerator":str(Q10_NUM),"denominator":str(Q10_DEN)},
    "q90":{"numerator":str(Q90_NUM),"denominator":str(Q90_DEN)}
  },
  "events":events
},indent=2,sort_keys=True)+"\n")

status={
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"FORWARD_POST_H1_V0.1",
  "classification":"FORWARD_SAMPLE_READY_FOR_OUTCOME" if sample_ready else "FORWARD_COLLECTING_INSUFFICIENT_SAMPLE",
  "transition_event_count":len(events),
  "negative_extreme_event_count":len(neg),
  "positive_extreme_event_count":len(pos),
  "required_total":MIN_TOTAL,
  "required_each_tail":MIN_EACH,
  "market_returns_opened":False,
  "pnl_opened":False,
  "promotion_credit":0
}
STATUS_OUT.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
print(json.dumps(status,indent=2,sort_keys=True))

if not sample_ready:
    raise SystemExit(0)

# Only after the frozen 20/6/6 gate may forward BTC outcomes be opened.
today=datetime.now(timezone.utc).date()
resolved=[e for e in events if date.fromisoformat(e["event_day"])+timedelta(days=2) < today]
rneg=[e for e in resolved if e["state"]=="NEGATIVE_EXTREME"]
rpos=[e for e in resolved if e["state"]=="POSITIVE_EXTREME"]
if len(resolved)<MIN_TOTAL or len(rneg)<MIN_EACH or len(rpos)<MIN_EACH:
    status["classification"]="FORWARD_SAMPLE_READY_OUTCOME_RESOLUTION_PENDING"
    STATUS_OUT.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps(status,indent=2,sort_keys=True))
    raise SystemExit(0)

BASE="https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d"

def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CBBTC-Forward/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read()

def fetch_open(day:str)->tuple[Decimal,dict]:
    name=f"BTCUSDT-1d-{day}.zip"
    url=f"{BASE}/{name}"
    blob=fetch(url)
    checksum=fetch(url+".CHECKSUM").decode().strip().split()[0].lower()
    got=hashlib.sha256(blob).hexdigest().lower()
    if checksum!=got:
        raise SystemExit(f"FORWARD_CHECKSUM_MISMATCH:{day}")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=z.namelist()
        if len(names)!=1:
            raise SystemExit(f"FORWARD_ZIP_FILE_COUNT:{day}")
        rows=z.read(names[0]).decode().strip().splitlines()
        if len(rows)!=1:
            raise SystemExit(f"FORWARD_DAILY_ROW_COUNT:{day}:{len(rows)}")
        cols=rows[0].split(",")
        if len(cols)<6:
            raise SystemExit(f"FORWARD_BAD_KLINE_ROW:{day}")
        px=Decimal(cols[1])
        if px<=0:
            raise SystemExit(f"FORWARD_NONPOSITIVE_OPEN:{day}")
    return px,{"day":day,"filename":name,"sha256":got,"checksum_verified":True}

needed=set()
for e in resolved:
    d=date.fromisoformat(e["event_day"])
    needed.add((d+timedelta(days=1)).isoformat())
    needed.add((d+timedelta(days=2)).isoformat())

prices={}
archives=[]
for day in sorted(needed):
    try:
        px,rec=fetch_open(day)
    except Exception as ex:
        status["classification"]="FORWARD_OUTCOME_SOURCE_PENDING"
        status["source_pending_day"]=day
        status["source_pending_error"]=str(ex)[:300]
        STATUS_OUT.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
        print(json.dumps(status,indent=2,sort_keys=True))
        raise SystemExit(0)
    prices[day]=px
    archives.append(rec)

rows=[]
for i,e in enumerate(resolved):
    d=date.fromisoformat(e["event_day"])
    entry_day=(d+timedelta(days=1)).isoformat()
    exit_day=(d+timedelta(days=2)).isoformat()
    entry=prices[entry_day]
    exitp=prices[exit_day]
    raw=(exitp-entry)/entry
    signed=raw if e["state"]=="POSITIVE_EXTREME" else -raw
    rows.append({
      "event_index":i,
      "event_day":e["event_day"],
      "state":e["state"],
      "entry_day":entry_day,
      "exit_day":exit_day,
      "raw_return_24h":format(raw,"f"),
      "signed_return_24h":format(signed,"f")
    })

vals=[Decimal(r["signed_return_24h"]) for r in rows]
neg_vals=[Decimal(r["signed_return_24h"]) for r in rows if r["state"]=="NEGATIVE_EXTREME"]
pos_vals=[Decimal(r["signed_return_24h"]) for r in rows if r["state"]=="POSITIVE_EXTREME"]

def mean(xs):
    return sum(xs,Decimal(0))/Decimal(len(xs))

rng=random.Random(20260926)
boots=[]
n=len(vals)
for _ in range(10_000):
    boots.append(mean([vals[rng.randrange(n)] for __ in range(n)]))
boots.sort()
lo=boots[max(0,int(0.025*len(boots))-1)]
hi=boots[min(len(boots)-1,int(0.975*len(boots))-1)]

passed=mean(vals)>0 and lo>0 and mean(neg_vals)>0 and mean(pos_vals)>0
result={
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"FORWARD_POST_H1_OUTCOME_V0.1",
  "classification":"FORWARD_PASS" if passed else "FORWARD_FAIL",
  "event_count":len(rows),
  "negative_extreme_event_count":len(neg_vals),
  "positive_extreme_event_count":len(pos_vals),
  "pooled_mean_signed_return_24h":format(mean(vals),"f"),
  "negative_mean_signed_return_24h":format(mean(neg_vals),"f"),
  "positive_mean_signed_return_24h":format(mean(pos_vals),"f"),
  "bootstrap":{
    "seed":20260926,
    "resamples":10000,
    "percentile_95_lower":format(lo,"f"),
    "percentile_95_upper":format(hi,"f")
  },
  "price_source":{
    "provider":"Binance public historical Spot data",
    "instrument":"BTCUSDT",
    "interval":"1d",
    "daily_archives":archives
  },
  "rows":rows,
  "market_returns_opened":True,
  "pnl_opened":False,
  "live_trading":False,
  "mutation":False,
  "promotion_credit":0
}
RESULT_OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
STATUS_OUT.write_text(json.dumps({
  **status,
  "classification":result["classification"],
  "market_returns_opened":True
},indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2,sort_keys=True))
