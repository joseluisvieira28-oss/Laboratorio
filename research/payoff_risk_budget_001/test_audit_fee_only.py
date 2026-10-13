"""Five synthetic-only cost/barrier tests. No market outcomes/network."""
import unittest
from audit_fee_only import pnl_margin

class CostMath(unittest.TestCase):
    def test_flat_fee(self):
        self.assertAlmostEqual(pnl_margin(100,100,.0008,0),-.0032)
    def test_target_40_margin(self):
        self.assertAlmostEqual(pnl_margin(100,120.17614091273018,.0008,0),.40, places=10)
    def test_stop_minus_10_margin(self):
        self.assertAlmostEqual(pnl_margin(100,95.15612489991994,.0008,0),-.10,places=10)
    def test_slippage_adverse(self):
        self.assertLess(pnl_margin(100,110,.0008,.0005),pnl_margin(100,110,.0008,0))
    def test_fee_adverse(self):
        self.assertLess(pnl_margin(100,110,.001,.0002),pnl_margin(100,110,.0008,.0002))

if __name__=="__main__":
    unittest.main()
