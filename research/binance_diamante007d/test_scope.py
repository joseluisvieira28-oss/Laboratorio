#!/usr/bin/env python3
"""Offline test of independent source choice; no historical market data read."""
import unittest
import probe_sol as p

class ProviderScope(unittest.TestCase):
    def test_exact_asset_month_and_provider(self):
        self.assertEqual(p.frozen.SYMBOL,"SOLUSDT")
        self.assertEqual(p.frozen.MONTH,"2026-08")
        self.assertEqual(p.frozen.DATASET,"Goooddy/crypto-lob-stream")
    def test_exact_three_original_files(self):
        self.assertEqual(len(p.frozen.PARTS),3)
        self.assertEqual(set(p.frozen.PARTS),{"depth","snapshots","trades"})
        self.assertTrue(all("/SOLUSDT/2026-08.parquet" in z for z in p.frozen.PARTS.values()))
    def test_unchanged_free_source_caps(self):
        self.assertEqual(p.frozen.MAX_FILE_BYTES,80_000_000)
        self.assertEqual(p.frozen.MAX_ALL_BYTES,160_000_000)
        self.assertEqual(p.frozen.MAX_DEPTH_ROWS,200_000)
    def test_no_raw_data_in_results(self):
        self.assertEqual(str(p.frozen.OUT),"binance007d-evidence")

if __name__=="__main__":unittest.main()
