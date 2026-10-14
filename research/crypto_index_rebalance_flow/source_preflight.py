#!/usr/bin/env python3
"""Source-only preflight for CRYPTO-INDEX-REBALANCE-FLOW-001.

No price, return, PnL, volume, or trading outcome is read.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

OUT = Path("artifacts/crypto_index_rebalance_flow")
UA = "CryptoLab-IndexRebalance-SourcePreflight/0.1 research-only"
API = "https://data-api.binance.vision/api/v3/exchangeInfo"
ARCHIVE = "https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip"
SYMBOLS = ["UNIUSDT","ZECUSDT","SKYUSDT","SUIUSDT","LTCUSDT","CRVUSDT","BTCUSDT"]
PROBE_DATE = "2026-09-26"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def req(url: str, method: str = "GET") -> tuple[int, bytes, dict[str,str]]:
    r = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(r, timeout=25) as x:
        return int(x.status), x.read(), dict(x.headers.items())


def exchange_info(symbol: str) -> dict[str, Any]:
    url = API + "?" + urllib.parse.urlencode({"symbol": symbol})
    status, raw, _ = req(url)
    payload = json.loads(raw.decode("utf-8"))
    rows = payload.get("symbols", [])
    row = rows[0] if rows else {}
    # Intentionally retain metadata only. No ticker/price endpoints are called.
    return {
        "symbol": symbol,
        "http_status": status,
        "exchange_symbol": row.get("symbol"),
        "status": row.get("status"),
        "baseAsset": row.get("baseAsset"),
        "quoteAsset": row.get("quoteAsset"),
        "isSpotTradingAllowed": row.get("isSpotTradingAllowed"),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }


def archive_head(symbol: str) -> dict[str, Any]:
    url = ARCHIVE.format(symbol=symbol, date=PROBE_DATE)
    try:
        status, raw, headers = req(url, "HEAD")
        return {
            "symbol": symbol,
            "probe_date": PROBE_DATE,
            "url": url,
            "http_status": status,
            "content_length": headers.get("Content-Length"),
            "body_bytes_read": len(raw),
        }
    except urllib.error.HTTPError as e:
        return {
            "symbol": symbol,
            "probe_date": PROBE_DATE,
            "url": url,
            "http_status": int(e.code),
            "content_length": None,
            "body_bytes_read": 0,
        }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    infos = [exchange_info(s) for s in SYMBOLS]
    archives = [archive_head(s) for s in SYMBOLS]
    all_symbols = all(x["exchange_symbol"] == x["symbol"] and x["status"] == "TRADING" for x in infos)
    all_archives = all(x["http_status"] == 200 for x in archives)
    classification = "SOURCE_ROUTE_PASS" if all_symbols and all_archives else "SOURCE_ROUTE_PARTIAL_OR_BLOCKED"

    receipt = {
        "schema": "CRYPTO_INDEX_REBALANCE_SOURCE_PREFLIGHT_V0.1",
        "generated_at_utc": now(),
        "probe_date": PROBE_DATE,
        "t0_utc": "2026-09-30T20:00:00Z",
        "symbols": infos,
        "archive_head_checks": archives,
        "classification": classification,
        "prices_read": False,
        "returns_computed": False,
        "pnl_computed": False,
        "orders": False,
        "exchange_mutation": False,
    }
    raw = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    (OUT/"source_preflight_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(classification)
    return 0 if classification == "SOURCE_ROUTE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
