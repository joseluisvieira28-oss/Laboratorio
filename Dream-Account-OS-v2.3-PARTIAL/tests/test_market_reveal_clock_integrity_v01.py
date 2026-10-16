import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from clock_integrity import (
    ClockSample,
    analyze_clock_samples,
    summarize_clock_transitions,
    transition,
)


class ClockIntegrityTests(unittest.TestCase):
    def test_equal_progress_has_zero_residual(self):
        row = transition(
            ClockSample(wall_ns=100, monotonic_ns=50),
            ClockSample(wall_ns=200, monotonic_ns=150),
        )
        self.assertEqual(row.residual_ns, 0)
        self.assertFalse(row.wall_reversed)
        self.assertFalse(row.monotonic_reversed)

    def test_wall_step_is_measured_not_thresholded(self):
        rows = analyze_clock_samples([
            ClockSample(wall_ns=100, monotonic_ns=100),
            ClockSample(wall_ns=1_100, monotonic_ns=200),
        ])
        self.assertEqual(rows[0].residual_ns, 900)
        summary = summarize_clock_transitions(rows)
        self.assertEqual(summary["max_abs_residual_ns"], 900)

    def test_wall_reversal_is_preserved_as_evidence(self):
        rows = analyze_clock_samples([
            ClockSample(wall_ns=1_000, monotonic_ns=100),
            ClockSample(wall_ns=900, monotonic_ns=200),
        ])
        self.assertTrue(rows[0].wall_reversed)
        self.assertFalse(rows[0].monotonic_reversed)

    def test_monotonic_reversal_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "monotonic clock reversed"):
            analyze_clock_samples([
                ClockSample(wall_ns=100, monotonic_ns=200),
                ClockSample(wall_ns=200, monotonic_ns=100),
            ])

    def test_no_samples_has_explicit_empty_summary(self):
        summary = summarize_clock_transitions(())
        self.assertEqual(summary["sample_transition_count"], 0)
        self.assertIsNone(summary["max_abs_residual_ns"])


if __name__ == "__main__":
    unittest.main()
