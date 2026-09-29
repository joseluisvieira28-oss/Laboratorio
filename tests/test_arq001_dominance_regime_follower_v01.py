import unittest

from research.arq001_dominance_regime_follower_v01 import (
    baseline_direction,
    gap_return,
    net_return_bps,
    regime_flags,
    round_trip_cost_bps,
    source_gate,
)


class ARQ001FrozenSemanticsTests(unittest.TestCase):
    def test_symmetric_long(self):
        direction = baseline_direction(0.80, -1.20)
        self.assertEqual(direction, 1)
        self.assertEqual(
            regime_flags(direction, -0.1, -0.2, 0.3),
            {"A": True, "B": True, "C": True, "D": True},
        )

    def test_symmetric_short(self):
        direction = baseline_direction(-0.90, 1.30)
        self.assertEqual(direction, -1)
        self.assertTrue(regime_flags(direction, 0.1, 0.2, -0.3)["D"])

    def test_no_trade_below_trigger(self):
        self.assertEqual(baseline_direction(0.70, -2.0), 0)

    def test_legacy_gap_definition(self):
        self.assertAlmostEqual(gap_return(0.0016, 1.4, 0.0032), -0.00288)

    def test_frozen_cost_bands(self):
        self.assertEqual(round_trip_cost_bps(1.0), 10.0)
        self.assertEqual(round_trip_cost_bps(2.0), 12.0)
        self.assertEqual(round_trip_cost_bps(3.0), 14.0)

    def test_net_bps(self):
        self.assertAlmostEqual(net_return_bps(0.0020, 2.0), 8.0)

    def test_source_gate_fails_closed(self):
        ok, missing = source_gate(
            btc_d_present=True,
            usdt_d_present=False,
            total3_present=True,
            binance_present=True,
        )
        self.assertFalse(ok)
        self.assertEqual(missing, ("tradingview_usdt_d",))


if __name__ == "__main__":
    unittest.main()
