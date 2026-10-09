#!/usr/bin/env python3
"""YT-AXIA-VAP-001 independent SOURCE-ONLY profile stability and placebo audit.

Runs on three preselected, previously unopened source days. Raw trade prices
used ONLY within each completed 5m bar. No future price return or PnL.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from datetime import datetime,timezone
import csv, hashlib, io, json, math, random, sys, tempfile, zipfile
from pathlib import Path
from urllib.request import Request,urlopen
import yt_axia_vap_001_source_census_v01 as first

ROOT=Path(__file__).resolve().parent
FREEZE=ROOT/"YT_AXIA_VAP_001_G3_GEOMETRY_ROBUSTNESS_FREEZE.json"
RECEIPT=ROOT/"YT_AXIA_VAP_001_G3_GEOMETRY_ROBUSTNESS_RECEIPT.json"
PREFIX="https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"
STEP=300000

class Blocked(Exception):pass

def load_freeze():
    f=json.loads(FREEZE.read_text())
    known=json.loads((ROOT/"YT_AXIA_VAP_001_SOURCE_CENSUS_FREEZE.json").read_text())
    if (f["lab_id"]!="YT-AXIA-VAP-001" or f["stage"]!="G3_INDEPENDENT_SOURCE_GEOMETRY_ROBUSTNESS"
        or set(f["independent_source_days"])&set(f["preceding_discovery_days_excluded"])
        or known["economic_outcomes_allowed"] is not False
        or f["independent_data_probe"]["minimum_jaccard_of_signal_bars"]!=.70
        or f["independent_data_probe"]["minimum_matched_strata_with_at_least_10_of_each_group"]!=6):
        raise Blocked("FREEZE_MISMATCH")
    return f

def bin_price(price,anchor,phase_half=False):
    # Fixed 1bp grid; optional half-1bp offset in the ORIGINAL price basis.
    numerator=(price-anchor)*20000+(anchor if phase_half else 0)
    return numerator//(2*anchor)

def flatten_profiles(day):
    name=f"BTCUSDT-aggTrades-{day}.zip"
    def read(url):
        req=Request(url,headers={"User-Agent":"CryptoLab-Axia-G3Source/0.1"})
        return urlopen(req,timeout=120)
    with read(PREFIX+name+".CHECKSUM") as r:
        tokens=r.read(150).decode("ascii").split()
    if len(tokens)<1 or len(tokens[0])!=64 or any(c not in "abcdef0123456789" for c in tokens[0].lower()):
        raise Blocked("INVALID_OFFICIAL_SHA256")
    if len(tokens)>1 and tokens[1].lstrip("*").split("/")[-1]!=name:
        raise Blocked("OFFICIAL_FILENAME_CHECKSUM_MISMATCH")
    digest=hashlib.sha256()
    total_bytes=0
    with tempfile.TemporaryFile() as f:
        with read(PREFIX+name) as r:
            while True:
                block=r.read(1024*1024)
                if not block:break
                total_bytes+=len(block)
                if total_bytes>200_000_000:raise Blocked("ZIP_EXCEEDS_SOURCE_BUDGET")
                digest.update(block);f.write(block)
        if digest.hexdigest()!=tokens[0].lower():raise Blocked("ARCHIVE_SHA256_MISMATCH")
        f.seek(0)
        day_start=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
        bar_map={}
        prev_id=None;prev_ts=None;trade_count=0
        with zipfile.ZipFile(f) as z:
            members=[x for x in z.namelist() if x.lower().endswith(".csv")]
            if len(members)!=1:raise Blocked("CSV_MEMBER_MISMATCH")
            with z.open(members[0]) as raw:
                for row in csv.reader(io.TextIOWrapper(raw,encoding="utf-8-sig",newline="")):
                    if not row:continue
                    if row[0].strip().lower() in ("agg_trade_id","a"):continue
                    if len(row)<7:raise Blocked("SHORT_AGGTRADE_ROW")
                    aid=int(row[0]);p=first.price_to_cents(row[1]);q=float(row[2]);t=first.bounded_ms(row[5]);maker=row[6].lower().strip()
                    if (not math.isfinite(q) or q<=0 or maker not in ("true","false")
                        or (prev_id is not None and aid<=prev_id)
                        or (prev_ts is not None and t<prev_ts)
                        or not day_start<=t<day_start+86_400_000):
                        raise Blocked("SOURCE_AGGTRADE_INTEGRITY_FAIL")
                    prev_id=aid;prev_ts=t
                    bstart=t//STEP*STEP
                    if bstart not in bar_map:
                        bar_map[bstart]={"anchor":p,"price_vol":defaultdict(float),"n":0,"buy":0.0,"sell":0.0}
                    b=bar_map[bstart]
                    b["price_vol"][p]+=q
                    b["n"]+=1
                    if maker=="true":b["sell"]+=q
                    else:b["buy"]+=q
                    trade_count+=1
    if (len(bar_map)!=288 or min(bar_map)!=day_start or max(bar_map)!=day_start+86_400_000-STEP
        or any(day_start+i*STEP not in bar_map for i in range(288))):
        raise Blocked("DAILY_5M_GAP")
    return bar_map,{"day":day,"sha256":digest.hexdigest(),"bytes":total_bytes,"aggtrade_rows":trade_count}

def by_grid(price_vol,anchor,phase_half=False):
    bins=defaultdict(float)
    for p,v in price_vol.items():
        bins[bin_price(p,anchor,phase_half)]+=v
    return dict(bins)

def cell_key(bins,buy,sell):
    poc=min((-v,k) for k,v in bins.items())[1] # tie break lowest price
    low,high=min(bins),max(bins)
    rank=min(2,(3*(poc-low))//(high-low+1))
    side="BUY" if buy>=sell else "SELL"
    width="WIDE" if high-low>=20 else "NARROW"
    return (rank,side,width)

def evaluate_day(day,bars,seed):
    base=set();half=set();nonshape=0;skip=0;controls=defaultdict(Counter)
    rng=random.Random(seed)
    shuffled_events=0;shuffled_tried=0
    for t,b in sorted(bars.items()):
        original=by_grid(b["price_vol"],b["anchor"])
        jittered=by_grid(b["price_vol"],b["anchor"],True)
        g0=first.qualifies_shape(original,b["n"])
        g1=first.qualifies_shape(jittered,b["n"])
        eligible=(b["n"]>=100 and len(original)>=8)
        if not eligible:
            skip+=1
            continue
        if g0:base.add(t)
        else:nonshape+=1
        if g1:half.add(t)
        controls[cell_key(original,b["buy"],b["sell"])]["SHAPE" if g0 else "CONTROL"]+=1
        # Descriptive placebo only: 8 reshuffles of occupied-bin volumes,
        # WITHOUT changing price-bin occupancy or total traded quantity.
        keys=sorted(original)
        amounts=[original[k] for k in keys]
        for _ in range(8):
            arr=amounts.copy();rng.shuffle(arr)
            shuffled_events+=int(first.qualifies_shape(dict(zip(keys,arr)),b["n"]))
            shuffled_tried+=1
    return {"day":day,"primary_signal_bars":len(base),"shifted_signal_bars":len(half),
        "intersection_signal_bars":len(base&half),
        "union_signal_bars":len(base|half),
        "eligible_control_bars":nonshape,"insufficient_profile_bars":skip,
        "placebo_shuffled_events":shuffled_events,
        "placebo_shuffled_total":shuffled_tried,
        "control_strata":{"|".join(map(str,k)):dict(v) for k,v in controls.items()}}

def main():
    f=load_freeze()
    reports=[];sources=[]
    for day in f["independent_source_days"]:
        raw,prov=flatten_profiles(day)
        reports.append(evaluate_day(day,raw,f["independent_data_probe"]["rng_seed"]+int(day[:4])*1000+int(day[-2:])))
        sources.append(prov)
        print("INDEPENDENT_SOURCE_VERIFIED",day,"trades",prov["aggtrade_rows"],"bars",reports[-1]["primary_signal_bars"],flush=True)
    total=Counter()
    strata=defaultdict(Counter)
    for report in reports:
        for k in ("primary_signal_bars","shifted_signal_bars","intersection_signal_bars","union_signal_bars",
            "eligible_control_bars","insufficient_profile_bars","placebo_shuffled_events","placebo_shuffled_total"):
            total[k]+=report[k]
        for k,v in report["control_strata"].items():
            strata[k].update(v)
    j=total["intersection_signal_bars"]/total["union_signal_bars"] if total["union_signal_bars"] else 0
    days_signal=sum(r["primary_signal_bars"]>0 for r in reports)
    matched=sum(v["SHAPE"]>=10 and v["CONTROL"]>=10 for v in strata.values())
    p=f["independent_data_probe"]
    gates={"SIGNAL_COUNT":total["primary_signal_bars"]>=p["minimum_signal_bars_across_3_days"],
           "SIGNAL_DAY_COUNT":days_signal>=p["minimum_days_with_signal"],
           "CONTROL_COUNT":total["eligible_control_bars"]>=p["minimum_control_bars"],
           "GRID_PHASE_JACCARD":j>=p["minimum_jaccard_of_signal_bars"],
           "MATCHED_STRATA":matched>=p["minimum_matched_strata_with_at_least_10_of_each_group"]}
    receipt={"lab_id":"YT-AXIA-VAP-001",
        "state":"INDEPENDENT_SOURCE_GEOMETRY_ROBUSTNESS_PASS" if all(gates.values()) else "INDEPENDENT_SOURCE_GEOMETRY_ROBUSTNESS_FAIL",
        "scientific_kind":"SOURCE_ONLY_NON_ECONOMIC",
        "source_day_sha256_receipts":sources,
        "source_shape_diagnostics":{k:v for k,v in total.items()},
        "source_day_count_summary":[{k:v for k,v in r.items() if k!="control_strata"} for r in reports],
        "grid_phase_jaccard":j,"days_with_pattern":days_signal,
        "matched_control_strata":matched,"gate_results":gates,
        "shuffled_placebo_positive_rate":total["placebo_shuffled_events"]/total["placebo_shuffled_total"] if total["placebo_shuffled_total"] else None,
        "observed_shape_positive_rate":total["primary_signal_bars"]/(total["primary_signal_bars"]+total["eligible_control_bars"]) if total["eligible_control_bars"] else None,
        "economic_outcomes_opened":False,"trade_execution_modeled":False,"new_strategy_proven":False,"trading_authority":"NONE",
        "limitations":"Source-only signal identification; no future returns or fees. Placebo shuffles are descriptive, cannot establish price predictability."
        }
    RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in receipt.items() if k not in ("source_day_sha256_receipts","source_day_count_summary")},indent=2))
    return receipt

if __name__=="__main__":
    try:main()
    except (Blocked,first.Blocked,ValueError,KeyError,zipfile.BadZipFile,TimeoutError) as e:
        d={"lab_id":"YT-AXIA-VAP-001","state":"SOURCE_BLOCKED",
           "reason":str(e),"economic_outcomes_opened":False,"trading_authority":"NONE"}
        RECEIPT.write_text(json.dumps(d,indent=2)+"\n")
        print(json.dumps(d),file=sys.stderr);sys.exit(2)
