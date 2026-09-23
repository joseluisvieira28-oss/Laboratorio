from __future__ import annotations

import json
import pathlib
import time
import urllib.request
from datetime import datetime, timezone

OUT = pathlib.Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

RPC = "https://ethereum-rpc.publicnode.com"
SEARCHER = "0x767c8bb1574bee5d4fe35e27e0003c89d43c5121".lower()
SYMBOLS = ["ETHUSDT","BTCUSDT","LINKUSDT","DODOUSDT","PEPEUSDT","SHIBUSDT"]
DURATION_SEC = 90
POLL_SEC = 2

def rpc(method, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(
        RPC, data=payload,
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-forward/0.1"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data.get("result")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"CryptoLab-AMM-LVR-001-forward/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

started = datetime.now(timezone.utc).isoformat()
deadline = time.monotonic() + DURATION_SEC
last_block = None
blocks = []
searcher_hits = []
bbo = []
errors = []

while time.monotonic() < deadline:
    ts = datetime.now(timezone.utc).isoformat()
    for sym in SYMBOLS:
        try:
            q = get_json(f"https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol={sym}")
            bbo.append({
                "observed_at_utc": ts,
                "symbol": sym,
                "bid": q.get("bidPrice"),
                "bid_qty": q.get("bidQty"),
                "ask": q.get("askPrice"),
                "ask_qty": q.get("askQty"),
            })
        except Exception as e:
            errors.append({"at":ts,"source":"binance","symbol":sym,"error":type(e).__name__+":"+str(e)[:200]})

    try:
        bn_hex = rpc("eth_blockNumber", [])
        bn = int(bn_hex, 16)
        if last_block is None:
            last_block = bn - 1
        for n in range(last_block + 1, bn + 1):
            block = rpc("eth_getBlockByNumber", [hex(n), True])
            if not block:
                continue
            txs = block.get("transactions", [])
            block_rec = {
                "number": n,
                "hash": block.get("hash"),
                "timestamp": int(block.get("timestamp","0x0"),16),
                "tx_count": len(txs),
            }
            blocks.append(block_rec)
            for tx in txs:
                fr = (tx.get("from") or "").lower()
                to = (tx.get("to") or "").lower()
                if fr == SEARCHER or to == SEARCHER:
                    receipt = rpc("eth_getTransactionReceipt", [tx.get("hash")])
                    searcher_hits.append({
                        "block_number": n,
                        "block_timestamp": block_rec["timestamp"],
                        "tx_hash": tx.get("hash"),
                        "from": fr,
                        "to": to,
                        "gas": int(tx.get("gas","0x0"),16),
                        "gas_price": int(tx.get("gasPrice","0x0"),16) if tx.get("gasPrice") else None,
                        "receipt_status": int(receipt.get("status","0x0"),16) if receipt else None,
                        "gas_used": int(receipt.get("gasUsed","0x0"),16) if receipt else None,
                        "effective_gas_price": int(receipt.get("effectiveGasPrice","0x0"),16) if receipt and receipt.get("effectiveGasPrice") else None,
                        "log_count": len(receipt.get("logs",[])) if receipt else None,
                    })
        last_block = max(last_block, bn)
    except Exception as e:
        errors.append({"at":ts,"source":"ethereum","error":type(e).__name__+":"+str(e)[:300]})

    time.sleep(POLL_SEC)

ended = datetime.now(timezone.utc).isoformat()
unique_blocks = {x["number"] for x in blocks}
per_symbol = {s: sum(1 for x in bbo if x["symbol"] == s) for s in SYMBOLS}
verdict = "FORWARD_OBSERVABILITY_PASS" if len(unique_blocks) >= 3 and min(per_symbol.values() or [0]) >= 5 else "FORWARD_OBSERVABILITY_FAIL"

receipt = {
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"FORWARD_OBSERVABILITY_V0.1",
    "started_at_utc":started,
    "ended_at_utc":ended,
    "duration_sec":DURATION_SEC,
    "verdict":verdict,
    "ethereum_unique_blocks":len(unique_blocks),
    "ethereum_block_records":len(blocks),
    "searcher_address":SEARCHER,
    "searcher_hits":len(searcher_hits),
    "bbo_snapshots":len(bbo),
    "bbo_per_symbol":per_symbol,
    "error_count":len(errors),
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "notes":[
        "This collector proves prospective observability only.",
        "No trading transaction, wallet action or CEX authenticated endpoint is used.",
        "Absence of a searcher hit in a 90-second window is not negative economic evidence."
    ]
}

(OUT/"forward_observability_v0_1_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
(OUT/"forward_bbo_v0_1.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True) for x in bbo),encoding="utf-8")
(OUT/"forward_blocks_v0_1.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True) for x in blocks),encoding="utf-8")
(OUT/"forward_searcher_hits_v0_1.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True) for x in searcher_hits),encoding="utf-8")
(OUT/"forward_errors_v0_1.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True) for x in errors),encoding="utf-8")

print(json.dumps(receipt,indent=2,sort_keys=True))
if verdict != "FORWARD_OBSERVABILITY_PASS":
    raise SystemExit(2)
