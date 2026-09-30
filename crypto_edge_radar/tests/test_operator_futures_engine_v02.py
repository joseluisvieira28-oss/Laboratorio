from __future__ import annotations

from datetime import datetime, timezone
import unittest

from radar.operator_futures_engine_v02 import (
    OperatorEngineError,
    compute_contract_volume,
    order_fee_usdt,
    timing_state,
    protective_prices,
)


class OperatorFuturesEngineV02Tests(unittest.TestCase):
    def test_zero_total_fee_falls_back_to_taker_fee(self):
        self.assertAlmostEqual(
            order_fee_usdt({"totalFee": 0, "takerFee": 0.0067, "makerFee": 0}),
            0.0067,
            places=10,
        )

    def test_positive_total_fee_has_precedence(self):
        self.assertAlmostEqual(
            order_fee_usdt({"totalFee": 0.01, "takerFee": 0.006, "makerFee": 0.004}),
            0.01,
            places=10,
        )

    def test_50_notional_maps_to_10_margin_at_5x(self):
        out = compute_contract_volume(
            target_notional_usdt=50.0,
            price=100.0,
            contract_size=0.01,
            min_vol=1,
            vol_unit=1,
        )
        self.assertEqual(out["volume_contracts"], 50)
        self.assertAlmostEqual(out["estimated_notional_usdt"], 50.0)
        self.assertAlmostEqual(out["estimated_initial_margin_usdt"], 10.0)

    def test_sizing_never_rounds_above_cap(self):
        out = compute_contract_volume(
            target_notional_usdt=50.0,
            price=123.0,
            contract_size=0.01,
            min_vol=1,
            vol_unit=1,
        )
        self.assertLessEqual(out["estimated_notional_usdt"], 50.0)

    def test_non_5x_sizing_is_rejected(self):
        with self.assertRaises(OperatorEngineError):
            compute_contract_volume(
                target_notional_usdt=10,
                price=100,
                contract_size=0.01,
                min_vol=1,
                vol_unit=1,
                leverage=1,
            )

    def test_timing_no_chase(self):
        target = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(
            timing_state(
                now=datetime(2026, 9, 29, 11, 59, 59, tzinfo=timezone.utc),
                entry_target=target,
                max_late_seconds=2,
            ),
            "WAITING",
        )
        self.assertEqual(
            timing_state(
                now=datetime(2026, 9, 29, 12, 0, 1, tzinfo=timezone.utc),
                entry_target=target,
                max_late_seconds=2,
            ),
            "DUE",
        )
        self.assertEqual(
            timing_state(
                now=datetime(2026, 9, 29, 12, 0, 3, tzinfo=timezone.utc),
                entry_target=target,
                max_late_seconds=2,
            ),
            "MISSED_NO_CHASE",
        )


    def test_protective_prices_round_conservatively_for_long(self):
        out = protective_prices(
            entry_price=100.0,
            direction="LONG",
            stop_distance_fraction=0.051,
            take_profit_distance_fraction=0.153,
            price_unit=0.1,
        )
        self.assertEqual(out["stop_loss_price"], 94.9)
        self.assertEqual(out["take_profit_price"], 115.3)

    def test_protective_prices_round_conservatively_for_short(self):
        out = protective_prices(
            entry_price=100.0,
            direction="SHORT",
            stop_distance_fraction=0.051,
            take_profit_distance_fraction=0.153,
            price_unit=0.1,
        )
        self.assertEqual(out["stop_loss_price"], 105.1)
        self.assertEqual(out["take_profit_price"], 84.7)


if __name__ == "__main__":
    unittest.main()
