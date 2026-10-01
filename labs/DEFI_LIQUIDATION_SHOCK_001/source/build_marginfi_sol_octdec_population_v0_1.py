#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"
EXPECTED={
 "marginfi-202410":{"start":"2024-10-01T00:00:00Z","end":"2024-11-01T00:00:00Z","count":1432},
 "marginfi-202411":{"start":"2024-11-01T00:00:00Z","end":"2024-12-01T00:00:00Z","count":10141},
 "marginfi-202412":{"start":"2024-12-01T00:00:00Z","end":"2025-01-01T00:00:00Z","count":4880},
}

ap=argparse.ArgumentParser()
ap.add_argument("--field-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_OCTDEC_POPULATION_RECEIPT_V0.1.json"
POP=OUT/"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_V0.1.ndjson"

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])

def all_json(root):
    for p in Path(root).rglob("*.json"):
        try:yield p,json.loads(p.read_text())
        except Exception:pass

bank_hits=[(p,o) for p,o in all_json(args.bank_registry_root)
           if o.get("classification")=="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS"]
errors=[]
if len(bank_hits)!=1:errors.append(f"bank_registry_hit_count={len(bank_hits)}")
registry={}
if bank_hits:
    registry={x["bank"]:x["mint"] for x in bank_hits[0][1].get("bank_registry") or []}
solbanks={b for b,m in registry.items() if m==SOL}
if not solbanks:errors.append("no_sol_bank_mapping")

parts={}
for p,o in all_json(args.field_root):
    pid=o.get("partition_id")
    if pid in EXPECTED:parts.setdefault(pid,[]).append((p,o))
for pid in EXPECTED:
    if len(parts.get(pid,[]))!=1:errors.append(f"{pid}:hit_count={len(parts.get(pid,[]))}")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_OCTDEC_POPULATION_BLOCKED","errors":errors},indent=2)+"\n")
    POP.write_text("");raise SystemExit(2)

rows=[];monthly={}
for pid,e in EXPECTED.items():
    o=parts[pid][0][1]
    perr=[]
    if o.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":perr.append("not_pass")
    if o.get("protocol")!="marginfi" or o.get("instruction_class")!="lending_account_liquidate":perr.append("identity")
    if o.get("effective_start")!=e["start"] or o.get("effective_end")!=e["end"]:perr.append("window")
    if int(o.get("baseline_success_count",-1))!=e["count"] or int(o.get("enriched_success_count",-1))!=e["count"]:perr.append("count")
    for k in ("missing_count","extra_count","duplicate_count","semantic_conflict_count","baseline_anomaly_count"):
        if int(o.get(k,-1))!=0:perr.append(k)
    if perr:errors.append(f"{pid}:{','.join(perr)}");continue
    solrows=[]
    for r in o.get("enriched_rows") or []:
        sem=r.get("semantic_accounts") or {}
        if sem.get("asset_bank") not in solbanks:continue
        solrows.append({
          "signature":r["signature"],"slot":r["slot"],"timestamp":r["timestamp"],
          "transactionIndex":r.get("transactionIndex"),"instructionAddress":r["instructionAddress"],
          "asset_bank":sem.get("asset_bank"),"liab_bank":sem.get("liab_bank"),
          "asset_mint":SOL,"liab_mint":registry.get(sem.get("liab_bank")),
          "partition_id":pid
        })
    monthly[pid]=len(solrows);rows.extend(solrows)

rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
ids=[ident(r) for r in rows]
dup=len(ids)-len(set(ids))
if dup:errors.append(f"duplicate_sol_identity={dup}")
unmapped=sum(1 for r in rows if not r.get("liab_mint"))
if unmapped:errors.append(f"unmapped_liability_mint={unmapped}")

classification="MARGINFI_SOL_OCTDEC_POPULATION_PASS" if not errors and rows else "MARGINFI_SOL_OCTDEC_POPULATION_BLOCKED"
with POP.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
rec={
 "schema_version":"0.1","classification":classification,
 "authority":"MARGINFI_ORCA_TOPQ_REBOUND_OOS_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "field_partition_counts":{"marginfi-202410":1432,"marginfi-202411":10141,"marginfi-202412":4880},
 "sol_population_month_counts":monthly,"sol_population_count":len(rows),
 "duplicate_identity_count":dup,"unmapped_liability_mint_count":unmapped,
 "error_count":len(errors),"errors":errors,
 "population_file":str(POP),"population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
             "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,indent=2,sort_keys=True))
if classification!="MARGINFI_SOL_OCTDEC_POPULATION_PASS":raise SystemExit(2)
