#!/usr/bin/env python3
import json, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import discovery_v01 as d

ROOT=Path("research/binance_premium_compression")
AUTH=d.AUTH
VAUTH=json.loads((ROOT/"BPC_VALIDATION_2024_AUTHORITY_V0_1.json").read_text())
OUT=Path("artifacts/binance_premium_compression_validation_2024_v01")
OUT.mkdir(parents=True,exist_ok=True)

d.START=datetime(2024,1,1,tzinfo=timezone.utc)
d.END=datetime(2025,1,1,tzinfo=timezone.utc)

def main():
    assert VAUTH["status"]=="FROZEN_BLOCKED_PENDING_PARENT_DISCOVERY_SURVIVES"
    assert VAUTH["parent_discovery_run"]==35324193354
    assert VAUTH["rules_identical"] is True
    assert AUTH["signal"]["threshold"]==3.0
    assert AUTH["signal"]["rolling_window_bars"]==2016
    assert AUTH["execution"]["max_hold_bars"]==12
    assert AUTH["execution"]["base_round_trip_pair_cost_fraction"]==0.003
    assert AUTH["execution"]["stress_round_trip_pair_cost_fraction"]==0.004

    result={
      "validation_id":VAUTH["validation_id"],"parent_discovery_run":VAUTH["parent_discovery_run"],
      "classification":None,"year_2024_opened":True,"year_2025_opened":False,"year_2026_opened":False,
      "live_trading":False,"exchange_mutation":False,"orders":False,"merge_to_main":False
    }
    source_receipts=[];coverage_doc={};all_trades=[];source_failures=[];execution_unresolved=0
    try:
        for asset,sym in d.ASSETS.items():
            prem,perp,spot,rc=d.merge_months(sym);source_receipts.extend(rc)
            trades,diag=d.simulate(asset,prem,perp,spot)
            all_trades.extend(trades);coverage_doc[asset]=diag
            source_failures.extend(diag["source_failures"]);execution_unresolved+=diag["execution_unresolved"]
        all_trades=sorted(all_trades,key=lambda x:(x["entry_ts"],x["asset"]))
        bm=d.metrics(all_trades,"base_net_bps");sm=d.metrics(all_trades,"stress_net_bps")
        byasset={a:d.metrics([t for t in all_trades if t["asset"]==a],"base_net_bps") for a in d.ASSETS}
        conc=d.concentration(all_trades,"base_net_bps") if all_trades else None
        g=VAUTH["gates_all_required"]
        gates={
          "sample_floor":bm["n"]>=VAUTH["sample_floor_resolved_trades"],
          "base_mean_net_bps_gt":bm["mean_bps"] is not None and bm["mean_bps"]>g["base_mean_net_bps_gt"],
          "base_profit_factor_gt":bm["profit_factor"] is not None and bm["profit_factor"]>g["base_profit_factor_gt"],
          "stress_mean_net_bps_gt":sm["mean_bps"] is not None and sm["mean_bps"]>g["stress_mean_net_bps_gt"],
          "stress_profit_factor_gt":sm["profit_factor"] is not None and sm["profit_factor"]>g["stress_profit_factor_gt"],
          "btc_only_mean_net_bps_gt":byasset["BTC"]["mean_bps"] is not None and byasset["BTC"]["mean_bps"]>g["btc_only_mean_net_bps_gt"],
          "eth_only_mean_net_bps_gt":byasset["ETH"]["mean_bps"] is not None and byasset["ETH"]["mean_bps"]>g["eth_only_mean_net_bps_gt"],
          "max_positive_month_share_lte":conc is not None and conc<=g["max_positive_month_share_lte"],
          "source_integrity_failures_eq":len(source_failures)==0,
          "execution_unresolved_eq":execution_unresolved==0
        }
        cls="INDEPENDENT_VALIDATION_SURVIVES" if all(gates.values()) else "INDEPENDENT_VALIDATION_FAIL"
        result.update({
          "classification":cls,"coverage":coverage_doc,"base_metrics":bm,"stress_metrics":sm,
          "by_asset":byasset,"max_positive_month_share":conc,"validation_gates":gates,
          "source_failures":source_failures,"execution_unresolved":execution_unresolved,
          "source_receipt_sha256":d.sha(json.dumps(source_receipts,sort_keys=True).encode()),
          "trades_base":all_trades
        })
    except Exception as e:
        result["classification"]="TECHNICAL_FAILURE";result["reason"]=f"{type(e).__name__}:{e}"
    p=OUT/"validation_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="trades_base"},indent=2,sort_keys=True,allow_nan=False))
    return 2 if result["classification"]=="TECHNICAL_FAILURE" else 0

if __name__=="__main__":
    sys.exit(main())
