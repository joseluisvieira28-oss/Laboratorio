from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from scripts.mexc_triple_fishing_operator_v04 import (
    BNB,
    DH03,
    OPTIONS,
    TripleFishingOperatorV04,
)


class FakeLedger:
    def __init__(self, reservations=None):
        self.reservations = list(reservations or [])
    def current(self):
        return {"capacity": 3, "reservations": list(self.reservations)}


class FakeEngine:
    def __init__(self, reservations=None):
        self.ledger = FakeLedger(reservations)
        self.entered = []
    def manage_all(self):
        return {"status": "MULTISLOT_MANAGEMENT_OK"}
    def enter_signal(self, signal):
        self.entered.append(dict(signal))
        self.ledger.reservations.append(
            {
                "candidate_id": signal["candidate_id"],
                "signal_identity": signal["immutable_signal_key"],
                "symbol": signal["symbol"],
            }
        )
        return {
            "status": "FILLED_EXIT_PENDING",
            "candidate_id": signal["candidate_id"],
            "signal_identity": signal["immutable_signal_key"],
        }


class FakeSource:
    def __init__(self, result):
        self.result = result
        self.marks = []
    def poll(self, **kwargs):
        return self.result
    def mark(self, signal_identity, status):
        self.marks.append((signal_identity, status))


def sig(candidate, key, symbol):
    now = datetime.now(timezone.utc)
    return {
        "candidate_id": candidate,
        "strategy_id": candidate,
        "immutable_signal_key": key,
        "symbol": symbol,
        "entry_target_utc": (now - timedelta(seconds=0.25)).isoformat().replace("+00:00", "Z"),
        "exit_target_utc": (now + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
        "max_late_seconds": 5,
    }


class SupervisorV04Tests(unittest.TestCase):
    def build(self, *, engine=None, bnb=None, options=None, dh03=None):
        self.td = tempfile.TemporaryDirectory()
        root = Path(self.td.name)
        engine = engine or FakeEngine()
        bnb = bnb or FakeSource({"status": "OK", "signals": []})
        options = options or FakeSource({"status": "OK", "signals": []})
        dh03 = dh03 or FakeSource({"status": "OK", "signals": []})
        sup = TripleFishingOperatorV04(
            engine=engine,
            bnb_source=bnb,
            options_source=options,
            dh03_source=dh03,
            state_path=str(root / "state.json"),
        )
        return sup, engine, bnb, options, dh03

    def tearDown(self):
        if hasattr(self, "td"):
            self.td.cleanup()

    def test_three_distinct_due_signals_are_entered_same_cycle(self):
        sup, engine, bnb, options, dh03 = self.build(
            bnb=FakeSource({"status": "OK", "signals": [sig(BNB, "b", "BNB_USDT")]}),
            options=FakeSource({"status": "OK", "signal": sig(OPTIONS, "o", "BTC_USDT")}),
            dh03=FakeSource({"status": "OK", "signals": [sig(DH03, "d", "XRP_USDT")]}),
        )
        out = sup.run_cycle()
        self.assertEqual(len(engine.entered), 3)
        self.assertEqual(out["reservation_count"], 3)
        self.assertEqual({x["candidate_id"] for x in engine.entered}, {OPTIONS, BNB, DH03})

    def test_fourth_due_signal_is_marked_capacity_no_chase(self):
        dh = FakeSource(
            {
                "status": "OK",
                "signals": [
                    sig(DH03, "d1", "XRP_USDT"),
                    sig(DH03, "d2", "DOGE_USDT"),
                ],
            }
        )
        sup, engine, bnb, options, dh03 = self.build(
            bnb=FakeSource({"status": "OK", "signals": [sig(BNB, "b", "BNB_USDT")]}),
            options=FakeSource({"status": "OK", "signal": sig(OPTIONS, "o", "BTC_USDT")}),
            dh03=dh,
        )
        sup.run_cycle()
        self.assertEqual(len(engine.entered), 3)
        all_marks = dh03.marks
        self.assertTrue(
            any(status == "MISSED_CAPACITY_NO_CHASE" for _, status in all_marks),
            all_marks,
        )

    def test_existing_options_btc_reservation_blocks_dh03_btc_only(self):
        engine = FakeEngine(
            [
                {
                    "candidate_id": OPTIONS,
                    "signal_identity": "existing-o",
                    "symbol": "BTC_USDT",
                }
            ]
        )
        dh = FakeSource({"status": "OK", "signals": [sig(DH03, "btc-d", "BTC_USDT")]})
        bnb = FakeSource({"status": "OK", "signals": [sig(BNB, "b", "BNB_USDT")]})
        sup, engine, bnb, options, dh03 = self.build(
            engine=engine,
            bnb=bnb,
            options=FakeSource({"status": "OK", "signals": []}),
            dh03=dh,
        )
        sup.run_cycle()
        self.assertEqual([x["candidate_id"] for x in engine.entered], [BNB])
        self.assertIn(("btc-d", "MISSED_SYMBOL_CONFLICT_NO_CHASE"), dh03.marks)


if __name__ == "__main__":
    unittest.main()
