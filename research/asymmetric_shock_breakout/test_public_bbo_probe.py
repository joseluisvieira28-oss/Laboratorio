#!/usr/bin/env python3
"""Synthetic-only BBO source integrity regression tests."""
import unittest
from public_bbo_probe import check

def fixture():
    return {"success": True, "code": 0, "data": {
        "bids": [[100., 30, 1], [99.9, 5, 1]],
        "asks": [[100.1, 35, 1], [100.2, 10, 1]],
        "version": 22, "timestamp": 1_800_000_000_000
    }}

class TestProbe(unittest.TestCase):
    def test_valid(self):
        o = check(fixture(), 1_800_000_000_500)
        self.assertAlmostEqual(o["bid"], 100)
        self.assertAlmostEqual(o["ask"], 100.1)
        self.assertEqual(o["exchange_age_ms"], 500)

    def test_stale(self):
        with self.assertRaisesRegex(ValueError, "STALE"):
            check(fixture(), 1_800_000_020_000)

    def test_clock_future(self):
        with self.assertRaisesRegex(ValueError, "STALE"):
            check(fixture(), 1_799_999_990_000)

    def test_crossed(self):
        a = fixture()
        a["data"]["asks"][0][0] = 99.0
        with self.assertRaisesRegex(ValueError, "CROSSED"):
            check(a, 1_800_000_000_100)

    def test_bad_timestamp_units(self):
        a = fixture()
        a["data"]["timestamp"] //= 1000
        with self.assertRaisesRegex(ValueError, "TIMESTAMP"):
            check(a, 1_800_000_000_100)

    def test_no_asks(self):
        a = fixture()
        a["data"]["asks"] = []
        with self.assertRaisesRegex(ValueError, "MISSING_ASKS"):
            check(a, 1_800_000_000_100)

    def test_bad_size(self):
        a = fixture()
        a["data"]["asks"][0][1] = 0
        with self.assertRaisesRegex(ValueError, "SIZE"):
            check(a, 1_800_000_000_100)

    def test_http_status(self):
        a = fixture()
        a["success"] = False
        with self.assertRaisesRegex(ValueError, "API_STATUS_FAIL"):
            check(a, 1_800_000_000_100)

if __name__ == "__main__":
    unittest.main()
