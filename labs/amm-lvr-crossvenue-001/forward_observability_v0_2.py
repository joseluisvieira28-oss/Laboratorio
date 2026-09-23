from __future__ import annotations

import json
import pathlib
import time
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
REGISTRY = json.loads((ROOT / "searcher_registry_v0_1.json").read_text(encoding="utf-8"))
RPC = "https://ethereum-rpc.publicnode.com"
SYMBOLS = ["ETHUSDT","BTCUSDT","LINKUSDT","DODOUSDT","PEPEUSDT","SHIBUSDT"]
DURATION_SEC = 120
POLL_SEC = 2

address_to_label={}
for label, addresses in REGISTRY["searchers"].items():
    for a in addresses:
        address_to_label[a.lower()]=label

def rpc(method, params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-forward/0.2"})
    with urllib.request.urlopen(req,timeout=25) as r:
        data=json.loads(r.read().decode())
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data.get("result")

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-AMM-LVR-001-forward/0.2"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read().decode())

started=datetime.now(timezone.utc).isoformat()
deadline=time.monotonic()+DURATION_SEC
last_block=None
blocks=[]
hits=[]
bbo=[]
errors=[]

while time.monotonic()<deadline:
    ts=datetime.now(timezone.utc).isoformat()
    for sym in SYMBOLS:
        try:
            q=get_json(f"https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol={sym}")
            bbo.append({"observed_at_utc":ts,"symbol":sym,"bid":q.get("bidPrice"),"bid_qty":q.get("bidQty"),"ask":q.get("askPrice"),"ask_qty":q.get("askQty")})
        except Exception as e:
            errors.append({"at":ts,"source":"binance","symbol":sym,"error":type(e).__name__+":"+str(e)[:200]})
    try:
        bn=int(rpc("eth_blockNumber",[]),16)
        if last_block is None:
            last_block=bn-1
        for n in range(last_block+1,bn+1):
            block=rpc("eth_getBlockByNumber",[hex(n),True])
            if not block:
                continue
            txs=block.get("transactions",[])
            block_ts=int(block.get("timestamp","0x0"),16)
            blocks.append({"number":n,"hash":block.get("hash"),"timestamp":block_ts,"tx_count":len(txs)})
            for tx in txs:
                fr=(tx.get("from") or "").lower()
                to=(tx.get("to") or "").lower()
                matched=fr if fr in address_to_label else (to if to in address_to_label else None)
                if matched:
                    rec=rpc("eth_getTransactionReceipt",[tx.get("hash")])
                    hits.append({
                        "observed_at_utc":ts,
                        "label":address_to_label[matched],
                        "matched_address":matched,
                        "match_side":"from" if fr==matched else "to",
                        "block_number":n,
                        "block_timestamp":block_ts,
                        "tx_hash":tx.get("hash"),
                        "from":fr,"to":to,
                        "gas_used":int(rec.get("gasUsed","0x0"),16) if rec else None,
                        "effective_gas_price":int(rec.get("effectiveGasPrice","0x0"),16) if rec and rec.get("effectiveGasPrice") else None,
                        "receipt_status":int(rec.get("status","0x0"),16) if rec else None,
                        "log_count":len(rec.get("logs",[])) if rec else None,
                    })
        last_block=max(last_block,bn)
    except Exception as e:
        errors.append({"at":ts,"source":"ethereum","error":type(e).__name__+":"+str(e)[:300]})
    time.sleep(POLL_SEC)

per_symbol={s:sum(1 for x in bbo if x["symbol"]==s) for s in SYMBOLS}
hit_labels={}
for h in hits:
    hit_labels[h["label"]]=hit_labels.get(h["label"],0)+1
unique_blocks=len({x["number"] for x in blocks})
verdict="FORWARD_MULTI_SEARCHER_OBSERVABILITY_PASS" if unique_blocks>=5 and min(per_symbol.values() or [0])>=10 else "FORWARD_MULTI_SEARCHER_OBSERVABILITY_FAIL"

receipt={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"FORWARD_OBSERVABILITY_V0.2",
    "started_at_utc":started,
    "ended_at_utc":datetime.now(timezone.utc).isoformat(),
    "duration_sec":DURATION_SEC,
    "verdict":verdict,
    "registry_labels":len(REGISTRY["searchers"]),
    "registry_addresses":len(address_to_label),
    "ethereum_unique_blocks":unique_blocks,
    "ethereum_block_records":len(blocks),
    "searcher_hits":len(hits),
    "searcher_hit_labels":hit_labels,
    "bbo_snapshots":len(bbo),
    "bbo_per_symbol":per_symbol,
    "error_count":len(errors),
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "notes":[
        "Published address registry is frozen before this run.",
        "No searcher hit is required for observability PASS; hit absence is not economic evidence.",
        "No wallet, authenticated exchange endpoint, order or transaction submission is used."
    ]
}
for name,data in [
    ("forward_observability_v0_2_receipt.json",json.dumps(receipt,indent=2,sort_keys=True)),
    ("forward_multi_searcher_hits_v0_2.jsonl","\n".join(json.dumps(x,sort_keys=True) for x in hits)),
    ("forward_bbo_v0_2.jsonl","\n".join(json.dumps(x,sort_keys=True) for x in bbo)),
    ("forward_blocks_v0_2.jsonl","\n".join(json.dumps(x,sort_keys=True) for x in blocks)),
    ("forward_errors_v0_2.jsonl","\n".join(json.dumps(x,sort_keys=True) for x in errors)),
]:
    (OUT/name).write_text(data,encoding="utf-8")

print(json.dumps(receipt,indent=2,sort_keys=True))
if verdict!="FORWARD_MULTI_SEARCHER_OBSERVABILITY_PASS":
    raise SystemExit(2)
