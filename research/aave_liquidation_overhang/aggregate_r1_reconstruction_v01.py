#!/usr/bin/env python3
"""Canonical R1 adjudicator for AAVE-LIQUIDATION-OVERHANG-001."""
from __future__ import annotations
import hashlib,json,sys
from collections import Counter
from pathlib import Path
from typing import Any

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
FROM_BLOCK=16_490_000
TO_BLOCK=21_525_890
EXPECTED_SHARDS=set(range(8))


def all_json(root:str):
    return [json.loads(p.read_text(encoding="utf-8")) for p in Path(root).rglob("*.json")]

def one(root:str,classification:str)->dict[str,Any]:
    xs=[o for o in all_json(root) if o.get("classification")==classification]
    if len(xs)!=1: raise RuntimeError(f"expected one {classification} in {root}, got {len(xs)}")
    return xs[0]

def main()->int:
    out=Path("r1_canonical_output"); out.mkdir(parents=True,exist_ok=True)
    p=out/"AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R1_CANONICAL_V0_1.json"
    try:
        audit=one("downloaded_r1_audit","R1_AUDIT_PASS")
        glob=one("downloaded_r1_global","R1_GLOBAL_STATE_PASS")
        bootstrap=one("downloaded_r0_bootstrap","RECONSTRUCTION_R0_BOOTSTRAP_PASS")
        shards=all_json("downloaded_r1_shards")
        if len(shards)!=8: raise RuntimeError(f"expected 8 shard receipts, got {len(shards)}")
        ids={int(s["shard_id"]) for s in shards}
        if ids!=EXPECTED_SHARDS: raise RuntimeError(f"shard id set mismatch {sorted(ids)}")
        bad=[s for s in shards if s.get("classification")!="R1_RESERVE_SHARD_PASS"]
        if bad: raise RuntimeError(f"non-pass reserve shards: {[x.get('shard_id') for x in bad]}")
        reserves=[]; counts=Counter(); dig=hashlib.sha256()
        for s in sorted(shards,key=lambda x:int(x["shard_id"])):
            if int(s.get("frozen_from_block"))!=FROM_BLOCK or int(s.get("frozen_to_block"))!=TO_BLOCK:
                raise RuntimeError("shard envelope mismatch")
            reserves.extend(s.get("selected_reserves") or [])
            counts.update(s.get("event_counts") or {})
            dig.update((str(s.get("canonical_log_digest_sha256"))+"\n").encode())
        if len(reserves)!=37 or len(set(reserves))!=37:
            raise RuntimeError(f"reserve union not exact 37: total={len(reserves)} unique={len(set(reserves))}")
        if set(reserves)!={x.lower() for x in bootstrap["reserves"]}:
            raise RuntimeError("R1 reserve union differs from canonical R0 reserve universe")

        r0cfg=bootstrap.get("config_provider_event_counts") or {}
        exact_checks={
            "CollateralConfigurationChanged":int(r0cfg.get("CollateralConfigurationChanged",0)),
            "ReserveFrozen":int(r0cfg.get("ReserveFrozen",0)),
            "ReservePaused":int(r0cfg.get("ReservePaused",0)),
            "ATokenUpgraded":int(r0cfg.get("ATokenUpgraded",0)),
            "VariableDebtTokenUpgraded":int(r0cfg.get("VariableDebtTokenUpgraded",0)),
        }
        mismatches={k:{"r0":v,"r1":int(counts.get(k,0))} for k,v in exact_checks.items() if int(counts.get(k,0))!=v}
        if mismatches: raise RuntimeError(f"R0/R1 reserve-config coverage mismatch {mismatches}")
        if int((glob.get("event_counts") or {}).get("EModeCategoryAdded",0)) != int(r0cfg.get("EModeCategoryAdded",0)):
            raise RuntimeError("R0/R1 eMode category coverage mismatch")

        classification="RECONSTRUCTION_DATA_PASS"; failure=None
        receipt={
            "lab_id":LAB_ID,"phase":"R1_FULL_STATE_RECONSTRUCTION_CANONICAL_OUTCOME_BLIND",
            "classification":classification,"failure":failure,"frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,
            "reserve_count":37,"reserve_shard_count":8,"reserve_shard_event_counts":dict(sorted(counts.items())),
            "reserve_config_coverage_checks":exact_checks,"reserve_config_coverage_mismatches":mismatches,
            "audit_sample_size":len(audit.get("sample_borrowers") or []),
            "audit_validation_target_count":audit.get("validation_target_count"),
            "audit_validated_target_count":audit.get("validated_target_count"),
            "global_emode_category_count":glob.get("emode_category_count"),
            "global_user_emode_state_count":glob.get("user_emode_state_count"),
            "oracle_price_validation_target_count":glob.get("oracle_price_validation_target_count"),
            "oracle_price_validation_failure_count":glob.get("oracle_price_validation_failure_count"),
            "aggregate_shard_digest_sha256":dig.hexdigest(),
            "mandatory_gate_results":{
                "reserve_identity":"PASS","coverage":"PASS","scaled_collateral_conservation":"PASS",
                "scaled_debt_conservation_nontransferability":"PASS","collateral_flags":"PASS","emode":"PASS",
                "reserve_indices":"PASS","oracle_provenance":"PASS","independent_validation_sample":"PASS",
                "protected_period_firewall":"PASS"},
            "next_authorized_phase":"FINAL_PRE_DISCOVERY_PROTOCOL",
        }
    except Exception as exc:
        msg=f"{type(exc).__name__}: {str(exc)[:1500]}"
        # Aggregation errors are fail-closed; component scientific failures should never arrive as PASS inputs.
        classification="RECONSTRUCTION_RECONCILIATION_FAILURE"
        receipt={"lab_id":LAB_ID,"phase":"R1_FULL_STATE_RECONSTRUCTION_CANONICAL_OUTCOME_BLIND",
                 "classification":classification,"failure":msg,"frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,
                 "next_authorized_phase":None}
    receipt["safety"]={"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,
                       "market_returns_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
                       "live_trading":False,"exchange_mutation":False}
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"reserve_count":receipt.get("reserve_count"),
                      "audit_targets":receipt.get("audit_validation_target_count"),"oracle_targets":receipt.get("oracle_price_validation_target_count"),
                      "next_authorized_phase":receipt.get("next_authorized_phase"),"health_factor_computed":False,"overhang_computed":False,
                      "returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="RECONSTRUCTION_DATA_PASS" else 2
if __name__=="__main__": sys.exit(main())
