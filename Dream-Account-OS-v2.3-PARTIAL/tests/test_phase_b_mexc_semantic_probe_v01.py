import json
from pathlib import Path
import tempfile
import unittest

from research.phase_b_mexc_semantic_probe_v01 import RAW_HEADER, probe_raw_semantics


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "phase_b_mexc_semantic_probe_v01.py"
LAUNCHER = ROOT / "research" / "probe_phase_b_mexc_semantics_windows.bat"


class PhaseBMEXCSemanticProbeTests(unittest.TestCase):
    def _write_sample(self, path: Path, unit: str = "ms", close_offset_ms: int = 899_999):
        base_ms = 1675209600000
        rows = []
        for index in range(4):
            open_ms = base_ms + index * 900_000
            close_ms = open_ms + close_offset_ms
            if unit == "s":
                open_raw = str(open_ms // 1000)
                close_raw = str(close_ms // 1000)
            else:
                open_raw = str(open_ms)
                close_raw = str(close_ms)
            rows.append(
                [open_raw, "100", "101", "99", "100.5", "10", "1005", close_raw]
            )
        text = ",".join(RAW_HEADER) + "\n" + "\n".join(",".join(row) for row in rows) + "\n"
        path.write_text(text, encoding="utf-8")

    def test_millisecond_sample_reports_only_redacted_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.csv"
            self._write_sample(path)
            result = probe_raw_semantics(path)

        self.assertEqual(result.status, "PASS_REDACTED_SEMANTICS")
        self.assertTrue(result.header_match)
        self.assertEqual(result.timestamp_unit_candidate, "MILLISECONDS")
        self.assertEqual(result.open_time_spacing_candidate_ms, 900_000)
        self.assertTrue(result.open_time_spacing_is_exact_15m)
        self.assertEqual(result.close_time_relation_candidate, "OPEN_PLUS_899999_MS")
        self.assertTrue(result.close_time_relation_consistent)
        self.assertTrue(result.numeric_market_columns_parseable)
        self.assertFalse(result.amount_semantics_authorized)
        self.assertFalse(result.market_values_returned)
        self.assertFalse(result.p00_evaluation_performed)
        self.assertFalse(result.network_access_performed)
        rendered = json.dumps(result.__dict__, sort_keys=True)
        for forbidden_value in ("100.5", "101", "1005", "1675209600000"):
            self.assertNotIn(forbidden_value, rendered)

    def test_second_epoch_sample_is_normalized_for_spacing_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.csv"
            base_s = 1675209600
            rows = []
            for index in range(4):
                open_s = base_s + index * 900
                close_s = open_s + 900
                rows.append([str(open_s), "1", "2", "0.5", "1.5", "3", "4", str(close_s)])
            path.write_text(
                ",".join(RAW_HEADER) + "\n" + "\n".join(",".join(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = probe_raw_semantics(path)

        self.assertEqual(result.status, "PASS_REDACTED_SEMANTICS")
        self.assertEqual(result.timestamp_unit_candidate, "SECONDS")
        self.assertEqual(result.open_time_spacing_candidate_ms, 900_000)
        self.assertEqual(result.close_time_relation_candidate, "OPEN_PLUS_900000_MS")

    def test_irregular_spacing_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.csv"
            path.write_text(
                ",".join(RAW_HEADER) + "\n"
                "1675209600000,1,2,0.5,1.5,3,4,1675210499999\n"
                "1675210800000,1,2,0.5,1.5,3,4,1675211699999\n",
                encoding="utf-8",
            )
            result = probe_raw_semantics(path)

        self.assertEqual(result.status, "BLOCKED_SEMANTIC_PROBE")
        self.assertIn("OPEN_TIME_SPACING_NOT_EXACT_15M", result.blocked_reasons)

    def test_wrong_header_blocks_before_interpretation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.csv"
            path.write_text("time,open,high,low,close,volume,amount,close_time\n1,2,3,4,5,6,7,8\n", encoding="utf-8")
            result = probe_raw_semantics(path)

        self.assertEqual(result.status, "BLOCKED_SEMANTIC_PROBE")
        self.assertIn("RAW_HEADER_MISMATCH", result.blocked_reasons)
        self.assertEqual(result.rows_inspected, 0)

    def test_non_numeric_market_field_blocks_without_returning_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.csv"
            path.write_text(
                ",".join(RAW_HEADER) + "\n"
                "1675209600000,SECRET,2,0.5,1.5,3,4,1675210499999\n"
                "1675210500000,1,2,0.5,1.5,3,4,1675211399999\n",
                encoding="utf-8",
            )
            result = probe_raw_semantics(path)

        self.assertEqual(result.status, "BLOCKED_SEMANTIC_PROBE")
        self.assertIn("MARKET_NUMERIC_PARSE_FAILURE", result.blocked_reasons)
        self.assertNotIn("SECRET", json.dumps(result.__dict__, sort_keys=True))

    def test_probe_and_windows_launcher_have_no_network_or_p00_wiring(self):
        source = SOURCE.read_text(encoding="utf-8").lower()
        launcher = LAUNCHER.read_text(encoding="utf-8").lower()
        combined = source + "\n" + launcher
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            "import socket",
            "invoke-webrequest",
            "curl ",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "phase_b_research_evaluator_v01",
            "simulate_outcome",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn("latest_semantic_probe.json", launcher)


if __name__ == "__main__":
    unittest.main()
