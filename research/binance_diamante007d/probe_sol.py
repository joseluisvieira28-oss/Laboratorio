#!/usr/bin/env python3
"""One pre-frozen SOLUSDT Aug public Spot L2 source probe, no market predictions.
Use original strict U/u source/replay engine without editing source study.
"""
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"binance_diamante007"))
import source_probe as frozen

frozen.DATASET="Goooddy/crypto-lob-stream"
frozen.SYMBOL="SOLUSDT"
frozen.MONTH="2026-08"
frozen.PARTS={
    "depth":"depth/binance/SOLUSDT/2026-08.parquet",
    "snapshots":"snapshots/binance/SOLUSDT/2026-08.parquet",
    "trades":"trades/binance/SOLUSDT/2026-08.parquet"
}
frozen.METADATA_OTHERS=("BTCUSDT","ETHUSDT")
frozen.OUT=Path("binance007d-evidence")

if __name__=="__main__":
    raise SystemExit(frozen.main())
