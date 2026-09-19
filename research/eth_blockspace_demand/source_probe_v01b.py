#!/usr/bin/env python3
"""Qualified-provider source-only probe for ETH-BLOCKSPACE-DEMAND-001 V0.1B."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from typing import Any
import requests

LAB_ID="ETH-BLOCKSPACE-DEMAND-001"
BLOCKS=[13_000_000,15_000_000,18_000_000,21_000_000]
END_TS_EXCLUSIVE=1_735_689_600
ENDPOINTS=["https://eth.drpc.org","https://rpc.flashbots.net"]
REQUIRED=["number","hash","parentHash","timestamp","gasLimit","gasUsed","baseFeePerGas"]

def rpc(ep:str,method:str,params:list[Any])->Any:
    r=requests.post(ep,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},
                    headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/source-probe-v0.1b"},
                    timeout=(10,30))
    r.raise_for_status()
    o=r.json()
    if o.get("error") is not None: raise RuntimeError(f"rpc error {o['error']}")
    return o.get("result")

def qint(x:Any)->int:
    if not isinstance(x,str) or not x.startswith("0x"): raise ValueError("expected JSON-RPC quantity")
    return int(x,16)

def main()->int:
    out=Path("eth_blockspace_source_probe_v01b"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_BLOCKSPACE_DEMAND_001_SOURCE_PROBE_V0_1B.json"
    receipt={"lab_id":LAB_ID,"phase":"SOURCE_ONLY_OUTCOME_BLIND","classification":None,
             "transport_policy":"QUALIFIED_PROVIDER_SET_V0_1B","frozen_blocks":BLOCKS,
             "providers":{},"blocks":{},
             "safety":{"economic_values_persisted":False,"market_prices_opened":False,
                       "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
                       "transaction_bodies_requested":False,"live_trading":False,
                       "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
    fail=None
    block_results={b:{} for b in BLOCKS}
    try:
        for ep in ENDPOINTS:
            ps={"chain_id_ok":False,"all_four_blocks_ok":False,"errors":[]}
            try:
                cid=rpc(ep,"eth_chainId",[])
                if cid!="0x1": raise RuntimeError("CHAIN_ID_NOT_MAINNET")
                ps["chain_id_ok"]=True
            except Exception as e:
                ps["errors"].append(f"CHAIN_ID:{type(e).__name__}:{str(e)[:120]}")
            for b in BLOCKS:
                try:
                    obj=rpc(ep,"eth_getBlockByNumber",[hex(b),False])
                    if not isinstance(obj,dict): raise RuntimeError("null_or_nonobject_block")
                    missing=[f for f in REQUIRED if obj.get(f) is None]
                    if missing: raise RuntimeError("missing_fields:"+",".join(missing))
                    n=qint(obj["number"]);ts=qint(obj["timestamp"]);gl=qint(obj["gasLimit"]);gu=qint(obj["gasUsed"]);bf=qint(obj["baseFeePerGas"])
                    if n!=b: raise RuntimeError("block_number_identity_mismatch")
                    if ts>=END_TS_EXCLUSIVE:
                        receipt["safety"]["accessed_2025_or_2026"]=True
                        raise RuntimeError("protected_period_timestamp_breach")
                    if gl<=0 or gu<=0 or gu>gl or bf<=0: raise RuntimeError("header_sanity_failure")
                    block_results[b][ep]={"block_hash":str(obj["hash"]).lower(),
                                          "parent_hash":str(obj["parentHash"]).lower(),
                                          "timestamp":ts,
                                          "required_fields_present":True,
                                          "economic_fields_sanity_pass":True}
                except Exception as e:
                    ps["errors"].append(f"BLOCK_{b}:{type(e).__name__}:{str(e)[:120]}")
            ps["all_four_blocks_ok"]=all(ep in block_results[b] for b in BLOCKS)
            receipt["providers"][ep]=ps

        for b in BLOCKS:
            vals=block_results[b]
            hashes=sorted({v["block_hash"] for v in vals.values()})
            timestamps=sorted({v["timestamp"] for v in vals.values()})
            status="PASS" if len(vals)==2 and len(hashes)==1 and len(timestamps)==1 else "FAIL"
            receipt["blocks"][str(b)]={"provider_quorum":len(vals),"identity_status":status,
                                      "canonical_block_hash":hashes[0] if len(hashes)==1 else None,
                                      "canonical_timestamp":timestamps[0] if len(timestamps)==1 else None,
                                      "required_fields":REQUIRED,"economic_values_persisted":False}
        provider_ok=all(v["chain_id_ok"] and v["all_four_blocks_ok"] and not v["errors"] for v in receipt["providers"].values())
        blocks_ok=all(v["identity_status"]=="PASS" for v in receipt["blocks"].values())
        if receipt["safety"]["accessed_2025_or_2026"]:
            receipt["classification"]="PROVENANCE_FAILURE"
        elif provider_ok and blocks_ok:
            receipt["classification"]="SOURCE_SCHEMA_PASS"
        else:
            receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"

        canonical=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
        receipt["receipt_sha256"]=hashlib.sha256(canonical).hexdigest()
    except Exception as e:
        receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        fail=f"{type(e).__name__}: {str(e)[:500]}"
        receipt["failure"]=fail

    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],
                      "provider_status":{k:{"chain_id_ok":v["chain_id_ok"],"all_four_blocks_ok":v["all_four_blocks_ok"],"error_count":len(v["errors"])} for k,v in receipt["providers"].items()},
                      "blocks":{k:{"quorum":v["provider_quorum"],"identity_status":v["identity_status"]} for k,v in receipt["blocks"].items()},
                      "economic_values_persisted":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
                      "accessed_2025_or_2026":receipt["safety"]["accessed_2025_or_2026"]},sort_keys=True))
    return 0 if receipt["classification"]=="SOURCE_SCHEMA_PASS" else 2

if __name__=="__main__": sys.exit(main())
