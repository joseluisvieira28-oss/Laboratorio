import datetime as dt
import math
import unittest
import backtest as b

class CausalityTests(unittest.TestCase):
    def test_exact_105_calendar_days(self):
        self.assertEqual((b.END-b.START).days+1,105)
        self.assertEqual(str(b.START),"2026-07-01")
        self.assertEqual(str(b.END),"2026-10-13")
    def test_from_positions_symmetric_barriers(self):
        positions=[(0.1,98000.)]*150+[(-0.1,103000.)]*120
        z=b.position_levels(positions,100000.)
        self.assertEqual(z["signal"],"DOWN")
        self.assertAlmostEqual(math.log(z["target"]/z["mark"]),
           -math.log(z["mirror"]/z["mark"]),places=10)
    def test_wrong_side_liquidations_not_used(self):
        positions=[(0.1,103000.)]*200+[(-0.1,97000.)]*200
        with self.assertRaises(ValueError):b.position_levels(positions,100000.)
    def test_unverifiable_filename_rejected(self):
        p="snapshots_perp/date=2026-10-13/1181670000_1791850169837.parquet"
        got=b.claim_time(dt.date(2026,10,13),p)
        self.assertEqual(got.date(),dt.date(2026,10,13))
        with self.assertRaises(ValueError):b.claim_time(dt.date(2026,10,12),p)
        with self.assertRaises(ValueError):b.claim_time(dt.date(2026,10,13),"snapshots_perp/date=2026-10-13/unknown.parquet")
    def test_empty_source_cannot_be_economic_go(self):
        x=b.result_gate([],list(range(105)))
        self.assertEqual(x["scientific_status"],"SOURCE_INSUFFICIENT")
        self.assertEqual(x["live_trading_verdict"],"NO_GO")
if __name__=="__main__":unittest.main()
