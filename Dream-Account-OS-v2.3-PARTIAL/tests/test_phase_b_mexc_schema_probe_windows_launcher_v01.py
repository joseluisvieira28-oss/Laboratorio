from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "research" / "probe_phase_b_mexc_source_windows.bat"


class PhaseBMEXCSchemaProbeWindowsLauncherTests(unittest.TestCase):
    def test_launcher_calls_only_structure_probe_module(self):
        text = LAUNCHER.read_text(encoding="utf-8").lower()
        self.assertIn("phase_b_mexc_schema_probe_v01", text)
        self.assertNotIn("phase_b_research_evaluator_v01", text)
        self.assertNotIn("derive_signal_geometries", text)
        self.assertNotIn("simulate_outcome", text)

    def test_launcher_contains_no_credentials_or_api_network_commands(self):
        text = LAUNCHER.read_text(encoding="utf-8").lower()
        for forbidden in (
            "mexc_readonly_access_key",
            "mexc_readonly_secret_key",
            "api.mexc.com",
            "curl ",
            "invoke-webrequest",
            "invoke-restmethod",
            "requests",
        ):
            self.assertNotIn(forbidden, text)

    def test_launcher_quotes_source_path_and_propagates_nonzero_exit(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('"%SOURCE_FILE%"', text)
        self.assertIn('set "RC=%ERRORLEVEL%"', text)
        self.assertIn('exit /b %RC%', text)

    def test_launcher_supports_drag_drop_and_handles_spaces_via_full_path(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('set "SOURCE_FILE=%~f1"', text)
        self.assertIn('%~1', text)
        self.assertIn('pushd "%PROJECT_ROOT%"', text)

    def test_launcher_explicitly_states_no_p00_on_block_and_success(self):
        text = LAUNCHER.read_text(encoding="utf-8").lower()
        self.assertGreaterEqual(text.count("no p00"), 1)
        self.assertIn("no market values", text)


if __name__ == "__main__":
    unittest.main()
