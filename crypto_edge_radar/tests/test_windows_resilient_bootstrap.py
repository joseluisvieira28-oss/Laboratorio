import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import windows_node_entry as entry


class WindowsResilientBootstrapTests(unittest.TestCase):
    @staticmethod
    def _registry_path() -> str:
        return str((Path(__file__).resolve().parents[1] / "deployment_registry_v1.json").resolve())

    @staticmethod
    def _authority_path() -> str:
        return str((Path(__file__).resolve().parents[1] / "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json").resolve())

    @classmethod
    def _resource(cls, name: str) -> str:
        if name == "deployment_registry_v1.json":
            return cls._registry_path()
        if name == "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json":
            return cls._authority_path()
        raise AssertionError(f"unexpected packaged resource requested in test: {name}")

    def test_dh03_clock_failure_blocks_only_dh03_and_still_serves_dashboard(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.getcwd()
            os.chdir(td)
            try:
                with (
                    patch.object(entry, "_resource_path", side_effect=self._resource),
                    patch.object(entry, "require_dh03_clock_preflight", side_effect=RuntimeError("synthetic clock fail")),
                    patch.object(entry, "_start_dh03_thread") as start_dh03,
                    patch.object(entry, "_start_forward_thread") as start_forward,
                    patch.object(entry, "_start_cirv_thread") as start_cirv,
                    patch.object(entry, "_start_render_sentinel_thread") as start_sentinel,
                    patch.object(entry, "main", return_value=0) as main,
                ):
                    rc = entry.run()
                self.assertEqual(rc, 0)
                start_dh03.assert_not_called()
                start_forward.assert_called_once()
                start_cirv.assert_called_once()
                start_sentinel.assert_called_once()
                args = main.call_args.args[0]
                self.assertEqual(args[0], "dashboard")
                self.assertNotIn("local-node", args)
                dh = json.loads(Path("data/dh03_local_status.json").read_text(encoding="utf-8"))
                self.assertEqual(dh["status"], "FAIL_CLOSED")
                self.assertEqual(dh["reason"], "DH03_NOT_STARTED_CLOCK_PREFLIGHT_FAILED")
                status = json.loads(Path("data/radar_status.json").read_text(encoding="utf-8"))
                self.assertEqual(status["health"], "OK")
                self.assertFalse(status["orders_created"])
            finally:
                os.chdir(old)

    def test_dh03_clock_pass_starts_collector_and_dashboard(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.getcwd()
            os.chdir(td)
            try:
                with (
                    patch.object(entry, "_resource_path", side_effect=self._resource),
                    patch.object(entry, "require_dh03_clock_preflight", return_value={"pass": True}),
                    patch.object(entry, "_start_dh03_thread") as start_dh03,
                    patch.object(entry, "_start_forward_thread") as start_forward,
                    patch.object(entry, "_start_cirv_thread") as start_cirv,
                    patch.object(entry, "_start_render_sentinel_thread") as start_sentinel,
                    patch.object(entry, "main", return_value=0) as main,
                ):
                    rc = entry.run()
                self.assertEqual(rc, 0)
                start_dh03.assert_called_once()
                start_forward.assert_called_once()
                start_cirv.assert_called_once()
                start_sentinel.assert_called_once()
                self.assertEqual(main.call_args.args[0][0], "dashboard")
                clock = json.loads(Path("data/dh03_clock_preflight.json").read_text(encoding="utf-8"))
                self.assertTrue(clock["pass"])
            finally:
                os.chdir(old)

    def test_duplicate_node_is_rejected_before_any_collector_or_dashboard(self):
        with (
            patch.object(entry, "_acquire_single_instance_lock", return_value=(False, "DUPLICATE_LOCAL_NODE")),
            patch.object(entry, "_resource_path") as resource_path,
            patch.object(entry, "require_dh03_clock_preflight") as clock_preflight,
            patch.object(entry, "_start_dh03_thread") as start_dh03,
            patch.object(entry, "_start_forward_thread") as start_forward,
            patch.object(entry, "_start_cirv_thread") as start_cirv,
            patch.object(entry, "_start_render_sentinel_thread") as start_sentinel,
            patch.object(entry, "main") as main,
        ):
            rc = entry.run()

        self.assertEqual(rc, 3)
        resource_path.assert_not_called()
        clock_preflight.assert_not_called()
        start_dh03.assert_not_called()
        start_forward.assert_not_called()
        start_cirv.assert_not_called()
        start_sentinel.assert_not_called()
        main.assert_not_called()

    def test_single_instance_lock_is_released_after_dashboard_returns(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.getcwd()
            os.chdir(td)
            try:
                with (
                    patch.object(entry, "_resource_path", side_effect=self._resource),
                    patch.object(entry, "_acquire_single_instance_lock", return_value=(True, "LOCK_ACQUIRED")),
                    patch.object(entry, "_release_single_instance_lock") as release_lock,
                    patch.object(entry, "require_dh03_clock_preflight", return_value={"pass": True}),
                    patch.object(entry, "_start_dh03_thread"),
                    patch.object(entry, "_start_forward_thread"),
                    patch.object(entry, "_start_cirv_thread"),
                    patch.object(entry, "_start_render_sentinel_thread"),
                    patch.object(entry, "main", return_value=0),
                ):
                    rc = entry.run()
                self.assertEqual(rc, 0)
                release_lock.assert_called_once()
            finally:
                os.chdir(old)

    def test_launcher_has_duplicate_and_unrelated_process_guards(self):
        script = (Path(__file__).resolve().parents[1] / "windows" / "START_RADAR_RECOVERY_V0141.ps1").read_text(encoding="utf-8")
        self.assertIn("CryptoEdgeRadarV0144Launcher", script)
        self.assertIn("approvedPaths -notcontains $ownerPath", script)
        self.assertNotIn('Get-Process -Name "CryptoEdgeRadarNode"', script)

    def test_watchdog_and_autostart_are_singleton_and_restart_capable(self):
        root = Path(__file__).resolve().parents[1] / "windows"
        watchdog = (root / "RUN_RADAR_24X7_V0143.ps1").read_text(encoding="utf-8")
        installer = (root / "INSTALL_RADAR_AUTOSTART_V0143.ps1").read_text(encoding="utf-8")
        self.assertIn("CryptoEdgeRadarV0143Watchdog", watchdog)
        self.assertIn("Start-Sleep -Seconds 15", watchdog)
        self.assertIn("Register-ScheduledTask", installer)
        self.assertIn("-AtLogOn", installer)

    def test_launcher_supports_stable_onedir_and_exact_v0144_identity(self):
        script = (Path(__file__).resolve().parents[1] / "windows" / "START_RADAR_RECOVERY_V0141.ps1").read_text(encoding="utf-8")
        self.assertIn("CryptoEdgeRadarNode\\CryptoEdgeRadarNode.exe", script)
        self.assertIn("v0.14.4-win-cirv-eight-motor", script)


if __name__ == "__main__":
    unittest.main()
