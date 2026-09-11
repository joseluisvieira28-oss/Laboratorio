from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "research" / "adapt_phase_b_mexc_source_windows.bat"
GITIGNORE = ROOT / "research" / ".gitignore"


class PhaseBMEXCBulkCsvAdapterWindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        self.text = LAUNCHER.read_text(encoding="utf-8").lower()

    def test_launcher_calls_only_frozen_adapter_module_and_not_p00(self):
        self.assertIn("research.phase_b_mexc_bulk_csv_adapter_v01", self.text)
        self.assertNotIn("phase_b_research_evaluator_v01", self.text)
        self.assertNotIn("derive_signal_geometries", self.text)
        self.assertNotIn("simulate_outcome", self.text)

    def test_launcher_contains_no_credentials_or_network_commands(self):
        for forbidden in (
            "mexc_readonly_access_key",
            "mexc_readonly_secret_key",
            "api.mexc.com",
            "invoke-webrequest",
            "curl ",
            "wget ",
            "powershell -command",
        ):
            self.assertNotIn(forbidden, self.text)

    def test_launcher_persists_only_local_intake_outputs(self):
        self.assertIn("local_data\\intake", self.text)
        self.assertIn("latest_adapter_receipt.json", self.text)
        self.assertIn("canonical", self.text)
        self.assertIn("latest_adapter_console.json", self.text)

    def test_launcher_propagates_nonzero_exit_and_states_no_p00(self):
        self.assertIn("set \"rc=%errorlevel%\"", self.text)
        self.assertIn("exit /b %rc%", self.text)
        self.assertIn("no p00 evaluation was run", self.text)

    def test_local_intake_directory_is_git_ignored(self):
        ignore = GITIGNORE.read_text(encoding="utf-8").lower()
        self.assertIn("local_data/", ignore)


if __name__ == "__main__":
    unittest.main()
