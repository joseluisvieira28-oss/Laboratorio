#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone

PROTOS={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral"
}
MONTHS=[f"{i:02d}" for i in range(1,13)]

def bounds(mm):
    m=int(mm)
    a=f"2025-{m:02d}-01T00:00:00Z"
    b="2026-01-01T00:00:00Z" if m==12 else f"2025-{m+1:02d}-01T00:00:00Z"
    return a,b

def canon(r):
    keep={
      "schema_version":r.get("schema_version"),
      "lab_id":r.get("lab_id"),
      "protocol":r.get("protocol"),
      "instruction_class":r.get("instruction_class"),
      "window_start":r.get("window_start"),
      "window_end":r.get("window_end"),
      "classification":r.get("classification"),
      "successful_instruction_count":r.get("successful_instruction_count"),
      "unique_collateral_mint_count":r.get("unique_collateral_mint_count"),
      "sol_collateral_event_count":r.get("sol_collateral_event_count"),
      "duplicate_count":r.get("duplicate_count"),
      "error_count":r.get("error_count"),
      "rows":r.get("rows") or [],
      "firewall":r.get("firewall") or {}
    }
    raw=json.dumps(keep,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--out",required=True);args=ap.parse_args()
root=Path(args.root); candidates={}; rejected=[]
for p in root.rglob("*.json"):
    try:r=json.loads(p.read_text())
    except Exception:continue
    proto=r.get("protocol")
    if proto not in PROTOS:continue
    ws=str(r.get("window_start") or "")
    mm=None
    for m in MONTHS:
        a,b=bounds(m)
        if ws==a and str(r.get("window_end") or "")==b:mm=m;break
    if mm is None:continue
    key=(proto,mm)
    if r.get("classification")!="PROTECTED_2025_PROTOCOL_SOURCE_PASS":
        rejected.append({"file":str(p),"key":key,"reason":"NOT_PASS","classification":r.get("classification")});continue
    if r.get("instruction_class")!=PROTOS[proto] or int(r.get("error_count") or 0)!=0 or int(r.get("duplicate_count") or 0)!=0:
        rejected.append({"file":str(p),"key":key,"reason":"INTEGRITY"});continue
    candidates.setdefault(key,[]).append((p,r,canon(r)))

selected={};conflicts=[]
for key,vals in sorted(candidates.items()):
    shas={x[2] for x in vals}
    if len(shas)!=1:
        conflicts.append({"protocol":key[0],"month":key[1],"payload_shas":sorted(shas),"files":[str(x[0]) for x in vals]})
        continue
    p,r,s=sorted(vals,key=lambda x:str(x[0]))[0]
    selected[key]={"protocol":key[0],"month":key[1],"payload_sha256":s,
                   "successful_instruction_count":r.get("successful_instruction_count"),
                   "sol_collateral_event_count":r.get("sol_collateral_event_count"),
                   "source_file":str(p)}
missing=[{"protocol":p,"month":m} for p in sorted(PROTOS) for m in MONTHS if (p,m) not in selected]
state={
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "schema":"DLS_PROTECTED_2025_SOURCE_CONSOLIDATION_V0.1",
 "generated_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"CONSOLIDATION_PASS" if not conflicts else "CONSOLIDATION_BLOCKED",
 "selected_pass_partition_count":len(selected),
 "expected_partition_count":48,
 "missing_partition_count":len(missing),
 "missing_partitions":missing,
 "selected_partitions":[selected[k] for k in sorted(selected)],
 "conflicts":conflicts,
 "rejected_count":len(rejected),
 "market_outcomes_opened":False,
 "trading_authority":"NONE"
}
stable={"selected":[selected[k] for k in sorted(selected)],"missing":missing}
state["consolidation_identity_sha256"]=hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":")).encode()).hexdigest()
out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(state,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:state[k] for k in ["classification","selected_pass_partition_count","missing_partition_count","missing_partitions","conflicts","consolidation_identity_sha256"]},indent=2,sort_keys=True))
if conflicts:raise SystemExit(2)
