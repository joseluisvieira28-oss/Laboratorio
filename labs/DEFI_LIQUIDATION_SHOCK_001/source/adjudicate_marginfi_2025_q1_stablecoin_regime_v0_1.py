#!/usr/bin/env python3
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_PERSISTENCE_RECEIPT_V0.1.json"

hits=sorted(Path(args.source_root).rglob("MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_RECEIPT_V0.1.json"))
if len(hits)!=1:
    rec={"classification":"MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_SOURCE_BLOCKED",
         "stage":"authority","detail":f"receipt_hit_count={len(hits)}"}
else:
    src=json.loads(hits[0].read_text())
    if src.get("classification")!="MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_PASS":
        rec={"classification":"MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_SOURCE_BLOCKED",
             "stage":"authority","source_classification":src.get("classification")}
    else:
        monthly=src.get("monthly") or {}
        sufficient={};dominant={}
        for m in ("202501","202502","202503"):
            r=monthly.get(m) or {}
            n=int(r.get("sol_collateral_event_count") or 0)
            share=r.get("usdc_usdt_combined_share")
            sufficient[m]=n>=30
            dominant[m]=bool(sufficient[m] and isinstance(share,(int,float)) and share>=0.80)
        gates={
          "source_pass":True,
          "q1_sol_events_ge_100":int(src.get("q1_sol_collateral_event_count") or 0)>=100,
          "q1_stablecoin_share_ge_0_80":isinstance(src.get("q1_usdc_usdt_combined_share"),(int,float)) and src["q1_usdc_usdt_combined_share"]>=0.80,
          "sufficient_months_ge_2":sum(sufficient.values())>=2,
          "stablecoin_dominant_months_ge_2":sum(dominant.values())>=2
        }
        classification="MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_PERSISTS" if all(gates.values()) else "MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_NOT_PROVEN"
        rec={"schema_version":"0.1","classification":classification,
             "authority":"MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_PERSISTENCE_GATE_FREEZE_V0.1.md",
             "source_classification":src.get("classification"),
             "q1_sol_collateral_event_count":src.get("q1_sol_collateral_event_count"),
             "q1_usdc_usdt_combined_share":src.get("q1_usdc_usdt_combined_share"),
             "monthly_sufficient":sufficient,"monthly_stablecoin_dominant":dominant,
             "monthly":monthly,"gate":gates}
rec["firewall"]={"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
                 "funding_2025_opened":False,"market_direction_2025_opened":False,
                 "prices_2026_opened":False,"returns_2026_opened":False,"live_trading":False,
                 "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,indent=2,sort_keys=True))
if rec["classification"]=="MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_SOURCE_BLOCKED":
    raise SystemExit(2)
