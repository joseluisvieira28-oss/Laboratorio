#!/usr/bin/env python3
import argparse,datetime as dt,json,math
from pathlib import Path

LOOKBACK=30
RANK=23

ap=argparse.ArgumentParser()
ap.add_argument("--history-root",required=True)
ap.add_argument("--current-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V01_PREOUTCOME_RECEIPT.json"
ROWS=OUT/"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V01_PREOUTCOME_ROWS.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def crosses_funding(a,b):
    d=a.date()-dt.timedelta(days=1)
    while d<=b.date():
        for h in (0,8,16):
            f=dt.datetime(d.year,d.month,d.day,h,tzinfo=dt.timezone.utc)
            if a<=f<=b:return True
        d+=dt.timedelta(days=1)
    return False

def blocked(stage,detail):
    rec={"schema_version":"0.1","classification":"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_SOURCE_BLOCKED",
         "stage":stage,"detail":str(detail),
         "firewall":{"feature_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
                     "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
                     "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

hrec=find_one(args.history_root,"MARGINFI_ORCA_EXTREME_REBOUND_V01_PREOUTCOME_SELECTION_RECEIPT.json")
hrows=find_one(args.history_root,"MARGINFI_ORCA_EXTREME_REBOUND_V01_PREOUTCOME_SELECTION_ROWS.ndjson")
crec=find_one(args.current_root,"MARGINFI_ORCA_TOPQ_REBOUND_OOS_V01_PREOUTCOME_SELECTION_RECEIPT.json")
crows=find_one(args.current_root,"MARGINFI_ORCA_TOPQ_REBOUND_OOS_V01_PREOUTCOME_SELECTION_ROWS.ndjson")
if None in (hrec,hrows,crec,crows):blocked("authority","feature artifact missing or duplicate")
hr=json.loads(hrec.read_text());cr=json.loads(crec.read_text())
for name,r in [("history",hr),("current",cr)]:
    fw=r.get("firewall") or {}
    if fw.get("ohlc_read") is not False or fw.get("returns_read") is not False or fw.get("pnl_read") is not False:
        blocked("feature_firewall",name)
if hr.get("source_cascade_count")!=192:blocked("history_population",hr.get("source_cascade_count"))
if cr.get("source_cascade_count")!=77:blocked("current_population",cr.get("source_cascade_count"))

history=[json.loads(x) for x in hrows.read_text().splitlines() if x.strip()]
current=[json.loads(x) for x in crows.read_text().splitlines() if x.strip()]
if len(history)!=192 or len(current)!=77:blocked("row_count",f"{len(history)}/{len(current)}")
history.sort(key=lambda r:(r["decision_time"],r["cascade_id"]))
current.sort(key=lambda r:(r["decision_time"],r["cascade_id"]))

hist=[float(r["flow_turnover_intensity"]) for r in history]
out=[];selected=[]
for r in current:
    a=parse_iso(r["decision_time"]);x=float(r["flow_turnover_intensity"])
    prior=hist[-LOOKBACK:]
    if len(prior)<LOOKBACK:
        rr={**r,"rolling_lookback":LOOKBACK,"rolling_threshold":None,"selected_pre_funding":False,
            "funding_excluded":False,"selected":False,"selection_reason":"WARMUP_EXCLUDED"}
    else:
        threshold=sorted(prior)[RANK-1]
        pre=x>=threshold
        fund=pre and crosses_funding(a,a+dt.timedelta(minutes=1))
        sel=pre and not fund
        rr={**r,"rolling_lookback":LOOKBACK,"rolling_percentile":0.75,"rolling_rank":RANK,
            "rolling_threshold":threshold,"selected_pre_funding":pre,"funding_excluded":fund,
            "selected":sel,"selection_reason":"SELECTED" if sel else ("FUNDING_EXCLUDED" if fund else "BELOW_ROLLING_Q75")}
        if sel:selected.append(rr)
    out.append(rr);hist.append(x)

n=len(selected);days=len({r["decision_time"][:10] for r in selected})
f1=sum(1 for r in selected if parse_iso(r["decision_time"])<dt.datetime(2024,12,1,tzinfo=dt.timezone.utc))
f2=n-f1
gate={"n_ge_25":n>=25,"days_ge_8":days>=8,"f1_n_ge_15":f1>=15,"f2_n_ge_8":f2>=8}
classification="MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_PREOUTCOME_READY" if all(gate.values()) else "MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_INSUFFICIENT_SAMPLE"

with ROWS.open("w") as fh:
    for r in out:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
receipt={"schema_version":"0.1","lab_id":"DLS-MARGINFI-ORCA-RELATIVE-INTENSITY-OOS-001",
 "classification":classification,
 "authority":"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "history_artifact":{"run_id":36781289721,"artifact_id":11127324942,
                     "digest":"sha256:8dfa5ef296ea65b4e51b46136cd6387b5d0586748ee081737d1ded101c182c87"},
 "current_feature_artifact":{"run_id":36815199005,"artifact_id":11140992589,
                             "digest":"sha256:b452730607f3db4c7f983ce748c74be1ee7f7a51301a1f3876e7d62698cac470"},
 "history_cascade_count":len(history),"current_cascade_count":len(current),
 "lookback_cascades":LOOKBACK,"rolling_percentile":0.75,"rolling_rank":RANK,
 "selected_count":n,"selected_distinct_utc_days":days,"F1_selected_count":f1,"F2_selected_count":f2,
 "funding_excluded_count":sum(1 for r in out if r.get("funding_excluded")),
 "sample_gate":gate,
 "firewall":{"feature_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
             "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
