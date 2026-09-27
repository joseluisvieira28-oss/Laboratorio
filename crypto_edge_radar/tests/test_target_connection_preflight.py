from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from radar.target_connection_preflight import (
    EXPECTED_CHAIN_HEAD,
    EXPECTED_EVENT_COUNT,
    EXPECTED_KEY_COUNT,
    EXPECTED_MAX_EVENT_ID,
    EXPECTED_SNAPSHOT_SHA,
    evaluate_target_snapshot,
    target_connection_preflight,
)


class TargetConnectionPreflightTests(TestCase):
    def test_missing_url_is_auth_required_and_non_mutating(self):
        result = target_connection_preflight("")
        self.assertEqual(result["classification"], "AUTH_REQUIRED_NOT_EXECUTED")
        self.assertFalse(result["connected"])
        self.assertFalse(result["target_url_configured"])
        self.assertFalse(result["database_mutation"])
        self.assertFalse(result["database_url_switch_authorized"])
        self.assertFalse(result["secret_value_exposed"])

    def test_connect_failure_is_fail_closed_and_secret_is_not_reflected(self):
        secret = "SUPER_SECRET_PASSWORD_123"
        url = f"postgresql://radar:{secret}@example.invalid:5432/postgres"
        with patch(
            "radar.target_connection_preflight._read_target_snapshot",
            side_effect=RuntimeError("synthetic connectivity failure"),
        ):
            result = target_connection_preflight(url)
        self.assertEqual(result["classification"], "TARGET_PREFLIGHT_FAIL_CLOSED")
        self.assertTrue(result["target_url_configured"])
        self.assertFalse(result["connected"])
        self.assertNotIn(secret, str(result))
        self.assertFalse(result["secret_value_exposed"])

    def test_exact_frozen_boundary_passes(self):
        snapshot = {"events": [{"id": i} for i in range(1, EXPECTED_MAX_EVENT_ID + 1)]}
        verified = {
            "event_count": EXPECTED_EVENT_COUNT,
            "key_count": EXPECTED_KEY_COUNT,
            "chain_head_sha256": EXPECTED_CHAIN_HEAD,
            "snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
        }
        with patch("radar.target_connection_preflight.verify_snapshot", return_value=verified):
            result = evaluate_target_snapshot(
                snapshot,
                sequence_last=EXPECTED_MAX_EVENT_ID,
                identity={"database_name": "postgres", "database_role": "radar"},
            )
        self.assertEqual(
            result["classification"],
            "TARGET_PREFLIGHT_PASS_AT_BACKUP_BOUNDARY",
        )
        self.assertTrue(all(result["checks"].values()))
        self.assertTrue(result["connected"])
        self.assertFalse(result["database_url_switch_authorized"])
        self.assertTrue(result["final_quiesced_refresh_required"])

    def test_any_mismatch_fails_closed(self):
        snapshot = {"events": [{"id": i} for i in range(1, EXPECTED_MAX_EVENT_ID + 1)]}
        verified = {
            "event_count": EXPECTED_EVENT_COUNT,
            "key_count": EXPECTED_KEY_COUNT - 1,
            "chain_head_sha256": EXPECTED_CHAIN_HEAD,
            "snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
        }
        with patch("radar.target_connection_preflight.verify_snapshot", return_value=verified):
            result = evaluate_target_snapshot(
                snapshot,
                sequence_last=EXPECTED_MAX_EVENT_ID,
                identity={},
            )
        self.assertEqual(
            result["classification"],
            "TARGET_PREFLIGHT_MISMATCH_FAIL_CLOSED",
        )
        self.assertFalse(result["checks"]["key_count_exact"])
        self.assertFalse(result["database_url_switch_authorized"])


if __name__ == "__main__":
    import unittest
    unittest.main()
