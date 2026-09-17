#!/usr/bin/env python3
"""Technical-only SQD boundary semantics probe for AAVE-LIQUIDATION-OVERHANG-001.

Determines whether Portal toBlock includes or excludes the stated boundary by
querying already-known protocol configuration events around activation block.
No economic source values, HF, overhang, future outcomes, returns or PnL.
"""
import json
import sys
from pathlib import Path
import requests
from eth_hash.auto import keccak

PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
CONFIGURATOR="0x64b761d848206f447fe2dd461b0c635ec39ebb27"
ORACLE="0x54586be62e3c3580375ae3723c145253060ca0c2"
B=16_496_792
T_RESERVE="0x"+keccak(b"ReserveInitialized(address,address,address,address,address)").hex()
T_SOURCE="0x"+keccak(b"AssetSourceUpdated(address,address)").hex()

CASES=[
  {"name":"left_to_B","from":B-1,"to":B},
  {"name":"B_to_B","from":B,"to":B},
  {"name":"B_to_Bplus1","from":B,"to":B+1},
  {"name":"left_to_Bplus1","from":B-1,"to":B+1},
]


def run_case(c):
    body={
      "type":"evm","fromBlock":c["from"],"toBlock":c["to"],
      "fields":{"block":{"number":True,"timestamp":True},"log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}},
      "logs":[
        {"address":[CONFIGURATOR],"topic0":[T_RESERVE]},
        {"address":[ORACLE],"topic0":[T_SOURCE]},
      ],
    }
    r=requests.post(PORTAL,json=body,timeout=(20,120),stream=True,headers={"Content-Type":"application/json","Accept-Encoding":"gzip","User-Agent":"AAVE-LIQUIDATION-OVERHANG-001/sqd-boundary-probe"})
    r.raise_for_status()
    rows=[]; logs=[]
    for raw in r.iter_lines(decode_unicode=True):
        if not raw: continue
        obj=json.loads(raw)
        if obj.get("error"): raise RuntimeError(obj["error"])
        h=obj.get("header") or obj.get("block") or {}
        bn=int(h["number"])
        rows.append(bn)
        for log in obj.get("logs") or []:
            topics=[str(x).lower() for x in (log.get("topics") or [])]
            logs.append({"block":bn,"address":str(log.get("address") or "").lower(),"topic0":topics[0] if topics else None,"tx":log.get("transactionHash"),"logIndex":log.get("logIndex")})
    r.close()
    return {**c,"row_blocks":rows,"log_count":len(logs),"logs":logs}


def main():
    out=[]
    try:
        for c in CASES: out.append(run_case(c))
        appears={x["name"]:any(int(y["block"])==B for y in x["logs"]) for x in out}
        if appears["B_to_Bplus1"] and not appears["left_to_B"]:
            classification="SQD_TO_BLOCK_EXCLUSIVE_CONFIRMED"
        elif appears["left_to_B"]:
            classification="SQD_TO_BLOCK_INCLUSIVE_OR_OTHER"
        else:
            classification="SQD_BOUNDARY_SEMANTICS_INCONCLUSIVE"
        failure=None
    except Exception as exc:
        classification="SQD_BOUNDARY_PROBE_TECHNICAL_FAILURE"; failure=f"{type(exc).__name__}: {str(exc)[:1000]}"
    receipt={"lab_id":"AAVE-LIQUIDATION-OVERHANG-001","phase":"SQD_BOUNDARY_SEMANTICS_TECHNICAL_PROBE","classification":classification,"activation_block":B,"cases":out,"failure":failure,"safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_return_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False}}
    p=Path("sqd_boundary_probe_output"); p.mkdir(exist_ok=True)
    (p/"AAVE_LIQUIDATION_OVERHANG_001_SQD_BOUNDARY_PROBE.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"cases":{x["name"]:{"rows":len(x["row_blocks"]),"logs":x["log_count"],"blocks":sorted(set(y["block"] for y in x["logs"]))} for x in out}},sort_keys=True))
    return 0 if classification in {"SQD_TO_BLOCK_EXCLUSIVE_CONFIRMED","SQD_TO_BLOCK_INCLUSIVE_OR_OTHER"} else 2

if __name__=="__main__": sys.exit(main())
