#!/usr/bin/env python3
"""AAVE R1 V0.3 global-state/oracle wrapper with frozen archive provider set."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("base_global", HERE/"r1_global_state_v01.py")
base=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)

PROVIDERS=[
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]
AUTHORITY="AAVE_LIQUIDATION_OVERHANG_001_R1_CONTINUATION_ORCHESTRATION_FREEZE_V0_3"


def main()->int:
    base.RPC_ENDPOINTS=list(PROVIDERS)
    rc=base.main()
    path=Path("r1_global_state_output")/"AAVE_LIQUIDATION_OVERHANG_001_R1_GLOBAL_STATE_V0_1.json"
    if not path.exists():
        raise SystemExit("global-state receipt missing")
    obj=json.loads(path.read_text(encoding="utf-8"))
    stats=obj.get("archive_rpc_stats") or {}
    if set(stats)!=set(PROVIDERS):
        obj["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        obj["failure"]="V0.3 provider-set binding mismatch"
        rc=2
    obj["provider_set_amendment"]=AUTHORITY
    obj["archive_rpc_provider_set"]=PROVIDERS
    obj["archive_rpc_provider_count"]=len(PROVIDERS)
    obj["archive_rpc_quorum_required"]=2
    obj["scientific_rule_changed"]=False
    obj["outcome_accessed"]=False
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "classification":obj.get("classification"),
        "oracle_price_targets":obj.get("oracle_price_validation_target_count"),
        "oracle_price_failures":obj.get("oracle_price_validation_failure_count"),
        "provider_count":len(PROVIDERS),
        "quorum_required":2,
        "health_factor_computed":False,
        "overhang_computed":False,
        "returns_opened":False,
        "pnl_opened":False,
    },sort_keys=True))
    return 0 if obj.get("classification")=="R1_GLOBAL_STATE_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())
