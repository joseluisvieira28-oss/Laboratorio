from __future__ import annotations

from pathlib import Path
import unittest


class ETFCMEExactSchedulerIntegrationTests(unittest.TestCase):
    def test_runtime_starts_dedicated_scheduler_thread_and_surfaces_state(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "radar" / "forward_web.py").read_text()
        self.assertIn("ETFCMEExactRuntimeScheduler", source)
        self.assertIn('name="etf-cme-exact-timing-scheduler"', source)
        self.assertIn('"etf_cme_exact_scheduler": self.etf_cme_exact_scheduler.state()', source)

    def test_scientific_timing_constants_are_not_redefined_in_runtime_scheduler(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "radar" / "etf_cme_exact_scheduler.py").read_text()
        self.assertNotIn("max_late_seconds=3", source)
        self.assertNotIn("max_late_seconds = 3", source)
        self.assertNotIn("INFORMATION_LAG_DAYS =", source)
        self.assertNotIn("HOLD_DAYS =", source)
        self.assertIn("ExactTimingPolicy()", source)
        self.assertIn('BOUNDARY_AS_OF_DATE = "2026-09-15"', source)


if __name__ == "__main__":
    unittest.main()
