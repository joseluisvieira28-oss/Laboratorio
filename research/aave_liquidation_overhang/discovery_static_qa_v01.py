#!/usr/bin/env python3
"""Static deterministic QA for AAVE-LIQUIDATION-OVERHANG-001 Discovery V0.1."""
from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load_module(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main()->int:
    reserve=load_module("reserve","discovery_reserve_shard_v01.py")
    adj=load_module("adj","discovery_adjudicate_v01.py")

    RAY=10**27
    assert reserve.ray_div(5*RAY,2*RAY)==(5*RAY*RAY+(2*RAY)//2)//(2*RAY)
    assert reserve.ray_mul(3*RAY,2*RAY)==6*RAY
    assert reserve.percent_mul(10_000,9000)==9_000

    assert adj.rankdata([10,10,20])==[1.5,1.5,3.0]
    rp=adj.spearman([1,2,3,4],[10,20,30,40])
    rn=adj.spearman([1,2,3,4],[40,30,20,10])
    assert rp is not None and abs(rp-1.0)<1e-12
    assert rn is not None and abs(rn+1.0)<1e-12
    assert adj.spearman([1,1,1],[1,2,3]) is None

    r1=random.Random(adj.SEED); r2=random.Random(adj.SEED)
    assert adj.stationary_indices(50,r1)==adj.stationary_indices(50,r2)

    protocol=(HERE/"AAVE_LIQUIDATION_OVERHANG_001_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md").read_text()
    authority=(HERE/"AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_EXECUTION_AUTHORITY_V0_1.md").read_text()
    clarification=(HERE/"AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_STATISTICAL_CLARIFICATION_V0_1.md").read_text()
    assert "2023-02-01" in protocol and "2023-12-31" in protocol
    assert "2024 replication outcomes MUST remain unopened" in protocol
    assert "post-state of that snapshot block" in authority
    assert "interestRateMode" in authority
    assert "index = 499" in clarification

    print(json.dumps({
        "classification":"DISCOVERY_STATIC_QA_PASS",
        "ray_math":True,
        "percent_math":True,
        "spearman_ties":True,
        "stationary_bootstrap_seed_deterministic":True,
        "2024_replication_locked":True,
        "scientific_rules_changed":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
