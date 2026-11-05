#!/usr/bin/env python3
"""V2.4 single bounded 2h public-data collector.

Reuses existing V2.2 collector UNCHANGED; adds only Bybit public liquidation
topic, changes study WINDOW to 7200s and protocol root for SHA attestation.
NO orders, credentials, account, exchange SDK, PnL or private endpoints.
"""
from __future__ import annotations
import asyncio
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source_reliability_v22"))
import compare as source

assert source.live_enabled() is False
assert source.SUB_BYBIT["args"] == ["orderbook.1.BTCUSDT","orderbook.50.BTCUSDT"]
source.WINDOW = 7200
source.HERE = HERE
source.SUB_BYBIT = {
    "op": "subscribe",
    "args": [
        "orderbook.1.BTCUSDT",
        "orderbook.50.BTCUSDT",
        "allLiquidation.BTCUSDT"
    ]
}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python capture_v24.py OUTPUT_DIR")
    asyncio.run(source.capture(Path(sys.argv[1])))
