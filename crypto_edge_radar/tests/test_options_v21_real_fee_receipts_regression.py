"""Regression evidence: four historical MEXC Futures positions, eight taker fills.

No credentials, account reads, exchange calls, orders, or modifications to original receipts.
The historical fee reconciliation is an operational accounting fix, NOT scientific edge.
"""
from __future__ import annotations

import unittest
from radar.options_v21_futures_autolive_engine import _fee


class RealTakerFeeRegressionTests(unittest.TestCase):
    # Values from immutable 2026-09-29 evidence receipt.
    HISTORICAL_EIGHT_FILL_FEES_USDT = (
        0.00672396, 0.00675169,
        0.00675228, 0.00675464,
        0.00675284, 0.00667683,
        0.00667659, 0.00669120,
    )

    def test_zero_totalfee_does_not_hide_eight_real_taker_fees(self):
        detected = []
        for charged in self.HISTORICAL_EIGHT_FILL_FEES_USDT:
            payload = {"totalFee": 0, "takerFee": charged, "makerFee": 0}
            actual = _fee(payload)
            self.assertAlmostEqual(actual, charged, places=8)
            detected.append(actual)
        self.assertAlmostEqual(sum(detected), 0.05378003, places=8)

    def test_nonzero_total_fee_not_double_counted(self):
        payload = {"totalFee": 0.00675284, "takerFee": 0.00675284, "makerFee": 0}
        self.assertAlmostEqual(_fee(payload), 0.00675284, places=8)

    def test_maker_component_is_not_discarded_when_totalfee_zero(self):
        payload = {"totalFee": "0", "takerFee": 0, "makerFee": "0.00125"}
        self.assertAlmostEqual(_fee(payload), 0.00125, places=8)


if __name__ == "__main__":
    unittest.main()
