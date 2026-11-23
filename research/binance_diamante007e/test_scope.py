#!/usr/bin/env python3
"""Offline BINANCE007E declared-only operating budget source metadata tests."""
import unittest
import probe_90mb as p
class FixedSource(unittest.TestCase):
    def test_exact_public_file_budget(self):
        self.assertEqual(p.pinned.frozen.MAX_FILE_BYTES,90_000_000)
        self.assertEqual(p.pinned.frozen.MAX_ALL_BYTES,160_000_000)
    def test_only_sol_august_2026_spot(self):
        self.assertEqual(p.pinned.frozen.SYMBOL,"SOLUSDT")
        self.assertEqual(p.pinned.frozen.MONTH,"2026-08")
        self.assertEqual(p.pinned.frozen.DATASET,"Goooddy/crypto-lob-stream")
        self.assertEqual(len(p.pinned.frozen.PARTS),3)
    def test_unchanged_book_event_limit_and_no_raw_output(self):
        self.assertEqual(p.pinned.frozen.MAX_DEPTH_ROWS,200000)
        self.assertEqual(str(p.pinned.frozen.OUT),"binance007e-evidence")
if __name__=="__main__":unittest.main()
