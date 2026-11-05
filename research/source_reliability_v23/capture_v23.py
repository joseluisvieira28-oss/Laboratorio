#!/usr/bin/env python3
"""V2.3 single-shot 900s source-only capture runner; no trading endpoints.

Uses the exact V2.2 public source observer for same-time Bybit L1/L50 + MEXC.
The V2.3 pre-capture protocol is independent and SHA-attested by raw manifest.
"""
import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"source_reliability_v22"))
import compare as original_v22

assert original_v22.live_enabled() is False
original_v22.WINDOW = 900
original_v22.HERE = ROOT

if __name__ == "__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python capture_v23.py OUTPUT_FOLDER")
    asyncio.run(original_v22.capture(pathlib.Path(sys.argv[1])))
