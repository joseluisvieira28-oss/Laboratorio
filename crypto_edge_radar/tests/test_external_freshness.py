import unittest
from unittest.mock import patch
from datetime import datetime, timezone

from radar.external_freshness import (
    ExternalFreshnessError,
    all_external_freshness,
    collector_freshness,
    fallback_freshness,
    validate_dh03_safe_progress,
)


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

    def test_dh03_safe_progress_counts_are_bound_to_latest_successful_run(self):
        candidate = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
        rows = run(
            candidate,
            ".github/workflows/htf-dh03-12h-forward-shadow.yml",
        )
        rows[0]["id"] = 36216704993
        safe = {
            "schema_version": "DH03_SAFE_PROGRESS_V0.1",
            "strategy_id": candidate,
            "source_workflow_run_id": 36216704993,
            "checked_at_utc": "2026-09-26T04:03:51Z",
            "latest_archive_day": "2026-09-25",
            "collector_status": "OK",
            "used_as_forward_evidence": True,
            "counts": {
                "signals": 4,
                "price_exits": 2,
                "final_resolutions": 1,
                "funding_pending": 1,
                "unresolved_price_paths": 2,
                "overlap_skipped": 3,
            },
            "outcomes_included": False,
            "prices_included": False,
            "returns_included": False,
            "r_multiples_included": False,
            "profit_factor_included": False,
            "trade_rows_included": False,
            "symbol_breakdown_included": False,
            "science_changed": False,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        with patch(
            "radar.external_freshness.fetch_dh03_safe_progress",
            return_value=safe,
        ) as fetch:
            state = collector_freshness(
                candidate,
                now=datetime(2026, 9, 19, 16, tzinfo=timezone.utc),
                runs=rows,
            )
        fetch.assert_called_once_with(expected_run_id=36216704993, timeout=15)
        self.assertEqual(state["eligible_event_count"], 4)
        self.assertEqual(state["resolved_forward_count"], 1)
        self.assertEqual(state["price_exit_count"], 2)
        self.assertEqual(state["funding_pending_count"], 1)
        self.assertEqual(state["unresolved_price_path_count"], 2)
        self.assertEqual(state["overlap_skipped_count"], 3)
        self.assertFalse(state["safe_progress_outcomes_imported"])
        self.assertIn("NO_OUTCOMES_IMPORTED", state["count_visibility"])

    def test_dh03_safe_progress_failure_keeps_counts_null(self):
        candidate = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
        rows = run(
            candidate,
            ".github/workflows/htf-dh03-12h-forward-shadow.yml",
        )
        with patch(
            "radar.external_freshness.fetch_dh03_safe_progress",
            side_effect=ExternalFreshnessError("run mismatch"),
        ):
            state = collector_freshness(
                candidate,
                now=datetime(2026, 9, 19, 16, tzinfo=timezone.utc),
                runs=rows,
            )
        self.assertIsNone(state["eligible_event_count"])
        self.assertIsNone(state["resolved_forward_count"])
        self.assertIn("FAIL_CLOSED", state["count_visibility"])
        self.assertIn("run mismatch", state["safe_progress_error"])

    def test_dh03_safe_progress_validator_rejects_outcome_firewall_flip(self):
        payload = {
            "schema_version": "DH03_SAFE_PROGRESS_V0.1",
            "strategy_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
            "source_workflow_run_id": 123,
            "checked_at_utc": "2026-09-26T04:03:51Z",
            "latest_archive_day": "2026-09-25",
            "collector_status": "OK",
            "used_as_forward_evidence": True,
            "counts": {
                "signals": 1,
                "price_exits": 1,
                "final_resolutions": 1,
                "funding_pending": 0,
                "unresolved_price_paths": 0,
                "overlap_skipped": 0,
            },
            "outcomes_included": False,
            "prices_included": False,
            "returns_included": True,
            "r_multiples_included": False,
            "profit_factor_included": False,
            "trade_rows_included": False,
            "symbol_breakdown_included": False,
            "science_changed": False,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        with self.assertRaisesRegex(ExternalFreshnessError, "firewall field not false"):
            validate_dh03_safe_progress(payload, expected_run_id=123)

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
