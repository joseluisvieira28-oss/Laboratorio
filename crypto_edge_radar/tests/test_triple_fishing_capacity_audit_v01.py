from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).resolve().parents[1]/"capacity_audit"/"audit_triple_fishing_capacity_v01.py"
spec=importlib.util.spec_from_file_location("cap",P)
cap=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(cap)

class CapacityAuditTests(unittest.TestCase):
    def rows(self):
        return [
            {"symbol":"SOLUSDT","entry_ms":0,"exit_ms":100,"candidate_id":"D"},
            {"symbol":"BTCUSDT","entry_ms":10,"exit_ms":30,"candidate_id":"D"},
            {"symbol":"ETHUSDT","entry_ms":10,"exit_ms":40,"candidate_id":"D"},
            {"symbol":"XRPUSDT","entry_ms":20,"exit_ms":50,"candidate_id":"D"},
        ]
    def test_single_slot_blocks_every_later_overlap(self):
        r=cap.capacity_sim(self.rows(),1)
        self.assertEqual(r["admitted"],1)
        self.assertEqual(r["blocked"],3)
    def test_two_slots_still_no_chase(self):
        r=cap.capacity_sim(self.rows(),2)
        self.assertEqual(r["admitted"],2)
        self.assertEqual(r["blocked"],2)
    def test_peak_concurrency(self):
        self.assertEqual(cap.peak_concurrency(self.rows()),4)

if __name__=="__main__":
    unittest.main()
