#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

def main():
    fs=list(Path("downloaded_v02a").rglob("AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2A.json"))
    if len(fs)!=1:
        raise SystemExit(f"expected exactly one receipt, found {len(fs)}")
    obj=json.loads(fs[0].read_text())
    failures=obj.get("validation_failures") or []
    by_block=Counter()
    by_reason=Counter()
    by_endpoint=Counter()
    sample=[]
    for f in failures:
        if isinstance(f,dict):
            b=f.get("block") or f.get("audit_block") or f.get("block_number")
            if b is not None: by_block[str(b)]+=1
            reason=f.get("classification") or f.get("error") or f.get("reason") or f.get("detail") or f.get("message")
            if reason is None:
                reason=json.dumps({k:v for k,v in f.items() if k not in ("user","token","address")},sort_keys=True)[:500]
            by_reason[str(reason)[:500]]+=1
            ep=f.get("endpoint") or f.get("rpc") or f.get("provider")
            if ep: by_endpoint[str(ep)]+=1
            if len(sample)<12:
                sample.append({k:v for k,v in f.items() if k not in ("user","token","address")})
        else:
            by_reason[str(f)[:500]]+=1
            if len(sample)<12: sample.append(str(f)[:500])
    out={
      "upstream_classification":obj.get("classification"),
      "upstream_failure":obj.get("failure"),
      "validation_target_count":obj.get("validation_target_count"),
      "validation_failure_count":obj.get("validation_failure_count"),
      "archive_rpc_stats":obj.get("archive_rpc_stats"),
      "failure_counts_by_block":dict(by_block),
      "failure_counts_by_reason":dict(by_reason),
      "failure_counts_by_endpoint":dict(by_endpoint),
      "failure_samples":sample,
      "safety":obj.get("safety"),
    }
    Path("r1_v02a_diag_output").mkdir(exist_ok=True)
    Path("r1_v02a_diag_output/AAVE_R1_V0_2A_FAILURE_DIAGNOSTIC.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__":
    main()
