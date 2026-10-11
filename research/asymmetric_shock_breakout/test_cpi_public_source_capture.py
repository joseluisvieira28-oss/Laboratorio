#!/usr/bin/env python3
"""Pure synthetic tests; never invoke collect() in CI before the event."""
import unittest
from cpi_public_source_capture import SLOTS, START_MS, INTERVAL_MS, summarize, SYMBOLS

def rows(bad=0, backwards=False, duplicate=False):
    result=[]
    for symbol in SYMBOLS:
        for i in range(SLOTS):
            result.append({"symbol":symbol,"slot_index":i,
              "slot_ms":START_MS+i*INTERVAL_MS,
              "status":"MISSING" if i<bad else "VALID",
              "version":100+i if not backwards or i != SLOTS-1 else 1})
    if duplicate:
        result[-1]["slot_index"]=0
    return result

class SourceFreezeTests(unittest.TestCase):
    def test_all_pass(self):
        self.assertEqual(summarize(rows(),True)["status"],"SOURCE_ONLY_COVERAGE_PASS")

    def test_boundary_47_pass(self):
        self.assertEqual(summarize(rows(bad=2),True)["status"],"SOURCE_ONLY_COVERAGE_PASS")

    def test_46_not_enough(self):
        self.assertEqual(summarize(rows(bad=3),True)["status"],"SOURCE_COVERAGE_BLOCKED")

    def test_clock(self):
        self.assertEqual(summarize(rows(),False)["status"],"BLOCKED_CLOCK")

    def test_version_regression(self):
        self.assertEqual(summarize(rows(backwards=True),True)["status"],"SOURCE_COVERAGE_BLOCKED")

    def test_slot_duplicate(self):
        self.assertEqual(summarize(rows(duplicate=True),True)["status"],"SOURCE_COVERAGE_BLOCKED")

    def test_large_gap(self):
        a=rows()
        for r in a:
            if r["slot_index"] in (15,16):
                r["status"]="MISSING"
        self.assertEqual(summarize(a,True)["status"],"SOURCE_COVERAGE_BLOCKED")

if __name__=="__main__":unittest.main()
