from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile

from dream_account.models import Candle
from research.phase_b_h03_binance_offline_adapter_v01 import (
    CLOSE_TIME_AMENDMENT_FINGERPRINT,
    adapt_binance_daily_archive_bytes,
)
from research.phase_b_h03_research_evaluator_v01 import BASE_COHORT_SOURCE, evaluate_h03_symbol
from research.phase_b_h03_stage_classifier_v01 import classify_h03_binance_discovery
from research.phase_b_research_evaluator_v01 import BootstrapInterval, EvaluationMetrics, FixedCohortCostMetrics
from research.phase_b_signal_formation_v01 import CostAssumptions, ResearchParameters, SignalGeometry, TradeOutcome


TF = 900_000
ROOT = Path(__file__).resolve().parents[1]
AMENDMENT_PATH = ROOT / "research" / "PHASE_B_H03_BINANCE_ADAPTER_CLOSE_TIME_AMENDMENT_V0.1.json"


def ms(y: int, m: int, d: int, h: int, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=timezone.utc).timestamp() * 1000)


def build_zip(
    day: str = "2021-02-01",
    *,
    omit_index: int | None = None,
    bad_close_index: int | None = None,
    early_close_index: int | None = None,
) -> tuple[str, bytes, str]:
    start = ms(2021, 2, 1, 0)
    text = StringIO()
    writer = csv.writer(text, lineterminator="\n")
    for i in range(96):
        if i == omit_index:
            continue
        ot = start + i * TF
        ct = ot + TF - 1
        if i == bad_close_index:
            ct += 1
        if i == early_close_index:
            ct -= 5_000
        writer.writerow([ot, "100", "102", "99", "101", "10", ct, "1000", "5", "6", "600", "0"])
    member = f"BTCUSDT-15m-{day}.csv"
    filename = f"BTCUSDT-15m-{day}.zip"
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, text.getvalue())
    raw = buffer.getvalue()
    checksum = f"{sha256(raw).hexdigest()}  {filename}\n"
    return filename, raw, checksum


def make_signal(entry_time: int, fingerprint: str) -> SignalGeometry:
    return SignalGeometry(
        setup_id="PBR01_BREAKOUT_RETEST_LONG",
        timeframe="15m",
        breakout_open_time=entry_time - 2 * TF,
        breakout_close_time=entry_time - TF - 1,
        retest_open_time=entry_time - TF,
        retest_close_time=entry_time - 1,
        entry_open_time=entry_time,
        resistance=100.0,
        atr_before_breakout=2.0,
        zone_low=99.5,
        zone_high=100.5,
        breakout_close=101.0,
        retest_low=100.0,
        retest_close=100.8,
        entry=101.0,
        stop=99.0,
        tp1=103.0,
        tp2=107.0,
        stop_distance_pct=(2.0 / 101.0) * 100,
        gross_rr_tp2=3.0,
        net_rr_tp2=2.5,
        estimated_round_trip_cost_pct=0.2,
        geometry_status="GEOMETRY_READY",
        full_trade_authorized=False,
        submitted_to_exchange=False,
        full_trade_blockers=("research_only",),
        fingerprint=fingerprint,
    )


def metrics(*, count: int, expectancy: float | None, pf: float | None) -> EvaluationMetrics:
    return EvaluationMetrics(
        cost_scenario="BASE_SENSITIVITY", raw_geometry_count=count,
        net_rr_rejected_count=0, selected_trade_count=count, overlap_skipped_count=0,
        unresolved_trade_count=0, resolved_trade_count=count,
        net_expectancy_r=expectancy, median_net_r=expectancy,
        win_rate=0.5 if count else None, loss_rate=0.5 if count else None,
        profit_factor_r=pf, tp1_reach_rate=0.5 if count else None,
        same_bar_ambiguity_rate=0.0 if count else None,
        time_exit_rate=0.0 if count else None, stop_gap_rate=0.0 if count else None,
        signal_frequency_per_30d=5.0 if count else None,
        symbol_distribution={"BTCUSDT": count} if count else {},
        contiguous_segment_count=1, detected_gap_count=0,
    )


def stress(*, count: int, expectancy: float | None) -> FixedCohortCostMetrics:
    return FixedCohortCostMetrics(
        cost_scenario="STRESS", cohort_source=BASE_COHORT_SOURCE,
        selected_trade_count=count, resolved_trade_count=count, unresolved_trade_count=0,
        net_expectancy_r=expectancy, median_net_r=expectancy,
        profit_factor_r=1.2 if expectancy is not None else None,
        net_rr_below_minimum_count=0, net_rr_violation_rate=0.0 if count else None,
    )


def bootstrap(lower: float | None) -> BootstrapInterval:
    return BootstrapInterval(
        method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP", repetitions=5000, seed=230911,
        confidence=0.95, sample_days=100, lower=lower,
        point_estimate=0.2 if lower is not None else None,
        upper=0.4 if lower is not None else None,
        undefined_reason=None if lower is not None else "undefined",
    )


class PhaseBH03OfflineHarnessTests(unittest.TestCase):
    def test_close_time_amendment_fingerprint_is_deterministic_and_pre_outcome(self):
        payload = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
        supplied = payload.pop("fingerprint")
        recomputed = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        self.assertEqual(supplied, CLOSE_TIME_AMENDMENT_FINGERPRINT)
        self.assertEqual(recomputed, CLOSE_TIME_AMENDMENT_FINGERPRINT)
        self.assertFalse(payload["authority_basis"]["first_outcome_evaluation_completed"])
        self.assertFalse(payload["authority_basis"]["performance_metrics_inspected"])
        self.assertEqual(payload["trigger"]["close_time_violations"], 22)
        self.assertEqual(payload["trigger"]["open_alignment_violations"], 0)

    def test_binance_daily_archive_checksum_schema_and_15m_integrity_pass(self):
        filename, raw, checksum = build_zip()
        result = adapt_binance_daily_archive_bytes(
            symbol="BTCUSDT", day="2021-02-01", archive_filename=filename,
            archive_bytes=raw, checksum_text=checksum,
        )
        self.assertEqual(result.status, "PASS_BINANCE_DAILY")
        self.assertTrue(result.checksum_verified)
        self.assertEqual(result.row_count, 96)
        self.assertEqual(len(result.candles), 96)
        self.assertEqual(result.detected_gap_count, 0)
        self.assertEqual(result.source_close_time_anomaly_count, 0)

    def test_bad_checksum_fails_before_zip_payload_is_promoted(self):
        filename, raw, _ = build_zip()
        bad = "0" * 64 + f"  {filename}\n"
        result = adapt_binance_daily_archive_bytes(
            symbol="BTCUSDT", day="2021-02-01", archive_filename=filename,
            archive_bytes=raw, checksum_text=bad,
        )
        self.assertEqual(result.status, "BLOCKED_CHECKSUM_MISMATCH")
        self.assertFalse(result.checksum_verified)
        self.assertEqual(result.candles, ())

    def test_exact_15m_multiple_gap_is_reported_never_interpolated(self):
        filename, raw, checksum = build_zip(omit_index=20)
        result = adapt_binance_daily_archive_bytes(
            symbol="BTCUSDT", day="2021-02-01", archive_filename=filename,
            archive_bytes=raw, checksum_text=checksum,
        )
        self.assertEqual(result.status, "PASS_BINANCE_DAILY_WITH_GAPS")
        self.assertEqual(result.row_count, 95)
        self.assertEqual(result.detected_gap_count, 1)
        self.assertEqual(result.missing_candle_count, 1)
        self.assertEqual(len(result.candles), 95)

    def test_early_source_close_time_is_reported_and_only_metadata_is_canonicalized(self):
        filename, raw, checksum = build_zip(early_close_index=10)
        result = adapt_binance_daily_archive_bytes(
            symbol="BTCUSDT", day="2021-02-01", archive_filename=filename,
            archive_bytes=raw, checksum_text=checksum,
        )
        self.assertEqual(result.status, "PASS_BINANCE_DAILY")
        self.assertEqual(result.source_close_time_anomaly_count, 1)
        candle = result.candles[10]
        self.assertEqual(candle.open, 100.0)
        self.assertEqual(candle.high, 102.0)
        self.assertEqual(candle.low, 99.0)
        self.assertEqual(candle.close, 101.0)
        self.assertEqual(candle.volume, 10.0)
        self.assertEqual(candle.close_time, candle.open_time + TF - 1)

    def test_source_close_time_past_canonical_boundary_still_blocks_all_candles(self):
        filename, raw, checksum = build_zip(bad_close_index=10)
        result = adapt_binance_daily_archive_bytes(
            symbol="BTCUSDT", day="2021-02-01", archive_filename=filename,
            archive_bytes=raw, checksum_text=checksum,
        )
        self.assertEqual(result.status, "BLOCKED_BINANCE_DAILY_INTEGRITY")
        self.assertIn("SOURCE_CLOSE_TIME_EXCEEDS_CANONICAL_BOUNDARY", result.reasons)
        self.assertEqual(result.candles, ())

    def test_session_rejection_occurs_before_overlap_selection(self):
        candles = [
            Candle(ms(2021, 2, 1, 12, 45), 100, 101, 99, 100, 1, ms(2021, 2, 1, 12, 45) + TF - 1, True),
            Candle(ms(2021, 2, 1, 13, 0), 100, 101, 99, 100, 1, ms(2021, 2, 1, 13, 0) + TF - 1, True),
        ]
        outside = make_signal(ms(2021, 2, 1, 12, 45), "outside")
        inside = make_signal(ms(2021, 2, 1, 13, 0), "inside")
        outcome = TradeOutcome("inside", "TP2", ms(2021, 2, 1, 13, 0), 107.0, 1, 5.0, 2.0, True, False, False)
        costs = CostAssumptions("BASE_SENSITIVITY", 0.05, 0.05, 0.025)
        with patch("research.phase_b_h03_research_evaluator_v01.derive_signal_geometries", return_value=[outside, inside]), patch(
            "research.phase_b_h03_research_evaluator_v01.simulate_h01_managed_outcome", return_value=outcome
        ) as sim:
            records, diagnostics = evaluate_h03_symbol("BTCUSDT", candles, ResearchParameters(), costs)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].signal.fingerprint, "inside")
        self.assertEqual(diagnostics["session_rejected_ready_count"], 1)
        self.assertEqual(sim.call_count, 1)

    def test_h03_classifier_is_insufficient_below_100_and_cannot_unlock_data(self):
        decision = classify_h03_binance_discovery(metrics(count=99, expectancy=1.0, pf=2.0), stress(count=99, expectancy=1.0), bootstrap(0.5))
        self.assertEqual(decision.classification, "INSUFFICIENT_SAMPLE")
        self.assertFalse(decision.mexc_target_venue_validation_eligible)
        self.assertFalse(decision.mexc_target_venue_validation_data_access_authorized)
        self.assertFalse(decision.holdout_2026_unlock_eligible)

    def test_h03_classifier_survives_only_when_all_four_edge_gates_pass(self):
        decision = classify_h03_binance_discovery(metrics(count=120, expectancy=0.2, pf=1.3), stress(count=120, expectancy=0.1), bootstrap(0.05))
        self.assertEqual(decision.classification, "SURVIVES")
        self.assertTrue(decision.mexc_target_venue_validation_eligible)
        self.assertFalse(decision.mexc_target_venue_validation_data_access_authorized)
        self.assertFalse(decision.holdout_2026_unlock_eligible)

    def test_any_failed_edge_gate_is_no_edge(self):
        decision = classify_h03_binance_discovery(metrics(count=120, expectancy=0.2, pf=1.3), stress(count=120, expectancy=-0.01), bootstrap(0.05))
        self.assertEqual(decision.classification, "NO_EDGE")
        self.assertIn("fixed_cohort_stress_expectancy_not_positive", decision.failed_conditions)
        self.assertFalse(decision.mexc_target_venue_validation_eligible)


if __name__ == "__main__":
    unittest.main()
