from __future__ import annotations

from datetime import datetime, timezone
import tempfile
from pathlib import Path
import unittest

from radar.bnb_launchpool_watcher import LaunchpoolAnnouncement
from scripts.mexc_bnb_operator_autolive_v01 import (
    BNBOperatorAutoLiveV01,
    build_signal,
)


class FakeReadonly:
    def __init__(self, positions=None):
        self.positions = positions or []

    def open_positions(self):
        return list(self.positions)


class FakeEngine:
    def __init__(self, *, positions=None, enter_result=None):
        self.readonly = FakeReadonly(positions)
        self.enter_result = enter_result or {"status": "FILLED_EXIT_PENDING"}
        self.entered = []

    def manage_active(self):
        return {"status": "IDLE_NO_OPERATOR_POSITION"}

    def enter_signal(self, signal):
        self.entered.append(signal)
        return dict(self.enter_result)


class FakeSource:
    def __init__(self, events):
        self.events = events

    def discover_eligible(self, *, now_ms):
        return list(self.events)


class BNBAutoLiveV01Tests(unittest.TestCase):
    def event(self, published_ms):
        return LaunchpoolAnnouncement(
            article_code="a" * 32,
            title="Launchpool BNB test",
            published_ms=published_ms,
            published_utc=datetime.fromtimestamp(
                published_ms / 1000, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            detail_sha256="b" * 64,
        )

    def test_signal_freezes_10_margin_50_notional_5x(self):
        event = self.event(1_790_000_000_000)
        signal = build_signal([event])
        self.assertEqual(signal["max_initial_margin_usdt"], 10.0)
        self.assertEqual(signal["max_notional_usdt"], 50.0)
        self.assertEqual(signal["leverage"], 5)
        self.assertEqual(signal["direction"], "LONG")
        self.assertFalse(signal["scientific_credit"])

    def test_slot_conflict_never_calls_executor(self):
        # publication at 11:50 UTC -> first 15m open 12:00 UTC
        published_ms = int(datetime(2026, 9, 29, 11, 50, tzinfo=timezone.utc).timestamp() * 1000)
        event = self.event(published_ms)
        now_ms = int(datetime(2026, 9, 29, 12, 0, 1, tzinfo=timezone.utc).timestamp() * 1000)
        with tempfile.TemporaryDirectory() as td:
            engine = FakeEngine(positions=[{"symbol": "BTC_USDT"}])
            sup = BNBOperatorAutoLiveV01(
                engine=engine,
                state_path=str(Path(td) / "state.json"),
                source=FakeSource([event]),
            )
            pre_ms = int(datetime(2026, 9, 29, 11, 59, 30, tzinfo=timezone.utc).timestamp() * 1000)
            sup.run_cycle(now_ms=pre_ms)
            state = sup.run_cycle(now_ms=now_ms)
            self.assertEqual(state["status"], "GLOBAL_SLOT_OCCUPIED")
            self.assertEqual(engine.entered, [])

    def test_due_free_slot_delegates_to_engine(self):
        published_ms = int(datetime(2026, 9, 29, 11, 50, tzinfo=timezone.utc).timestamp() * 1000)
        event = self.event(published_ms)
        now_ms = int(datetime(2026, 9, 29, 12, 0, 1, tzinfo=timezone.utc).timestamp() * 1000)
        with tempfile.TemporaryDirectory() as td:
            engine = FakeEngine()
            sup = BNBOperatorAutoLiveV01(
                engine=engine,
                state_path=str(Path(td) / "state.json"),
                source=FakeSource([event]),
            )
            pre_ms = int(datetime(2026, 9, 29, 11, 59, 30, tzinfo=timezone.utc).timestamp() * 1000)
            sup.run_cycle(now_ms=pre_ms)
            state = sup.run_cycle(now_ms=now_ms)
            self.assertEqual(state["status"], "FILLED_EXIT_PENDING")
            self.assertEqual(len(engine.entered), 1)


if __name__ == "__main__":
    unittest.main()
