from __future__ import annotations

import csv
import io
import json
import pathlib
import urllib.request
import urllib.error

LAB_ID = "AMM-LVR-CROSSVENUE-001"
SAMPLE_URL = "https://raw.githubusercontent.com/tivas-g/Wu_Comparing_CEX_DEX_Execution/main/cexdex_data_sample_20230808.csv"
RPC = "https://ethereum-rpc.publicnode.com"
OUT = pathlib.Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"CryptoLab-AMM-LVR-001-historical/0.1"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def rpc(method: str, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(
        RPC, data=payload,
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-historical/0.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode())
        return {"http_status":r.status,"result":body.get("result"),"rpc_error":body.get("error")}
    except urllib.error.HTTPError as e:
        return {"http_status":e.code,"result":None,"rpc_error":e.read(1000).decode("utf-8","ignore")[:1000]}
    except Exception as e:
        return {"http_status":None,"result":None,"rpc_error":type(e).__name__+":"+str(e)[:500]}

raw = download(SAMPLE_URL)
reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
rows = list(reader)

# Freeze mechanically: first transaction per non-empty published label in the public one-day sample.
first_by_label = {}
for row in rows:
    label = (row.get("mev_bot_label") or "").strip()
    txh = (row.get("tx_hash") or "").strip()
    if label and txh and label not in first_by_label:
        first_by_label[label] = row

probes = []
trace_success = 0
for label in sorted(first_by_label):
    row = first_by_label[label]
    txh = row["tx_hash"]
    tx = rpc("eth_getTransactionByHash",[txh])
    receipt = rpc("eth_getTransactionReceipt",[txh])
    block_hex = tx["result"].get("blockNumber") if isinstance(tx.get("result"),dict) else None
    block = rpc("eth_getBlockByNumber",[block_hex,False]) if block_hex else {"http_status":None,"result":None,"rpc_error":"NO_BLOCK_NUMBER"}
    trace = rpc("trace_transaction",[txh])
    if isinstance(trace.get("result"),list):
        trace_success += 1
    probes.append({
        "label":label,
        "tx_hash":txh,
        "sample_block_number":row.get("block_number"),
        "sample_block_time":row.get("block_time"),
        "tx_found":isinstance(tx.get("result"),dict),
        "receipt_found":isinstance(receipt.get("result"),dict),
        "block_found":isinstance(block.get("result"),dict),
        "receipt_log_count":len(receipt["result"].get("logs",[])) if isinstance(receipt.get("result"),dict) else None,
        "effective_gas_price":receipt["result"].get("effectiveGasPrice") if isinstance(receipt.get("result"),dict) else None,
        "gas_used":receipt["result"].get("gasUsed") if isinstance(receipt.get("result"),dict) else None,
        "trace_supported_for_tx":isinstance(trace.get("result"),list),
        "trace_item_count":len(trace["result"]) if isinstance(trace.get("result"),list) else None,
        "trace_rpc_error":trace.get("rpc_error"),
    })

n=len(probes)
tx_ok=sum(p["tx_found"] for p in probes)
receipt_ok=sum(p["receipt_found"] for p in probes)
block_ok=sum(p["block_found"] for p in probes)
core_ratio=min(tx_ok,receipt_ok,block_ok)/n if n else 0
core_txblock_ratio=min(tx_ok,block_ok)/n if n else 0
receipt_ratio=receipt_ok/n if n else 0
verdict="HISTORICAL_TXBLOCK_PASS_RECEIPT_ARCHIVE_BLOCKED" if n>=10 and core_txblock_ratio>=0.95 and receipt_ratio<0.95 else ("HISTORICAL_ONCHAIN_REPLAY_PASS" if n>=10 and core_ratio>=0.95 else "HISTORICAL_ONCHAIN_REPLAY_FAIL")
trace_verdict="TRACE_PUBLIC_PASS" if n and trace_success/n>=0.80 else "TRACE_PUBLIC_BLOCKED_OR_INCOMPLETE"

receipt_out={
    "lab_id":LAB_ID,
    "phase":"HISTORICAL_ONCHAIN_REPLAY_PROBE_V0.1",
    "sample_date":"2023-08-08",
    "sample_rows":len(rows),
    "labels_probed":n,
    "tx_found":tx_ok,
    "receipt_found":receipt_ok,
    "block_found":block_ok,
    "core_replay_ratio":core_ratio,
    "core_txblock_ratio":core_txblock_ratio,
    "receipt_ratio":receipt_ratio,
    "verdict":verdict,
    "trace_success_count":trace_success,
    "trace_verdict":trace_verdict,
    "economic_outcomes_opened":False,
    "cex_markouts_opened":False,
    "pnl_computed":False,
    "probes":probes,
    "note":"Tests archival Ethereum observability only. It does not reconstruct CEX hedge execution or economic PnL."
}
(OUT/"historical_onchain_replay_probe_v0_1_receipt.json").write_text(json.dumps(receipt_out,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt_out,indent=2,sort_keys=True))
if verdict=="HISTORICAL_ONCHAIN_REPLAY_FAIL":
    raise SystemExit(2)
