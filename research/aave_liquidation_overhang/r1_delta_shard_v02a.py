#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, os
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("base_audit", HERE/"r1_scaled_ledger_audit_v01.py")
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

def load_sample():
    fs=list(Path("downloaded_r1_sample").rglob("AAVE_LIQUIDATION_OVERHANG_001_R1_BORROW_SAMPLE_V0_2A.json"))
    if len(fs)!=1: raise RuntimeError(f"expected one sample receipt, found {len(fs)}")
    obj=json.loads(fs[0].read_text())
    if obj.get("classification")!="R1_BORROW_SAMPLE_PASS": raise RuntimeError("sample receipt not PASS")
    sample=[str(x).lower() for x in obj.get("sample_borrowers") or []]
    if len(sample)!=16 or len(set(sample))!=16: raise RuntimeError("invalid 16-borrower sample")
    sha=hashlib.sha256("\n".join(sample).encode()).hexdigest()
    if sha!=obj.get("sample_sha256"): raise RuntimeError("sample SHA mismatch")
    return obj,sample

def main():
    sid=os.environ["R1_SHARD_ID"]
    start=int(os.environ["R1_BLOCK_START"]); end=int(os.environ["R1_BLOCK_END"])
    base.FROM_BLOCK=start; base.TO_BLOCK=end
    sample_receipt,sample=load_sample()
    bootstrap=base.load_bootstrap()
    if int(bootstrap.get("frozen_from_block"))!=16490000 or int(bootstrap.get("frozen_to_block"))!=21525890:
        raise RuntimeError("canonical R0 bootstrap envelope mismatch")
    token_meta,atokens,debts=base.build_token_maps(bootstrap)
    stats=Counter()
    block_deltas,event_counts,debt_transfer_count=base.acquire_sample_token_deltas(sample,token_meta,atokens,debts,stats)
    ledger=[]
    for (user,token),by in sorted(block_deltas.items()):
        ledger.append({
          "user":user,"token":token,
          "by_block":[[int(bn),str(int(delta))] for bn,delta in sorted(by.items())]
        })
    digest=hashlib.sha256(
      "\n".join(
        f"{x['user']}|{x['token']}|{bn}|{delta}"
        for x in ledger for bn,delta in x["by_block"]
      ).encode()
    ).hexdigest()
    classification="DELTA_SHARD_PASS" if debt_transfer_count==0 else "RECONSTRUCTION_PROVENANCE_FAILURE"
    receipt={
      "classification":classification,
      "shard_id":sid,"block_start":start,"block_end":end,
      "sample_sha256":sample_receipt["sample_sha256"],
      "ledger":ledger,
      "touched_user_token_pairs":len(block_deltas),
      "scaled_event_counts":dict(sorted(event_counts.items())),
      "variable_debt_balance_transfer_count":int(debt_transfer_count),
      "delta_ledger_digest_sha256":digest,
      "transport_stats":dict(stats),
      "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    out=Path("r1_delta_shards"); out.mkdir(parents=True,exist_ok=True)
    p=out/f"delta_shard_{sid}.json"; p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"shard":sid,"touched_pairs":len(block_deltas),"event_count":sum(event_counts.values()),"debt_balance_transfer_count":debt_transfer_count,"ledger_digest":digest},sort_keys=True))
    return 0 if classification=="DELTA_SHARD_PASS" else 2
if __name__=="__main__":
    raise SystemExit(main())
