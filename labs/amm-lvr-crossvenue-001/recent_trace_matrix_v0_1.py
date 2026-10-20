from __future__ import annotations

import json
import pathlib
import urllib.request
import urllib.error

OUT=pathlib.Path(__file__).resolve().parent/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

# Frozen from FORWARD_OBSERVABILITY_V0.2 evidence before this probe.
TX="0x7b33ccd9b5e80f36e38158c266c76d9680590ed1c5ece3ee3ba5e7775e73aaf7"
EXPECTED_LABEL="Shen"
PROVIDERS={
    "publicnode":"https://ethereum-rpc.publicnode.com",
    "drpc":"https://eth.drpc.org",
    "cloudflare":"https://cloudflare-eth.com",
    "flashbots":"https://rpc.flashbots.net",
    "llamarpc":"https://eth.llamarpc.com",
}

def rpc(url,method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-recent-trace/0.1"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            body=json.loads(r.read().decode())
        return {"status":r.status,"result":body.get("result"),"error":body.get("error")}
    except urllib.error.HTTPError as e:
        raw=e.read(2000).decode("utf-8","ignore")
        try: body=json.loads(raw)
        except Exception: body={}
        return {"status":e.code,"result":body.get("result"),"error":body.get("error") or raw[:1200]}
    except Exception as e:
        return {"status":None,"result":None,"error":type(e).__name__+":"+str(e)[:500]}

matrix={}
for name,url in PROVIDERS.items():
    receipt=rpc(url,"eth_getTransactionReceipt",[TX])
    parity_trace=rpc(url,"trace_transaction",[TX])
    debug_trace=rpc(url,"debug_traceTransaction",[TX,{"tracer":"callTracer","timeout":"10s"}])
    matrix[name]={
        "receipt_found":isinstance(receipt.get("result"),dict),
        "receipt_log_count":len(receipt["result"].get("logs",[])) if isinstance(receipt.get("result"),dict) else None,
        "trace_transaction_pass":isinstance(parity_trace.get("result"),list),
        "trace_transaction_count":len(parity_trace["result"]) if isinstance(parity_trace.get("result"),list) else None,
        "debug_calltracer_pass":isinstance(debug_trace.get("result"),dict),
        "receipt_error":receipt.get("error"),
        "trace_error":parity_trace.get("error"),
        "debug_trace_error":debug_trace.get("error"),
    }

trace_providers=[k for k,v in matrix.items() if v["trace_transaction_pass"] or v["debug_calltracer_pass"]]
receipt_providers=[k for k,v in matrix.items() if v["receipt_found"]]
verdict="RECENT_TRACE_PUBLIC_PASS" if trace_providers else "RECENT_TRACE_PUBLIC_BLOCKED"

receipt={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"RECENT_TRACE_MATRIX_V0.1",
    "frozen_tx_hash":TX,
    "expected_registry_label":EXPECTED_LABEL,
    "receipt_providers":receipt_providers,
    "trace_providers":trace_providers,
    "verdict":verdict,
    "matrix":matrix,
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "note":"Trace capability probe on a forward-observed registry hit; no claim that the transaction is CEX-DEX arbitrage."
}
(OUT/"recent_trace_matrix_v0_1_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
