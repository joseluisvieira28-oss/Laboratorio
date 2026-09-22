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
