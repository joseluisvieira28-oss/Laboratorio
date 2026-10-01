#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
SOL="So11111111111111111111111111111111111111112"
ap=argparse.ArgumentParser()
ap.add_argument("--field-root",required=True)
ap.add_argument("--bank-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
POP=OUT/"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_V0.2.ndjson"
REC=OUT/"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_RECEIPT_V0.2.json"
def one(root,name):
 h=sorted(Path(root).rglob(name));return h[0] if len(h)==1 else None
bank=one(args.bank_root,"MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.2.json")
if not bank:raise SystemExit("bank_registry_missing")
br=json.loads(bank.read_text())
if br.get("classification")!="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS":raise SystemExit("bank_registry_not_pass")
bm={x["bank"]:x["mint"] for x in br["bank_registry"]}
rows=[];month_all={};month_sol={};errors=[]
for m in ("202410","202411","202412"):
 f=one(args.field_root,f"marginfi-{m}.json")
 if not f:errors.append(f"{m}:field_missing");continue
 d=json.loads(f.read_text())
 if d.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":errors.append(f"{m}:not_pass");continue
 er=d.get("enriched_rows") or [];month_all[m]=len(er);n=0
 for x in er:
  sa=x.get("semantic_accounts") or {};ab=sa.get("asset_bank");lb=sa.get("liab_bank")
  am=bm.get(ab);lm=bm.get(lb)
  if not am or not lm:errors.append(f"{m}:bank_unmapped:{ab}:{lb}");continue
  if am!=SOL:continue
  rows.append({"signature":x["signature"],"slot":x["slot"],"timestamp":x["timestamp"],
    "transactionIndex":x["transactionIndex"],"instructionAddress":x["instructionAddress"],
    "asset_bank":ab,"liab_bank":lb,"asset_mint":am,"liab_mint":lm})
  n+=1
 month_sol[m]=n
def ak(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
ids=[r["signature"]+"|"+ak(r["instructionAddress"]) for r in rows]
dup=len(ids)-len(set(ids))
rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],ak(r["instructionAddress"])))
with POP.open("w") as f:
 for r in rows:f.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
cls="MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_PASS" if not errors and dup==0 and rows else "MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_BLOCKED"
rec={"schema_version":"0.2","classification":cls,"authority":"MARGINFI_ORCA_FORCED_FLOW_IMPACT_V0_2_CLEAN_PERIOD_FREEZE_2026-10-01.md",
"canonical_marginfi_count":sum(month_all.values()),"sol_population_count":len(rows),"month_marginfi_counts":month_all,
"month_sol_counts":month_sol,"duplicate_identity_count":dup,"error_count":len(errors),"errors":errors[:100],
"population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
"firewall":{"prices":False,"returns":False,"pnl":False,"oct_dec_market_outcomes_opened":False,
"market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}}
REC.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");print(json.dumps(rec,indent=2,sort_keys=True))
if cls.endswith("BLOCKED"):raise SystemExit(2)
