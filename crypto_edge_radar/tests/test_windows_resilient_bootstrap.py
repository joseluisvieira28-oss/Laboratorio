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

    def test_dh03_clock_failure_blocks_only_dh03_and_still_serves_dashboard(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.getcwd()
            os.chdir(td)
            try:
                with (
                    patch.object(entry, "_resource_path", return_value=self._registry_path()),
                    patch.object(entry, "dh03_clock_preflight", return_value={"pass": False, "blockers": ["CLOCK_OFFSET_OUTSIDE_DH03_BUDGET"], "server_minus_local_midpoint_ms": 1234.5, "request_rtt_ms": 42.0, "max_abs_offset_ms": 500.0, "max_rtt_ms": 1000.0, "authenticated_exchange_api_used": False, "orders_created": False, "exchange_mutation_performed": False, "live_capital_enabled": False}),
                    patch.object(entry, "_start_dh03_thread") as start_dh03,
                    patch.object(entry, "_start_forward_thread") as start_forward,
                    patch.object(entry, "_start_render_sentinel_thread") as start_sentinel,
                    patch.object(entry, "main", return_value=0) as main,
                ):
                    rc = entry.run()
                self.assertEqual(rc, 0)
                start_dh03.assert_not_called()
                start_forward.assert_called_once()
                start_sentinel.assert_called_once()
                args = main.call_args.args[0]
                self.assertEqual(args[0], "dashboard")
                self.assertNotIn("local-node", args)
                dh = json.loads(Path("data/dh03_local_status.json").read_text(encoding="utf-8"))
                self.assertEqual(dh["status"], "FAIL_CLOSED")
                self.assertEqual(dh["reason"], "DH03_NOT_STARTED_CLOCK_PREFLIGHT_FAILED")
                self.assertEqual(dh["server_minus_local_midpoint_ms"], 1234.5)
                self.assertEqual(dh["request_rtt_ms"], 42.0)
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
                    patch.object(entry, "_resource_path", return_value=self._registry_path()),
                    patch.object(entry, "dh03_clock_preflight", return_value={"pass": True, "blockers": [], "server_minus_local_midpoint_ms": 4.0, "request_rtt_ms": 30.0, "max_abs_offset_ms": 500.0, "max_rtt_ms": 1000.0}),
                    patch.object(entry, "_start_dh03_thread") as start_dh03,
                    patch.object(entry, "_start_forward_thread") as start_forward,
                    patch.object(entry, "_start_render_sentinel_thread") as start_sentinel,
                    patch.object(entry, "main", return_value=0) as main,
                ):
                    rc = entry.run()
                self.assertEqual(rc, 0)
                start_dh03.assert_called_once()
                start_forward.assert_called_once()
                start_sentinel.assert_called_once()
                self.assertEqual(main.call_args.args[0][0], "dashboard")
                clock = json.loads(Path("data/dh03_clock_preflight.json").read_text(encoding="utf-8"))
                self.assertTrue(clock["pass"])
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
