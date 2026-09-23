from __future__ import annotations

import json
import pathlib
import urllib.request
import urllib.error

OUT=pathlib.Path(__file__).resolve().parent/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

TX="0xed2cbfc2373854e7c7b91a1e5f84b7e3b6b8689cbdbf6b5a4003bf251d9cf99b"
BLOCK=17866552
PROVIDERS={
    "publicnode":"https://ethereum-rpc.publicnode.com",
    "llamarpc":"https://eth.llamarpc.com",
    "flashbots":"https://rpc.flashbots.net",
    "cloudflare":"https://cloudflare-eth.com",
    "drpc":"https://eth.drpc.org",
}

def rpc(url,method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-rpc-matrix/0.1"})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            body=json.loads(r.read().decode())
            return {"http_status":r.status,"result":body.get("result"),"rpc_error":body.get("error")}
    except urllib.error.HTTPError as e:
        raw=e.read(1500).decode("utf-8","ignore")
        try:
            body=json.loads(raw)
        except Exception:
            body={}
        return {"http_status":e.code,"result":body.get("result"),"rpc_error":body.get("error") or raw[:1000]}
    except Exception as e:
        return {"http_status":None,"result":None,"rpc_error":type(e).__name__+":"+str(e)[:500]}

matrix={}
for name,url in PROVIDERS.items():
    tx=rpc(url,"eth_getTransactionByHash",[TX])
    receipt=rpc(url,"eth_getTransactionReceipt",[TX])
    block=rpc(url,"eth_getBlockByNumber",[hex(BLOCK),False])
    block_receipts=rpc(url,"eth_getBlockReceipts",[hex(BLOCK)])
    trace=rpc(url,"trace_transaction",[TX])
    matrix[name]={
        "url":url,
        "tx_found":isinstance(tx.get("result"),dict),
        "receipt_found":isinstance(receipt.get("result"),dict),
        "block_found":isinstance(block.get("result"),dict),
        "block_receipts_found":isinstance(block_receipts.get("result"),list),
        "block_receipts_count":len(block_receipts["result"]) if isinstance(block_receipts.get("result"),list) else None,
        "trace_found":isinstance(trace.get("result"),list),
        "trace_count":len(trace["result"]) if isinstance(trace.get("result"),list) else None,
        "tx_error":tx.get("rpc_error"),
        "receipt_error":receipt.get("rpc_error"),
        "block_receipts_error":block_receipts.get("rpc_error"),
        "trace_error":trace.get("rpc_error"),
    }

receipt_pass=[k for k,v in matrix.items() if v["receipt_found"] or v["block_receipts_found"]]
trace_pass=[k for k,v in matrix.items() if v["trace_found"]]
txblock_pass=[k for k,v in matrix.items() if v["tx_found"] and v["block_found"]]

receipt={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"ARCHIVE_RPC_MATRIX_V0.1",
    "frozen_tx_hash":TX,
    "frozen_block_number":BLOCK,
    "providers_tested":len(PROVIDERS),
    "txblock_pass_providers":txblock_pass,
    "historical_receipt_pass_providers":receipt_pass,
    "historical_trace_pass_providers":trace_pass,
    "receipt_verdict":"FREE_ARCHIVAL_RECEIPT_PASS" if receipt_pass else "FREE_ARCHIVAL_RECEIPT_BLOCKED",
    "trace_verdict":"FREE_ARCHIVAL_TRACE_PASS" if trace_pass else "FREE_ARCHIVAL_TRACE_BLOCKED",
    "matrix":matrix,
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "note":"One frozen public-sample tx only; source-capability probe, not economic evidence."
}
(OUT/"archive_rpc_matrix_v0_1_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
