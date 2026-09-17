import unittest
from datetime import datetime, timezone

from radar.timing import ExactTimingPolicy, TimingState

UTC = timezone.utc
TARGET = datetime(2026, 9, 23, 0, 0, 0, tzinfo=UTC)


class ExactTimingPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = ExactTimingPolicy(arm_lead_seconds=60, max_late_seconds=2)

    def test_waiting_before_arm_window(self):
        now = datetime(2026, 9, 22, 23, 58, 59, tzinfo=UTC)
        self.assertEqual(self.policy.classify(now=now, target=TARGET), TimingState.WAITING)

    def test_armed_before_exact_target(self):
        now = datetime(2026, 9, 22, 23, 59, 30, tzinfo=UTC)
        self.assertEqual(self.policy.classify(now=now, target=TARGET), TimingState.ARMED)

    def test_exact_target_is_due(self):
        self.assertEqual(self.policy.classify(now=TARGET, target=TARGET), TimingState.DUE)

    def test_small_technical_lag_is_due(self):
        now = datetime(2026, 9, 23, 0, 0, 1, 500000, tzinfo=UTC)
        self.assertEqual(self.policy.classify(now=now, target=TARGET), TimingState.DUE)

    def test_past_frozen_budget_is_missed(self):
        now = datetime(2026, 9, 23, 0, 0, 2, 1, tzinfo=UTC)
        self.assertEqual(self.policy.classify(now=now, target=TARGET), TimingState.MISSED)
        receipt = self.policy.receipt(now=now, target=TARGET)
        self.assertFalse(receipt["entry_window_open"])
        self.assertFalse(receipt["late_chase_allowed"])

    def test_naive_datetimes_fail_closed(self):
        with self.assertRaises(ValueError):
            self.policy.classify(now=datetime(2026, 9, 23), target=TARGET)


if __name__ == "__main__":
    unittest.main()
