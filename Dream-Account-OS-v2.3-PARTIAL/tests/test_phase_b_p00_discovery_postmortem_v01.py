from __future__ import annotations

import json
import unittest
from pathlib import Path

from research.phase_b_p00_discovery_postmortem_v01 import (
    _net_r_distribution,
    _summarize_records,
    _tp1_path,
    _volatility_quartiles,
)
from research.phase_b_research_evaluator_v01 import ResearchTradeRecord
from research.phase_b_signal_formation_v01 import SignalGeometry, TradeOutcome


ROOT = Path(__file__).resolve().parents[1]


def _record(symbol: str, index: int, net_r: float, exit_reason: str, tp1: bool, atr: float = 2.0) -> ResearchTradeRecord:
    entry = 100.0
    stop = 99.0
    signal = SignalGeometry(
        setup_id="PBR01_BREAKOUT_RETEST_LONG",
        timeframe="15m",
        breakout_open_time=1_700_000_000_000 + index * 3_600_000,
        breakout_close_time=1_700_000_899_999 + index * 3_600_000,
        retest_open_time=1_700_000_900_000 + index * 3_600_000,
        retest_close_time=1_700_001_799_999 + index * 3_600_000,
        entry_open_time=1_700_001_800_000 + index * 3_600_000,
        resistance=99.5,
        atr_before_breakout=atr,
        zone_low=99.0,
        zone_high=99.5,
        breakout_close=100.2,
        retest_low=99.4,
        retest_close=99.8,
        entry=entry,
        stop=stop,
        tp1=101.0,
        tp2=103.0,
        stop_distance_pct=1.0,
        gross_rr_tp2=3.0,
        net_rr_tp2=2.5,
        estimated_round_trip_cost_pct=0.2,
        geometry_status="GEOMETRY_READY",
        full_trade_authorized=False,
        submitted_to_exchange=False,
        full_trade_blockers=("research_only",),
        fingerprint=f"sig-{index}",
    )
    outcome = TradeOutcome(
        setup_fingerprint=signal.fingerprint,
        exit_reason=exit_reason,
        exit_open_time=signal.entry_open_time + 900_000,
        exit_price=101.0 if net_r > 0 else 99.0,
        bars_held=2,
        gross_return_pct=1.0 if net_r > 0 else -1.0,
        net_r=net_r,
        tp1_reached=tp1,
        same_bar_stop_target_ambiguity=False,
        submitted_to_exchange=False,
    )
    return ResearchTradeRecord(symbol=symbol, signal=signal, outcome=outcome)


class PhaseBP00DiscoveryPostMortemTests(unittest.TestCase):
    def test_tp1_then_stop_is_descriptive_and_counted(self) -> None:
        records = [
            _record("BTCUSDT", 1, -1.0, "STOP", True),
            _record("BTCUSDT", 2, 2.0, "TP2", True),
            _record("ETHUSDT", 3, -1.0, "STOP", False),
        ]
        result = _tp1_path(records)
        self.assertEqual(result["tp1_reached_count"], 2)
        self.assertEqual(result["tp1_then_stop_like_count"], 1)
        self.assertAlmostEqual(result["tp1_then_stop_like_rate_of_tp1_reached"], 0.5)
        self.assertIn("does not authorize", result["warning"])

    def test_summary_and_distribution_do_not_drop_losers(self) -> None:
        records = [
            _record("BTCUSDT", 1, -1.0, "STOP", False),
            _record("BTCUSDT", 2, -0.5, "TIME_EXIT_NEXT_OPEN", True),
            _record("BTCUSDT", 3, 2.0, "TP2", True),
        ]
        summary = _summarize_records(records)
        distribution = _net_r_distribution(records)
        self.assertEqual(summary["resolved_trade_count"], 3)
        self.assertAlmostEqual(summary["net_expectancy_r"], 1.0 / 6.0)
        self.assertEqual(summary["exit_reason_counts"]["STOP"], 1)
        self.assertAlmostEqual(distribution["total"], 0.5)
        self.assertEqual(distribution["min"], -1.0)
        self.assertEqual(distribution["max"], 2.0)

    def test_volatility_quartiles_are_explicitly_posthoc_descriptive(self) -> None:
        records = [
            _record("BTCUSDT", 1, -1.0, "STOP", False, atr=1.0),
            _record("BTCUSDT", 2, -1.0, "STOP", False, atr=2.0),
            _record("ETHUSDT", 3, 2.0, "TP2", True, atr=3.0),
            _record("ETHUSDT", 4, 2.0, "TP2", True, atr=4.0),
        ]
        result = _volatility_quartiles(records)
        self.assertEqual(result["method"], "POSTHOC_DESCRIPTIVE_ATR_PCT_QUARTILES")
        self.assertEqual(sum(group["resolved_trade_count"] for group in result["groups"].values()), 4)
        self.assertIn("cannot rescue P00", result["warning"])

    def test_closeout_allows_diagnostics_but_forbids_rescue(self) -> None:
        closeout = json.loads((ROOT / "research" / "PHASE_B_P00_DISCOVERY_CLOSEOUT_V0.1.json").read_text(encoding="utf-8"))
        governance = closeout["governance_closeout"]
        self.assertEqual(closeout["classification"], "NO_EDGE")
        self.assertTrue(governance["descriptive_postmortem_on_already_open_discovery_data_allowed"])
        self.assertFalse(governance["sensitivity_profile_may_rescue_p00"])
        self.assertFalse(governance["2025_may_be_used_to_rescue_p00"])
        self.assertFalse(governance["2026_may_be_opened"])

    def test_postmortem_and_launcher_are_offline_diagnostic_only(self) -> None:
        source = (ROOT / "research" / "phase_b_p00_discovery_postmortem_v01.py").read_text(encoding="utf-8")
        launcher = (ROOT / "research" / "run_phase_b_p00_postmortem_windows.bat").read_text(encoding="utf-8")
        lowered = source.lower()
        for forbidden in ("requests", "urllib", "websockets", "socket", "/api/v3/order", "subprocess"):
            self.assertNotIn(forbidden, lowered)
        self.assertIn('"may_rescue_p00": False', source)
        self.assertIn('"may_unlock_2025": False', source)
        self.assertIn('"may_open_2026": False', source)
        self.assertIn("P00 remains CLOSED NO_EDGE", launcher)
        self.assertIn("No 2025/2026 data was read", launcher)
        self.assertNotIn("MEXC_API_KEY", launcher)
        self.assertNotIn("MEXC_API_SECRET", launcher)


if __name__ == "__main__":
    unittest.main()
