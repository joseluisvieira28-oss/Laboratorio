from __future__ import annotations

import os
from unittest import TestCase
from unittest.mock import patch

from radar.deploy_drift import deployment_drift_receipt


class DeployDriftTests(TestCase):
    def test_not_render_runtime_is_explicit(self):
        with patch.dict(os.environ, {}, clear=True):
            r = deployment_drift_receipt(timeout=1)
        self.assertEqual(r["classification"], "NOT_RENDER_RUNTIME")
        self.assertIsNone(r["in_sync"])
        self.assertFalse(r["automatic_deploy_performed"])

    def test_in_sync(self):
        sha = "a" * 40
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": sha}, clear=True), patch(
            "radar.deploy_drift._fetch_json",
            return_value={"commit": {"sha": sha}},
        ):
            r = deployment_drift_receipt(timeout=1)
        self.assertEqual(r["classification"], "IN_SYNC")
        self.assertTrue(r["in_sync"])

    def test_stale_runtime(self):
        deployed = "a" * 40
        head = "b" * 40
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": deployed}, clear=True), patch(
            "radar.deploy_drift._fetch_json",
            return_value={"commit": {"sha": head}},
        ):
            r = deployment_drift_receipt(timeout=1)
        self.assertEqual(r["classification"], "STALE_RUNTIME")
        self.assertFalse(r["in_sync"])
        self.assertEqual(r["canonical_head_commit"], head)

    def test_api_failure_uses_atom_fallback(self):
        sha = "b" * 40
        atom = f'<entry><link href="https://github.com/x/y/commit/{sha}"/></entry>'
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": sha}, clear=True), patch(
            "radar.deploy_drift._fetch_json",
            side_effect=RuntimeError("rate limited"),
        ), patch(
            "radar.deploy_drift._fetch_text",
            return_value=atom,
        ):
            r = deployment_drift_receipt(timeout=1)
        self.assertEqual(r["classification"], "IN_SYNC")
        self.assertTrue(r["in_sync"])
        self.assertEqual(r["source"], "GITHUB_ATOM_FALLBACK")
        self.assertIn("rate limited", r["primary_error"])

    def test_both_sources_failure_is_fail_closed(self):
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": "a" * 40}, clear=True), patch(
            "radar.deploy_drift._fetch_json",
            side_effect=RuntimeError("boom"),
        ), patch(
            "radar.deploy_drift._fetch_text",
            side_effect=RuntimeError("atom boom"),
        ):
            r = deployment_drift_receipt(timeout=1)
        self.assertEqual(r["classification"], "UNAVAILABLE_FAIL_CLOSED")
        self.assertIsNone(r["in_sync"])
        self.assertIsNone(r["source"])
        self.assertIn("boom", r["primary_error"])
        self.assertIn("atom boom", r["fallback_error"])


if __name__ == "__main__":
    import unittest
    unittest.main()
