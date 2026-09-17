import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from radar.scheduler import ExactTimingScheduler

UTC = timezone.utc
TARGET = "2026-09-23T00:00:00Z"


class FakeAdapter:
    strategy_id = "TEST-001"

    def __init__(self, state):
        self.state = state

    def timing_plan(self, now):
        return {
            "strategy_id": self.strategy_id,
            "operational_timing": {
                "timing_state": self.state,
                "target_time_utc": TARGET,
                "arm_at_utc": "2026-09-22T23:59:00Z",
            },
        }


class FakeRunner:
    def __init__(self, adapter):
        self.engine = SimpleNamespace(registry=SimpleNamespace(adapters=(adapter,)))
        self.cycle_no = 0
        self.code = 0

    def run_cycle(self):
        self.cycle_no += 1
        return self.code, {"health": "OK" if self.code == 0 else "FAIL_CLOSED"}


class SchedulerTests(unittest.TestCase):
    def test_armed_wakes_at_exact_target(self):
        adapter = FakeAdapter("ARMED")
        runner = FakeRunner(adapter)
        scheduler = ExactTimingScheduler(runner=runner, normal_interval=30)
        now = datetime(2026, 9, 22, 23, 59, 30, tzinfo=UTC)
        decision = scheduler.next_decision(now)
        self.assertEqual(decision.reason, "WAKE_AT_EXACT_ENTRY")
        self.assertEqual(decision.sleep_seconds, 30.0)
        self.assertEqual(decision.target_time_utc, TARGET)

    def test_due_event_retries_until_success(self):
        adapter = FakeAdapter("DUE")
        runner = FakeRunner(adapter)
        scheduler = ExactTimingScheduler(runner=runner, normal_interval=30, due_retry_seconds=0.25)
        now = datetime(2026, 9, 23, 0, 0, 1, tzinfo=UTC)
        decision = scheduler.next_decision(now)
        self.assertEqual(decision.reason, "EXACT_ENTRY_DUE_RETRY")
        self.assertEqual(decision.sleep_seconds, 0.25)

    def test_successful_due_event_is_consumed(self):
        adapter = FakeAdapter("DUE")
        runner = FakeRunner(adapter)
        scheduler = ExactTimingScheduler(runner=runner, normal_interval=30)
        now = datetime(2026, 9, 23, 0, 0, 1, tzinfo=UTC)
        scheduler.mark_successful_due_events(now)
        decision = scheduler.next_decision(now)
        self.assertEqual(decision.reason, "NORMAL_HEARTBEAT")
        self.assertEqual(decision.sleep_seconds, 30.0)

    def test_missed_event_is_never_chased(self):
        adapter = FakeAdapter("MISSED")
        runner = FakeRunner(adapter)
        scheduler = ExactTimingScheduler(runner=runner, normal_interval=30)
        now = datetime(2026, 9, 23, 0, 0, 3, tzinfo=UTC)
        decision = scheduler.next_decision(now)
        self.assertEqual(decision.reason, "NORMAL_HEARTBEAT")


if __name__ == "__main__":
    unittest.main()
