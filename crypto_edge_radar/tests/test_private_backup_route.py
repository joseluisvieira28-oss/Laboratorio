from __future__ import annotations

from pathlib import Path
from unittest import TestCase


class PrivateBackupTemporaryWindowTests(TestCase):
    def test_temporary_backup_surface_is_present_but_strictly_token_gated(self):
        source = (Path(__file__).resolve().parents[1] / "radar" / "forward_web.py").read_text()
        self.assertIn("/api/private/evidence-backup", source)
        self.assertIn("RADAR_BACKUP_EXPORT_TOKEN", source)
        self.assertIn("RADAR_BACKUP_EXPORT_ENABLED", source)
        self.assertIn("provided != expected", source)
        self.assertIn('{"error": "not_found"}', source)
        self.assertIn("build_private_evidence_snapshot", source)
        self.assertNotIn("RADAR_DATABASE_URL", source)


if __name__ == "__main__":
    import unittest
    unittest.main()
