#!/usr/bin/env python3
"""Protected-date Blockchair dump filename probe. No market outcomes, no 2025/2026."""
from __future__ import annotations
import hashlib, json, urllib.error, urllib.request
from pathlib import Path

OUT = Path("artifacts/stablecoin_exchange_flow_dump_probe_v01")
DATE = "20221111"
BASE = "https://gz.blockchair.com/ethereum/erc-20/transactions"
CANDIDATES = [
    f"{BASE}/blockchair_ethereum_erc-20_transactions_{DATE}.tsv.gz",
    f"{BASE}/blockchair_ethereum_erc_20_transactions_{DATE}.tsv.gz",
    f"{BASE}/blockchair_ethereum_erc20_transactions_{DATE}.tsv.gz",
    f"{BASE}/ethereum_erc-20_transactions_{DATE}.tsv.gz",
    f"{BASE}/{DATE}.tsv.gz",
]

def probe(url: str) -> dict:
    # Range request avoids downloading a large dump; a valid file should return 200/206.
    req = urllib.request.Request(url, headers={"User-Agent":"CryptoLab-SEF-dump-probe/0.1", "Range":"bytes=0-63"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(64)
            return {"url":url,"status":r.status,"content_type":r.headers.get("Content-Type"),"content_length":r.headers.get("Content-Length"),"content_range":r.headers.get("Content-Range"),"prefix_sha256":hashlib.sha256(raw).hexdigest(),"prefix_hex":raw[:16].hex()}
    except urllib.error.HTTPError as e:
        return {"url":url,"status":e.code,"content_type":e.headers.get("Content-Type"),"content_length":e.headers.get("Content-Length")}
    except Exception as e:
        return {"url":url,"status":None,"error":f"{type(e).__name__}:{e}"}

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    probes = [probe(u) for u in CANDIDATES]
    hits = [p for p in probes if p.get("status") in (200,206)]
    classification = "DUMP_ROUTE_PASS" if hits else "DUMP_ROUTE_NOT_FOUND"
    receipt = {
        "lab_id":"STABLECOIN-EXCHANGE-FLOW-001",
        "mve_id":"SEF-BINANCE-PUBLIC-USDT-ETH-1D-001",
        "classification":classification,
        "protected_probe_date":"2022-11-11",
        "access_2025":False,"access_2026":False,"btc_market_data_accessed":False,"returns_computed":False,"pnl_computed":False,
        "hits":hits,"probes":probes,
    }
    (OUT/"DUMP_PROBE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
