"""Synthetic-only tests: no 200h POST-boundary wait; no 2026 real outcomes."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import faststart_three_way as fast

class FastSourceTests(unittest.TestCase):
    def sample(self):
        b=[{"t":fast.BOUNDARY+(i-200)*fast.H,
           "open":100.,"high":101.,"low":99.,"close":100.,
           "volume":1000.} for i in range(202)]
        return {"status":"SOURCE_OK","trading_authority":"NONE",
          "parent_v02_freeze_sha":fast.PARENT_SHA,
          "parent_v02_source_receipt_sha256":"SYNTHETIC_UNIT_TEST_ONLY",
          "science_boundary_ms":fast.BOUNDARY,"bars":b,
          "warmup_sha256":fast.digest(b[:200]),
          "marks":{str(x["t"]):{"open":100.,"high":101.,"low":99.,"close":100.}
                   for x in b[200:]},
          "funding":{},"verified_complete_through_ms":b[-1]["t"]+fast.H,
          "funding_verified_through_ms":b[-1]["t"]+fast.H}

    def test_two_forward_bars_sufficient(self):
        d=self.sample()
        result=fast.compare(d)
        self.assertEqual(result["economic_events_before_boundary"],0)
        self.assertEqual(result["warmup_hours_before_boundary"],200)
        self.assertEqual(result["trading_authority"],"NONE")
        self.assertEqual(set(result["scenarios"]["BASE"]),{"PARENT","PAYOFF_4R","NETSTOP_CHILD"})

    def test_no_hist_authority(self):
        d=self.sample();d["parent_v02_freeze_sha"]="changed"
        with self.assertRaisesRegex(ValueError,"AUTHORITY"):
            fast.compare(d)

    def test_wrong_boundary(self):
        d=self.sample();d["science_boundary_ms"]+=fast.H
        with self.assertRaisesRegex(ValueError,"BOUNDARY"):
            fast.compare(d)

    def test_mismatched_source_checksum(self):
        d=self.sample();d["warmup_sha256"]="bad"
        with self.assertRaisesRegex(ValueError,"DIGEST"):
            fast.compare(d)

    def test_market_gap_fails(self):
        d=self.sample();d["bars"][110]["t"]+=fast.H
        with self.assertRaisesRegex(ValueError,"CONTIGUITY"):
            fast.compare(d)

    def test_no_future_bars(self):
        d=self.sample();d["bars"]=d["bars"][:200]
        with self.assertRaisesRegex(ValueError,"INSUFFICIENT"):
            fast.compare(d)

    def test_old_funding_outcome_forbidden(self):
        d=self.sample();d["funding"]={str(fast.BOUNDARY-fast.H):.001}
        with self.assertRaisesRegex(ValueError,"PRE_BOUNDARY_FUNDING"):
            fast.compare(d)

    def test_incomplete_future_bar_forbidden(self):
        d=self.sample();d["verified_complete_through_ms"]=fast.BOUNDARY
        with self.assertRaisesRegex(ValueError,"NOT_CLOSED"):
            fast.compare(d)

if __name__=="__main__":unittest.main()
