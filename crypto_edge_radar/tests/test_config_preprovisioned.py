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
