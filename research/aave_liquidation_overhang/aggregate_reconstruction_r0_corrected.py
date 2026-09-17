#!/usr/bin/env python3
"""Canonical corrected R0 aggregator for AAVE-LIQUIDATION-OVERHANG-001.

Consumes only previously produced outcome-blind component receipts:
- sharded bootstrap aggregate,
- token replay primitive probe,
- identity/pagination-corrected oracle bootstrap provenance V0.2.2.

No protocol acquisition, HF, overhang, future outcomes, returns or PnL occur here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
EXPECTED_PROVIDER="0x2f39d218133afab8f2b819b1066c7e434ad94e9e"
EXPECTED_ORACLE="0x54586be62e3c3580375ae3723c145253060ca0c2"
BOOTSTRAP_RUN_ID=35218275356
ORACLE_RUN_ID=35223450025


def one_json(root: str) -> tuple[Path,dict]:
    files=sorted(Path(root).rglob("*.json"))
    if len(files)!=1:
        raise RuntimeError(f"expected exactly one JSON under {root}, got {len(files)}")
    p=files[0]
    return p,json.loads(p.read_text(encoding="utf-8"))


def sha256_file(p:Path)->str:
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()


def safety_clean(x:dict)->bool:
    s=x.get("safety") or {}
    forbidden=[
        "health_factor_computed","overhang_computed","future_liquidation_outcome_computed",
        "market_return_prices_opened","returns_opened","pnl_opened","accessed_2025_or_2026",
        "live_trading","exchange_mutation",
    ]
    return all(not bool(s.get(k,False)) for k in forbidden)


def main()->int:
    failure=None
    try:
        bp,bootstrap=one_json("r0_parts/bootstrap")
        tp,token=one_json("r0_parts/token")
        op,oracle=one_json("r0_parts/oracle")

        if bootstrap.get("lab_id")!=LAB_ID or token.get("lab_id")!=LAB_ID or oracle.get("lab_id")!=LAB_ID:
            raise RuntimeError("component lab_id mismatch")
        if bootstrap.get("classification")!="RECONSTRUCTION_R0_BOOTSTRAP_PASS":
            raise RuntimeError(f"bootstrap not pass: {bootstrap.get('classification')}")
        if token.get("classification")!="RECONSTRUCTION_R0_TOKEN_ROUTE_PASS":
            raise RuntimeError(f"token route not pass: {token.get('classification')}")
        if oracle.get("classification")!="ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2_2":
            raise RuntimeError(f"corrected oracle provenance not pass: {oracle.get('classification')}")
        if oracle.get("corrected_provider","").lower()!=EXPECTED_PROVIDER:
            raise RuntimeError("corrected provider identity mismatch")
        if oracle.get("active_oracle_at_activation","").lower()!=EXPECTED_ORACLE:
            raise RuntimeError("activation oracle mismatch")
        if not oracle.get("identity_erratum_applied") or not oracle.get("transport_pagination_fix_applied"):
            raise RuntimeError("required technical errata markers missing")

        reserve_count=int(bootstrap.get("reserve_count",0))
        borrow_count=int(bootstrap.get("borrow_event_count",0))
        modes=bootstrap.get("borrow_interest_rate_mode_counts") or {}
        exact_shards=bootstrap.get("exact_shard_coverage") or []
        if reserve_count<1 or borrow_count<1 or set(modes)!={"2"} or int(modes.get("2",0))!=borrow_count:
            raise RuntimeError("bootstrap reserve/borrow invariants failed")
        if len(exact_shards)!=8:
            raise RuntimeError("expected 8 exact R0 shards")
        prev=None
        for s in exact_shards:
            a=int(s["from_block"]); b=int(s["to_block"])
            if b<a: raise RuntimeError("invalid shard range")
            if prev is not None and a!=prev+1: raise RuntimeError("R0 shard gap/overlap")
            prev=b
        if int(exact_shards[0]["from_block"])!=16_490_000 or int(exact_shards[-1]["to_block"])!=21_525_890:
            raise RuntimeError("R0 shard envelope mismatch")

        tr=token.get("result") or {}
        events=tr.get("event_counts") or {}
        required_token=["aToken_BalanceTransfer","aToken_Mint","aToken_Burn","vDebt_Mint","vDebt_Burn"]
        if int(tr.get("abi_shape_failures",-1))!=0 or any(int(events.get(k,0))<1 for k in required_token):
            raise RuntimeError("token replay primitives insufficient")
        if int(tr.get("aToken_count",0))!=reserve_count or int(tr.get("variableDebtToken_count",0))!=reserve_count:
            raise RuntimeError("token/reserve identity count mismatch")

        oc=oracle.get("oracle_bootstrap_event_counts") or {}
        if int(oc.get("AssetSourceUpdated",0))<1 or int(oc.get("BaseCurrencySet",0))<1:
            raise RuntimeError("oracle bootstrap configuration evidence incomplete")
        transitions=oracle.get("provider_oracle_registry_transitions") or []
        if len(transitions)<1:
            raise RuntimeError("provider oracle registry transition missing")
        first=oracle.get("first_reserve_initialized") or {}
        if int(first.get("block",0))!=16_496_792:
            raise RuntimeError("activation boundary mismatch")
        if not all(safety_clean(x) for x in (bootstrap,token,oracle)):
            raise RuntimeError("component safety firewall violation")

        classification="RECONSTRUCTION_R0_PREFLIGHT_PASS_CORRECTED"
    except Exception as exc:
        classification="RECONSTRUCTION_R0_PREFLIGHT_FAIL_CLOSED"
        failure=f"{type(exc).__name__}: {str(exc)[:1200]}"
        bootstrap=locals().get("bootstrap",{}); token=locals().get("token",{}); oracle=locals().get("oracle",{})
        bp=locals().get("bp"); tp=locals().get("tp"); op=locals().get("op")
        reserve_count=int(bootstrap.get("reserve_count",0) or 0); borrow_count=int(bootstrap.get("borrow_event_count",0) or 0)
        modes=bootstrap.get("borrow_interest_rate_mode_counts") or {}; events=(token.get("result") or {}).get("event_counts") or {}; oc=oracle.get("oracle_bootstrap_event_counts") or {}; transitions=oracle.get("provider_oracle_registry_transitions") or []

    receipt={
        "lab_id":LAB_ID,
        "phase":"RECONSTRUCTION_R0_CANONICAL_REAGGREGATION_OUTCOME_BLIND",
        "classification":classification,
        "upstream_runs":{"bootstrap_and_token":BOOTSTRAP_RUN_ID,"corrected_oracle":ORACLE_RUN_ID},
        "component_receipts":{
            "bootstrap":{"classification":bootstrap.get("classification"),"sha256":sha256_file(bp) if bp else None},
            "token":{"classification":token.get("classification"),"sha256":sha256_file(tp) if tp else None},
            "oracle":{"classification":oracle.get("classification"),"sha256":sha256_file(op) if op else None},
        },
        "identity_erratum":{"corrected_provider":oracle.get("corrected_provider"),"expected_provider":EXPECTED_PROVIDER,"applied":oracle.get("identity_erratum_applied")},
        "transport_erratum":{"sqd_pagination_fix_applied":oracle.get("transport_pagination_fix_applied")},
        "frozen_envelope":{"from_block":16_490_000,"to_block":21_525_890},
        "reserve_count":reserve_count,
        "borrow_event_count":borrow_count,
        "borrow_interest_rate_mode_counts":modes,
        "token_event_counts":events,
        "active_oracle_at_activation":oracle.get("active_oracle_at_activation"),
        "oracle_bootstrap_event_counts":oc,
        "oracle_registry_transition_count":len(transitions),
        "first_reserve_initialized":oracle.get("first_reserve_initialized"),
        "failure":failure,
        "safety":{"source_only":True,"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_return_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False},
        "next_authorized_phase":"R1_FULL_STATE_RECONSTRUCTION" if classification=="RECONSTRUCTION_R0_PREFLIGHT_PASS_CORRECTED" else None,
    }
    out=Path("reconstruction_r0_corrected_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R0_CANONICAL_CORRECTED.json"
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"reserve_count":reserve_count,"borrow_event_count":borrow_count,"borrow_modes":modes,"oracle":oracle.get("active_oracle_at_activation"),"oracle_transition_count":len(transitions),"next_authorized_phase":receipt["next_authorized_phase"],"health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if classification=="RECONSTRUCTION_R0_PREFLIGHT_PASS_CORRECTED" else 2

if __name__=="__main__": sys.exit(main())
