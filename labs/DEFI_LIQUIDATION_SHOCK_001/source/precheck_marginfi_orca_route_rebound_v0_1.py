#!/usr/bin/env python3
import argparse,datetime as dt,json
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"
START=dt.datetime(2024,10,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
FOLD_CUT=dt.datetime(2024,12,1,tzinfo=dt.timezone.utc)
LINK_MIN=5
HOLD_MIN=1

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_ROUTE_REBOUND_V01_PREOUTCOME_RECEIPT.json"
ROWS=OUT/"MARGINFI_ORCA_ROUTE_REBOUND_V01_PREOUTCOME_CASCADES.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])
def entry_minute(t):return t.replace(second=0,microsecond=0)+dt.timedelta(minutes=1)

def crosses_funding(a,x):
    d=a.date()-dt.timedelta(days=1)
    while d<=x.date():
        for h in (0,8,16):
            f=dt.datetime(d.year,d.month,d.day,h,tzinfo=dt.timezone.utc)
            if a<=f<=x:return True
        d+=dt.timedelta(days=1)
    return False

def blocked(stage,detail):
    rec={"schema_version":"0.1","classification":"MARGINFI_ORCA_ROUTE_REBOUND_PREOUTCOME_BLOCKED",
         "stage":stage,"detail":str(detail),
         "firewall":{"ohlc_read":False,"returns_read":False,"pnl_read":False,
                     "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,
                     "market_2026_opened":False,"live_trading":False,"orders":False,
                     "exchange_mutation":False,"merge_main":False}}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

srec=find_one(args.source_root,"MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json")
srows=find_one(args.source_root,"MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_ROWS_V0.2.ndjson")
if srec is None or srows is None:blocked("authority","source receipt or rows missing/duplicate")
sr=json.loads(srec.read_text())
if sr.get("classification")!="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS":
    blocked("authority",sr.get("classification"))

src=[json.loads(x) for x in srows.read_text().splitlines() if x.strip()]
events=[]
for r in src:
    if r.get("classification")!="DIRECTION_PROVEN":continue
    if r.get("route_semantic")!="COLLATERAL_TO_LIABILITY_ORCA_PROVEN":continue
    if r.get("asset_label")!="SIGNED_SELL_PRESSURE_PROVEN":continue
    if r.get("asset_mint")!=SOL:continue
    t=parse_iso(r["timestamp"])
    if START<=t<END:events.append({**r,"t":t})
events.sort(key=lambda r:(r["t"],r["signature"],addrkey(r["instructionAddress"])))

cascades=[]
for e in events:
    if not cascades or e["t"]>cascades[-1]["last"]+dt.timedelta(minutes=LINK_MIN):
        cascades.append({"first":e["t"],"last":e["t"],"events":[e]})
    else:
        cascades[-1]["events"].append(e);cascades[-1]["last"]=e["t"]

rows=[];funding_excluded=0
for i,c in enumerate(cascades,1):
    A=entry_minute(c["last"]);X=A+dt.timedelta(minutes=HOLD_MIN)
    if not(START<=A<END) or X>END:continue
    fold="F1" if A<FOLD_CUT else "F2"
    funding=crosses_funding(A,X)
    if funding:funding_excluded+=1
    rows.append({
      "cascade_id":f"route-{i:05d}","first_event_time":c["first"].isoformat(),
      "last_event_time":c["last"].isoformat(),"entry_time":A.isoformat(),"exit_time":X.isoformat(),
      "fold":fold,"source_event_count":len(c["events"]),"funding_excluded":funding,
      "member_identities":[ident(e) for e in c["events"]]
    })

with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

cand=[r for r in rows if not r["funding_excluded"]]
n=len(cand);days=len({r["entry_time"][:10] for r in cand})
f1=sum(1 for r in cand if r["fold"]=="F1");f2=n-f1
gate={"n_ge_40":n>=40,"days_ge_8":days>=8,"f1_n_ge_10":f1>=10,"f2_n_ge_20":f2>=20}
classification="MARGINFI_ORCA_ROUTE_REBOUND_PREOUTCOME_READY" if all(gate.values()) else "MARGINFI_ORCA_ROUTE_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE"
receipt={
 "schema_version":"0.1","lab_id":"DLS-MARGINFI-ORCA-ROUTE-REBOUND-001",
 "classification":classification,
 "authority":"MARGINFI_ORCA_ROUTE_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "source_classification":sr.get("classification"),"eligible_source_events":len(events),
 "source_cascade_count":len(cascades),"funding_excluded_count":funding_excluded,
 "candidate_count":n,"distinct_utc_candidate_days":days,"F1_candidate_count":f1,"F2_candidate_count":f2,
 "sample_gate":gate,
 "firewall":{"source_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
             "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,
             "market_2026_opened":False,"live_trading":False,"orders":False,
             "exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
