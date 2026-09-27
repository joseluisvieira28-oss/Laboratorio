from __future__ import annotations

import json
import unittest

from radar.persistence_hardening import (
    CANONICAL_RENDER_SERVICE_ID,
    historical_preflight_view,
    persistence_watchdog_state,
    post_cutover_persistence_state,
)


def verified_identity(*, max_id: int = 1121):
    return {
        "status": "VERIFIED",
        "backend": "postgres",
        "event_count": max_id,
        "key_count": max_id - 78,
        "max_event_id": max_id,
        "chain_head_sha256": "a" * 64,
        "key_binding_sha256": "b" * 64,
        "sequence_last_value": max_id,
        "sequence_is_called": True,
        "chain_verified": True,
    }


class PersistenceHardeningTests(unittest.TestCase):
    def test_canonical_supabase_route_passes_without_exposing_secret(self):
        env = {
            "RENDER": "true",
            "RENDER_SERVICE_ID": CANONICAL_RENDER_SERVICE_ID,
            "RENDER_SERVICE_NAME": "crypto-edge-radar-v05-canary",
            "RADAR_USE_SUPABASE_TARGET": "true",
            "RADAR_SUPABASE_POOLER_HOST": "aws-0-eu-central-1.pooler.supabase.com",
            "RADAR_SUPABASE_POOLER_PASSWORD": "synthetic-super-secret",
            "RADAR_DATABASE_URL": "postgresql://historical/source",
        }
        state = persistence_watchdog_state(
            database_target_mode="SUPABASE_POOLER",
            evidence_backend="postgres",
            evidence_chain_ok=True,
            evidence_identity=verified_identity(),
            environ=env,
        )
        self.assertTrue(state["pass"])
        self.assertTrue(state["writes_allowed"])
        self.assertEqual(
            state["classification"],
            "PASS_CANONICAL_SUPABASE_SINGLE_WRITER",
        )
        self.assertTrue(state["cutover_complete"])
        self.assertTrue(state["configuration"]["credential_configured"])
        self.assertNotIn("synthetic-super-secret", json.dumps(state))

    def test_canonical_service_cannot_silently_fall_back_to_source(self):
        env = {
            "RENDER": "true",
            "RENDER_SERVICE_ID": CANONICAL_RENDER_SERVICE_ID,
            "RENDER_SERVICE_NAME": "crypto-edge-radar-v05-canary",
            "RADAR_USE_SUPABASE_TARGET": "false",
            "RADAR_DATABASE_URL": "postgresql://historical/source",
        }
        state = persistence_watchdog_state(
            database_target_mode="SOURCE",
            evidence_backend="postgres",
            evidence_chain_ok=True,
            evidence_identity=verified_identity(),
            environ=env,
        )
        self.assertFalse(state["pass"])
        self.assertFalse(state["writes_allowed"])
        self.assertIn("target_flag_enabled", state["failures"])
        self.assertIn(
            "database_target_mode_is_supabase_pooler",
            state["failures"],
        )

    def test_noncanonical_render_radar_is_rejected_as_writer(self):
        env = {
            "RENDER": "true",
            "RENDER_SERVICE_ID": "srv-old-radar",
            "RENDER_SERVICE_NAME": "crypto-edge-radar-v09-forward-preflight",
            "RADAR_USE_SUPABASE_TARGET": "true",
            "RADAR_SUPABASE_POOLER_HOST": "aws-0-eu-central-1.pooler.supabase.com",
            "RADAR_SUPABASE_POOLER_PASSWORD": "synthetic",
        }
        state = persistence_watchdog_state(
            database_target_mode="SUPABASE_POOLER",
            evidence_backend="postgres",
            evidence_chain_ok=True,
            evidence_identity=verified_identity(),
            environ=env,
        )
        self.assertFalse(state["pass"])
        self.assertIn("canonical_writer_service", state["failures"])

    def test_sequence_mismatch_fails_closed(self):
        identity = verified_identity()
        identity["sequence_last_value"] = 1120
        state = persistence_watchdog_state(
            database_target_mode="SUPABASE_POOLER",
            evidence_backend="postgres",
            evidence_chain_ok=True,
            evidence_identity=identity,
            environ={
                "RADAR_USE_SUPABASE_TARGET": "true",
                "RADAR_SUPABASE_POOLER_HOST": "aws-0-eu-central-1.pooler.supabase.com",
                "RADAR_SUPABASE_POOLER_PASSWORD": "synthetic",
                "RADAR_ENFORCE_CANONICAL_PERSISTENCE": "true",
            },
        )
        self.assertFalse(state["pass"])
        self.assertIn("sequence_exact_to_max_event_id", state["failures"])

    def test_local_source_context_is_not_forced_into_cutover(self):
        state = persistence_watchdog_state(
            database_target_mode="SOURCE",
            evidence_backend="sqlite",
            evidence_chain_ok=True,
            evidence_identity={"status": "VERIFIED", "backend": "sqlite"},
            environ={},
        )
        self.assertTrue(state["pass"])
        self.assertFalse(state["enforcement_required"])
        self.assertEqual(
            state["classification"],
            "NON_RENDER_LOCAL_CONTEXT_NOT_ENFORCED",
        )

    def test_post_cutover_overlay_replaces_stale_migration_story(self):
        watchdog = persistence_watchdog_state(
            database_target_mode="SUPABASE_POOLER",
            evidence_backend="postgres",
            evidence_chain_ok=True,
            evidence_identity=verified_identity(),
            environ={
                "RADAR_USE_SUPABASE_TARGET": "true",
                "RADAR_SUPABASE_POOLER_HOST": "aws-0-eu-central-1.pooler.supabase.com",
                "RADAR_SUPABASE_POOLER_PASSWORD": "synthetic",
                "RADAR_ENFORCE_CANONICAL_PERSISTENCE": "true",
            },
        )
        state = post_cutover_persistence_state(
            {
                "classification": "OK",
                "expiry_utc": "2026-10-17T08:47:15Z",
                "migration_required": False,
                "target_url_configured": False,
                "target_pooler_host_discovered": False,
                "target_connection_credential_configured": False,
                "cutover_blocker": "FINAL_QUIESCED_REFRESH_REQUIRED",
                "final_quiesced_refresh_required": True,
                "final_cutover_authorized": False,
            },
            watchdog=watchdog,
        )
        self.assertEqual(
            state["classification"],
            "CUTOVER_COMPLETE_CANONICAL_SUPABASE",
        )
        self.assertIsNone(state["cutover_blocker"])
        self.assertFalse(state["final_quiesced_refresh_required"])
        self.assertTrue(state["target_url_configured"])
        self.assertTrue(state["target_pooler_host_discovered"])
        self.assertTrue(state["target_connection_credential_configured"])
        self.assertEqual(
            state["historical_source_role"],
            "NON_CANONICAL_ROLLBACK_ONLY",
        )
        self.assertTrue(state["rollback_requires_reconciliation"])
        self.assertFalse(state["rollback_blind_url_flip_allowed"])

    def test_historical_preflight_is_explicitly_non_authoritative_after_cutover(self):
        state = historical_preflight_view(
            {"classification": "TARGET_PREFLIGHT_PASS_BACKUP_PREFIX_CURRENT_CHAIN_OK"},
            cutover_complete=True,
        )
        self.assertEqual(
            state["operational_relevance"],
            "HISTORICAL_PRE_CUTOVER_RECEIPT_ONLY",
        )
        self.assertTrue(state["cutover_complete"])


if __name__ == "__main__":
    unittest.main()
