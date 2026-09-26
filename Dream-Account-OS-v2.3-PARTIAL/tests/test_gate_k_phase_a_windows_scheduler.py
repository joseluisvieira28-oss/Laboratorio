import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GateKWindowsSchedulerTests(unittest.TestCase):
    def read(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def test_secure_task_reuses_existing_controlled_batch(self):
        text = self.read("gate_k_phase_a_secure_task.ps1")
        self.assertIn("run_gate_k_phase_a_campaign_windows.bat", text)
        self.assertIn("No retry attempted", text)
        self.assertNotIn("/api/v3/order", text)
        self.assertNotIn("POST", text)
        self.assertNotIn("PUT", text)
        self.assertNotIn("PATCH", text)
        self.assertNotIn("DELETE", text)

    def test_secure_task_loads_dpapi_ciphertext_and_cleans_plaintext_env(self):
        text = self.read("gate_k_phase_a_secure_task.ps1")
        self.assertIn("ConvertTo-SecureString", text)
        self.assertIn("mexc_readonly_access.dpapi", text)
        self.assertIn("mexc_readonly_secret.dpapi", text)
        self.assertIn("Remove-Item Env:MEXC_READONLY_ACCESS_KEY", text)
        self.assertIn("Remove-Item Env:MEXC_READONLY_SECRET_KEY", text)

    def test_secure_task_builds_quoted_cmd_commands_without_backslash_escapes(self):
        text = self.read("gate_k_phase_a_secure_task.ps1")
        self.assertIn("$batchCommand", text)
        self.assertIn("$summaryCommand", text)
        self.assertNotIn('\\"{0}\\"', text)

    def test_installer_never_embeds_credentials(self):
        text = self.read("install_gate_k_phase_a_scheduler.ps1")
        self.assertIn("ConvertFrom-SecureString", text)
        self.assertIn("MEXC_READONLY_ACCESS_KEY", text)
        self.assertIn("MEXC_READONLY_SECRET_KEY", text)
        self.assertNotIn("sk-", text)
        self.assertNotIn("apiKey=", text)

    def test_installer_creates_three_daily_windows(self):
        text = self.read("install_gate_k_phase_a_scheduler.ps1")
        self.assertIn("MORNING", text)
        self.assertIn("MIDDAY", text)
        self.assertIn("EVENING", text)
        self.assertIn("New-ScheduledTaskTrigger -Daily", text)
        self.assertIn("MultipleInstances IgnoreNew", text)
        self.assertIn("WakeToRun", text)

    def test_installer_quotes_runner_path_and_hardens_acl_subject(self):
        text = self.read("install_gate_k_phase_a_scheduler.ps1")
        self.assertIn("-File \"{0}\"", text)
        self.assertIn("${env:USERNAME}:(OI)(CI)F", text)
        self.assertNotIn('$env:USERNAME:(OI)(CI)F', text)

    def test_default_schedule_is_diverse_and_controlled(self):
        text = self.read("install_gate_k_phase_a_scheduler.ps1")
        self.assertIn("'07:30'", text)
        self.assertIn("'13:00'", text)
        self.assertIn("'19:30'", text)
        self.assertIn("[int]$Cycles = 5", text)
        self.assertIn("[int]$IntervalSeconds = 900", text)

    def test_uninstaller_preserves_evidence_by_default(self):
        text = self.read("uninstall_gate_k_phase_a_scheduler.ps1")
        self.assertIn("Unregister-ScheduledTask", text)
        self.assertIn("Existing SQLite evidence and logs were not deleted", text)
        self.assertIn("[switch]$RemoveCredentials", text)

    def test_status_tool_uses_quoted_summary_command(self):
        text = self.read("show_gate_k_phase_a_scheduler_status.ps1")
        self.assertIn("$summaryCommand", text)
        self.assertNotIn('\\"{0}\\"', text)

    def test_one_command_wrappers_are_present(self):
        for name in (
            "install_gate_k_phase_a_scheduler_windows.bat",
            "uninstall_gate_k_phase_a_scheduler_windows.bat",
            "show_gate_k_phase_a_scheduler_status_windows.bat",
        ):
            self.assertTrue((ROOT / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
