from __future__ import annotations

import json
import pathlib
import urllib.request
import urllib.error

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)
REG=json.loads((ROOT/"forward_hit_registry_v0_2.json").read_text(encoding="utf-8"))
RPC="https://eth.drpc.org"

def rpc(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(
        RPC,
        data=payload,
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-inclusion/0.1"},
    )
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            body=json.loads(r.read().decode())
        return body.get("result"), body.get("error")
    except urllib.error.HTTPError as e:
        raw=e.read(2000).decode("utf-8","ignore")
        return None, raw[:1000]
    except Exception as e:
        return None, type(e).__name__+":"+str(e)[:500]

def hx(v):
    if v is None:
        return None
    return int(v,16) if isinstance(v,str) and v.startswith("0x") else int(v)

rows=[]
for h in REG.get("hits",[]):
    tx=h["tx_hash"]
    receipt,e1=rpc("eth_getTransactionReceipt",[tx])
    if not isinstance(receipt,dict):
        rows.append({"tx_hash":tx,"label":h.get("label"),"receipt_pass":False,"error":e1})
        continue

    block_num=receipt["blockNumber"]
    block,e2=rpc("eth_getBlockByNumber",[block_num,False])
    trace,e3=rpc("trace_transaction",[tx])
    block_pass=isinstance(block,dict)
    trace_pass=isinstance(trace,list)

    base=hx(block.get("baseFeePerGas")) if block_pass else None
    effective=hx(receipt.get("effectiveGasPrice"))
    gas_used=hx(receipt.get("gasUsed"))
    fee_recipient=(block.get("miner") or "").lower() if block_pass else ""

    priority_per_gas=max((effective or 0)-(base or 0),0) if effective is not None and base is not None else None
    priority_paid=(priority_per_gas*gas_used) if priority_per_gas is not None and gas_used is not None else None

    direct=0
    direct_calls=0
    if trace_pass and fee_recipient:
        for t in trace:
            if t.get("type")!="call":
                continue
            a=t.get("action") or {}
            if (a.get("to") or "").lower()!=fee_recipient:
                continue
            val=hx(a.get("value") or "0x0")
            if val>0:
                direct+=val
                direct_calls+=1

    observed=(priority_paid+direct) if priority_paid is not None and trace_pass else None
    rows.append({
        "tx_hash":tx,
        "label":h.get("label"),
        "block_number":hx(block_num),
        "receipt_pass":True,
        "block_pass":block_pass,
        "trace_pass":trace_pass,
        "fee_recipient":fee_recipient or None,
        "gas_used":gas_used,
        "base_fee_per_gas_wei":base,
        "effective_gas_price_wei":effective,
        "priority_fee_per_gas_wei":priority_per_gas,
        "priority_fee_paid_wei":priority_paid,
        "direct_fee_recipient_transfer_calls":direct_calls,
        "direct_fee_recipient_transfer_wei":direct if trace_pass else None,
        "observed_inclusion_payment_wei":observed,
        "trace_error":e3 if not trace_pass else None,
        "block_error":e2 if not block_pass else None,
    })

summary={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"INCLUSION_COST_ATTRIBUTION_V0.1",
    "input_registry_hits":len(REG.get("hits",[])),
    "receipt_pass":sum(1 for r in rows if r.get("receipt_pass")),
    "block_pass":sum(1 for r in rows if r.get("block_pass")),
    "trace_pass":sum(1 for r in rows if r.get("trace_pass")),
    "transactions_with_direct_fee_recipient_transfer":sum(1 for r in rows if (r.get("direct_fee_recipient_transfer_wei") or 0)>0),
    "transactions_with_observed_inclusion_payment":sum(1 for r in rows if (r.get("observed_inclusion_payment_wei") or 0)>0),
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "verdict":"OBSERVED_INCLUSION_COST_SOURCE_PASS" if rows and all(r.get("receipt_pass") and r.get("block_pass") and r.get("trace_pass") for r in rows) else "OBSERVED_INCLUSION_COST_SOURCE_PARTIAL",
    "limitation":"Observed on-chain priority fee + direct transfer to fee recipient only. Private/off-chain builder economics and failure probability remain unbound."
}
(OUT/"inclusion_cost_attribution_v0_1.json").write_text(json.dumps(rows,indent=2,sort_keys=True),encoding="utf-8")
(OUT/"inclusion_cost_attribution_v0_1_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(summary,indent=2,sort_keys=True))
