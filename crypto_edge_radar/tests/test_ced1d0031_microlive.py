from decimal import Decimal
import unittest

from radar.ced1d0031_microlive import (
    FIRST_REAL_ENTRY,
    MAX_NOTIONAL_USDT,
    TARGET_NOTIONAL_USDT,
    _client_id,
    _round_qty,
    _validate_signal_payload,
)
from radar.ced1d0031_public import CANDIDATE, PROVIDER, SYMBOL


def signal():
    return {
        "candidate": CANDIDATE,
        "strategy_id": CANDIDATE,
        "symbol": SYMBOL,
        "provider": PROVIDER,
        "signal_key": "CED1D-0031:2026-09-20",
        "signal_day": "2026-09-20",
        "lag_day": "2026-08-31",
        "signal_completion": "2026-09-21T00:00:00+00:00",
        "reference_entry": "2026-09-21T00:01:00+00:00",
        "reference_exit": "2026-09-22T00:01:00+00:00",
        "lookback_calendar_days": 20,
        "horizon_calendar_days": 1,
        "direction_rule": "CONTINUATION_SIGN_LOG_CLOSE_RATIO",
        "direction": "LONG",
    }


class CED1D0031MicroLiveTests(unittest.TestCase):
    def test_exact_identity_and_boundary(self):
        out = _validate_signal_payload(signal())
        self.assertEqual(out["entry"], FIRST_REAL_ENTRY)

    def test_wrong_symbol_fails(self):
        row = signal()
        row["symbol"] = "BTCUSDT"
        with self.assertRaises(Exception):
            _validate_signal_payload(row)

    def test_target_below_hard_cap(self):
        self.assertLess(TARGET_NOTIONAL_USDT, MAX_NOTIONAL_USDT)

    def test_rounding_respects_cap_and_minimums(self):
        qty = _round_qty(
            price=Decimal("31.37"),
            step_size=Decimal("0.1"),
            min_qty=Decimal("0.1"),
            min_notional=Decimal("5"),
        )
        self.assertGreaterEqual(qty * Decimal("31.37"), Decimal("5"))
        self.assertLessEqual(qty * Decimal("31.37"), MAX_NOTIONAL_USDT)

    def test_min_notional_fail_closed(self):
        with self.assertRaises(Exception):
            _round_qty(
                price=Decimal("31.37"),
                step_size=Decimal("0.1"),
                min_qty=Decimal("0.1"),
                min_notional=Decimal("50"),
            )

    def test_client_ids_are_deterministic_and_distinct(self):
        a = _client_id("CED1D-0031:2026-09-20", "e")
        b = _client_id("CED1D-0031:2026-09-20", "e")
        x = _client_id("CED1D-0031:2026-09-20", "x")
        self.assertEqual(a, b)
        self.assertNotEqual(a, x)
        self.assertLessEqual(len(a), 32)


if __name__ == "__main__":
    unittest.main()
