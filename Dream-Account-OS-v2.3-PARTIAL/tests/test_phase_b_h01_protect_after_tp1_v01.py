import json
from pathlib import Path
import unittest

from dream_account.models import Candle
from research.phase_b_h01_protect_after_tp1_v01 import (
    EXCHANGE_MUTATION_AUTHORIZED,
    HOLDOUT_2026_AUTHORIZED,
    HYPOTHESIS_ID,
    LIVE_AUTHORIZED,
    VALIDATION_2025_AUTHORIZED,
    simulate_h01_managed_outcome,
)
from research.phase_b_signal_formation_v01 import (
    CostAssumptions,
    ResearchParameters,
    derive_signal_geometries,
)


STEP = 15 * 60 * 1000
ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "PHASE_B_H01_PROTECT_AFTER_TP1_PROSPECTIVE_FREEZE_V0.1.json"
MODULE_PATH = ROOT / "research" / "phase_b_h01_protect_after_tp1_v01.py"


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


def base_series():
    return [
        candle(0, 97.5, 98.0, 97.0, 97.8),
        candle(1, 97.8, 99.0, 97.5, 98.8),
        candle(2, 98.8, 100.0, 98.5, 99.5),
        candle(3, 99.5, 99.8, 99.0, 99.4),
        candle(4, 99.8, 101.2, 99.7, 101.0),
        candle(5, 101.0, 101.1, 99.8, 100.1),
        candle(6, 100.2, 101.0, 100.0, 100.6),
        candle(7, 100.6, 103.0, 100.4, 102.7),
    ]


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


def base_costs():
    return CostAssumptions("BASE_SENSITIVITY", 0.05, 0.05, 0.025)


def signal():
    signals = derive_signal_geometries(base_series(), parameters(), base_costs())
    if not signals:
        raise AssertionError("synthetic fixture did not create a P00 signal")
    return signals[0]


def bar(index, *, open_, high, low, close):
    return candle(index, open_, high, low, close)


class PhaseBH01ProtectAfterTP1Tests(unittest.TestCase):
    def test_freeze_is_new_hypothesis_and_2025_2026_remain_locked(self):
        freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(freeze["hypothesis_id"], HYPOTHESIS_ID)
        self.assertTrue(freeze["origin"]["data_driven_hypothesis_generation"])
        self.assertTrue(freeze["origin"]["confirmatory_reuse_of_2023_2024_forbidden"])
        self.assertFalse(freeze["authority_boundary"]["this_file_authorizes_2025_data_access"])
        self.assertTrue(freeze["data_contract"]["discovery_2025"]["status"].startswith("LOCKED_"))
        self.assertTrue(freeze["data_contract"]["validation_2025"]["status"].startswith("PHYSICALLY_LOCKED_"))
        self.assertTrue(freeze["data_contract"]["final_holdout_2026"]["status"].startswith("LOCKED_"))
        self.assertFalse(LIVE_AUTHORIZED)
        self.assertFalse(VALIDATION_2025_AUTHORIZED)
        self.assertFalse(HOLDOUT_2026_AUTHORIZED)
        self.assertFalse(EXCHANGE_MUTATION_AUTHORIZED)

    def test_tp1_touch_does_not_protect_inside_same_bar(self):
        s = signal()
        series = base_series()
        # First TP1-touch bar trades below entry but stays above the original stop.
        # If H01 incorrectly activated intrabar, this candle would exit at entry.
        series[6] = bar(6, open_=s.entry, high=s.tp1 + 0.05, low=s.entry - 0.05, close=s.entry + 0.10)
        series[7] = bar(7, open_=s.entry + 0.10, high=s.tp2 + 0.05, low=s.entry + 0.05, close=s.tp2)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "TP2")
        self.assertTrue(outcome.tp1_reached)

    def test_surviving_tp1_touch_activates_entry_stop_from_next_bar(self):
        s = signal()
        series = base_series()
        series[6] = bar(6, open_=s.entry, high=s.tp1 + 0.05, low=s.entry - 0.05, close=s.entry + 0.10)
        series[7] = bar(7, open_=s.entry + 0.10, high=s.entry + 0.20, low=s.entry - 0.01, close=s.entry + 0.05)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "PROTECTIVE_STOP")
        self.assertAlmostEqual(outcome.exit_price, s.entry)
        self.assertTrue(outcome.tp1_reached)

    def test_entry_price_protection_is_not_fake_zero_after_costs(self):
        s = signal()
        series = base_series()
        series[6] = bar(6, open_=s.entry, high=s.tp1 + 0.05, low=s.entry - 0.05, close=s.entry + 0.10)
        series[7] = bar(7, open_=s.entry + 0.10, high=s.entry + 0.20, low=s.entry - 0.01, close=s.entry + 0.05)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "PROTECTIVE_STOP")
        self.assertAlmostEqual(outcome.gross_return_pct, 0.0)
        self.assertLess(outcome.net_r, 0.0)
        self.assertNotAlmostEqual(outcome.net_r, 0.0)

    def test_same_bar_initial_stop_and_tp1_touch_is_stop_without_protection(self):
        s = signal()
        series = base_series()
        series[6] = bar(6, open_=s.entry, high=s.tp1 + 0.05, low=s.stop - 0.01, close=s.entry)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "STOP")
        self.assertFalse(outcome.tp1_reached)
        self.assertAlmostEqual(outcome.net_r, -1.0)

    def test_same_bar_tp1_and_tp2_without_stop_exits_tp2(self):
        s = signal()
        series = base_series()
        series[6] = bar(6, open_=s.entry, high=s.tp2 + 0.05, low=s.entry - 0.05, close=s.tp2)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "TP2")
        self.assertTrue(outcome.tp1_reached)
        self.assertAlmostEqual(outcome.exit_price, s.tp2)

    def test_later_protective_stop_and_tp2_same_bar_protective_stop_wins(self):
        s = signal()
        series = base_series()
        series[6] = bar(6, open_=s.entry, high=s.tp1 + 0.05, low=s.entry - 0.05, close=s.entry + 0.10)
        series[7] = bar(7, open_=s.entry + 0.10, high=s.tp2 + 0.05, low=s.entry - 0.01, close=s.tp2)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "PROTECTIVE_STOP_AMBIGUOUS_SAME_BAR")
        self.assertTrue(outcome.same_bar_stop_target_ambiguity)
        self.assertAlmostEqual(outcome.exit_price, s.entry)

    def test_gap_through_active_protective_stop_exits_at_adverse_open(self):
        s = signal()
        series = base_series()
        series[6] = bar(6, open_=s.entry, high=s.tp1 + 0.05, low=s.entry - 0.05, close=s.entry + 0.10)
        adverse_open = s.entry - 0.20
        series[7] = bar(7, open_=adverse_open, high=s.entry, low=adverse_open - 0.10, close=adverse_open + 0.05)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "PROTECTIVE_STOP_GAP")
        self.assertAlmostEqual(outcome.exit_price, adverse_open)
        self.assertLess(outcome.net_r, 0.0)

    def test_without_tp1_touch_max_hold_semantics_remain_next_bar_open(self):
        s = signal()
        series = base_series()
        series[6] = bar(6, open_=s.entry, high=s.entry + 0.10, low=s.entry - 0.10, close=s.entry + 0.05)
        next_open = s.entry + 0.07
        series[7] = bar(7, open_=next_open, high=next_open + 0.10, low=next_open - 0.10, close=next_open)
        outcome = simulate_h01_managed_outcome(s, series, base_costs(), max_holding_bars=1)
        self.assertEqual(outcome.exit_reason, "TIME_EXIT_NEXT_OPEN")
        self.assertEqual(outcome.exit_open_time, 7 * STEP)
        self.assertAlmostEqual(outcome.exit_price, next_open)
        self.assertFalse(outcome.tp1_reached)

    def test_h01_module_is_offline_and_has_no_stage_unlock_or_exchange_route(self):
        text = MODULE_PATH.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "mexc_client",
            "execution_layer",
            "classify_stage",
            "run_p00_discovery",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("2025-01", text)
        self.assertNotIn("2026-", text)


if __name__ == "__main__":
    unittest.main()
