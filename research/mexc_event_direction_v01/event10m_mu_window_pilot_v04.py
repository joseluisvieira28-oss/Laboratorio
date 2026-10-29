#!/usr/bin/env python3
"""Frozen 10-slot MU/index one-day-ahead-direction pilot; historical discovery only."""
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import event10m_mu_source_forensics_v03 as source

OUT=Path("artifacts/event10m_mu_window_pilot_v04")
NY=ZoneInfo("America/New_York")
UTC=dt.timezone.utc
DAYS=source.DAYS
STOCK_HASH={"2026-10-26":"d47ed00b747bc37f8e6b557d151496015b8f7b0776ca8e3476bf9a8bf04288d2",
            "2026-10-27":"95060301367034d6b33b9f5633d4a5779938cf5574c5eaa305640b74bf294528"}
INDEX_HASH={"2026-10-26":"6d263827363061ccb8f30a08b32a4472874b5a021ad16b1278f01fd4006a43db",
            "2026-10-27":"3fc8f721b9028be5452d7583f99fdb0360ea42aeaad7c4f586c73ec3cdc205d6"}
PAYOUTS=(0.80,0.85)
RULES=("MU_SIGN","ALWAYS_UP","ALWAYS_DOWN","INDEX_MOMENTUM")

def frozen_times(day):
    a=dt.datetime.combine(day,dt.time(9,40),NY)
    return [int((a+dt.timedelta(minutes=10*i)).timestamp()) for i in range(5)]

def side(a,b):
    return 1 if a>b else -1 if a<b else 0

def outcome(prediction,delta):
    if delta==0:return "TIE"
    return "WIN" if prediction*delta>0 else "LOSS"

def scores(sequence):
    w=sequence.count("WIN");loss=sequence.count("LOSS");tie=sequence.count("TIE");n=len(sequence)
    return {"n":n,"wins":w,"losses":loss,"ties":tie,
            "accuracy_ex_tie":w/(w+loss) if w+loss else None,
            "illustrative_unit_ev":{str(q):round((q*w-loss)/n,8) if n else None for q in PAYOUTS}}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"EVENT10M_MU_LOCKED_WINDOW_DIAGNOSTIC_V04",
     "stage":"HISTORICAL_DISCOVERY_ONLY",
     "source_window_parent":[40907599978,40907759684],
     "source_verified_before_outcomes":False,
     "dates":[str(d) for d in DAYS],"scheduled_slots":10,
     "NVIDIA_excluded":True,"SPCX_excluded":True,"MLI_not_aliased":True,
     "historical_event_futures_payouts_available":False,
     "event_futures_server_entry_settlement_equivalence":False,
     "live_collector_asof_proven":False,
     "protected_sep_2026_holdout_opened":False,"real_orders":0,
     "gate":"STARTING","sources":[],"by_day":{},"event_observations":[],
     "summary":{}}
    try:
        stock=source.stock("query1.finance.yahoo.com")
        for day in DAYS:
            values=source.portion(stock,day,60)
            if values["valid_minutes"]!=60 or values["canonical_sha256"]!=STOCK_HASH[str(day)]:
                raise RuntimeError("FROZEN_STOCK_OPENING_SHA_MISMATCH_"+str(day))
            report["sources"].append({"symbol":"MU","type":"STOCK_CLOSE","day":str(day),
               "sha256":values["canonical_sha256"],"minutes":60})
        indices={}
        for day in DAYS:
            ix=source.index(day)
            values=source.portion(ix,day,61)
            if values["valid_minutes"]!=61 or values["canonical_sha256"]!=INDEX_HASH[str(day)]:
                raise RuntimeError("FROZEN_INDEX_OPENING_SHA_MISMATCH_"+str(day))
            indices[day]=ix["series"]
            report["sources"].append({"symbol":"MUSTOCK_USDT","type":"MEXC_INDEX_OPEN","day":str(day),
               "sha256":values["canonical_sha256"],"minutes":61})
        report["source_verified_before_outcomes"]=True
        preds={k:[] for k in RULES}
        by_day={str(day):{"scheduled":5,"missing":0,"flat":0,"agree":0,"triggered":0} for day in DAYS}
        for day in DAYS:
            mu=stock["series"];idx=indices[day]
            for t in frozen_times(day):
                req_stock=(t-300,t-180)
                req_idx=(t-300,t-180,t,t+600)
                if not all(k in mu for k in req_stock) or not all(k in idx for k in req_idx):
                    by_day[str(day)]["missing"]+=1
                    continue
                mu_sign=side(mu[t-180],mu[t-300])
                idx_sign=side(idx[t-180],idx[t-300])
                if not mu_sign or not idx_sign:
                    by_day[str(day)]["flat"]+=1
                    continue
                if mu_sign==idx_sign:
                    by_day[str(day)]["agree"]+=1
                    continue
                by_day[str(day)]["triggered"]+=1
                delta=idx[t+600]-idx[t]
                choices={"MU_SIGN":mu_sign,"ALWAYS_UP":1,
                         "ALWAYS_DOWN":-1,"INDEX_MOMENTUM":idx_sign}
                item={"decision_utc":dt.datetime.fromtimestamp(t,UTC).isoformat(),
                      "stock_sign":mu_sign,"index_sign":idx_sign,"outcomes":{}}
                for k,pred in choices.items():
                    label=outcome(pred,delta)
                    preds[k].append(label);item["outcomes"][k]=label
                report["event_observations"].append(item)
        report["by_day"]=by_day
        report["summary"]={k:scores(v) for k,v in preds.items()}
        report["gate"]="FROZEN_DIAGNOSTIC_EXECUTED"
        report["economic_verdict"]="NO_INDEPENDENT_EDGE_PROOF_NO_LIVE_GO"
    except Exception as e:
        report["gate"]="SOURCE_OR_RULE_BLOCKED"
        report["reason"]=type(e).__name__+":"+str(e)[:160]
        report["economic_verdict"]="NOT_EVALUATED"
        raise
    finally:
        (OUT/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":main()
