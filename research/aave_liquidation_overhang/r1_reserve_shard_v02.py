#!/usr/bin/env python3
"""R1 reserve shard V0.2.

Runs the frozen V0.1 replay unchanged. If and only if its sole terminal issue is
missing aToken Initialized decimals caused by the V0.1 dispatch-order bug, this
wrapper performs a second source-only Initialized-event pass and re-adjudicates
that coverage check. No scientific rule, ledger delta or sample changes.
"""
from __future__ import annotations
import json,os,sys
from collections import Counter
from pathlib import Path
import r1_reserve_shard_v01 as v


def main()->int:
    shard_id=int(os.environ.get("R1_SHARD_ID","0")); shard_count=int(os.environ.get("R1_SHARD_COUNT","8"))
    v.main()
    src=Path("r1_reserve_shards")/f"r1_reserve_shard_{shard_id:02d}.json"
    if not src.exists(): return 2
    receipt=json.loads(src.read_text(encoding="utf-8"))
    original_class=receipt.get("classification"); original_failure=str(receipt.get("failure") or "")
    remediated=False
    if original_class=="RECONSTRUCTION_INSUFFICIENT_COVERAGE" and original_failure.startswith("missing aToken Initialized decimals"):
        try:
            bootstrap=v.load_json_under("downloaded_r0_bootstrap","RECONSTRUCTION_R0_BOOTSTRAP_PASS")
            allres=sorted((u.lower(),m) for u,m in bootstrap["reserves"].items())
            selected=[(u,m) for i,(u,m) in enumerate(allres) if i%shard_count==shard_id]
            atokens={str(m["aToken"]).lower():u for u,m in selected}
            filters=[{"address":sorted(atokens),"topic0":[v.T_INITIALIZED]}]
            stats=Counter(); decimals={}
            for obj in v.stream(filters,stats):
                for log in obj.get("logs") or []:
                    addr=str(log.get("address","")).lower(); topics=[str(x).lower() for x in (log.get("topics") or [])]
                    if addr not in atokens or not topics or topics[0]!=v.T_INITIALIZED: raise RuntimeError("unexpected Initialized remediation log")
                    if len(topics)<3: raise RuntimeError("aToken Initialized ABI")
                    reserve=v.topic_addr(topics[1]); pool=v.topic_addr(topics[2])
                    if atokens[addr]!=reserve or pool!=v.POOL: raise RuntimeError("Initialized identity mismatch")
                    dec=v.words(log.get("data",""),3)[2]
                    if dec>255: raise RuntimeError("invalid decimals")
                    if reserve in decimals and decimals[reserve]!=dec: raise RuntimeError("decimals changed")
                    decimals[reserve]=dec
            missing=[u for u,_ in selected if u not in decimals]
            receipt["decimals_remediation_transport_stats"]=dict(stats)
            receipt["decimals"]=decimals
            receipt["decimals_remediation_missing"]=missing
            if not missing:
                receipt["classification"]="R1_RESERVE_SHARD_PASS"
                receipt["failure"]=None
                receipt["v01_original_classification"]=original_class
                receipt["v01_original_failure"]=original_failure
                receipt["technical_remediation"]="V0.2 separate Initialized-event source pass; ledger/config rules unchanged"
                remediated=True
        except Exception as exc:
            receipt["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
            receipt["failure"]=f"V0.2 decimals remediation failed: {type(exc).__name__}: {str(exc)[:1000]}"
    receipt["phase"]="R1_FULL_RESERVE_SHARD_V0_2_OUTCOME_BLIND"
    dst=Path("r1_reserve_shards")/f"r1_reserve_shard_v02_{shard_id:02d}.json"
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"shard":shard_id,"classification":receipt.get("classification"),"remediated":remediated,"decimals":len(receipt.get("decimals") or {}),"health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt.get("classification")=="R1_RESERVE_SHARD_PASS" else 2
if __name__=="__main__": sys.exit(main())
