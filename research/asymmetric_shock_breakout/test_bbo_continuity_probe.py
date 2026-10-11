#!/usr/bin/env python3
import unittest
from bbo_continuity_probe import adjudicate, SYMBOLS

def rows(n=16,bad=0,regression=False):
    out=[]
    for symbol in SYMBOLS:
        for i in range(n):
            out.append({"symbol": symbol,"status":"INVALID_BBO" if i < bad else "VALID_BBO",
                "version":100+i if not regression or i != n-1 else 3,
                "observation_timestamp_ms":1_800_000_000_000+i*5_000})
    return out

class TestContinuity(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(adjudicate(rows(), 75, 16)["status"],"SOURCE_CONTINUITY_PASS_BOUNDED")

    def test_insufficient_duration(self):
        self.assertEqual(adjudicate(rows(), 30, 16)["status"],"SOURCE_CONTINUITY_BLOCKED")

    def test_missing(self):
        self.assertEqual(adjudicate(rows(bad=3),75,16)["status"],"SOURCE_CONTINUITY_BLOCKED")

    def test_version_regression(self):
        self.assertEqual(adjudicate(rows(regression=True),75,16)["status"],"SOURCE_CONTINUITY_BLOCKED")

if __name__=="__main__":
    unittest.main()
