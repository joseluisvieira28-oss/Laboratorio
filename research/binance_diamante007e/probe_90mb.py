#!/usr/bin/env python3
"""Independent pre-registered SOL Aug source-only budget; actual code unchanged."""
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"binance_diamante007d"))
import probe_sol as pinned

pinned.frozen.MAX_FILE_BYTES=90_000_000
pinned.frozen.MAX_ALL_BYTES=160_000_000
pinned.frozen.OUT=Path("binance007e-evidence")

if __name__=="__main__":
    raise SystemExit(pinned.frozen.main())
