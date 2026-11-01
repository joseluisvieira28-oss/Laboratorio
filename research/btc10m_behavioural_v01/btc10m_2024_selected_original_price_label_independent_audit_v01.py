#!/usr/bin/env python3
"""Independent offline 2024 exact source Binance spot 1m OPEN(t) vs OPEN(t+10m) audits.
ONLY original pinned archived source and selected 2024 predictions: no ML re-tuning, market requests or trades.
"""
import csv
import hashlib
import io
import json
import math
import pathlib
import zipfile
from collections import defaultdict
from datetime import datetime,timezone
import random

S=pathlib.Path("original/original_source")
R=pathlib.Path("results")
O=pathlib.Path("artifacts/btc10m_behavioural_oos_label_audit")
O.mkdir(parents=True,exist_ok=True)
MONTHS=["2023-12"]+[f"2024-{m:02d}" for m in range(1,13)]
def fail(msg):raise ValueError(msg)
def as_int_timestamp(x):
    t=int(x)
    if t>=10**15 and t%1000==0:t//=1000
    return t
def get_prices():
    opens={};closes={};manifest=[]
    for m in MONTHS:
        zp=S/(m+".zip")
        raw=zp.read_bytes();check=(S/(m+".zip.CHECKSUM")).read_text("ascii").strip().split()[0].lower()
        d=hashlib.sha256(raw).hexdigest()
        if d!=check:fail("OFFICIAL_ARCHIVE_SHA_MISMATCH_"+m)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            fs=[k for k in z.namelist() if k.endswith(".csv")]
            if len(fs)!=1:fail("CSV_MEMBER_COUNT")
            with io.TextIOWrapper(z.open(fs[0]),encoding="utf-8-sig") as file:
                for row in csv.reader(file):
                    if not row or not row[0].isdigit():continue
                    t=as_int_timestamp(row[0])
                    if t in opens:fail("DUPLICATE_ORIGINAL_TIME")
                    op=float(row[1]);c=float(row[4])
                    if op<=0 or c<=0:fail("BAD_ORIGINAL_OPEN_CLOSE")
                    opens[t]=op;closes[t]=c
        manifest.append({"month":m,"verified_official_sha256":d})
    return opens,closes,manifest
def bootstrap(rows,q,seed=20261107):
    day=defaultdict(lambda:[0.,0])
    for a in rows:
        val=q if a["win"] else (0 if a["tie"] else -1)
        day[a["date"]][0]+=val;day[a["date"]][1]+=1
    day=list(day.values())
    rng=random.Random(seed+int(q*1000))
    boots=[]
    for _ in range(2000):
        num=0;den=0
        for _ in range(len(day)):
            s,c=day[rng.randrange(len(day))]
            num+=s;den+=c
        boots.append(num/den)
    boots.sort()
    return boots[50]
def audit():
    original=json.loads((R/"receipt.json").read_text())
    outcome=original["one_selected_2024OOS"]
    if outcome is None or outcome["selected_candidate"]!="LOGIT_P60":fail("ORIGINAL_SELECTED_CANDIDATE_ID")
    if original["status"]!="2024_OOS_NO_EDGE_OR_INSUFFICIENT":fail("ORIGINAL_VERDICT_NOT_EXPECTED")
    opens,closes,manifest=get_prices()
    rows=[];seen=set()
    with (R/"2024_SELECTED_CANDIDATE_EVENTS.csv").open() as f:
        for row in csv.DictReader(f):
            t=int(row["time_ms"]);side=int(row["side"]);truth=int(row["truth"])
            if side not in (-1,1) or t in seen or t%(600000)!=0:fail("BAD_OR_DUPLICATE_10MIN_SIGNAL")
            seen.add(t)
            date=datetime.fromtimestamp(t/1000,timezone.utc).date().isoformat()
            if date[:4]!="2024" or row["date"]!=date:fail("FORECAST_NOT_2024_UTC")
            if t not in opens or t+600000 not in opens:fail("NO_EXACT_ORIGINAL_PRICE_TARGET")
            op=opens[t];future=opens[t+600000]
            expected=1 if future>op else -1 if future<op else 0
            if expected!=truth:fail("ORIGINAL_LABEL_DIFFERS")
            if abs(op-float(row["spot_open"]))>1e-8 or abs(future-float(row["target_spot_open"]))>1e-8:
                fail("ORIGINAL_ENTRY_OR_FUTURE_SPOT_PRICE_DIFFERS")
            # Previous 61 closed minutes needed for causal 60 one-minute squared log returns.
            try:
                past=[closes[t-i*60000] for i in range(1,62)]
            except KeyError:fail("MISSING_CLOSED_MINUTE_AT_ELIGIBLE_FORECAST")
            ret=[math.log(past[i]/past[i+1]) for i in range(60)]
            sigma=math.sqrt(sum(x*x for x in ret)/60)
            z5=math.log(past[0]/past[5])/(sigma*math.sqrt(5))
            z5=max(-10,min(10,z5))
            if abs(z5-float(row["z5"]))>1e-8:fail("SOURCE_DERIVED_Z5_FEATURE_DIFFERS")
            rows.append({"date":date,"side":side,"win":side==truth,"tie":truth==0,
                  "always_up_win":truth==1,"truth":truth})
    wins=sum(x["win"] for x in rows);ties=sum(x["tie"] for x in rows)
    loss=len(rows)-wins-ties
    m=outcome["metrics"]
    if (len(rows),wins,loss,ties)!=(m["signal_count"],m["wins"],m["losses"],m["ties"]):
        fail("TOTAL_SOURCE_LABEL_COUNTS_ORIGINAL_DIFFERS")
    q70=(wins*.7-loss)/len(rows);q80=(wins*.8-loss)/len(rows)
    if abs(q70-m["synthetic_payoff_per_stake_q0p7"])>1e-11 or abs(q80-m["synthetic_payoff_per_stake_q0p8"])>1e-11:
        fail("INDEPENDENT_PAYOUT_AGREEMENT_MISSING")
    # 95% Wilson non-tie directional interval, NOT dependency corrected; day block payoff is below.
    n=wins+loss;p=wins/n;z=1.959963984540054
    mid=(p+z*z/(2*n))/(1+z*z/n)
    rad=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return {"study":"BTC10M_BEHAVIOURAL_2024_OOS_INDEPENDENT_BINANCE_SPOT_ORIGINAL_PRICE_LABELS_V01",
        "original_market_file_artifact":13078359511,
        "original_selected_signal_artifact":13079057884,
        "source_original_archive_sha_verified":len(manifest),
        "independently_source_rechecked_selected_2024_signals":len(rows),
        "2024_distinct_signal_days":len({x["date"] for x in rows}),
        "wins":wins,"losses":loss,"ties":ties,
        "non_tie_directional_accuracy":p,
        "illustrative_naive_wilson_95pct_interval":[mid-rad,mid+rad],
        "hypothetical_q070_mean_per_stake":q70,"hypothetical_q080_mean_per_stake":q80,
        "q070_2000_daily_boot_one_sided_97p5_lower":bootstrap(rows,.7),
        "q080_2000_daily_boot_one_sided_97p5_lower":bootstrap(rows,.8),
        "hypothetical_10USDT_stake_q070_total":(wins*7-loss*10),
        "hypothetical_10USDT_stake_q080_total":(wins*8-loss*10),
        "all_selected_timestamps_and_10min_outcomes_reproduced_from_original_spot_zip":True,
        "one_causal_lookback_feature_z5_reproduced":True,
        "independently_refit_ML_or_independently_recomputed_all_model_probabilities":False,
        "new_public_or_private_market_api_calls":0,"capital":0,"real_orders":0,
        "Event_Futures_price_parity_proven":False,"economic_edge_certified":False,
        "status":"INDEPENDENT_ORIGINAL_2024_SOURCE_PRICE_LABEL_REPLAY_PASS"}
try:r=audit()
except Exception as exc:r={"status":"INDEPENDENT_SOURCE_LABEL_AUDIT_FAIL","reason":type(exc).__name__+":"+str(exc)[:320],
    "market_api_calls":0,"trades":0}
(O/"receipt.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print("FINAL_INDEPENDENT_SOURCE_LABEL_AUDIT",json.dumps(r,sort_keys=True),flush=True)
if r["status"]!="INDEPENDENT_ORIGINAL_2024_SOURCE_PRICE_LABEL_REPLAY_PASS":raise SystemExit(2)
