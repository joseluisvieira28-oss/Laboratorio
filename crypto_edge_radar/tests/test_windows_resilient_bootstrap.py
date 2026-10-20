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

    def test_retired_eight_motor_bundle_serves_dashboard_without_collectors(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.getcwd()
            os.chdir(td)
            try:
                with (
                    patch.object(entry, "_resource_path", side_effect=self._resource),
                    patch.object(entry, "require_dh03_clock_preflight") as clock,
                    patch.object(entry, "_start_dh03_thread") as dh03,
                    patch.object(entry, "_start_forward_thread") as forward,
                    patch.object(entry, "_start_cirv_thread") as cirv,
                    patch.object(entry, "_start_render_sentinel_thread") as sentinel,
                    patch.object(entry, "main", return_value=0) as dashboard,
                ):
                    result = entry.run()
                self.assertEqual(result, 0)
                clock.assert_not_called()
                dh03.assert_not_called()
                forward.assert_not_called()
                cirv.assert_not_called()
                sentinel.assert_not_called()
                self.assertEqual(dashboard.call_args.args[0][0], "dashboard")
                status=json.loads(Path("data/radar_status.json").read_text(encoding="utf-8"))
                self.assertEqual(status["health"], "NO_ACTIVE_CANDIDATES")
                self.assertEqual(status["mode"], "ZERO_PALHA_OPERATIONAL_RETIREMENT")
                self.assertFalse(status["orders_created"])
                registry=json.loads(Path("data/deployment_registry_v1.json").read_text(encoding="utf-8"))
                self.assertEqual(registry["candidates"], [])
                self.assertEqual(registry["focus_strategy_ids"], [])
            finally:
                os.chdir(old)

    def test_registry_selftest_intentional_zero(self):
        payload, state = entry._verify_registry_file(self._registry_path())
        self.assertTrue(state["retirement_active"])
        self.assertEqual(state["candidate_count"], 0)
        self.assertEqual(state["focus_strategy_count"], 0)
        self.assertFalse(state["required_strategy_present"])
        self.assertEqual(payload["operator_retirement"]["live_trading_authority"], "NONE")

    def test_no_autoreturn_if_retirement_metadata_removed(self):
        baseline=json.loads(Path(self._registry_path()).read_text(encoding="utf-8"))
        # Any attempt to reintroduce legacy motors, even with old registry flags,
        # must fail before any worker is started by this retired executable.
        baseline.pop("operator_retirement")
        baseline["focus_strategy_ids"]=["OPTIONS-SPOTPERP-001-V2.1"]
        baseline["candidates"]=[{"strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
                                  "micro_live_allowed_now":True,"shadow_allowed":True}]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"registry.json"
            p.write_text(json.dumps(baseline),encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"ECONOMIC_HARDSTOP_NO_AUTORETURN"):
                entry._verify_registry_file(str(p))

    def test_no_registry_version_downgrade_in_retired_build(self):
        baseline=json.loads(Path(self._registry_path()).read_text(encoding="utf-8"))
        baseline["registry_version"]="3.7"
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"registry.json"
            p.write_text(json.dumps(baseline),encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"ECONOMIC_HARDSTOP_REGISTRY_VERSION_MISMATCH"):
                entry._verify_registry_file(str(p))

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


    def test_v0144_watchdog_autostart_and_upgrade_are_fail_closed(self):
        root = Path(__file__).resolve().parents[1] / "windows"
        watchdog = (root / "RUN_RADAR_24X7_V0144.ps1").read_text(encoding="utf-8")
        installer = (root / "INSTALL_RADAR_AUTOSTART_V0144.ps1").read_text(encoding="utf-8")
        upgrade = (root / "UPGRADE_RADAR_V0144.ps1").read_text(encoding="utf-8")
        self.assertIn("CryptoEdgeRadarV0144Watchdog", watchdog)
        self.assertIn('TaskName "CryptoEdgeRadarV0144"', installer)
        self.assertIn("v0.14.3.3-win-single-instance-lock", upgrade)
        self.assertIn("v0.14.4-win-cirv-eight-motor", upgrade)
        self.assertIn("registry.focus_loaded", upgrade)
        self.assertIn("cirv_status", upgrade)
        self.assertIn("Rolling back", upgrade)
        self.assertIn("Refusing automatic", upgrade)


if __name__ == "__main__":
    unittest.main()
