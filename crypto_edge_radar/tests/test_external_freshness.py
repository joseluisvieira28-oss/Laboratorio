import unittest
from datetime import datetime, timezone

from radar.external_freshness import collector_freshness


def run(candidate, path, created="2026-09-18T15:00:00Z", conclusion="success"):
    return [{
        "id": 123,
        "path": path,
        "created_at": created,
        "updated_at": "2026-09-18T15:10:00Z",
        "conclusion": conclusion,
    }]


class ExternalFreshnessTests(unittest.TestCase):
    def test_ced_fresh_without_importing_outcomes(self):
        candidate = "CED1D-0031"
        rows = run(candidate, ".github/workflows/ced1d-0031-prospective-shadow-collector.yml")
        state = collector_freshness(candidate, now=datetime(2026, 9, 19, 16, tzinfo=timezone.utc), runs=rows)
        self.assertEqual(state["freshness_classification"], "FRESH")
        self.assertIsNone(state["eligible_event_count"])
        self.assertIn("NO_OUTCOMES", state["count_visibility"])

    def test_stale_is_explicit(self):
        candidate = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
        rows = run(candidate, ".github/workflows/htf-dh03-12h-forward-shadow.yml")
        state = collector_freshness(candidate, now=datetime(2026, 9, 22, tzinfo=timezone.utc), runs=rows)
        self.assertEqual(state["freshness_classification"], "STALE")

    def test_failed_run_is_fail_closed(self):
        candidate = "CED1D-0031"
        rows = run(candidate, ".github/workflows/ced1d-0031-prospective-shadow-collector.yml", conclusion="failure")
        state = collector_freshness(candidate, now=datetime(2026, 9, 19, tzinfo=timezone.utc), runs=rows)
        self.assertEqual(state["freshness_classification"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
