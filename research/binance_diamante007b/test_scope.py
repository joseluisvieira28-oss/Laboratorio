#!/usr/bin/env python3
"""BINANCE007B strictly pre-registered source-only scope tests. No network."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import probe_goooddy as p
from source_probe import MAX_FILE_BYTES,MAX_ALL_BYTES

class SecondSourceTests(unittest.TestCase):
    def test_source_exact(self):
        self.assertEqual(p.frozen.DATASET,"Goooddy/crypto-lob-stream")
    def test_no_posthoc_month_selection(self):
        self.assertEqual(p.frozen.MONTH,"2026-09")
    def test_all_required_public_l2_types(self):
        self.assertEqual(set(p.frozen.PARTS),{"depth","snapshots","trades"})
        self.assertTrue(all("BTCUSDT/2026-09.parquet" in u for u in p.frozen.PARTS.values()))
    def test_same_limits_as_original(self):
        self.assertEqual(MAX_FILE_BYTES,80_000_000)
        self.assertEqual(MAX_ALL_BYTES,160_000_000)
        self.assertEqual(p.frozen.MAX_DEPTH_ROWS,200_000)
    def test_artifacts_only_diagnostics(self):
        self.assertEqual(str(p.frozen.OUT),"binance007b-evidence")

if __name__=="__main__":
    unittest.main()
