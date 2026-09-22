from __future__ import annotations

from unittest import TestCase
from pathlib import Path


class PrivateBackupRouteStaticTests(TestCase):
    def test_route_is_token_gated_and_no_secret_value_is_returned(self):
        source = (Path(__file__).resolve().parents[1] / "radar" / "forward_web.py").read_text()
        self.assertIn("/api/private/evidence-backup", source)
        self.assertIn("RADAR_BACKUP_EXPORT_ENABLED", source)
        self.assertIn("RADAR_BACKUP_EXPORT_TOKEN", source)
        self.assertIn('provided != expected', source)
        self.assertIn('{"error": "not_found"}', source)


if __name__ == "__main__":
    import unittest
    unittest.main()
