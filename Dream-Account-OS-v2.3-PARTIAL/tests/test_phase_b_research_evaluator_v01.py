from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from dream_account.models import Candle
from research.phase_b_research_evaluator_v01 import (
    ResearchTradeRecord,
    day_block_bootstrap_expectancy,
    evaluate_symbol,
    evaluate_universe,
    split_contiguous_segments,
)
from research.phase_b_signal_formation_v01 import (
    CostAssumptions,
    ResearchParameters,
    TradeOutcome,
    derive_signal_geometries,
    simulate_outcome,
)


STEP = 15 * 60 * 1000
DAY = 24 * 60 * 60 * 1000
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "PHASE_B_PRE_DATA_RESEARCH_FREEZE_V0.1.json"


def candle(index, open_, high, low, close, *, start=0):
    timestamp = start + index * STEP
    return Candle(timestamp, open_, high, low, close, 1_000.0, timestamp + STEP - 1, True)


def base_series(*, start=0):
    return [
        candle(0, 97.5, 98.0, 97.0, 97.8, start=start),
        candle(1, 97.8, 99.0, 97.5, 98.8, start=start),
        candle(2, 98.8, 100.0, 98.5, 99.5, start=start),
        candle(3, 99.5, 99.8, 99.0, 99.4, start=start),
        candle(4, 99.8, 101.2, 99.7, 101.0, start=start),
        candle(5, 101.0, 101.1, 99.8, 100.1, start=start),
        candle(6, 100.2, 101.0, 100.0, 100.6, start=start),
        candle(7, 100.6, 103.0, 100.4, 102.7, start=start),
    ]


def parameters(**changes):
    values = dict(
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
    values.update(changes)
    return ResearchParameters(**values)


def costs(name="BASE_SENSITIVITY"):
    return CostAssumptions(name, 0.05, 0.05, 0.025)


def signal_for(series=None):
    signals = derive_signal_geometries(series or base_series(), parameters(), costs())
    if not signals:
        raise AssertionError("fixture did not produce signal")
    return signals[0]


class PhaseBResearchEvaluatorTests(unittest.TestCase):
    def test_gap_is_split_without_interpolation(self):
        first = base_series()
        second = base_series(start=first[-1].open_time + 3 * STEP)
        segments, gaps = split_contiguous_segments(first + second)
        self.assertEqual(len(segments), 2)
        self.assertEqual(gaps, 1)
        self.assertEqual(sum(len(segment) for segment in segments), 16)

    def test_empty_signal_universe_reports_undefined_metrics_not_fake_zeroes(self):
        flat = [candle(i, 100.0, 100.1, 99.9, 100.0) for i in range(12)]
        records, metrics = evaluate_universe({"BTCUSDT": flat}, parameters(), costs())
        self.assertEqual(records, [])
        self.assertEqual(metrics.resolved_trade_count, 0)
        self.assertIsNone(metrics.net_expectancy_r)
        self.assertIsNone(metrics.win_rate)
        self.assertIsNone(metrics.profit_factor_r)

    def test_base_fixture_produces_resolved_winner(self):
        records, metrics = evaluate_universe({"BTCUSDT": base_series()}, parameters(), costs())
        self.assertEqual(len(records), 1)
        self.assertEqual(metrics.resolved_trade_count, 1)
        self.assertGreater(metrics.net_expectancy_r, 0)
        self.assertEqual(metrics.win_rate, 1.0)
        self.assertIsNone(metrics.profit_factor_r)
        self.assertEqual(metrics.symbol_distribution, {"BTCUSDT": 1})

    def test_same_symbol_overlap_is_skipped_until_prior_trade_exits(self):
        series = base_series()
        signal1 = signal_for(series)
        signal2 = replace(
            signal1,
            entry_open_time=signal1.entry_open_time + STEP,
            fingerprint="b" * 64,
        )
        outcome1 = TradeOutcome(
            setup_fingerprint=signal1.fingerprint,
            exit_reason="TIME_EXIT_NEXT_OPEN",
            exit_open_time=signal2.entry_open_time,
            exit_price=signal1.entry,
            bars_held=1,
            gross_return_pct=0.0,
            net_r=-0.1,
            tp1_reached=False,
            same_bar_stop_target_ambiguity=False,
        )
        with patch(
            "research.phase_b_research_evaluator_v01.derive_signal_geometries",
            return_value=[signal1, signal2],
        ), patch(
            "research.phase_b_research_evaluator_v01.simulate_outcome",
            return_value=outcome1,
        ) as simulator:
            records, diagnostics = evaluate_symbol("BTCUSDT", series, parameters(), costs())
        self.assertEqual(len(records), 1)
        self.assertEqual(diagnostics["overlap_skipped_count"], 1)
        self.assertEqual(simulator.call_count, 1)

    def test_cost_gate_rejections_are_counted_and_not_traded(self):
        expensive = CostAssumptions("EXPENSIVE", 0.25, 0.50, 0.25)
        records, metrics = evaluate_universe({"BTCUSDT": base_series()}, parameters(), expensive)
        self.assertEqual(records, [])
        self.assertGreaterEqual(metrics.net_rr_rejected_count, 1)
        self.assertEqual(metrics.selected_trade_count, 0)

    def test_day_block_bootstrap_is_deterministic(self):
        base_signal = signal_for()
        template = simulate_outcome(base_signal, base_series(), costs(), max_holding_bars=2)
        records = []
        values = [1.0, -0.5, 0.75, -0.25]
        for day_index, value in enumerate(values):
            signal = replace(
                base_signal,
                entry_open_time=day_index * DAY + base_signal.entry_open_time,
                fingerprint=f"{day_index + 1:064x}",
            )
            outcome = replace(
                template,
                setup_fingerprint=signal.fingerprint,
                net_r=value,
                exit_open_time=signal.entry_open_time + STEP,
            )
            records.append(ResearchTradeRecord("BTCUSDT", signal, outcome))
        first = day_block_bootstrap_expectancy(records, repetitions=500, seed=230911)
        second = day_block_bootstrap_expectancy(records, repetitions=500, seed=230911)
        self.assertEqual(first, second)
        self.assertEqual(first.sample_days, 4)
        self.assertAlmostEqual(first.point_estimate, sum(values) / len(values))
        self.assertLessEqual(first.lower, first.point_estimate)
        self.assertGreaterEqual(first.upper, first.point_estimate)

    def test_day_block_bootstrap_empty_input_is_explicitly_undefined(self):
        result = day_block_bootstrap_expectancy([], repetitions=10)
        self.assertIsNone(result.lower)
        self.assertIsNone(result.point_estimate)
        self.assertIsNone(result.upper)
        self.assertEqual(result.undefined_reason, "NO_RESOLVED_TRADES")

    def test_manifest_is_research_only_and_2026_holdout_is_locked(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "RESEARCH_ONLY_NOT_LIVE_AUTHORITY")
        authority = data["authority_boundary"]
        self.assertFalse(authority["phase_b_live_integration_authorized"])
        self.assertFalse(authority["real_trading_authorized"])
        self.assertFalse(authority["exchange_mutation_authorized"])
        self.assertEqual(data["data_contract"]["final_holdout"]["status"], "LOCKED_UNTIL_SEPARATE_UNLOCK_AFTER_DISCOVERY_AND_VALIDATION_PASS")

    def test_manifest_primary_profile_is_unique_and_sensitivities_cannot_replace_it(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["primary_hypothesis"]["profile_id"], "P00_PRIMARY")
        self.assertEqual(data["decision_policy"]["primary_profile_only"], "P00_PRIMARY")
        self.assertFalse(data["sensitivity_policy"]["may_replace_primary_after_results"])
        self.assertFalse(data["sensitivity_policy"]["may_be_selected_as_winner"])
        for profile in data["sensitivity_profiles"]:
            self.assertEqual(len(profile["change_only"]), 1)

    def test_manifest_cost_scenarios_are_arithmetically_consistent(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for scenario in data["cost_scenarios"]:
            total = 2 * scenario["fee_pct_each_side"] + scenario["spread_pct"] + 2 * scenario["slippage_pct_each_side"]
            self.assertAlmostEqual(total, scenario["round_trip_cost_pct"])

    def test_manifest_forbids_cross_exchange_backfill_and_interpolation(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(data["data_contract"]["cross_exchange_backfill_allowed"])
        self.assertIn("no candle interpolation", data["data_contract"]["listing_and_missing_data"].lower())

    def test_evaluator_source_has_no_network_client_or_exchange_mutations(self):
        text = (ROOT / "research" / "phase_b_research_evaluator_v01.py").read_text(encoding="utf-8").lower()
        for forbidden in ("import requests", "import urllib", "import websockets", ".post(", ".put(", ".patch(", ".delete("):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("mexc_client", text)
        self.assertNotIn("execution_layer", text)


if __name__ == "__main__":
    unittest.main()
