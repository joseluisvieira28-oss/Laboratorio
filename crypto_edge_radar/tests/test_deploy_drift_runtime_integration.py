from __future__ import annotations

from pathlib import Path
from unittest import TestCase


class DeployDriftRuntimeIntegrationTests(TestCase):
    def test_forward_runtime_surfaces_hourly_deploy_drift_without_auto_deploy(self):
        source = (
            Path(__file__).resolve().parents[1] / "radar" / "forward_web.py"
        ).read_text()
        self.assertIn("deployment_drift_receipt", source)
        self.assertIn("_last_deploy_drift_check_ms", source)
        self.assertIn("60 * 60 * 1000", source)
        self.assertIn('"deployment_drift": deploy_drift', source)
        self.assertIn('"operational_attention_required"', source)
        self.assertNotIn("trigger_deploy", source)
        self.assertNotIn("deploy_hook", source)


if __name__ == "__main__":
    import unittest
    unittest.main()
