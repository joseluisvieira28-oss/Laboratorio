from __future__ import annotations

import calendar
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from research.phase_b_mexc_discovery_corpus_v01 import (
    MEXC_BULK_MONTH_PARTITION_OFFSET_HOURS,
    MEXC_BULK_MONTH_PARTITION_TIMEZONE,
    _source_partition_bounds,
    build_discovery_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "phase_b_mexc_discovery_corpus_v01.py"
LAUNCHER = ROOT / "research" / "build_phase_b_mexc_discovery_corpus_windows.bat"


class PhaseBMEXCDiscoveryCorpusTests(unittest.TestCase):
    def _write_month(self, path: Path, month: str, *, skip_indices: set[int] | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        year, month_number = map(int, month.split("-"))
        start = datetime(year, month_number, 1, tzinfo=timezone.utc) - timedelta(hours=8)
        rows = calendar.monthrange(year, month_number)[1] * 96
        skipped = skip_indices or set()
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(("open_time", "open", "high", "low", "close", "volume", "amount", "close_time"))
            for index in range(rows):
                if index in skipped:
                    continue
                open_ms = int((start + timedelta(minutes=15 * index)).timestamp() * 1000)
                writer.writerow((open_ms, "100", "101", "99", "100", "10", "1000", open_ms + 900000))

    def test_observed_vendor_month_partition_is_frozen_to_utc_plus_8(self):
        start, next_start = _source_partition_bounds("2023-02")
        self.assertEqual(MEXC_BULK_MONTH_PARTITION_OFFSET_HOURS, 8)
        self.assertEqual(MEXC_BULK_MONTH_PARTITION_TIMEZONE, "UTC+08:00")
        self.assertEqual(start, datetime(2023, 1, 31, 16, 0, tzinfo=timezone.utc))
        self.assertEqual(next_start, datetime(2023, 2, 28, 16, 0, tzinfo=timezone.utc))

    def test_complete_month_passes_without_p00_network_or_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            source = raw / "BTC_USDT-Min15-2023-02-01.csv"
            self._write_month(source, "2023-02")
            result = build_discovery_corpus(raw, root / "out", symbol="BTCUSDT", start_month="2023-02", end_month="2023-02")

        self.assertEqual(result.status, "PASS_CORPUS_AUDIT_ONLY")
        self.assertEqual(result.expected_month_count, 1)
        self.assertEqual(result.passed_month_count, 1)
        self.assertEqual(result.total_row_count, 2688)
        self.assertEqual(result.months_with_gaps_count, 0)
        self.assertEqual(result.total_detected_gap_count, 0)
        self.assertEqual(result.total_missing_candle_count, 0)
        self.assertEqual(result.gap_handling, "REPORT_AND_SPLIT_LATER_NEVER_INTERPOLATE")
        self.assertEqual(result.source_partition_timezone, "UTC+08:00")
        self.assertTrue(result.utc_discovery_boundary_reconciliation_required)
        self.assertFalse(result.p00_evaluation_performed)
        self.assertFalse(result.network_access_performed)
        self.assertFalse(result.exchange_mutation_performed)
        month = result.months[0]
        self.assertEqual(month.status, "PASS_MONTH")
        self.assertEqual(month.row_count, 2688)
        self.assertTrue(month.first_open_time_match)
        self.assertTrue(month.last_open_time_match)
        self.assertEqual(month.detected_gap_count, 0)
        self.assertEqual(month.missing_candle_count, 0)

    def test_missing_expected_month_blocks_before_outputs_are_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            result = build_discovery_corpus(root / "raw", out, symbol="BTCUSDT", start_month="2023-02", end_month="2023-03")
            self.assertEqual(result.status, "BLOCKED_CORPUS")
            self.assertTrue(any(reason.startswith("MISSING_EXPECTED_MONTH:") for reason in result.reasons))
            self.assertFalse((out / "canonical").exists())
            self.assertTrue(result.utc_discovery_boundary_reconciliation_required)

    def test_2025_is_blocked_before_market_files_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_discovery_corpus(Path(tmp) / "missing", Path(tmp) / "out", symbol="BTCUSDT", start_month="2025-01", end_month="2025-01")
        self.assertEqual(result.status, "BLOCKED_CORPUS")
        self.assertIn("CORPUS_RANGE_OUTSIDE_FROZEN_DISCOVERY", result.reasons)
        self.assertEqual(result.months, ())

    def test_valid_exact_multiple_gap_passes_and_continues_without_interpolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            self._write_month(
                raw / "BTC_USDT-Min15-2023-02-01.csv",
                "2023-02",
                skip_indices={100, 101},
            )
            self._write_month(raw / "BTC_USDT-Min15-2023-03-01.csv", "2023-03")
            result = build_discovery_corpus(raw, root / "out", symbol="BTCUSDT", start_month="2023-02", end_month="2023-03")

        self.assertEqual(result.status, "PASS_CORPUS_AUDIT_ONLY_WITH_GAPS")
        self.assertEqual(result.expected_month_count, 2)
        self.assertEqual(result.passed_month_count, 2)
        self.assertEqual(len(result.months), 2)
        self.assertEqual(result.months_with_gaps_count, 1)
        self.assertEqual(result.total_detected_gap_count, 1)
        self.assertEqual(result.total_missing_candle_count, 2)
        self.assertEqual(result.gap_handling, "REPORT_AND_SPLIT_LATER_NEVER_INTERPOLATE")

        first = result.months[0]
        self.assertEqual(first.status, "PASS_MONTH_WITH_GAPS")
        self.assertEqual(first.row_count, 2686)
        self.assertEqual(first.expected_row_count, 2688)
        self.assertEqual(first.detected_gap_count, 1)
        self.assertEqual(first.missing_candle_count, 2)
        self.assertTrue(first.first_open_time_match)
        self.assertTrue(first.last_open_time_match)
        self.assertEqual(first.reasons, ())

        second = result.months[1]
        self.assertEqual(second.status, "PASS_MONTH")
        self.assertEqual(second.row_count, 2976)
        self.assertEqual(second.detected_gap_count, 0)
        self.assertEqual(second.missing_candle_count, 0)

        self.assertEqual(result.total_row_count, 2686 + 2976)
        self.assertFalse(result.p00_evaluation_performed)
        self.assertFalse(result.network_access_performed)
        self.assertFalse(result.exchange_mutation_performed)

    def test_source_has_no_evaluator_or_network_wiring(self):
        text = SOURCE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "phase_b_research_evaluator_v01",
            "derive_signal_geometries",
            "simulate_outcome",
            "import requests",
            "import urllib",
            "import websockets",
            "import socket",
            "api.mexc.com",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("utc_discovery_boundary_reconciliation_required", text)
        self.assertIn("utc+08:00", text)
        self.assertIn("report_and_split_later_never_interpolate", text)
        self.assertIn("pass_with_gaps_adapter_bound_audit", text)

    def test_windows_launcher_has_import_path_and_no_network_or_p00_evaluator(self):
        text = LAUNCHER.read_text(encoding="utf-8").lower()
        self.assertIn('set "pythonpath=%project_root%\\src;%project_root%;%pythonpath%"', text)
        self.assertIn("research.phase_b_mexc_discovery_corpus_v01", text)
        self.assertNotIn("phase_b_research_evaluator_v01", text)
        self.assertNotIn("api.mexc.com", text)
        self.assertNotIn("invoke-webrequest", text)
        self.assertGreaterEqual(text.count("no p00 evaluation was run"), 2)


if __name__ == "__main__":
    unittest.main()
