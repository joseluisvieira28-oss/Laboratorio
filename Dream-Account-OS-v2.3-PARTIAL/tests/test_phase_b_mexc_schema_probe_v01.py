import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from research.phase_b_mexc_schema_probe_v01 import (
    EXPECTED_HEADER,
    MAX_HEADER_LINE_BYTES,
    probe_raw_schema,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research" / "PHASE_B_OFFLINE_DATA_INGEST_FREEZE_V0.1.json"
SOURCE = ROOT / "research" / "phase_b_mexc_schema_probe_v01.py"


class PhaseBMEXCRawSchemaProbeTests(unittest.TestCase):
    def test_canonical_csv_reports_structure_but_not_market_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            path.write_text(
                ",".join(EXPECTED_HEADER) + "\n"
                + "1672531200000,100,101,99,100.5,10,1672532099999\n",
                encoding="utf-8",
            )
            result = probe_raw_schema(path)

        self.assertEqual(result.status, "PASS_STRUCTURE_ONLY")
        self.assertEqual(result.header_fields, EXPECTED_HEADER)
        self.assertEqual(result.first_data_field_count, 7)
        self.assertTrue(result.canonical_header_match)
        self.assertFalse(result.market_values_returned)
        self.assertFalse(result.p00_evaluation_performed)
        self.assertFalse(result.network_access_performed)
        rendered = json.dumps(result.__dict__, default=str)
        self.assertNotIn("100.5", rendered)
        self.assertNotIn("1672531200000", rendered)

    def test_unknown_csv_header_is_visible_without_data_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.csv"
            path.write_text("time,o,h,l,c,v,end,quote\n1,2,3,4,5,6,7,8\n", encoding="utf-8")
            result = probe_raw_schema(path)

        self.assertEqual(result.status, "PASS_STRUCTURE_ONLY")
        self.assertEqual(result.header_fields, ("time", "o", "h", "l", "c", "v", "end", "quote"))
        self.assertEqual(result.first_data_field_count, 8)
        self.assertFalse(result.canonical_header_match)
        self.assertFalse(result.market_values_returned)

    def test_json_probe_reports_only_top_level_array_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "klines.json"
            path.write_text('[[1672531200000,"100","101","99","100.5","10",1672532100000,"1000"]]', encoding="utf-8")
            result = probe_raw_schema(path)

        self.assertEqual(result.status, "PASS_STRUCTURE_ONLY")
        self.assertEqual(result.json_top_level_shape, "ARRAY")
        self.assertEqual(result.header_fields, ())
        self.assertFalse(result.market_values_returned)

    def test_safe_zip_probes_csv_header_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mexc.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("BTCUSDT/raw.csv", "a,b,c,d\n111,222,333,444\n")
            result = probe_raw_schema(path)

        self.assertEqual(result.status, "PASS_STRUCTURE_ONLY")
        self.assertEqual(result.zip_entry_count, 1)
        self.assertEqual(len(result.zip_text_entries_probed), 1)
        entry = result.zip_text_entries_probed[0]
        self.assertEqual(entry.header_fields, ("a", "b", "c", "d"))
        self.assertEqual(entry.first_data_field_count, 4)
        self.assertIsNone(entry.reason)
        rendered = json.dumps(result, default=lambda item: item.__dict__)
        self.assertNotIn("111", rendered)
        self.assertNotIn("222", rendered)

    def test_zip_path_traversal_blocks_entire_schema_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unsafe.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("../escape.csv", "a,b\n1,2\n")
            result = probe_raw_schema(path)

        self.assertEqual(result.status, "BLOCKED_SCHEMA_PROBE")
        self.assertIn("ZIP_PATH_TRAVERSAL_ENTRY", result.blocked_reasons)

    def test_overlong_csv_header_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "huge.csv"
            path.write_bytes(b"x" * (MAX_HEADER_LINE_BYTES + 1) + b"\n1\n")
            result = probe_raw_schema(path)

        self.assertEqual(result.status, "BLOCKED_SCHEMA_PROBE")
        self.assertIn("HEADER_LINE_TOO_LARGE", result.blocked_reasons)

    def test_unsupported_file_suffix_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.bin"
            path.write_bytes(b"abc")
            result = probe_raw_schema(path)

        self.assertEqual(result.status, "BLOCKED_SCHEMA_PROBE")
        self.assertIn("UNSUPPORTED_SCHEMA_PROBE_SUFFIX", result.blocked_reasons)

    def test_missing_file_blocks_without_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = probe_raw_schema(Path(tmp) / "missing.csv")

        self.assertEqual(result.status, "BLOCKED_SCHEMA_PROBE")
        self.assertIn("SOURCE_FILE_NOT_FOUND", result.blocked_reasons)
        self.assertIsNone(result.sha256)

    def test_probe_fingerprint_is_deterministic_and_file_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stable.csv"
            path.write_text("a,b\n1,2\n", encoding="utf-8")
            first = probe_raw_schema(path)
            second = probe_raw_schema(path)
            path.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
            changed = probe_raw_schema(path)

        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertNotEqual(first.fingerprint, changed.fingerprint)
        self.assertNotEqual(first.sha256, changed.sha256)

    def test_contract_allows_only_structure_probe_and_forbids_market_values(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        probe = contract["schema_probe"]
        self.assertEqual(probe["status"], "AUTHORIZED_STRUCTURE_ONLY_BEFORE_ADAPTER_FREEZE")
        self.assertTrue(probe["plain_csv_header_probe_allowed"])
        self.assertTrue(probe["zip_text_entry_header_probe_allowed"])
        self.assertFalse(probe["plain_csv_first_data_row_values_may_be_returned"])
        self.assertFalse(probe["zip_text_entry_market_values_may_be_returned"])
        self.assertFalse(probe["json_market_values_may_be_returned"])
        self.assertFalse(probe["adapter_activation_from_probe_alone"])
        self.assertFalse(probe["p00_evaluation_allowed"])

    def test_probe_source_has_no_network_or_evaluator_wiring(self):
        text = SOURCE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            "import socket",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "phase_b_research_evaluator_v01",
            "derive_signal_geometries",
            "simulate_outcome",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
