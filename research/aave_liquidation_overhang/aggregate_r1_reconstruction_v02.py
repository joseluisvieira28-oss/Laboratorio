#!/usr/bin/env python3
"""Canonical R1 adjudicator V0.2 — preserves component terminal failure class."""
from __future__ import annotations
import hashlib,json,sys
from collections import Counter
from pathlib import Path

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"; FROM_BLOCK=16_490_000; TO_BLOCK=21_525_890
EXPECTED_SHARDS=set(range(8))
FAIL_PRECEDENCE=["RECONSTRUCTION_PROVENANCE_FAILURE","RECONSTRUCTION_RECONCILIATION_FAILURE","RECONSTRUCTION_INSUFFICIENT_COVERAGE","RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"]

def js(root): return [json.loads(p.read_text(encoding="utf-8")) for p in Path(root).rglob("*.json")]
def exactly_one(root):
    xs=js(root)
    if len(xs)!=1: raise RuntimeError(f"expected exactly one receipt in {root}, got {len(xs)}")
    return xs[0]
def fail_class(classes):
    for c in FAIL_PRECEDENCE:
        if c in classes: return c
    return "RECONSTRUCTION_RECONCILIATION_FAILURE"

def main():
    out=Path("r1_canonical_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R1_CANONICAL_V0_2.json"
    try:
        audit=exactly_one("downloaded_r1_audit"); glob=exactly_one("downloaded_r1_global"); bootstrap=exactly_one("downloaded_r0_bootstrap"); shards=js("downloaded_r1_shards")
        components={"audit":audit.get("classification"),"global":glob.get("classification"),"shards":{str(s.get("shard_id")):s.get("classification") for s in shards}}
        expected_pass=[audit.get("classification")=="R1_AUDIT_PASS",glob.get("classification")=="R1_GLOBAL_STATE_PASS",len(shards)==8,all(s.get("classification")=="R1_RESERVE_SHARD_PASS" for s in shards)]
        if not all(expected_pass):
            classes=[audit.get("classification"),glob.get("classification")]+[s.get("classification") for s in shards]
            classification=fail_class(classes)
            receipt={"classification":classification,"failure":"one or more mandatory R1 components did not pass","component_status":components,"next_authorized_phase":None}
        else:
            if bootstrap.get("classification")!="RECONSTRUCTION_R0_BOOTSTRAP_PASS": raise RuntimeError("R0 bootstrap not canonical pass")
            ids={int(s["shard_id"]) for s in shards}
            if ids!=EXPECTED_SHARDS: raise RuntimeError(f"shard ids mismatch {sorted(ids)}")
            reserves=[]; counts=Counter(); dig=hashlib.sha256()
            for s in sorted(shards,key=lambda x:int(x["shard_id"])):
                if int(s.get("frozen_from_block"))!=FROM_BLOCK or int(s.get("frozen_to_block"))!=TO_BLOCK: raise RuntimeError("shard envelope mismatch")
                reserves.extend(s.get("selected_reserves") or []); counts.update(s.get("event_counts") or {}); dig.update((str(s.get("canonical_log_digest_sha256"))+"\n").encode())
            expected_reserves={x.lower() for x in bootstrap["reserves"]}
            if len(reserves)!=37 or len(set(reserves))!=37 or set(reserves)!=expected_reserves: raise RuntimeError("reserve union is not exact canonical 37")
            r0=bootstrap.get("config_provider_event_counts") or {}
            checks={k:int(r0.get(k,0)) for k in ["CollateralConfigurationChanged","ReserveFrozen","ReservePaused","ATokenUpgraded","VariableDebtTokenUpgraded"]}
            mism={k:{"r0":v,"r1":int(counts.get(k,0))} for k,v in checks.items() if int(counts.get(k,0))!=v}
            if mism: raise RuntimeError(f"R0/R1 config coverage mismatch {mism}")
            if int((glob.get("event_counts") or {}).get("EModeCategoryAdded",0))!=int(r0.get("EModeCategoryAdded",0)): raise RuntimeError("R0/R1 eMode coverage mismatch")
            receipt={"classification":"RECONSTRUCTION_DATA_PASS","failure":None,"component_status":components,"reserve_count":37,"reserve_shard_count":8,
                     "reserve_shard_event_counts":dict(sorted(counts.items())),"reserve_config_coverage_checks":checks,"reserve_config_coverage_mismatches":mism,
                     "audit_sample_size":len(audit.get("sample_borrowers") or []),"audit_validation_target_count":audit.get("validation_target_count"),"audit_validated_target_count":audit.get("validated_target_count"),
                     "global_emode_category_count":glob.get("emode_category_count"),"global_user_emode_state_count":glob.get("user_emode_state_count"),
                     "oracle_price_validation_target_count":glob.get("oracle_price_validation_target_count"),"oracle_price_validation_failure_count":glob.get("oracle_price_validation_failure_count"),
                     "aggregate_shard_digest_sha256":dig.hexdigest(),"mandatory_gate_results":{"reserve_identity":"PASS","coverage":"PASS","scaled_collateral_conservation":"PASS","scaled_debt_conservation_nontransferability":"PASS","collateral_flags":"PASS","emode":"PASS","reserve_indices":"PASS","oracle_provenance":"PASS","independent_validation_sample":"PASS","protected_period_firewall":"PASS"},"next_authorized_phase":"FINAL_PRE_DISCOVERY_PROTOCOL"}
    except Exception as exc:
        receipt={"classification":"RECONSTRUCTION_RECONCILIATION_FAILURE","failure":f"{type(exc).__name__}: {str(exc)[:1500]}","next_authorized_phase":None}
    receipt.update({"lab_id":LAB_ID,"phase":"R1_FULL_STATE_RECONSTRUCTION_CANONICAL_V0_2_OUTCOME_BLIND","frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,
                    "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_returns_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}})
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"reserve_count":receipt.get("reserve_count"),"next_authorized_phase":receipt.get("next_authorized_phase"),"health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="RECONSTRUCTION_DATA_PASS" else 2
if __name__=="__main__": sys.exit(main())
