from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase

from radar.persistence_expiry import persistence_expiry_state


class PersistenceExpiryTests(TestCase):
    def test_thresholds(self):
        expiry="2026-10-17T08:47:15.255900Z"

        ok=persistence_expiry_state(
            expiry, now=datetime(2026,9,22,8,47,15,tzinfo=timezone.utc)
        )
        self.assertEqual(ok["classification"],"OK")
        self.assertFalse(ok["migration_required"])
        self.assertTrue(ok["verified_backup_exists"])
        self.assertEqual(
            ok["backup_receipt"],
            "RADAR_EVIDENCE_BACKUP_CLOSEOUT_2026-09-27.json",
        )
        self.assertEqual(ok["backup_event_count"], 1032)
        self.assertEqual(ok["backup_key_count"], 954)
        self.assertEqual(
            ok["backup_canonical_snapshot_sha256"],
            "6c74bdcf1013b1ab49fdcefd2e046db6471ea2816c6b425f4a6378dda22de9cb",
        )
        self.assertEqual(
            ok["backup_drive_file_id"],
            "1oam9hmileBQbV80C6o0cQUicXfu-vzvZ",
        )
        self.assertEqual(ok["target_provider"], "SUPABASE")
        self.assertEqual(ok["target_project_ref"], "jqzdvgjeuveiktftyrlz")
        self.assertTrue(ok["target_provisioned"])
        self.assertTrue(ok["target_equivalence_verified_at_backup_boundary"])
        self.assertEqual(ok["target_event_count_at_backup_boundary"], 1032)
        self.assertEqual(ok["target_key_count_at_backup_boundary"], 954)
        self.assertFalse(ok["target_url_configured"])
        self.assertEqual(
            ok["cutover_blocker"],
            "TARGET_CONNECTION_CREDENTIAL_NOT_CONFIGURED",
        )
        self.assertTrue(ok["final_quiesced_refresh_required"])

        warn=persistence_expiry_state(
            expiry, now=datetime(2026,10,5,8,47,15,tzinfo=timezone.utc)
        )
        self.assertEqual(warn["classification"],"WARN")
        self.assertTrue(warn["migration_required"])

        critical=persistence_expiry_state(
            expiry, now=datetime(2026,10,12,8,47,15,tzinfo=timezone.utc)
        )
        self.assertEqual(critical["classification"],"CRITICAL")

        expired=persistence_expiry_state(
            expiry, now=datetime(2026,10,18,8,47,15,tzinfo=timezone.utc)
        )
        self.assertEqual(expired["classification"],"EXPIRED")

    def test_missing_config_is_unknown_not_false_alarm(self):
        r=persistence_expiry_state(None)
        self.assertEqual(r["classification"],"UNKNOWN")
        self.assertFalse(r["migration_required"])


if __name__=="__main__":
    import unittest
    unittest.main()
