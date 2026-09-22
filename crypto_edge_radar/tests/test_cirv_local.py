import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from radar.cirv_local import CIRVLocalWatcher, STRATEGY_ID


class CIRVLocalWatcherTests(unittest.TestCase):
    def test_before_first_clean_target_waits_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            watcher = CIRVLocalWatcher(root=td)
            state = watcher.run_once(now=pd.Timestamp("2026-09-22T09:05:00Z"))
            self.assertEqual(state["status"], "WATCHING")
            self.assertEqual(state["runtime_phase"], "WAITING_FIRST_CLEAN_TARGET")
            self.assertEqual(state["first_clean_target"], "2026-09-23")
            self.assertFalse(state["orders_created"])
            self.assertFalse(state["exchange_mutation_performed"])

    def test_in_window_waits_fail_closed_until_both_archives_exist(self):
        with tempfile.TemporaryDirectory() as td:
            watcher = CIRVLocalWatcher(root=td)
            with patch.object(watcher, "_source_ready", return_value=(False, {"BTCUSDT": True, "ETHUSDT": False})):
                state = watcher.run_once(now=pd.Timestamp("2026-09-23T09:05:00Z"))
            self.assertEqual(state["status"], "WATCHING")
            self.assertEqual(state["runtime_phase"], "WAITING_CANONICAL_D_MINUS_1_ARCHIVES")
            self.assertFalse(Path(td, "cirv_forward_forecast_2026-09-23.json").exists())

    def test_after_window_never_backfills_missing_target(self):
        with tempfile.TemporaryDirectory() as td:
            watcher = CIRVLocalWatcher(root=td)
            state = watcher.run_once(now=pd.Timestamp("2026-09-23T10:31:00Z"))
            self.assertEqual(state["status"], "FAIL_CLOSED")
            self.assertEqual(state["runtime_phase"], "MISSED_FORWARD_TARGET_NO_FORECAST")
            self.assertEqual(state["reason"], "NO_BACKFILL_AFTER_DAILY_EXECUTION_WINDOW")
            self.assertFalse(Path(td, "cirv_forward_forecast_2026-09-23.json").exists())

    def test_ready_source_persists_forecast_without_execution_path(self):
        with tempfile.TemporaryDirectory() as td:
            watcher = CIRVLocalWatcher(root=td)
            synthetic = {
                "forward_id": "CIRV-BTCETH-FORWARD-001",
                "strategy_id": STRATEGY_ID,
                "mode": "FORECAST",
                "target_date": "2026-09-23",
                "classification": "PROSPECTIVE_BLIND_DELAYED_SOURCE",
                "generated_without_target_outcome": True,
                "forecasts": [
                    {"asset": "BTCUSDT", "target_date": "2026-09-23", "forecast_har_rv": 1.0, "forecast_har_dow_rv": 1.1},
                    {"asset": "ETHUSDT", "target_date": "2026-09-23", "forecast_har_rv": 2.0, "forecast_har_dow_rv": 2.1},
                ],
                "orders_created": False,
                "authenticated_exchange_api_used": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            }
            with (
                patch.object(watcher, "_source_ready", return_value=(True, {"BTCUSDT": True, "ETHUSDT": True})),
                patch.object(watcher, "_compute_forecast", return_value=(synthetic, pd.DataFrame())),
            ):
                state = watcher.run_once(now=pd.Timestamp("2026-09-23T09:05:00Z"))
            self.assertEqual(state["status"], "FORECAST_READY")
            self.assertEqual(state["runtime_phase"], "FORECAST_PERSISTED")
            saved = json.loads(Path(td, "cirv_forward_forecast_2026-09-23.json").read_text(encoding="utf-8"))
            self.assertTrue(saved["generated_without_target_outcome"])
            self.assertFalse(saved["orders_created"])
            self.assertFalse(saved["exchange_mutation_performed"])

    def test_forecast_generation_requests_history_only_through_d_minus_one(self):
        with tempfile.TemporaryDirectory() as td:
            watcher = CIRVLocalWatcher(root=td)
            target = pd.Timestamp("2026-09-23", tz="UTC")
            captured = {}

            def fake_fetch(cutoff):
                captured["cutoff"] = cutoff
                raise RuntimeError("stop after cutoff capture")

            with patch("radar.cirv_local._fetch_history_through", side_effect=fake_fetch):
                with self.assertRaisesRegex(RuntimeError, "stop after cutoff capture"):
                    watcher._compute_forecast(target)
            self.assertEqual(captured["cutoff"], pd.Timestamp("2026-09-22", tz="UTC"))


if __name__ == "__main__":
    unittest.main()
