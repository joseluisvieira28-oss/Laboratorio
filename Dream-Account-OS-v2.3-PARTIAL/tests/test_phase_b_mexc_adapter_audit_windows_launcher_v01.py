from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "research" / "audit_phase_b_mexc_adapted_windows.bat"
LOCAL_DATA_GITIGNORE = ROOT / "research" / "local_data" / ".gitignore"


class PhaseBMEXCAdapterAuditWindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        self.text = LAUNCHER.read_text(encoding="utf-8").lower()

    def test_launcher_calls_only_adapter_bound_audit_module(self):
        self.assertIn("research.phase_b_mexc_adapter_audit_binding_v01", self.text)
        self.assertNotIn("phase_b_research_evaluator_v01", self.text)
        self.assertNotIn("derive_signal_geometries", self.text)
        self.assertNotIn("simulate_outcome", self.text)

    def test_launcher_contains_no_credentials_network_or_exchange_commands(self):
        for forbidden in (
            "mexc_readonly_access_key",
            "mexc_readonly_secret_key",
            "api.mexc.com",
            "curl ",
            "wget ",
            "invoke-webrequest",
            "invoke-restmethod",
        ):
            self.assertNotIn(forbidden, self.text)

    def test_launcher_requires_explicit_symbol_and_declared_range(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('set "SYMBOL=%~4"', text)
        self.assertIn('set "DECLARED_START=%~5"', text)
        self.assertIn('set "DECLARED_END=%~6"', text)
        self.assertIn('--symbol "%SYMBOL%"', text)
        self.assertIn('--declared-start "%DECLARED_START%"', text)
        self.assertIn('--declared-end "%DECLARED_END%"', text)

    def test_launcher_propagates_nonzero_exit_and_states_no_p00(self):
        self.assertIn('set "rc=%errorlevel%"', self.text)
        self.assertIn("exit /b %rc%", self.text)
        self.assertGreaterEqual(self.text.count("no p00 evaluation was run"), 2)

    def test_launcher_writes_only_gitignored_local_receipt(self):
        self.assertTrue(LOCAL_DATA_GITIGNORE.is_file())
        rules = LOCAL_DATA_GITIGNORE.read_text(encoding="utf-8").splitlines()
        self.assertIn("*", rules)
        self.assertIn("!.gitignore", rules)
        self.assertIn("local_data\\intake", self.text)
        self.assertIn("latest_adapter_bound_audit.json", self.text)


if __name__ == "__main__":
    unittest.main()
