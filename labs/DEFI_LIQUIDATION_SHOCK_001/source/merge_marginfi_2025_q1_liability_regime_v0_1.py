#!/usr/bin/env python3
import argparse,json
from collections import Counter
from pathlib import Path

USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_RECEIPT_V0.1.json"

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])
def load_nd(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

errors=[];months={};allrows=[]
for m in ("202501","202502","202503"):
    rh=sorted(ROOT.rglob(f"MARGINFI_2025_Q1_LIABILITY_REGIME_{m}_RECEIPT_V0.1.json"))
    wh=sorted(ROOT.rglob(f"MARGINFI_2025_Q1_LIABILITY_REGIME_{m}_ROWS_V0.1.ndjson"))
    if len(rh)!=1 or len(wh)!=1:
        errors.append(f"{m}:file_count:{len(rh)}/{len(wh)}");continue
    r=json.loads(rh[0].read_text());w=load_nd(wh[0])
    months[m]=r
    if r.get("classification")!="MARGINFI_2025_Q1_LIABILITY_REGIME_MONTH_PASS":errors.append(f"{m}:not_pass")
    if len(w)!=int(r.get("successful_marginfi_liquidation_count",-1)):errors.append(f"{m}:count_mismatch")
    allrows.extend(w)

ids=[ident(r) for r in allrows];dup=len(ids)-len(set(ids))
if dup:errors.append(f"global_duplicate_identities:{dup}")
sol=[r for r in allrows if r.get("asset_mint")=="So11111111111111111111111111111111111111112"]
liabs=Counter(r.get("liab_mint") for r in sol if r.get("liab_mint"))
usdc=sum(1 for r in sol if r.get("liab_mint")==USDC)
usdt=sum(1 for r in sol if r.get("liab_mint")==USDT)
top=liabs.most_common(10)

classification="MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_PASS" if len(months)==3 and not errors else "MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_BLOCKED"
receipt={
 "schema_version":"0.1","classification":classification,
 "authority":"MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_FREEZE_V0.1.md",
 "month_count":len(months),"monthly":{
   m:{k:months[m].get(k) for k in [
     "successful_marginfi_liquidation_count","sol_collateral_event_count",
     "usdc_liability_count","usdc_liability_share","usdt_liability_count","usdt_liability_share",
     "usdc_usdt_combined_count","usdc_usdt_combined_share","liability_top10","liability_top1_share","liability_top3_share"
   ]} for m in sorted(months)
 },
 "q1_successful_marginfi_liquidation_count":len(allrows),
 "q1_sol_collateral_event_count":len(sol),
 "q1_usdc_liability_count":usdc,"q1_usdc_liability_share":usdc/len(sol) if sol else None,
 "q1_usdt_liability_count":usdt,"q1_usdt_liability_share":usdt/len(sol) if sol else None,
 "q1_usdc_usdt_combined_count":usdc+usdt,
 "q1_usdc_usdt_combined_share":(usdc+usdt)/len(sol) if sol else None,
 "q1_distinct_liability_mint_count":len(liabs),"q1_liability_top10":top,
 "q1_liability_top1_share":top[0][1]/len(sol) if sol and top else None,
 "q1_liability_top3_share":sum(n for _,n in top[:3])/len(sol) if sol else None,
 "global_duplicate_identity_count":dup,"error_count":len(errors),"errors":errors,
 "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
             "funding_2025_opened":False,"market_direction_2025_opened":False,
             "prices_2026_opened":False,"returns_2026_opened":False,"token_amounts":False,
             "oracle_values":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_PASS":raise SystemExit(2)
