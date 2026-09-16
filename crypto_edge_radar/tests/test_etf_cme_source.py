import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from radar.strategies.etf_cme_instflow_001 import CFTCObservation
from radar.strategies.etf_cme_source import current_signal_receipt


PREVIOUS = CFTCObservation("2026-09-01", 1000, 400, 300)
CURRENT = CFTCObservation("2026-09-08", 1000, 450, 300)


class ETFCMECurrentSignalTrapTests(unittest.TestCase):
    @patch("radar.strategies.etf_cme_source.fetch_latest_two")
    def test_before_information_safe_time_waits(self, fetch):
        fetch.return_value = (PREVIOUS, CURRENT)
        receipt = current_signal_receipt(
            now=datetime(2026, 9, 15, 23, 59, tzinfo=timezone.utc)
        )
        self.assertEqual(receipt["state"], "WAITING_INFORMATION_SAFE_TIME")
        self.assertFalse(receipt["entry_eligible_now"])

    @patch("radar.strategies.etf_cme_source.fetch_latest_two")
    def test_exact_information_safe_time_can_signal(self, fetch):
        fetch.return_value = (PREVIOUS, CURRENT)
        receipt = current_signal_receipt(
            now=datetime(2026, 9, 16, 0, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(receipt["state"], "EXACT_ENTRY_TIME")
        self.assertEqual(receipt["direction"], "LONG")
        self.assertTrue(receipt["entry_eligible_now"])
        self.assertFalse(receipt["micro_live_eligible"])

    @patch("radar.strategies.etf_cme_source.fetch_latest_two")
    def test_late_entry_is_blocked(self, fetch):
        fetch.return_value = (PREVIOUS, CURRENT)
        receipt = current_signal_receipt(
            now=datetime(2026, 9, 16, 0, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(receipt["state"], "ENTRY_WINDOW_PASSED_DO_NOT_CHASE")
        self.assertFalse(receipt["entry_eligible_now"])


if __name__ == "__main__":
    unittest.main()
