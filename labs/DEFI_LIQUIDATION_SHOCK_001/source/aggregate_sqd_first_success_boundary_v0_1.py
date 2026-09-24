#!/usr/bin/env python3
import datetime as dt, hashlib, json, sys
from pathlib import Path

ROOT=Path(sys.argv[1])
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_CANDIDATES_V0.1.json")
CFG={
 "marginfi":{"lower":"2023-02-07T15:47:04Z","upper":"2025-01-01T00:00:00Z",
             "pass_class":"MARGINFI_FIRST_SUCCESS_BOUNDARY_SQD_CANDIDATE_PENDING_RAW"},
 "save0c":{"lower":"2021-12-08T00:00:00Z","upper":"2025-01-01T00:00:00Z",
            "pass_class":"SAVE0C_FIRST_SUCCESS_BOUNDARY_SQD_CANDIDATE_PENDING_RAW"}
}
def iso(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def addr_key(v): return tuple(v) if isinstance(v,list) else (999999,)
def month_next(x):
    y,m=x.year,x.month
    return dt.datetime(y+1,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(y,m+1,1,tzinfo=dt.timezone.utc)

files=sorted(ROOT.rglob("*.json"))
rows=[]
for p in files:
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol") in CFG and "effective_start" in r and "effective_end" in r:
        r["_path"]=str(p); rows.append(r)

result={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":"IN_PROGRESS","protocols":{},
"firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
"economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
"wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}

all_pass=True
for protocol,cfg in CFG.items():
    ps=[r for r in rows if r.get("protocol")==protocol]
    ps.sort(key=lambda r:iso(r["effective_start"]))
    lower=iso(cfg["lower"]); upper=iso(cfg["upper"])
    expected=lower
    required=[]
    candidate=None
    state="NEEDS_MORE_CHRONOLOGICAL_PARTITIONS"
    anomaly_count=0
    gap=None
    for r in ps:
        s=iso(r["effective_start"]); e=iso(r["effective_end"])
        if e<=expected: continue
        if s!=expected:
            gap={"expected_start":expected.isoformat().replace("+00:00","Z"),"observed_start":r["effective_start"]}
            state="SQD_FIRST_SUCCESS_BOUNDARY_BLOCKED"
            break
        required.append(r)
        if r.get("classification")!="SOURCE_PARTITION_PASS" or r.get("stream_complete") is not True:
            state="SQD_FIRST_SUCCESS_BOUNDARY_BLOCKED"; break
        anomaly_count += int(r.get("anomaly_count") or 0)
        if anomaly_count:
            state="SOURCE_ANOMALY_FAIL_CLOSED"; break
        succ=[x for x in (r.get("rows") or []) if x.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
        succ.sort(key=lambda x:(iso(x["timestamp"]),x.get("slot",-1),x.get("signature",""),addr_key(x.get("instructionAddress"))))
        if succ:
            candidate=succ[0]
            state=cfg["pass_class"]
            expected=e
            break
        expected=e
        if expected>=upper:
            state=("MARGINFI_FIRST_SUCCESS_BOUNDARY_NO_MATCH_IN_COMPLETE_SQD_WINDOW" if protocol=="marginfi"
                   else "SAVE0C_FIRST_SUCCESS_BOUNDARY_NO_MATCH_IN_COMPLETE_SQD_WINDOW")
            break
    if not ps:
        state="NEEDS_MORE_CHRONOLOGICAL_PARTITIONS"
    result["protocols"][protocol]={
      "classification":state,
      "required_partition_count":len(required),
      "covered_through":expected.isoformat().replace("+00:00","Z"),
      "candidate":candidate,
      "gap":gap,
      "anomaly_count":anomaly_count,
      "observed_partition_count":len(ps)
    }
    if not state.endswith("_CANDIDATE_PENDING_RAW"): all_pass=False

if all_pass:
    result["classification"]="MARGINFI_SAVE0C_SQD_CANDIDATES_READY_FOR_RAW"
elif any(v["classification"] in ("SQD_FIRST_SUCCESS_BOUNDARY_BLOCKED","SOURCE_ANOMALY_FAIL_CLOSED") for v in result["protocols"].values()):
    result["classification"]="MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_BLOCKED_FAIL_CLOSED"
else:
    result["classification"]="MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_INCOMPLETE"

OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))
if result["classification"].endswith("BLOCKED_FAIL_CLOSED"): raise SystemExit(2)
