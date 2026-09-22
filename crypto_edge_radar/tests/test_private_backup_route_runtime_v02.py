from pathlib import Path
from unittest import TestCase

class PrivateBackupRouteRuntimeV02Tests(TestCase):
    def test_current_head_contains_only_token_gated_get_route(self):
        source=(Path(__file__).resolve().parents[1]/"radar"/"forward_web.py").read_text()
        self.assertIn('/api/private/evidence-backup', source)
        self.assertIn('RADAR_BACKUP_EXPORT_ENABLED', source)
        self.assertIn('RADAR_BACKUP_EXPORT_TOKEN', source)
        self.assertIn('provided != expected', source)
        self.assertIn('build_private_evidence_snapshot', source)
        self.assertNotIn('RADAR_DATABASE_URL', source)
