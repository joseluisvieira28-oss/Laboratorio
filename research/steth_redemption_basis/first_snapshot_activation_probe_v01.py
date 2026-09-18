#!/usr/bin/env python3
from __future__ import annotations
import json,time
from pathlib import Path
import requests
from eth_hash.auto import keccak

QUEUE="0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1"
ACTIVATION_TX="0x592d68a259af899fb435da0ac08c2fd500cb423f37f1d8ce8e3120cb84186b21"
TARGET_TS=1684152000  # 2023-05-15T12:00:00Z
MIN_BLOCK=17_200_000
MAX_BLOCK=17_270_000
PROVIDERS=[
 "https://eth-mainnet.public.blastapi.io",
 "https://rpc.mevblocker.io",
 "https://ethereum.blinklabs.xyz/",
]
SEL="0x"+keccak(b"getLastRequestId()")[:4].hex()

def rpc(ep,method,params,retries=3):
    last=None
    for k in range(retries):
        try:
            r=requests.post(ep,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},
                            timeout=(10,45),headers={"Content-Type":"application/json","User-Agent":"STETH-FIRST-SNAPSHOT-PROBE-V0.1"})
            r.raise_for_status(); o=r.json(); r.close()
            if o.get("error") is not None:
                return {"ok":False,"error":str(o["error"])[:240]}
            return {"ok":True,"result":o.get("result")}
        except Exception as e:
            last=e; time.sleep(1.5*(k+1))
    return {"ok":False,"error":f"{type(last).__name__}: {str(last)[:240]}"}

def header(ep,bn):
    o=rpc(ep,"eth_getBlockByNumber",[hex(bn),False])
    if not o["ok"] or not o["result"]: raise RuntimeError(f"block {bn} unavailable: {o}")
    return o["result"]

def first_at_or_after(ep,ts):
    lo,hi=MIN_BLOCK,MAX_BLOCK
    if int(header(ep,lo)["timestamp"],16)>ts or int(header(ep,hi)["timestamp"],16)<ts:
        raise RuntimeError("target outside binary-search bounds")
    while lo<hi:
        mid=(lo+hi)//2
        if int(header(ep,mid)["timestamp"],16)<ts: lo=mid+1
        else: hi=mid
    h=header(ep,lo)
    prev=header(ep,lo-1)
    if int(h["timestamp"],16)<ts or int(prev["timestamp"],16)>=ts:
        raise RuntimeError("timestamp mapping invariant")
    return lo,int(h["timestamp"],16),h.get("hash")

def call_queue(ep,bn):
    return rpc(ep,"eth_call",[{"to":QUEUE,"data":SEL},hex(bn)])

def main():
    rows=[]
    for ep in PROVIDERS:
        row={"provider":ep}
        try:
            bn,ts,bh=first_at_or_after(ep,TARGET_TS)
            row.update({"snapshot_block":bn,"snapshot_timestamp":ts,"snapshot_block_hash":bh})
            code=rpc(ep,"eth_getCode",[QUEUE,hex(bn)])
            row["proxy_code_nonempty"]=bool(code.get("ok") and isinstance(code.get("result"),str) and code["result"] not in ("0x","0x0"))
            pre=call_queue(ep,bn)
            row["snapshot_method_accessible"]=bool(pre.get("ok") and isinstance(pre.get("result"),str) and pre["result"].startswith("0x") and len(pre["result"])>2)
            if not row["snapshot_method_accessible"]:
                row["snapshot_method_error"]=pre.get("error","invalid/nonempty result")

            tx=rpc(ep,"eth_getTransactionReceipt",[ACTIVATION_TX])
            if tx.get("ok") and isinstance(tx.get("result"),dict) and tx["result"].get("blockNumber"):
                ab=int(tx["result"]["blockNumber"],16)
                row["activation_receipt_accessible"]=True
                row["activation_block"]=ab
                post=call_queue(ep,ab)
                row["activation_method_accessible"]=bool(post.get("ok") and isinstance(post.get("result"),str) and post["result"].startswith("0x") and len(post["result"])>2)
                if not row["activation_method_accessible"]:
                    row["activation_method_error"]=post.get("error","invalid/nonempty result")
            else:
                row["activation_receipt_accessible"]=False
                row["activation_receipt_error"]=tx.get("error","missing receipt")
        except Exception as e:
            row["technical_error"]=f"{type(e).__name__}: {str(e)[:300]}"
        rows.append(row)

    snapshot_blocks=[r.get("snapshot_block") for r in rows if r.get("snapshot_block") is not None]
    snapshot_quorum=(len(snapshot_blocks)>=2 and len(set(snapshot_blocks))==1)
    activation_blocks=[r.get("activation_block") for r in rows if r.get("activation_receipt_accessible")]
    activation_quorum=(len(activation_blocks)>=2 and len(set(activation_blocks))==1)
    pre_access=sum(1 for r in rows if r.get("snapshot_method_accessible"))
    post_access=sum(1 for r in rows if r.get("activation_method_accessible"))
    proxy_access=sum(1 for r in rows if r.get("proxy_code_nonempty"))

    if snapshot_quorum and activation_quorum and proxy_access>=2 and pre_access==0 and post_access>=2:
        classification="FROZEN_SOURCE_BOUNDARY_PROVENANCE_FAILURE"
    elif snapshot_quorum and pre_access>=2:
        classification="FROZEN_FIRST_SNAPSHOT_SOURCE_VALID"
    else:
        classification="TECHNICAL_INCONCLUSIVE"

    out={
      "lab_id":"STETH-REDEMPTION-BASIS-001",
      "probe_id":"FIRST-SNAPSHOT-ACTIVATION-PROVENANCE-V0.1",
      "classification":classification,
      "frozen_first_snapshot_utc":"2023-05-15T12:00:00Z",
      "activation_tx":ACTIVATION_TX,
      "snapshot_mapping_quorum":snapshot_quorum,
      "activation_receipt_quorum":activation_quorum,
      "proxy_code_nonempty_provider_count":proxy_access,
      "snapshot_method_accessible_provider_count":pre_access,
      "activation_method_accessible_provider_count":post_access,
      "provider_rows":rows,
      "safety":{"curve_quote_values_opened":False,"redemption_predictor_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    Path("source_gate_output").mkdir(exist_ok=True)
    Path("source_gate_output/STETH_REDEMPTION_BASIS_001_FIRST_SNAPSHOT_ACTIVATION_PROBE_V0_1.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"snapshot_quorum":snapshot_quorum,"activation_quorum":activation_quorum,"pre_access":pre_access,"post_access":post_access,"proxy_access":proxy_access},sort_keys=True))
    return 0 if classification!="TECHNICAL_INCONCLUSIVE" else 2

if __name__=="__main__":
    raise SystemExit(main())
