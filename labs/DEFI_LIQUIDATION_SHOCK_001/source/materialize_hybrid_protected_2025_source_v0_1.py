#!/usr/bin/env python3
import argparse,hashlib,json,shutil
from pathlib import Path

PROTOS={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral"
}
MONTHS=[f"{i:02d}" for i in range(1,13)]

def bounds(mm):
    m=int(mm)
    return (f"2025-{m:02d}-01T00:00:00Z",
            "2026-01-01T00:00:00Z" if m==12 else f"2025-{m+1:02d}-01T00:00:00Z")

def canonical_payload(r):
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
      "rows":[
        {k:row.get(k) for k in (
          "protocol","instruction_class","signature","instructionAddress","slot","timestamp",
          "account_count","data_length","collateral_mint","collateral_decimals",
          "collateral_token_mint","unit_resolution"
        ) if k in row}
        for row in (r.get("rows") or [])
      ],
      "firewall":r.get("firewall") or {}
    }
    raw=json.dumps(keep,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--outdir",required=True)
ap.add_argument("--receipt",required=True)
args=ap.parse_args()
root=Path(args.root);out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
candidates={};rejected=[]
for p in root.rglob("*.json"):
    try:r=json.loads(p.read_text())
    except Exception:continue
    proto=r.get("protocol")
    if proto not in PROTOS:continue
    key=None
    for mm in MONTHS:
        a,b=bounds(mm)
        if r.get("window_start")==a and r.get("window_end")==b:key=(proto,mm);break
    if key is None:continue
    if r.get("classification")!="PROTECTED_2025_PROTOCOL_SOURCE_PASS":
        rejected.append({"file":str(p),"key":key,"reason":"NOT_PASS","classification":r.get("classification")});continue
    if r.get("instruction_class")!=PROTOS[proto] or int(r.get("error_count") or 0)!=0 or int(r.get("duplicate_count") or 0)!=0:
        rejected.append({"file":str(p),"key":key,"reason":"INTEGRITY"});continue
    candidates.setdefault(key,[]).append((p,r,canonical_payload(r)))

conflicts=[];selected=[]
for proto in sorted(PROTOS):
  for mm in MONTHS:
    key=(proto,mm);vals=candidates.get(key,[])
    if not vals:continue
    shas={x[2] for x in vals}
    if len(shas)!=1:
        conflicts.append({"protocol":proto,"month":mm,"scientific_payload_shas":sorted(shas),
                          "files":[str(x[0]) for x in vals]})
        continue
    p,r,s=sorted(vals,key=lambda x:str(x[0]))[0]
    dest=out/f"{proto}-2025{mm}.json"
    dest.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    selected.append({"protocol":proto,"month":mm,"scientific_payload_sha256":s,
                     "selected_file":str(p),"dest":str(dest),
                     "successful_instruction_count":r.get("successful_instruction_count"),
                     "sol_collateral_event_count":r.get("sol_collateral_event_count")})

missing=[{"protocol":p,"month":m} for p in sorted(PROTOS) for m in MONTHS
         if not (out/f"{p}-2025{m}.json").exists()]
classification="HYBRID_48_PARTITION_PASS" if not conflicts and not missing and len(selected)==48 else "HYBRID_PARTITION_BLOCKED"
receipt={
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "schema":"DLS_PROTECTED_2025_HYBRID_MATERIALIZATION_V0.1",
 "classification":classification,
 "selected_partition_count":len(selected),
 "expected_partition_count":48,
 "missing_partitions":missing,
 "conflicts":conflicts,
 "rejected_count":len(rejected),
 "selected":selected,
 "market_outcomes_opened":False,
 "trading_authority":"NONE"
}
stable={"selected":[{k:x[k] for k in ["protocol","month","scientific_payload_sha256"]} for x in selected]}
receipt["hybrid_identity_sha256"]=hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path(args.receipt).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","selected_partition_count","missing_partitions","conflicts","hybrid_identity_sha256"]},indent=2,sort_keys=True))
if classification!="HYBRID_48_PARTITION_PASS":raise SystemExit(2)
