#!/usr/bin/env python3
"""Outcome-blind 2024 replication preflight for AAVE-LIQUIDATION-OVERHANG-001."""
from __future__ import annotations
import json, sys
from pathlib import Path

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
FROM_BLOCK=16_490_000
TO_BLOCK=21_525_890

def load_r0():
    hits=[]
    for p in Path("downloaded_r0_bootstrap").rglob("*.json"):
        x=json.loads(p.read_text())
        if x.get("classification")=="RECONSTRUCTION_R0_BOOTSTRAP_PASS":
            hits.append((p,x))
    if len(hits)!=1:
        raise RuntimeError(f"expected exactly one canonical R0 bootstrap, got {len(hits)}")
    return hits[0]

def main():
    out=Path("replication_2024_preflight_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_2024_REPLICATION_PREFLIGHT_V0_1.json"
    try:
        p,x=load_r0()
        if int(x.get("frozen_from_block"))!=FROM_BLOCK or int(x.get("frozen_to_block"))!=TO_BLOCK:
            raise RuntimeError("R0 envelope mismatch")
        reserves={str(u).lower():m for u,m in (x.get("reserves") or {}).items()}
        if len(reserves)!=37:
            raise RuntimeError(f"canonical reserve master !=37: {len(reserves)}")
        active={u:m for u,m in reserves.items() if int(m["init_block"])<=TO_BLOCK}
        future={u:m for u,m in reserves.items() if int(m["init_block"])>TO_BLOCK}
        init_blocks=sorted({int(m["init_block"]) for m in active.values()})
        receipt={
            "lab_id":LAB_ID,
            "classification":"REPLICATION_2024_PREFLIGHT_PASS",
            "canonical_r0_receipt":str(p),
            "frozen_from_block":FROM_BLOCK,
            "frozen_to_block":TO_BLOCK,
            "master_reserve_count":len(reserves),
            "active_by_2024_end_count":len(active),
            "future_after_2024_count":len(future),
            "active_reserves":sorted(active),
            "future_reserves":sorted(future),
            "activation_block_min":min(init_blocks) if init_blocks else None,
            "activation_block_max":max(init_blocks) if init_blocks else None,
            "snapshot_date_start":"2024-01-01",
            "snapshot_date_end":"2024-12-31",
            "expected_snapshot_count":366,
            "hard_timestamp_ceiling":"2024-12-31T23:59:59Z",
            "safety":{
                "predictor_computed":False,
                "liquidation_outcomes_opened":False,
                "market_returns_opened":False,
                "pnl_opened":False,
                "opened_2025_or_2026":False,
                "live_trading":False,
                "exchange_mutation":False
            }
        }
    except Exception as exc:
        receipt={
            "lab_id":LAB_ID,
            "classification":"REPLICATION_2024_PREFLIGHT_FAILURE",
            "failure":f"{type(exc).__name__}: {str(exc)[:1200]}",
            "safety":{"predictor_computed":False,"liquidation_outcomes_opened":False,
                      "market_returns_opened":False,"pnl_opened":False,
                      "opened_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:receipt.get(k) for k in [
        "classification","master_reserve_count","active_by_2024_end_count",
        "future_after_2024_count","expected_snapshot_count"]},sort_keys=True))
    return 0 if receipt["classification"]=="REPLICATION_2024_PREFLIGHT_PASS" else 2

if __name__=="__main__":
    sys.exit(main())
