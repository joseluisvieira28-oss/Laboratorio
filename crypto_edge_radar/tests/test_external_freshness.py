import unittest
from datetime import datetime, timezone

from radar.external_freshness import collector_freshness, fallback_freshness


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

    def test_public_fallback_is_explicit_proxy_and_imports_no_outcomes(self):
        state = fallback_freshness(
            "CED1D-0031",
            now=datetime(2026, 9, 19, 16, tzinfo=timezone.utc),
            row={
                "created_at": "2026-09-18T15:00:00Z",
                "conclusion": "success",
                "source_status": "GITHUB_PUBLIC_BADGE_AND_BRANCH_ATOM_FALLBACK",
            },
        )
        self.assertEqual(state["freshness_classification"], "FRESH")
        self.assertIn("PROXY", state["timestamp_semantics"])
        self.assertIsNone(state["eligible_event_count"])



    def test_ced1d_legacy_route_is_superseded_without_querying_github(self):
        with patch("radar.external_freshness.fetch_runs") as fetch_runs, patch(
            "radar.external_freshness.fetch_public_fallback"
        ) as fallback:
            result = all_external_freshness(
                now=datetime(2026, 9, 22, 8, 0, tzinfo=timezone.utc)
            )
        ced = result["CED1D-0031"]
        self.assertEqual(ced["collector_status"], "SUPERSEDED")
        self.assertEqual(ced["freshness_classification"], "SUPERSEDED")
        self.assertEqual(ced["superseded_by"], "RENDER_SHADOW_V0.3")
        self.assertEqual(ced["new_forward_boundary"], "2026-09-22T00:00:00Z")
        # Other collectors may still query GitHub; CED1D itself must never use the old route.
        self.assertFalse(
            any(
                call.kwargs.get("branch") == "ced-1d-v3-byte-recovery-2026-09-17"
                for call in fetch_runs.call_args_list
            )
        )
        self.assertFalse(
            any(
                call.kwargs.get("branch") == "ced-1d-v3-byte-recovery-2026-09-17"
                for call in fallback.call_args_list
            )
        )

if __name__ == "__main__":
    unittest.main()
