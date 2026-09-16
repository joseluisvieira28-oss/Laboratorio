import unittest

from radar.models import Direction
from radar.strategies.etf_cme_instflow_001 import (
    CFTCObservation,
    CFTC_CONTRACT_CODE,
    compute_frozen_signal,
)


class ETFCMEInstFlowSignalTests(unittest.TestCase):
    def test_positive_delta_is_long(self):
        previous = CFTCObservation("2026-09-08", 1000, 400, 300)
        current = CFTCObservation("2026-09-15", 1000, 450, 300)
        signal = compute_frozen_signal(previous, current)
        self.assertEqual(signal.contract_code, CFTC_CONTRACT_CODE)
        self.assertEqual(signal.direction, Direction.LONG)
        self.assertAlmostEqual(signal.signal_value, 0.05)
        self.assertEqual(signal.information_lag_days, 8)
        self.assertEqual(signal.hold_days, 7)

    def test_negative_delta_is_short(self):
        previous = CFTCObservation("2026-09-08", 1000, 450, 300)
        current = CFTCObservation("2026-09-15", 1000, 400, 300)
        signal = compute_frozen_signal(previous, current)
        self.assertEqual(signal.direction, Direction.SHORT)
        self.assertAlmostEqual(signal.signal_value, -0.05)

    def test_zero_delta_is_flat(self):
        previous = CFTCObservation("2026-09-08", 1000, 400, 300)
        current = CFTCObservation("2026-09-15", 1200, 400, 300)
        signal = compute_frozen_signal(previous, current)
        self.assertEqual(signal.direction, Direction.NONE)
        self.assertEqual(signal.signal_value, 0.0)

    def test_non_positive_open_interest_fails_closed(self):
        previous = CFTCObservation("2026-09-08", 1000, 400, 300)
        current = CFTCObservation("2026-09-15", 0, 450, 300)
        with self.assertRaises(ValueError):
            compute_frozen_signal(previous, current)


if __name__ == "__main__":
    unittest.main()
