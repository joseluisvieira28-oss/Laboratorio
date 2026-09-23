from __future__ import annotations

import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

TX = "0x7b33ccd9b5e80f36e38158c266c76d9680590ed1c5ece3ee3ba5e7775e73aaf7"
RPC = "https://eth.drpc.org"

def rpc(method, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(
        RPC, data=payload,
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-builder-binding/0.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode())
        return {"status":r.status,"result":body.get("result"),"error":body.get("error")}
    except urllib.error.HTTPError as e:
        raw = e.read(2000).decode("utf-8","ignore")
        try: body=json.loads(raw)
        except Exception: body={}
        return {"status":e.code,"result":body.get("result"),"error":body.get("error") or raw[:1200]}
    except Exception as e:
        return {"status":None,"result":None,"error":type(e).__name__+":"+str(e)[:500]}

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"CryptoLab-AMM-LVR-001-builder-binding/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"status":r.status,"result":json.loads(r.read().decode()),"error":None}
    except urllib.error.HTTPError as e:
        raw=e.read(2000).decode("utf-8","ignore")
        try: body=json.loads(raw)
        except Exception: body=None
        return {"status":e.code,"result":body,"error":raw[:1200]}
    except Exception as e:
        return {"status":None,"result":None,"error":type(e).__name__+":"+str(e)[:500]}

def h2i(v):
    if v is None: return None
    if isinstance(v,int): return v
    return int(v,16) if str(v).startswith("0x") else int(v)

tx = rpc("eth_getTransactionByHash",[TX])
receipt = rpc("eth_getTransactionReceipt",[TX])
trace = rpc("debug_traceTransaction",[TX,{"tracer":"callTracer","timeout":"10s"}])

txr = tx.get("result") if isinstance(tx.get("result"),dict) else None
rr = receipt.get("result") if isinstance(receipt.get("result"),dict) else None
block = None
if rr and rr.get("blockNumber"):
    block_resp = rpc("eth_getBlockByNumber",[rr["blockNumber"],False])
    block = block_resp.get("result") if isinstance(block_resp.get("result"),dict) else None

fee_recipient = (block.get("miner") or "").lower() if block else None
base_fee = h2i(block.get("baseFeePerGas")) if block else None
gas_used = h2i(rr.get("gasUsed")) if rr else None
effective_gas_price = h2i(rr.get("effectiveGasPrice")) if rr else None
priority_per_gas = max(0,effective_gas_price-base_fee) if effective_gas_price is not None and base_fee is not None else None
priority_fee_paid = priority_per_gas*gas_used if priority_per_gas is not None and gas_used is not None else None

direct = []
def walk(node,path="root"):
    if not isinstance(node,dict): return
    to=(node.get("to") or "").lower()
    value=h2i(node.get("value") or "0x0") or 0
    if fee_recipient and to==fee_recipient and value>0:
        direct.append({"path":path,"type":node.get("type"),"from":node.get("from"),"to":node.get("to"),"value_wei":value})
    for i,c in enumerate(node.get("calls") or []):
        walk(c,f"{path}.calls[{i}]")

tr = trace.get("result")
if isinstance(tr,dict):
    walk(tr)

direct_wei=sum(x["value_wei"] for x in direct)

relay = {"status":None,"result":None,"error":"block unavailable"}
if block and block.get("hash"):
    q=urllib.parse.urlencode({"block_hash":block["hash"]})
    relay=get_json("https://boost-relay.flashbots.net/relay/v1/data/bidtraces/proposer_payload_delivered?"+q)

relay_rows = relay.get("result") if isinstance(relay.get("result"),list) else []
relay_match = relay_rows[0] if relay_rows else None

local_binding_pass = all([
    txr is not None,
    rr is not None,
    block is not None,
    isinstance(tr,dict),
    priority_fee_paid is not None,
    fee_recipient is not None,
])

receipt_out = {
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"BUILDER_PAYMENT_BINDING_PROBE_V0.1",
    "frozen_tx_hash":TX,
    "verdict":"TX_LOCAL_BUILDER_COST_BINDING_PASS" if local_binding_pass else "TX_LOCAL_BUILDER_COST_BINDING_BLOCKED",
    "tx_found":txr is not None,
    "receipt_found":rr is not None,
    "debug_calltracer_pass":isinstance(tr,dict),
    "block_number":h2i(rr.get("blockNumber")) if rr else None,
    "block_hash":block.get("hash") if block else None,
    "fee_recipient":fee_recipient,
    "base_fee_per_gas_wei":base_fee,
    "effective_gas_price_wei":effective_gas_price,
    "gas_used":gas_used,
    "priority_fee_paid_wei":priority_fee_paid,
    "direct_fee_recipient_transfer_count":len(direct),
    "direct_fee_recipient_transfer_wei":direct_wei,
    "direct_transfers":direct,
    "flashbots_relay_query_status":relay.get("status"),
    "flashbots_delivered_payload_match":relay_match,
    "bundle_level_off_tx_payment_bound":False,
    "failed_inclusion_risk_bound":False,
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "note":"Capability probe only on a frozen forward registry touch. It proves transaction-local priority fee and internal fee-recipient transfer observability when debug trace is available. It does not prove bundle-level off-transaction payment or failed-inclusion risk."
}

(OUT/"builder_payment_binding_probe_v0_1_receipt.json").write_text(json.dumps(receipt_out,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt_out,indent=2,sort_keys=True))
if not local_binding_pass:
    raise SystemExit(2)
