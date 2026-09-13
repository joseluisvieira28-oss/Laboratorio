import json
from pathlib import Path
import unittest

from dream_account.models import Candle
from research.phase_b_h01_discovery_postmortem_v01 import (
    _feature_quartiles,
    _tp1_path,
)
from research.phase_b_h01_research_evaluator_v01 import evaluate_h01_universe
from research.phase_b_signal_formation_v01 import CostAssumptions, ResearchParameters, derive_signal_geometries


STEP = 15 * 60 * 1000
ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_PATH = ROOT / "research" / "PHASE_B_H01_DISCOVERY_CLOSEOUT_V0.1.json"
POSTMORTEM_PATH = ROOT / "research" / "phase_b_h01_discovery_postmortem_v01.py"
LAUNCHER_PATH = ROOT / "research" / "run_phase_b_h01_postmortem_windows.bat"


def candle(index, open_, high, low, close):
    timestamp = index * STEP
    return Candle(
        open_time=timestamp,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1_000.0,
        close_time=timestamp + STEP - 1,
        closed=True,
    )


def parameters():
    return ResearchParameters(
        timeframe="15m",
        lookback_bars=4,
        atr_length=2,
        zone_atr_fraction=0.25,
        retest_window_bars=2,
        stop_atr_fraction=0.25,
        tp1_r_multiple=1.0,
        tp2_r_multiple=3.0,
        min_net_rr=2.0,
        max_holding_bars=2,
        require_bullish_breakout_body=True,
    )


def costs():
    return CostAssumptions("BASE_SENSITIVITY", 0.05, 0.05, 0.025)


def managed_series():
    base = [
        candle(0, 97.5, 98.0, 97.0, 97.8),
        candle(1, 97.8, 99.0, 97.5, 98.8),
        candle(2, 98.8, 100.0, 98.5, 99.5),
        candle(3, 99.5, 99.8, 99.0, 99.4),
        candle(4, 99.8, 101.2, 99.7, 101.0),
        candle(5, 101.0, 101.1, 99.8, 100.1),
        candle(6, 100.2, 101.0, 100.0, 100.6),
        candle(7, 100.6, 103.0, 100.4, 102.7),
    ]
    signal = derive_signal_geometries(base, parameters(), costs())[0]
    base[6] = candle(6, signal.entry, signal.tp1 + 0.05, signal.entry - 0.05, signal.entry + 0.10)
    base[7] = candle(7, signal.entry + 0.10, signal.entry + 0.20, signal.entry - 0.01, signal.entry + 0.05)
    return base


class PhaseBH01DiscoveryPostMortemTests(unittest.TestCase):
    def test_closeout_authorizes_diagnostics_but_forbids_rescue(self):
        closeout = json.loads(CLOSEOUT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(closeout["status"], "CLOSED_NO_EDGE")
        self.assertEqual(closeout["classification"], "NO_EDGE")
        governance = closeout["governance_closeout"]
        self.assertTrue(governance["descriptive_postmortem_on_already_open_discovery_data_allowed"])
        self.assertTrue(governance["reproducibility_rerun_with_identical_frozen_inputs_allowed"])
        self.assertFalse(governance["validation_unlock_eligible"])
        self.assertFalse(governance["2026_may_be_opened"])
        self.assertFalse(governance["h01_may_be_retuned_and_reclassified_as_same_hypothesis"])

    def test_tp1_path_counts_protective_stop_without_promoting_it(self):
        records, metrics = evaluate_h01_universe({"BTCUSDT": managed_series()}, parameters(), costs())
        self.assertGreaterEqual(metrics.resolved_trade_count, 1)
        result = _tp1_path(records)
        self.assertGreaterEqual(result["tp1_reached_count"], 1)
        self.assertGreaterEqual(result["tp1_then_protective_exit_count"], 1)
        self.assertIn("No partial exit", result["warning"])

    def test_posthoc_quartiles_are_explicitly_descriptive(self):
        records, _ = evaluate_h01_universe({"BTCUSDT": managed_series()}, parameters(), costs())
        result = _feature_quartiles(
            records,
            name="atr_pct",
            feature_fn=lambda r: r.signal.atr_before_breakout / r.signal.entry * 100.0,
        )
        self.assertEqual(result["method"], "POSTHOC_DESCRIPTIVE_QUARTILES")
        self.assertIn("cannot filter", result["warning"])
        self.assertIn("not H02 evidence", result["warning"])

    def test_postmortem_and_launcher_keep_future_stages_and_live_routes_blocked(self):
        source = POSTMORTEM_PATH.read_text(encoding="utf-8")
        launcher = LAUNCHER_PATH.read_text(encoding="utf-8")
        combined = (source + "\n" + launcher).lower()
        for forbidden in (
            "/api/v3/order",
            "requests.post",
            "requests.put",
            "requests.patch",
            "requests.delete",
            "render deploy",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn('"candidate_selection_performed": false', source.lower())
        self.assertIn('"h02_frozen_or_evaluated": false', source.lower())
        self.assertIn("validation 2025-09..12: locked", launcher.lower())
        self.assertIn("holdout 2026: locked", launcher.lower())
        self.assertIn("h01 retuning / rescue: forbidden", launcher.lower())


if __name__ == "__main__":
    unittest.main()
