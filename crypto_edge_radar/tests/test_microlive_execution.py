from datetime import datetime, timezone
from decimal import Decimal
import os
import tempfile
import unittest

from radar.execution import (
    ARM_TOKEN,
    ExecutionBlocked,
    ExecutionState,
    MicroLiveCoordinator,
    MicroLiveSettings,
    inspect_signal_identity,
    round_quantity,
    validate_signal,
)

UTC = timezone.utc


def valid_signal():
    return {
        "strategy_id": "CED1D-0031",
        "symbol": "AVAXUSDT",
        "market_provider": "BINANCE_USDM_PUBLIC",
        "direction": "LONG",
        "metadata": {
            "candidate": "CED1D-0031",
            "signal_key": "CED1D-0031:2026-09-20",
            "reference_entry": "2026-09-21T00:01:00+00:00",
            "reference_exit": "2026-09-22T00:01:00+00:00",
            "direction_rule": "CONTINUATION_SIGN_LOG_CLOSE_RATIO",
            "lookback_calendar_days": 20,
            "horizon_calendar_days": 1,
            "provider": "BINANCE_USDM_PUBLIC",
        },
    }


class FakeVenue:
    name = "BINANCE_USDM"

    def __init__(self):
        self.orders = []

    def preflight(self, symbol):
        return {"ok": True}

    def market_rules(self, symbol):
        return {"step_size": Decimal("0.1"), "min_qty": Decimal("0.1")}

    def mark_or_last_price(self, symbol):
        return Decimal("25")

    def submit_market(self, **kwargs):
        self.orders.append(kwargs)
        return {"status": "FILLED", "clientOrderId": kwargs["client_order_id"]}


class MicroLiveSafetyTests(unittest.TestCase):
    def test_identity_can_be_checked_before_entry(self):
        x = inspect_signal_identity(valid_signal())
        self.assertEqual(x["signal_key"], "CED1D-0031:2026-09-20")

    def test_exact_entry_window(self):
        x = validate_signal(
            valid_signal(), now=datetime(2026, 9, 21, 0, 1, 4, tzinfo=UTC)
        )
        self.assertEqual(x["direction"], "LONG")
        with self.assertRaises(ExecutionBlocked):
            validate_signal(
                valid_signal(), now=datetime(2026, 9, 21, 0, 1, 6, tzinfo=UTC)
            )

    def test_wrong_venue_blocked(self):
        s = MicroLiveSettings(True, ARM_TOKEN, "mexc", "x", "y")
        with self.assertRaises(ExecutionBlocked):
            s.assert_armed()

    def test_rounding_never_exceeds_cap(self):
        q = round_quantity(
            notional_usdt=Decimal("25"),
            price=Decimal("31.37"),
            step_size=Decimal("0.1"),
            min_qty=Decimal("0.1"),
        )
        self.assertLessEqual(q * Decimal("31.37"), Decimal("25"))

    def test_one_event_entry_then_exit(self):
        with tempfile.TemporaryDirectory() as td:
            state = os.path.join(td, "state.json")
            receipts = os.path.join(td, "r.jsonl")
            settings = MicroLiveSettings(True, ARM_TOKEN, "binance_usdm", state, receipts)
            venue = FakeVenue()
            c = MicroLiveCoordinator(settings, venue)
            entry = c.process_signal(
                valid_signal(), now=datetime(2026, 9, 21, 0, 1, 2, tzinfo=UTC)
            )
            self.assertEqual(entry["event"], "MICROLIVE_ENTRY_SUBMITTED")
            st = ExecutionState.load(state)
            self.assertEqual(st.status, "OPEN")
            out = c.maybe_exit_due(
                now=datetime(2026, 9, 22, 0, 1, 2, tzinfo=UTC)
            )
            self.assertEqual(out["event"], "MICROLIVE_EXIT_SUBMITTED")
            self.assertTrue(venue.orders[1]["reduce_only"])
            st = ExecutionState.load(state)
            self.assertEqual(st.completed_events, 1)

    def test_late_exit_closes_but_flags_incident(self):
        with tempfile.TemporaryDirectory() as td:
            state = os.path.join(td, "state.json")
            receipts = os.path.join(td, "r.jsonl")
            settings = MicroLiveSettings(True, ARM_TOKEN, "binance_usdm", state, receipts)
            venue = FakeVenue()
            c = MicroLiveCoordinator(settings, venue)
            c.process_signal(
                valid_signal(), now=datetime(2026, 9, 21, 0, 1, 2, tzinfo=UTC)
            )
            out = c.maybe_exit_due(
                now=datetime(2026, 9, 22, 0, 2, 0, tzinfo=UTC)
            )
            self.assertTrue(out["late_exit_incident"])
            self.assertEqual(out["event"], "MICROLIVE_EXIT_SUBMITTED")

    def test_no_second_real_event_under_v01(self):
        with tempfile.TemporaryDirectory() as td:
            state = os.path.join(td, "state.json")
            receipts = os.path.join(td, "r.jsonl")
            settings = MicroLiveSettings(True, ARM_TOKEN, "binance_usdm", state, receipts)
            venue = FakeVenue()
            c = MicroLiveCoordinator(settings, venue)
            c.process_signal(
                valid_signal(), now=datetime(2026, 9, 21, 0, 1, 2, tzinfo=UTC)
            )
            c.maybe_exit_due(now=datetime(2026, 9, 22, 0, 1, 2, tzinfo=UTC))
            with self.assertRaises(ExecutionBlocked):
                c.process_signal(
                    valid_signal(), now=datetime(2026, 9, 21, 0, 1, 3, tzinfo=UTC)
                )

    def test_not_armed_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            s = MicroLiveSettings(False, "", "binance_usdm", td + "/s", td + "/r")
            with self.assertRaises(ExecutionBlocked):
                MicroLiveCoordinator(s, FakeVenue()).process_signal(
                    valid_signal(), now=datetime(2026, 9, 21, 0, 1, 2, tzinfo=UTC)
                )


if __name__ == "__main__":
    unittest.main()
