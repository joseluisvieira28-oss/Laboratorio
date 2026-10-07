#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, itertools, json, statistics, urllib.request, zipfile
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path
from zoneinfo import ZoneInfo

getcontext().prec = 50

ROOT=Path(__file__).resolve().parents[2]
FREEZE_PATH=ROOT/"Dream-Account-OS-v2.3-PARTIAL/research/NEWS_SHOCK_LAB_V03_NFP_SURPRISE_PRE_OUTCOME_FREEZE_V0.1.json"
OUT=Path("nfp_surprise_discovery_v01")
OUT.mkdir(exist_ok=True)
BASE="https://data.binance.vision/data/spot/daily/klines"
HEADERS={"User-Agent":"Mozilla/5.0 CryptoLabResearch/1.0"}

def get(url, timeout=30):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.read(), dict(r.headers)

def sha256(b): return hashlib.sha256(b).hexdigest()

def dmean(xs):
    return sum(xs,Decimal("0"))/Decimal(len(xs))

def dmedian(xs):
    ys=sorted(xs)
    n=len(ys)
    if n%2: return ys[n//2]
    return (ys[n//2-1]+ys[n//2])/Decimal(2)

def target_ms(event_date, hhmm):
    h,m=map(int,hhmm.split(":"))
    dt=datetime.fromisoformat(event_date).replace(hour=h,minute=m,second=0,microsecond=0,tzinfo=ZoneInfo("America/New_York"))
    return int(dt.astimezone(timezone.utc).timestamp()*1000), dt.astimezone(timezone.utc).isoformat()

def read_open(zip_bytes, target):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names=z.namelist()
        if len(names)!=1:
            raise RuntimeError(f"unexpected zip members: {names}")
        data=z.read(names[0]).decode("utf-8")
    found=None
    for row in csv.reader(io.StringIO(data)):
        if not row: continue
        try: ts=int(row[0])
        except ValueError: continue
        # 2025+ Binance archives may use microseconds; 2021 should be ms.
        if ts>10**14: ts//=1000
        if ts==target:
            found=Decimal(row[1]); break
    if found is None: raise RuntimeError(f"target timestamp missing: {target}")
    return found

def acquire(symbol,event_date):
    fn=f"{symbol}-1m-{event_date}.zip"
    url=f"{BASE}/{symbol}/1m/{fn}"
    csum_url=url+".CHECKSUM"
    b,h=get(url)
    cb,ch=get(csum_url)
    expected=cb.decode("utf-8").strip().split()[0].lower()
    actual=sha256(b)
    if actual!=expected:
        raise RuntimeError(f"checksum mismatch {symbol} {event_date}: {actual} != {expected}")
    entry_ms,entry_utc=target_ms(event_date,"08:31")
    exit_ms,exit_utc=target_ms(event_date,"08:45")
    entry=read_open(b,entry_ms)
    exitp=read_open(b,exit_ms)
    return {
        "symbol":symbol,"event_date":event_date,"url":url,"checksum_url":csum_url,
        "zip_sha256":actual,"bytes":len(b),"entry_ms":entry_ms,"entry_utc":entry_utc,
        "exit_ms":exit_ms,"exit_utc":exit_utc,"entry_open":str(entry),"exit_open":str(exitp)
    },entry,exitp

def exact_test(gross_by_event, labels):
    ids=list(gross_by_event)
    obs_signs=[labels[e]["shock_sign"] for e in ids]
    cooler_count=sum(1 for s in obs_signs if s==-1)
    hotter_count=sum(1 for s in obs_signs if s==1)
    if cooler_count+hotter_count!=len(ids): raise RuntimeError("neutral event in directional test")
    obs_aligned=[-Decimal(obs_signs[i])*gross_by_event[e] for i,e in enumerate(ids)]
    obs=dmean(obs_aligned)
    stats=[]
    for cooler_idx in itertools.combinations(range(len(ids)),cooler_count):
        cool=set(cooler_idx)
        signs=[Decimal("-1") if i in cool else Decimal("1") for i in range(len(ids))]
        aligned=[-signs[i]*gross_by_event[e] for i,e in enumerate(ids)]
        stats.append(dmean(aligned))
    ge=sum(1 for s in stats if s>=obs)
    p=Decimal(ge)/Decimal(len(stats))
    return {
        "observed_mean_aligned_gross_bps":str(obs),
        "permutation_count":len(stats),
        "ge_observed_count":ge,
        "exact_one_sided_p_value":str(p),
        "hotter_count":hotter_count,
        "cooler_count":cooler_count
    },obs_aligned

def main():
    freeze=json.loads(FREEZE_PATH.read_text())
    labels=freeze["signal"]["frozen_event_labels"]
    if freeze["governance"]["market_outcomes_accessed_at_freeze"] is not False:
        raise SystemExit("freeze invalid: outcomes already accessed")
    if freeze["primary_test"]["exact_unique_assignments"]!=45:
        raise SystemExit("freeze permutation count drift")
    directional=[eid for eid,v in labels.items() if v["shock_sign"]!=0]
    neutral=[eid for eid,v in labels.items() if v["shock_sign"]==0]
    if len(directional)!=10 or len(neutral)!=2:
        raise SystemExit("frozen label counts drift")

    source_manifest=[]
    event_results={}
    data_errors=[]
    for eid in labels:
        date=eid.rsplit("_",1)[-1]
        event_results[eid]={"event_id":eid,"date":date,"label":labels[eid]["label"],"shock_sign":labels[eid]["shock_sign"],"assets":{}}
        for symbol in freeze["market_outcome_contract"]["symbols"]:
            try:
                rec,entry,exitp=acquire(symbol,date)
                source_manifest.append(rec)
                gross=Decimal("10000")*(exitp/entry-Decimal("1"))
                event_results[eid]["assets"][symbol]={
                    "entry_open":str(entry),"exit_open":str(exitp),"gross_return_bps":str(gross)
                }
            except Exception as e:
                data_errors.append({"event_id":eid,"symbol":symbol,"error":repr(e)})

    if data_errors:
        closeout={
            "lab_id":freeze["lab_id"],"decision":"DATA_INADEQUATE_STOP_BEFORE_INFERENCE",
            "data_errors":data_errors,"market_outcomes_opened":True,"inference_computed":False
        }
        (OUT/"discovery_closeout.json").write_text(json.dumps(closeout,indent=2)+"\n")
        (OUT/"source_manifest.json").write_text(json.dumps(source_manifest,indent=2)+"\n")
        print(json.dumps(closeout,indent=2))
        raise SystemExit(0)

    results={"lab_id":freeze["lab_id"],"assets":{},"directional_event_ids":directional,"neutral_event_ids":neutral}
    all_pass=True
    for symbol in freeze["market_outcome_contract"]["symbols"]:
        gross={eid:Decimal(event_results[eid]["assets"][symbol]["gross_return_bps"]) for eid in directional}
        test,aligned=exact_test(gross,labels)
        aligned_by={eid:aligned[i] for i,eid in enumerate(directional)}
        net=[x-Decimal(str(freeze["return_and_cost_contract"]["fixed_round_trip_cost_bps"])) for x in aligned]
        loo=[]
        for eid in directional:
            vals=[aligned_by[e]-Decimal("10") for e in directional if e!=eid]
            loo.append({"left_out":eid,"mean_aligned_net_bps":str(dmean(vals))})
        criteria={
            "exact_one_sided_p_lte_0_05":Decimal(test["exact_one_sided_p_value"])<=Decimal("0.05"),
            "mean_aligned_net_bps_gt_0":dmean(net)>0,
            "median_aligned_gross_bps_gt_0":dmedian(aligned)>0,
            "every_leave_one_out_mean_aligned_net_bps_gt_0":all(Decimal(x["mean_aligned_net_bps"])>0 for x in loo)
        }
        passed=all(criteria.values())
        all_pass=all_pass and passed
        results["assets"][symbol]={
            **test,
            "mean_aligned_net_bps":str(dmean(net)),
            "median_aligned_gross_bps":str(dmedian(aligned)),
            "hit_rate_aligned_gross_gt_zero":str(Decimal(sum(1 for x in aligned if x>0))/Decimal(len(aligned))),
            "minimum_leave_one_out_mean_aligned_net_bps":str(min(Decimal(x["mean_aligned_net_bps"]) for x in loo)),
            "criteria":criteria,"pass":passed,"leave_one_out":loo
        }

    decision=("DISCOVERY_SURVIVES_LOW_N_ELIGIBLE_ONLY_FOR_SEPARATELY_FROZEN_OOS_SOURCE_EXTENSION"
              if all_pass else "NO_EDGE_STOP_UNDER_2021_NFP_SIGN_VOTE_DEFINITION")
    closeout={
        "lab_id":freeze["lab_id"],"version":"0.1","decision":decision,
        "event_count":12,"directional_event_count":10,"neutral_event_count":2,
        "market_outcome_contract":freeze["market_outcome_contract"],
        "signal_contract":freeze["signal"],
        "results":results,
        "governance":{
            "live_trading_authorized":False,"exchange_mutation_authorized":False,
            "main_merge_authorized":False,
            "oos_extension_authorized":bool(all_pass),
            "alternate_window_weight_asset_or_threshold_search_authorized":False
        }
    }
    (OUT/"source_manifest.json").write_text(json.dumps(source_manifest,indent=2)+"\n")
    (OUT/"event_returns.json").write_text(json.dumps(event_results,indent=2)+"\n")
    (OUT/"discovery_results.json").write_text(json.dumps(results,indent=2)+"\n")
    (OUT/"discovery_closeout.json").write_text(json.dumps(closeout,indent=2)+"\n")
    print(json.dumps(closeout,indent=2))

if __name__=="__main__":
    main()
