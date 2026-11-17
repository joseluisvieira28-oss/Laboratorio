import unittest
from research.microstructure_scalping.sweep_features_v01 import sweep_features


class SweepFeatureTests(unittest.TestCase):
    def prefixes(self, trades):
        times=[]; pb=[0.0]; ps=[0.0]
        for t,side,n in trades:
            times.append(t)
            pb.append(pb[-1]+(n if side=="Buy" else 0.0))
            ps.append(ps[-1]+(n if side=="Sell" else 0.0))
        return times,pb,ps

    def test_strictly_pre_anchor(self):
        times,pb,ps=self.prefixes([
            (1000,"Buy",100),(1500,"Buy",100),(2000,"Sell",10000)
        ])
        f=sweep_features(
            2000,100,101,10,10,100,102,10,5,times,pb,ps,
            burst_window_ms=1000,baseline_window_ms=1000)
        self.assertEqual(f["direction"],1)
        self.assertEqual(f["buy_notional_1s"],200)
        self.assertEqual(f["sell_notional_1s"],0)

    def test_buy_sweep_uses_ask_displacement_and_depth(self):
        times,pb,ps=self.prefixes([
            (0,"Buy",10),(500,"Buy",10),(1500,"Buy",100)
        ])
        f=sweep_features(
            2000,100,101,20,10,100,102,20,4,times,pb,ps,
            burst_window_ms=1000,baseline_window_ms=1000)
        self.assertEqual(f["direction"],1)
        self.assertGreater(f["displacement_bps"],0)
        self.assertAlmostEqual(f["replenishment_failure"],0.6)
        self.assertGreater(f["burst_ratio"],1)

    def test_sell_sweep_uses_bid_displacement(self):
        times,pb,ps=self.prefixes([
            (0,"Sell",10),(500,"Sell",10),(1500,"Sell",100)
        ])
        f=sweep_features(
            2000,100,101,10,20,99,101,4,20,times,pb,ps,
            burst_window_ms=1000,baseline_window_ms=1000)
        self.assertEqual(f["direction"],-1)
        self.assertGreater(f["displacement_bps"],0)
        self.assertAlmostEqual(f["replenishment_failure"],0.6)

    def test_zero_net_flow_has_no_direction(self):
        times,pb,ps=self.prefixes([(1500,"Buy",10),(1600,"Sell",10)])
        f=sweep_features(
            2000,100,101,10,10,100,101,10,10,times,pb,ps,
            burst_window_ms=1000,baseline_window_ms=1000)
        self.assertIsNone(f)


if __name__=="__main__":
    unittest.main()
