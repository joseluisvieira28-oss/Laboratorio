from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from radar.forward_web import _runtime_identity


class RuntimeIdentityTests(unittest.TestCase):
    def test_render_identity_uses_only_documented_nonsecret_fields(self):
        env={
            "RENDER":"true",
            "RENDER_GIT_COMMIT":"abc123",
            "RENDER_GIT_BRANCH":"crypto-edge-radar-postgres-v0.5",
            "RENDER_SERVICE_ID":"srv-test",
            "RENDER_SERVICE_NAME":"radar-test",
            "RENDER_INSTANCE_ID":"instance-test",
            "RADAR_DATABASE_URL":"postgresql://must-not-leak",
            "SOLSCAN_API_KEY":"must-not-leak",
        }
        with patch.dict(os.environ,env,clear=True):
            x=_runtime_identity()
        self.assertEqual(x["git_commit"],"abc123")
        self.assertTrue(x["render"])
        self.assertEqual(set(x),{
            "render","git_commit","git_branch","service_id","service_name","instance_id"
        })
        self.assertNotIn("postgresql://must-not-leak",repr(x))
        self.assertNotIn("must-not-leak",repr(x))


if __name__=="__main__":
    unittest.main()
