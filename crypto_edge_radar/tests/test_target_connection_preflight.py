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


def _events(n: int):
    return [
        {
            "id": i,
            "chain_sha256": EXPECTED_CHAIN_HEAD if i == EXPECTED_MAX_EVENT_ID else f"chain-{i}",
        }
        for i in range(1, n + 1)
    ]


def _keys(n: int, *, suffix_start: int | None = None):
    rows = []
    for i in range(1, n + 1):
        event_id = i
        if suffix_start is not None and i > EXPECTED_KEY_COUNT:
            event_id = suffix_start + (i - EXPECTED_KEY_COUNT - 1)
        rows.append(
            {
                "event_type": "T",
                "event_key": f"k-{i}",
                "event_id": event_id,
            }
        )
    return rows


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
        snapshot = {
            "events": _events(EXPECTED_EVENT_COUNT),
            "event_keys": _keys(EXPECTED_KEY_COUNT),
        }
        full = {
            "event_count": EXPECTED_EVENT_COUNT,
            "key_count": EXPECTED_KEY_COUNT,
            "chain_head_sha256": EXPECTED_CHAIN_HEAD,
            "snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
        }
        boundary = dict(full)
        with patch(
            "radar.target_connection_preflight.verify_snapshot",
            side_effect=[full, boundary],
        ):
            result = evaluate_target_snapshot(
                snapshot,
                sequence_last=EXPECTED_MAX_EVENT_ID,
                identity={"database_name": "postgres", "database_role": "radar_runtime"},
            )
        self.assertEqual(
            result["classification"],
            "TARGET_PREFLIGHT_PASS_BACKUP_PREFIX_CURRENT_CHAIN_OK",
        )
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["suffix_event_count"], 0)
        self.assertEqual(result["suffix_key_count"], 0)
        self.assertFalse(result["database_url_switch_authorized"])
        self.assertTrue(result["final_quiesced_refresh_required"])

    def test_append_only_suffix_is_accepted_when_frozen_prefix_remains_exact(self):
        current_events = EXPECTED_EVENT_COUNT + 3
        current_keys = EXPECTED_KEY_COUNT + 3
        snapshot = {
            "events": _events(current_events),
            "event_keys": _keys(current_keys, suffix_start=EXPECTED_EVENT_COUNT + 1),
        }
        full = {
            "event_count": current_events,
            "key_count": current_keys,
            "chain_head_sha256": "current-chain-head",
            "snapshot_sha256": "current-snapshot",
        }
        boundary = {
            "event_count": EXPECTED_EVENT_COUNT,
            "key_count": EXPECTED_KEY_COUNT,
            "chain_head_sha256": EXPECTED_CHAIN_HEAD,
            "snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
        }
        with patch(
            "radar.target_connection_preflight.verify_snapshot",
            side_effect=[full, boundary],
        ):
            result = evaluate_target_snapshot(
                snapshot,
                sequence_last=current_events,
                identity={},
            )
        self.assertEqual(
            result["classification"],
            "TARGET_PREFLIGHT_PASS_BACKUP_PREFIX_CURRENT_CHAIN_OK",
        )
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["suffix_event_count"], 3)
        self.assertEqual(result["suffix_key_count"], 3)
        self.assertEqual(result["current_event_count"], current_events)
        self.assertEqual(result["backup_boundary_event_count"], EXPECTED_EVENT_COUNT)

    def test_any_frozen_prefix_mismatch_fails_closed(self):
        snapshot = {
            "events": _events(EXPECTED_EVENT_COUNT + 1),
            "event_keys": _keys(EXPECTED_KEY_COUNT + 1, suffix_start=EXPECTED_EVENT_COUNT + 1),
        }
        full = {
            "event_count": EXPECTED_EVENT_COUNT + 1,
            "key_count": EXPECTED_KEY_COUNT + 1,
            "chain_head_sha256": "current-chain-head",
            "snapshot_sha256": "current-snapshot",
        }
        boundary = {
            "event_count": EXPECTED_EVENT_COUNT,
            "key_count": EXPECTED_KEY_COUNT - 1,
            "chain_head_sha256": EXPECTED_CHAIN_HEAD,
            "snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
        }
        with patch(
            "radar.target_connection_preflight.verify_snapshot",
            side_effect=[full, boundary],
        ):
            result = evaluate_target_snapshot(
                snapshot,
                sequence_last=EXPECTED_EVENT_COUNT + 1,
                identity={},
            )
        self.assertEqual(
            result["classification"],
            "TARGET_PREFLIGHT_MISMATCH_FAIL_CLOSED",
        )
        self.assertFalse(result["checks"]["backup_boundary_key_count_exact"])
        self.assertFalse(result["database_url_switch_authorized"])

    def test_sequence_drift_fails_closed_even_with_valid_prefix(self):
        snapshot = {
            "events": _events(EXPECTED_EVENT_COUNT),
            "event_keys": _keys(EXPECTED_KEY_COUNT),
        }
        verified = {
            "event_count": EXPECTED_EVENT_COUNT,
            "key_count": EXPECTED_KEY_COUNT,
            "chain_head_sha256": EXPECTED_CHAIN_HEAD,
            "snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
        }
        with patch(
            "radar.target_connection_preflight.verify_snapshot",
            side_effect=[verified, verified],
        ):
            result = evaluate_target_snapshot(
                snapshot,
                sequence_last=EXPECTED_EVENT_COUNT - 1,
                identity={},
            )
        self.assertEqual(
            result["classification"],
            "TARGET_PREFLIGHT_MISMATCH_FAIL_CLOSED",
        )
        self.assertFalse(result["checks"]["current_sequence_exact_to_max_id"])


if __name__ == "__main__":
    import unittest
    unittest.main()
