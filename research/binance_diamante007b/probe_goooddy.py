#!/usr/bin/env python3
"""Second pre-registered no-cost L2 provider, immutable base source/sequence engine.
First 007 SOURCE_BLOCKED is preserved, never substituted within original run.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"binance_diamante007"))
import source_probe as frozen

frozen.DATASET="Goooddy/crypto-lob-stream"
frozen.SYMBOL="BTCUSDT"
frozen.MONTH="2026-09"
frozen.PARTS={
    "depth":"depth/binance/BTCUSDT/2026-09.parquet",
    "snapshots":"snapshots/binance/BTCUSDT/2026-09.parquet",
    "trades":"trades/binance/BTCUSDT/2026-09.parquet"
}
frozen.OUT=Path("binance007b-evidence")

if __name__=="__main__":
    raise SystemExit(frozen.main())
