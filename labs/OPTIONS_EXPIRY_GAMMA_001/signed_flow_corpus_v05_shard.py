#!/usr/bin/env python3
"""OEG signed-flow full-corpus source shard V0.5.

SOURCE ONLY. Reuses the frozen V0.4 per-date probe semantics unchanged.
No option values, gamma exposure, dealer sign, BTC outcomes, returns or PnL are retained.
"""
from __future__ import annotations
import hashlib,json,os,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import signed_flow_source_v04 as v4

AUTH_PATH=HERE/"SIGNED_FLOW_CORPUS_AUTHORITY_V0.5.json"
AUTH=json.loads(AUTH_PATH.read_text(encoding="utf-8"))
OUT=Path("artifacts/options_expiry_gamma_signed_flow_corpus_v05_shards")

def main()->int:
    sid=int(os.environ["OEG_SHARD_ID"])
    n=int(os.environ.get("OEG_SHARD_COUNT",str(AUTH["shard_count"])))
    if n!=int(AUTH["shard_count"]) or not (0<=sid<n):
        raise SystemExit("FAIL_CLOSED_INVALID_SHARD")
    dates=list(AUTH["deterministic_dates"])
    selected=[d for i,d in enumerate(dates) if i % n == sid]
    if len(selected)!=6:
        raise SystemExit(f"FAIL_CLOSED_EXPECTED_6_DATES got={len(selected)}")
    # Reuse exact V0.4 probe function with V0.5 authority carrying identical window/gates.
    v4.AUTH=AUTH
    probes=[]
    for i,d in enumerate(selected,1):
        try:
            p=v4.probe(d)
        except Exception as exc:
            p={"date":d,"pass":False,"technical_error":f"{type(exc).__name__}: {str(exc)[:800]}"}
        probes.append(p)
        print(f"OEG_V05_SHARD_PROGRESS shard={sid} {i}/{len(selected)} date={d} pass={p.get('pass')}",flush=True)
    tech=sum(1 for p in probes if p.get("technical_error"))
    result={
      "lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],
      "phase":"SIGNED_FLOW_CORPUS_SHARD_SOURCE_ONLY","shard_id":sid,"shard_count":n,
      "dates":selected,"classification":"SIGNED_GAMMA_FLOW_CORPUS_SHARD_PASS" if tech==0 else "SIGNED_GAMMA_FLOW_CORPUS_SHARD_TECHNICAL_FAILURE",
      "technical_error_dates":tech,"probes":probes,
      "authority_sha256":hashlib.sha256(AUTH_PATH.read_bytes()).hexdigest(),
      "api_key_used":False,"subscription_purchase":False,
      "option_values_retained":False,"gamma_exposure_computed":False,
      "dealer_inventory_computed":False,"dealer_gamma_sign_computed":False,
      "btc_price_outcomes_opened":False,"returns_opened":False,"pnl_opened":False,
      "access_2025":False,"access_2026":False,"live_trading":False,
      "exchange_mutation":False,"wallet_access":False,"merge_to_main":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/f"shard_{sid}.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"shard_id":sid,"classification":result["classification"],"dates":len(probes),
                      "passing_dates":sum(bool(x.get("pass")) for x in probes),"technical_error_dates":tech,
                      "returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
