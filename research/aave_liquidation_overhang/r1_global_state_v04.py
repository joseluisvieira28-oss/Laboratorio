#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("base_global",HERE/"r1_global_state_v01.py")
base=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(base)

PROVIDERS=[
 "https://eth-mainnet.public.blastapi.io",
 "https://rpc.mevblocker.io",
 "https://ethereum.blinklabs.xyz/",
]
AUTHORITY="AAVE_LIQUIDATION_OVERHANG_001_R1_GLOBAL_STATE_DIAGNOSTIC_PRESERVATION_V0_4"

def main()->int:
    base.RPC_ENDPOINTS=list(PROVIDERS)
    base.main()
    path=Path("r1_global_state_output")/"AAVE_LIQUIDATION_OVERHANG_001_R1_GLOBAL_STATE_V0_1.json"
    if not path.exists(): raise SystemExit("global-state receipt missing")
    x=json.loads(path.read_text())
    original_class=x.get("classification")
    original_failure=x.get("failure")
    stats=x.get("archive_rpc_stats")
    if stats is not None and set(stats)!=set(PROVIDERS):
        x["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        x["failure"]="V0.4 provider-set binding mismatch"
    else:
        x["classification"]=original_class
        x["failure"]=original_failure
    x["diagnostic_preservation_authority"]=AUTHORITY
    x["archive_rpc_provider_set"]=PROVIDERS
    x["archive_rpc_provider_count"]=len(PROVIDERS)
    x["archive_rpc_quorum_required"]=2
    x["original_base_classification"]=original_class
    x["original_base_failure"]=original_failure
    x["scientific_rule_changed"]=False
    x["outcome_accessed"]=False
    path.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "classification":x.get("classification"),
      "failure":x.get("failure"),
      "provider_stats_present":stats is not None,
      "health_factor_computed":False,
      "overhang_computed":False,
      "returns_opened":False,
      "pnl_opened":False
    },sort_keys=True))
    return 0 if x.get("classification")=="R1_GLOBAL_STATE_PASS" else 2

if __name__=="__main__": sys.exit(main())
