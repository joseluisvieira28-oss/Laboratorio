from __future__ import annotations

import unittest
from pathlib import Path


class GateKWindowsLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher = (
            Path(__file__).resolve().parents[1]
            / "run_gate_k_phase_a_cycle_windows.bat"
        ).read_text(encoding="utf-8")

    def test_src_layout_is_added_to_pythonpath(self):
        self.assertIn('set "PYTHONPATH=%CD%\\src', self.launcher)

    def test_delayed_expansion_is_enabled_for_runtime_exit_codes(self):
        self.assertIn("EnableDelayedExpansion", self.launcher)
        self.assertIn('set "RC=!ERRORLEVEL!"', self.launcher)
        self.assertIn('if "!RC!"=="0"', self.launcher)
        self.assertIn("exit /b !RC!", self.launcher)

    def test_launcher_remains_one_shot_shadow_read_only(self):
        self.assertIn("execution_phase_a_campaign_runner", self.launcher)
        self.assertIn("SHADOW / READ-ONLY only", self.launcher)
        self.assertNotIn("/api/v3/order", self.launcher)
        self.assertNotIn("POST ", self.launcher)
        self.assertNotIn("PUT ", self.launcher)
        self.assertNotIn("PATCH ", self.launcher)
        self.assertNotIn("DELETE ", self.launcher)

    def test_launcher_does_not_embed_credentials(self):
        self.assertIn("MEXC_READONLY_ACCESS_KEY", self.launcher)
        self.assertIn("MEXC_READONLY_SECRET_KEY", self.launcher)
        self.assertNotIn("sk-", self.launcher)


if __name__ == "__main__":
    unittest.main()
