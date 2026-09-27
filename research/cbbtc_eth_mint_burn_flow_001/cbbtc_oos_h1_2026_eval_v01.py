#!/usr/bin/env python3
from __future__ import annotations

import hashlib, io, json, random, urllib.request, zipfile
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec=60

HERE=Path("research/cbbtc_eth_mint_burn_flow_001")
CENSUS=Path("artifacts/oos_h1_2026/CBBTC_OOS_H1_2026_CENSUS_RECEIPT_V0.1.json")
DAILY=Path("artifacts/oos_h1_2026/CBBTC_OOS_H1_2026_DAILY_FLOW_V0.1.json")
OUT_DIR=Path("artifacts/oos_h1_2026")
SAMPLE_OUT=OUT_DIR/"CBBTC_OOS_H1_2026_SAMPLE_RECEIPT_V0.1.json"
RESULT_OUT=OUT_DIR/"CBBTC_OOS_H1_2026_RESULT_V0.1.json"

if not CENSUS.exists() or not DAILY.exists():
    raise SystemExit("OOS_CENSUS_ARTIFACT_MISSING")

census=json.loads(CENSUS.read_text())
daily_obj=json.loads(DAILY.read_text())
if census.get("classification")!="OOS_PREDICTOR_CENSUS_PASS":
    raise SystemExit("OOS_PREDICTOR_CENSUS_NOT_PASS")

# Exact frozen Discovery thresholds. Never recalibrate on 2026.
Q10_NUM=-18316281339
Q10_DEN=1601692985627
Q90_NUM=35266522085
Q90_DEN=1057456895899

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

days=daily_obj.get("days",[])
by_day={r["utc_day"]:r for r in days}
expected=[]
d=date(2025,12,31)
while d<=date(2026,6,30):
    expected.append(d.isoformat())
    d+=timedelta(days=1)

missing=[x for x in expected if x not in by_day]
if missing:
    raise SystemExit("OOS_MISSING_DAYS:"+",".join(missing[:10]))

states={day:classify(by_day[day]) for day in expected}
events=[]
prev=states["2025-12-31"]
for day in expected[1:]:
    st=states[day]
    if st=="NEGATIVE_EXTREME" and prev!="NEGATIVE_EXTREME":
        events.append({"event_day":day,"state":st})
    elif st=="POSITIVE_EXTREME" and prev!="POSITIVE_EXTREME":
        events.append({"event_day":day,"state":st})
    prev=st

neg=[e for e in events if e["state"]=="NEGATIVE_EXTREME"]
pos=[e for e in events if e["state"]=="POSITIVE_EXTREME"]
eligible=[e for e in events if e["event_day"]<="2026-06-28"]
eligible_neg=[e for e in eligible if e["state"]=="NEGATIVE_EXTREME"]
eligible_pos=[e for e in eligible if e["state"]=="POSITIVE_EXTREME"]

sample_pass=(
    census.get("supply_reconciliation",{}).get("exact_equal") is True
    and census.get("duplicate_txhash_logindex_count")==0
    and not census.get("decode_errors")
    and not census.get("errors")
    and len(events)>=20
    and len(neg)>=6
    and len(pos)>=6
    and len(eligible)>=20
    and len(eligible_neg)>=6
    and len(eligible_pos)>=6
)

sample={
    "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
    "stage":"OOS_H1_2026_PREDICTOR_SAMPLE_GATE_V0.1",
    "classification":"OOS_PREDICTOR_SAMPLE_PASS" if sample_pass else "OOS_INSUFFICIENT_SAMPLE",
    "calendar":{"start":"2026-01-01","end":"2026-06-30"},
    "predecessor_day":"2025-12-31",
    "transition_event_count":len(events),
    "negative_extreme_event_count":len(neg),
    "positive_extreme_event_count":len(pos),
    "outcome_eligible_event_count":len(eligible),
    "outcome_eligible_negative_count":len(eligible_neg),
    "outcome_eligible_positive_count":len(eligible_pos),
    "thresholds":{
        "q10":{"numerator":str(Q10_NUM),"denominator":str(Q10_DEN)},
        "q90":{"numerator":str(Q90_NUM),"denominator":str(Q90_DEN)}
    },
    "events":events,
    "protected_2026_predictor_opened":True,
    "market_returns_opened":False,
    "pnl_opened":False,
    "mutation":False,
    "promotion_credit":0
}
OUT_DIR.mkdir(parents=True,exist_ok=True)
SAMPLE_OUT.write_text(json.dumps(sample,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in sample.items() if k!="events"},indent=2,sort_keys=True))

if not sample_pass:
    RESULT_OUT.write_text(json.dumps({
        "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
        "stage":"OOS_H1_2026_V0.1",
        "classification":"OOS_INSUFFICIENT_SAMPLE",
        "market_returns_opened":False,
        "protected_2026_predictor_opened":True,
        "protected_2026_price_opened":False,
        "pnl_opened":False,
        "mutation":False,
        "promotion_credit":0
    },indent=2,sort_keys=True)+"\n")
    raise SystemExit(0)

# Only now may 2026 BTC prices be opened.
BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d"
MONTHS=[f"2026-{m:02d}" for m in range(1,7)]

def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CBBTC-OOS/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read()

def ms_or_us_to_date(v:int)->str:
    sec=(v/1_000_000) if v>100_000_000_000_000 else (v/1_000)
    return datetime.fromtimestamp(sec,tz=timezone.utc).date().isoformat()

prices={}
archives=[]
for ym in MONTHS:
    name=f"BTCUSDT-1d-{ym}.zip"
    url=f"{BASE}/{name}"
    blob=fetch(url)
    checksum_blob=fetch(url+".CHECKSUM").decode().strip()
    expected_sha=checksum_blob.split()[0].lower()
    got=hashlib.sha256(blob).hexdigest().lower()
    if got!=expected_sha:
        raise SystemExit(f"OOS_CHECKSUM_MISMATCH:{ym}:{expected_sha}:{got}")
    archives.append({"month":ym,"filename":name,"sha256":got,"checksum_verified":True})
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=z.namelist()
        if len(names)!=1:
            raise SystemExit(f"OOS_ZIP_FILE_COUNT:{ym}:{len(names)}")
        for line in z.read(names[0]).decode().strip().splitlines():
            cols=line.split(",")
            if len(cols)<6:
                raise SystemExit(f"OOS_BAD_KLINE_ROW:{ym}")
            day=ms_or_us_to_date(int(cols[0]))
            if not ("2026-01-01"<=day<="2026-06-30"):
                raise SystemExit("OOS_PRICE_OUTSIDE_H1:"+day)
            px=Decimal(cols[1])
            if px<=0:
                raise SystemExit("OOS_NONPOSITIVE_OPEN:"+day)
            if day in prices:
                raise SystemExit("OOS_DUPLICATE_PRICE_DAY:"+day)
            prices[day]=px

d=date(2026,1,1)
while d<=date(2026,6,30):
    if d.isoformat() not in prices:
        raise SystemExit("OOS_MISSING_PRICE_DAY:"+d.isoformat())
    d+=timedelta(days=1)

def plus(day:str,n:int)->str:
    return (date.fromisoformat(day)+timedelta(days=n)).isoformat()

rows=[]
for i,e in enumerate(eligible):
    t=e["event_day"]
    entry_day=plus(t,1)
    exit_day=plus(t,2)
    if entry_day not in prices or exit_day not in prices:
        raise SystemExit("OOS_PRIMARY_PRICE_MISSING:"+t)
    entry=prices[entry_day]
    exitp=prices[exit_day]
    raw=(exitp-entry)/entry
    if e["state"]=="POSITIVE_EXTREME":
        signed=raw
    elif e["state"]=="NEGATIVE_EXTREME":
        signed=-raw
    else:
        raise SystemExit("OOS_NON_EXTREME_EVENT:"+t)
    sec=None
    if t<="2026-06-26":
        sec_day=plus(t,4)
        if sec_day not in prices:
            raise SystemExit("OOS_SECONDARY_PRICE_MISSING:"+t)
        sec_raw=(prices[sec_day]-entry)/entry
        sec=sec_raw if e["state"]=="POSITIVE_EXTREME" else -sec_raw
    rows.append({
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

neg_vals=[Decimal(r["signed_return_24h"]) for r in rows if r["state"]=="NEGATIVE_EXTREME"]
pos_vals=[Decimal(r["signed_return_24h"]) for r in rows if r["state"]=="POSITIVE_EXTREME"]
vals=[Decimal(r["signed_return_24h"]) for r in rows]

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
secondary=[Decimal(r["signed_return_72h_diagnostic"]) for r in rows if r["signed_return_72h_diagnostic"] is not None]

result={
    "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
    "stage":"OOS_H1_2026_V0.1",
    "classification":"OOS_PASS" if passed else "OOS_FAIL",
    "price_source":{
        "provider":"Binance public historical Spot data",
        "instrument":"BTCUSDT",
        "interval":"1d",
        "months":archives,
        "opened_years":[2026]
    },
    "holdout":{"start":"2026-01-01","end":"2026-06-30"},
    "primary_horizon_hours":24,
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
    "secondary_72h_diagnostic":{
        "valid_count":len(secondary),
        "mean_signed_return":None if not secondary else format(mean(secondary),"f"),
        "can_rescue_primary":False
    },
    "rows":rows,
    "protected_2026_predictor_opened":True,
    "protected_2026_price_opened":True,
    "market_returns_opened":True,
    "pnl_opened":False,
    "live_trading":False,
    "mutation":False,
    "promotion_credit":0
}
RESULT_OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2,sort_keys=True))
