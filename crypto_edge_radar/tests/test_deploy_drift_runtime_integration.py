from __future__ import annotations

from pathlib import Path
from unittest import TestCase


class DeployDriftRuntimeIntegrationTests(TestCase):
    def test_forward_runtime_surfaces_hourly_deploy_drift_without_auto_deploy(self):
        source = (
            Path(__file__).resolve().parents[1] / "radar" / "forward_web.py"
        ).read_text()
        # Deployment drift may be sourced either by the legacy direct runtime
        # helper or by the hardened public Atom fallback. Both must remain
        # visibility-only and must never auto-deploy.
        has_legacy = (
            "deployment_drift_receipt" in source
            and "_last_deploy_drift_check_ms" in source
            and "60 * 60 * 1000" in source
            and '"deployment_drift": deploy_drift' in source
        )
        has_hardened_fallback = (
            "all_external_freshness" in source
            and '"external_collectors"' in source
            and '"operational_attention_required"' in source
        )
        self.assertTrue(has_legacy or has_hardened_fallback)
        self.assertIn('"operational_attention_required"', source)
        self.assertNotIn("trigger_deploy", source)
        self.assertNotIn("deploy_hook", source)


if __name__ == "__main__":
    import unittest
    unittest.main()
