#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"

ap=argparse.ArgumentParser()
ap.add_argument("--oct-root",required=True)
ap.add_argument("--nov-root",required=True)
ap.add_argument("--dec-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()

OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_RECEIPT_V0.1.json"
POP=OUT/"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_V0.1.ndjson"

EXPECTED={
 "202410":{"partition_id":"marginfi-202410","start":"2024-10-01T00:00:00Z","end":"2024-11-01T00:00:00Z","artifact_id":10924878593},
 "202411":{"partition_id":"marginfi-202411","start":"2024-11-01T00:00:00Z","end":"2024-12-01T00:00:00Z","artifact_id":10925847270},
 "202412":{"partition_id":"marginfi-202412","start":"2024-12-01T00:00:00Z","end":"2025-01-01T00:00:00Z","artifact_id":10927608033},
}

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])

def find_json(root,pred):
    hits=[]
    for p in Path(root).rglob("*.json"):
        try:o=json.loads(p.read_text())
        except Exception:continue
        if pred(o):hits.append((p,o))
    return hits

roots={"202410":args.oct_root,"202411":args.nov_root,"202412":args.dec_root}

bh=find_json(args.bank_registry_root,lambda o:o.get("classification")=="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS")
errors=[]
if len(bh)!=1:errors.append(f"bank_registry_hit_count:{len(bh)}")
registry={}
if bh:
    registry={x["bank"]:x["mint"] for x in bh[0][1].get("bank_registry") or []}
solbanks={b for b,m in registry.items() if m==SOL}
if not solbanks:errors.append("no_sol_bank_mapping")

rows=[];month_counts={}
for m,root in roots.items():
    exp=EXPECTED[m]
    fh=find_json(root,lambda o:o.get("partition_id")==exp["partition_id"])
    if len(fh)!=1:
        errors.append(f"{m}:field_hit_count:{len(fh)}");continue
    o=fh[0][1]
    if o.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":errors.append(f"{m}:not_pass")
    if o.get("protocol")!="marginfi" or o.get("instruction_class")!="lending_account_liquidate":errors.append(f"{m}:identity_mismatch")
    if o.get("effective_start")!=exp["start"] or o.get("effective_end")!=exp["end"]:errors.append(f"{m}:window_mismatch")
    for k in ("missing_count","extra_count","duplicate_count","semantic_conflict_count","baseline_anomaly_count"):
        if int(o.get(k,-1))!=0:errors.append(f"{m}:{k}_nonzero")
    month=[]
    for r in o.get("enriched_rows") or []:
        sem=r.get("semantic_accounts") or {}
        if sem.get("asset_bank") not in solbanks:continue
        liab=sem.get("liab_bank")
        month.append({
          "month":m,
          "signature":r["signature"],
          "slot":r["slot"],
          "timestamp":r["timestamp"],
          "transactionIndex":r.get("transactionIndex"),
          "instructionAddress":r["instructionAddress"],
          "asset_bank":sem.get("asset_bank"),
          "liab_bank":liab,
          "asset_mint":SOL,
          "liab_mint":registry.get(liab)
        })
    month_counts[m]=len(month)
    rows.extend(month)

rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
ids=[ident(r) for r in rows]
dup=len(ids)-len(set(ids))
if dup:errors.append(f"duplicate_identity_count:{dup}")

with POP.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

classification="MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_PASS" if not errors and len(rows)>0 else "MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_BLOCKED"
receipt={
 "schema_version":"0.1",
 "classification":classification,
 "authority":"MARGINFI_ORCA_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "month_population_counts":month_counts,
 "population_count":len(rows),
 "duplicate_identity_count":dup,
 "error_count":len(errors),
 "errors":errors,
 "population_file":str(POP),
 "population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
             "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_PASS":raise SystemExit(2)
