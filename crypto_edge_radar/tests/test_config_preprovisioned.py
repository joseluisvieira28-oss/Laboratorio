from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from radar.config import Settings


class PreprovisionedPostgresConfigTests(unittest.TestCase):
    def test_preprovisioned_flag_is_explicit_opt_in(self):
        with patch.dict(
            os.environ,
            {
                "RADAR_DATABASE_URL": "postgresql://example/test",
                "RADAR_POSTGRES_SCHEMA_PREPROVISIONED": "true",
            },
            clear=True,
        ):
            settings = Settings.from_env()
        self.assertEqual(settings.database_url, "postgresql://example/test")
        self.assertTrue(settings.database_schema_preprovisioned)

    def test_preprovisioned_flag_defaults_false(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()
        self.assertFalse(settings.database_schema_preprovisioned)

    def test_supabase_target_override_is_explicit_and_forces_preprovisioned(self):
        with patch.dict(
            os.environ,
            {
                "RADAR_DATABASE_URL": "postgresql://source.example/source",
                "RADAR_USE_SUPABASE_TARGET": "true",
                "RADAR_SUPABASE_POOLER_HOST": "aws-1-eu-central-1.pooler.supabase.com",
                "RADAR_SUPABASE_POOLER_PASSWORD": "synthetic p@ss:/?#",
            },
            clear=True,
        ):
            settings = Settings.from_env()

        self.assertEqual(settings.database_target_mode, "SUPABASE_POOLER")
        self.assertTrue(settings.database_schema_preprovisioned)
        self.assertIn(
            "@aws-1-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require",
            settings.database_url,
        )
        self.assertIn("radar_runtime.jqzdvgjeuveiktftyrlz", settings.database_url)
        self.assertNotIn("synthetic p@ss:/?#", settings.database_url)
        self.assertNotIn("source.example", settings.database_url)

    def test_supabase_target_missing_secret_fails_closed(self):
        with patch.dict(
            os.environ,
            {
                "RADAR_USE_SUPABASE_TARGET": "true",
                "RADAR_SUPABASE_POOLER_HOST": "aws-1-eu-central-1.pooler.supabase.com",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "RADAR_SUPABASE_POOLER_PASSWORD is required",
            ):
                Settings.from_env()

    def test_supabase_target_rejects_unverified_host_shape(self):
        with patch.dict(
            os.environ,
            {
                "RADAR_USE_SUPABASE_TARGET": "true",
                "RADAR_SUPABASE_POOLER_HOST": "db.jqzdvgjeuveiktftyrlz.supabase.co",
                "RADAR_SUPABASE_POOLER_PASSWORD": "synthetic",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "must be an audited eu-central-1 Supavisor host",
            ):
                Settings.from_env()

    def test_settings_repr_never_exposes_database_url(self):
        secret_url = "postgresql://user:super-secret@example/db"
        settings = Settings(database_url=secret_url)
        rendered = repr(settings)
        self.assertNotIn("super-secret", rendered)
        self.assertNotIn(secret_url, rendered)
        self.assertNotIn("database_url=", rendered)

    def test_invalid_boolean_fails_closed(self):
        with patch.dict(
            os.environ,
            {"RADAR_POSTGRES_SCHEMA_PREPROVISIONED": "maybe"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "must be a boolean"):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
