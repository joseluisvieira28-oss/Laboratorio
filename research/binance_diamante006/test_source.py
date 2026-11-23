#!/usr/bin/env python3
"""BINANCE006 source pinning tests; synthetic-only, no real archives downloaded."""
import hashlib
import unittest
from flow_study import START,VALID_START,TEST_START,END
from run_history import (HOST,MONTHS,SYMBOLS,MAX_TOTAL_COMPRESSED,requests_for,
                         checked_url,verify_coverage,remote_check)
from l2_probe import TARGETS

class SourceTests(unittest.TestCase):
    def test_strict_18_official_monthly_files(self):
        z=requests_for()
        self.assertEqual(len(z),18)
        self.assertEqual(len(set(a["filename"] for a in z)),18)
        self.assertEqual(set(a["kind"] for a in z),{"aggTrades","klines"})
        self.assertTrue(all(a["url"].startswith(HOST+"/data/spot/monthly/") for a in z))
    def test_no_futures_or_private_endpoints(self):
        self.assertTrue(all("/futures/" not in a["url"] and "api/v3" not in a["url"]
                            for a in requests_for()))
    def test_url_whitelist_blocks_private_urls(self):
        for s in ("https://api.binance.com/api/v3/account",
                  "http://data.binance.vision/data/spot/monthly/x",
                  "https://attacker.example/archive"):
            with self.assertRaisesRegex(ValueError,"WHITELISTED"):
                checked_url(s)
    def test_predeclared_unmodified_splits(self):
        self.assertEqual((VALID_START-START).days,30)
        self.assertEqual((TEST_START-VALID_START).days,30)
        self.assertEqual((END-TEST_START).days,30)
    def test_bounded_volume_budget(self):
        self.assertLessEqual(MAX_TOTAL_COMPRESSED,900_000_000)
        self.assertEqual(len(SYMBOLS),3)
        self.assertEqual(len(MONTHS),3)
    def test_l2_is_not_claimed_to_be_complete(self):
        self.assertEqual(len(TARGETS),2)
        self.assertTrue(all(url.startswith("https://") for _,url in TARGETS))
if __name__=="__main__":unittest.main()
