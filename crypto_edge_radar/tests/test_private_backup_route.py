from __future__ import annotations

from pathlib import Path
from unittest import TestCase


class PrivateBackupCleanupTests(TestCase):
    def test_temporary_backup_surfaces_are_absent_from_runtime(self):
        source = (Path(__file__).resolve().parents[1] / "radar" / "forward_web.py").read_text()
        self.assertNotIn("/api/private/evidence-backup", source)
        self.assertNotIn("RADAR_BACKUP_EXPORT_TOKEN", source)
        self.assertNotIn("RADAR_BACKUP_EXPORT_ENABLED", source)
        self.assertNotIn("RADAR_BACKUP_LOG_EMIT_ON_START", source)
        self.assertNotIn("build_private_evidence_snapshot", source)
        self.assertNotIn("emit_snapshot_log_chunks", source)


if __name__ == "__main__":
    import unittest
    unittest.main()
