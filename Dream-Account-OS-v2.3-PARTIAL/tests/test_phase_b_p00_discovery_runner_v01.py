import csv
import json
from pathlib import Path
import tempfile
import unittest

from research.phase_b_p00_discovery_runner_v01 import (
    AMENDMENT_PATH,
    FROZEN_UNIVERSE,
    START_MONTH,
    END_MONTH,
    _freeze_bindings,
    _load_canonical_window,
    _month_sequence,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "research" / "phase_b_p00_discovery_runner_v01.py"
LAUNCHER = ROOT / "research" / "run_phase_b_p00_discovery_windows.bat"
STEP = 900_000


class PhaseBP00DiscoveryRunnerTests(unittest.TestCase):
    def test_amendment_is_frozen_before_first_p00_and_keeps_future_stages_locked(self):
        data = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "FROZEN_BEFORE_FIRST_P00_OUTCOME_EVALUATION")
        authority = data["authority_boundary"]
        self.assertTrue(authority["p00_discovery_evaluation_authorized_after_preflight"])
        self.assertFalse(authority["validation_2025_access_authorized"])
        self.assertFalse(authority["holdout_2026_access_authorized"])
        self.assertFalse(authority["exchange_network_access_authorized"])
        self.assertFalse(authority["exchange_mutation_authorized"])
        self.assertFalse(authority["live_integration_authorized"])

    def test_effective_utc_window_reconciles_plus8_without_opening_2025_partition(self):
        data = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
        window = data["effective_discovery_window"]
        self.assertEqual(window["start_utc_inclusive"], "2023-02-01T00:00:00.000Z")
        self.assertEqual(window["end_utc_exclusive"], "2024-12-31T16:00:00.000Z")
        self.assertEqual(window["first_partition_leading_candles_excluded_per_symbol"], 32)
        self.assertFalse(window["2025_partition_read_required"])
        self.assertFalse(window["boundary_extension_after_outcomes_allowed"])
        self.assertEqual(data["source_contract"]["source_partition_timezone"], "UTC+08:00")

    def test_frozen_universe_and_source_months_are_exact(self):
        self.assertEqual(FROZEN_UNIVERSE, ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"))
        self.assertEqual(START_MONTH, "2023-02")
        self.assertEqual(END_MONTH, "2024-12")
        months = _month_sequence(START_MONTH, END_MONTH)
        self.assertEqual(len(months), 23)
        self.assertEqual(months[0], "2023-02")
        self.assertEqual(months[-1], "2024-12")
        self.assertNotIn("2025-01", months)

    def test_authority_binding_loads_current_freezes(self):
        freeze, amendment, start_ms, end_ms = _freeze_bindings()
        self.assertEqual(freeze["primary_hypothesis"]["profile_id"], "P00_PRIMARY")
        self.assertEqual(tuple(amendment["frozen_universe"]), FROZEN_UNIVERSE)
        self.assertLess(start_ms, end_ms)

    def test_canonical_loader_trims_leading_provider_partition_and_end_exclusive(self):
        start_ms = 1_000_000_000
        end_ms = start_ms + 2 * STEP
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.canonical.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms"])
                for open_time in (start_ms - STEP, start_ms, start_ms + STEP, end_ms):
                    writer.writerow([open_time, "100", "101", "99", "100.5", "1", open_time + STEP - 1])
            candles = _load_canonical_window(path, start_ms=start_ms, end_ms=end_ms)
        self.assertEqual([item.open_time for item in candles], [start_ms, start_ms + STEP])

    def test_runner_and_launcher_are_offline_and_have_no_exchange_mutation_route(self):
        runner = RUNNER.read_text(encoding="utf-8").lower()
        launcher = LAUNCHER.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "/api/v3/order",
            "/api/v3/capital/withdraw",
        ):
            self.assertNotIn(forbidden, runner)
            self.assertNotIn(forbidden, launcher)
        self.assertIn("p00 discovery", launcher)
        self.assertIn("pythonpath", launcher)


if __name__ == "__main__":
    unittest.main()
