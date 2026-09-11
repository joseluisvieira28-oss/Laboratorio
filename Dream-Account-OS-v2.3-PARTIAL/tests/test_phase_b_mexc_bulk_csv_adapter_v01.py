import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research.phase_b_mexc_bulk_csv_adapter_v01 import (
    ADAPTER_ID,
    RAW_HEADER,
    REFERENCE_SAMPLE_SHA256,
    REFERENCE_SEMANTIC_PROBE_FINGERPRINT,
    REFERENCE_STRUCTURE_PROBE_FINGERPRINT,
    adapt_mexc_bulk_csv,
    mapping_fingerprint,
)
from research.phase_b_mexc_offline_ingest_v01 import EXPECTED_HEADER, TIMEFRAME_MS


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research" / "PHASE_B_MEXC_RAW_ADAPTER_FREEZE_V0.1.json"
SOURCE = ROOT / "research" / "phase_b_mexc_bulk_csv_adapter_v01.py"
START_MS = 1675209600000  # 2023-02-01T00:00:00Z; synthetic tests only.


def raw_row(index=0, *, start=START_MS, amount="1000", close_delta=TIMEFRAME_MS):
    open_time = start + index * TIMEFRAME_MS
    return (
        str(open_time),
        "100",
        "101",
        "99",
        "100.5",
        "10",
        str(amount),
        str(open_time + close_delta),
    )


def raw_text(rows, header=RAW_HEADER):
    lines = [",".join(header)]
    lines.extend(",".join(row) for row in rows)
    return "\n".join(lines) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PhaseBMEXCBulkCsvAdapterTests(unittest.TestCase):
    def test_frozen_reference_evidence_matches_real_probe_receipts(self):
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        sample = freeze["reference_sample"]
        self.assertEqual(freeze["adapter_id"], ADAPTER_ID)
        self.assertEqual(sample["raw_source_sha256"], REFERENCE_SAMPLE_SHA256)
        self.assertEqual(sample["structure_probe_fingerprint"], REFERENCE_STRUCTURE_PROBE_FINGERPRINT)
        self.assertEqual(sample["semantic_probe_fingerprint"], REFERENCE_SEMANTIC_PROBE_FINGERPRINT)
        self.assertEqual(freeze["raw_schema"]["header_exact"], list(RAW_HEADER))
        self.assertEqual(freeze["canonical_mapping"]["target_header"], list(EXPECTED_HEADER))
        self.assertFalse(freeze["raw_schema"]["amount_semantics_authorized"])

    def test_valid_raw_rows_map_to_canonical_without_amount(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "raw.csv"
            canonical = root / "canonical.csv"
            source.write_text(raw_text([raw_row(0), raw_row(1)]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
            with canonical.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))

        self.assertEqual(receipt.status, "PASS_ADAPTER_ONLY")
        self.assertEqual(receipt.raw_row_count, 2)
        self.assertEqual(tuple(rows[0]), EXPECTED_HEADER)
        self.assertEqual(len(rows[1]), 7)
        self.assertEqual(rows[1][0], str(START_MS))
        self.assertEqual(rows[1][1:6], ["100", "101", "99", "100.5", "10"])
        self.assertEqual(rows[1][6], str(START_MS + TIMEFRAME_MS - 1))
        self.assertNotIn("1000", rows[1])
        self.assertTrue(receipt.amount_field_ignored)
        self.assertFalse(receipt.amount_semantics_authorized)
        self.assertFalse(receipt.market_values_returned_in_receipt)
        self.assertFalse(receipt.p00_evaluation_performed)
        self.assertFalse(receipt.network_access_performed)
        self.assertFalse(receipt.exchange_mutation_performed)

    def test_exact_multiple_gap_is_preserved_not_interpolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "gap.csv"
            canonical = root / "canonical.csv"
            source.write_text(raw_text([raw_row(0), raw_row(2)]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
            with canonical.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
        self.assertEqual(receipt.status, "PASS_ADAPTER_ONLY")
        self.assertEqual(len(rows), 3)
        self.assertEqual(int(rows[2][0]) - int(rows[1][0]), 2 * TIMEFRAME_MS)

    def test_raw_header_mismatch_blocks_without_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "bad.csv"
            canonical = root / "canonical.csv"
            source.write_text(raw_text([raw_row(0)], header=("time",) + RAW_HEADER[1:]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
        self.assertEqual(receipt.status, "BLOCKED_ADAPTER")
        self.assertIn("RAW_HEADER_MISMATCH", receipt.blocked_reasons)
        self.assertFalse(canonical.exists())

    def test_timestamp_seconds_or_other_width_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "seconds.csv"
            canonical = root / "canonical.csv"
            bad = list(raw_row(0))
            bad[0] = "1675209600"
            bad[7] = "1675210500"
            source.write_text(raw_text([tuple(bad)]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
        self.assertIn("TIMESTAMP_NOT_13_DIGIT_MILLISECONDS", receipt.blocked_reasons)
        self.assertFalse(canonical.exists())

    def test_raw_close_time_relation_must_be_open_plus_900000(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "close.csv"
            canonical = root / "canonical.csv"
            source.write_text(raw_text([raw_row(0, close_delta=TIMEFRAME_MS - 1)]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
        self.assertIn("RAW_CLOSE_TIME_RELATION_MISMATCH", receipt.blocked_reasons)
        self.assertFalse(canonical.exists())

    def test_irregular_20_minute_spacing_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "irregular.csv"
            canonical = root / "canonical.csv"
            second_start = START_MS + 20 * 60 * 1000
            source.write_text(raw_text([raw_row(0), raw_row(0, start=second_start)]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
        self.assertIn("IRREGULAR_OPEN_TIME_SPACING", receipt.blocked_reasons)
        self.assertFalse(canonical.exists())

    def test_duplicate_or_reversed_open_time_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "order.csv"
            canonical = root / "canonical.csv"
            source.write_text(raw_text([raw_row(1), raw_row(0)]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
        self.assertIn("OPEN_TIME_NOT_STRICTLY_INCREASING", receipt.blocked_reasons)
        self.assertFalse(canonical.exists())

    def test_amount_must_parse_but_is_never_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "amount.csv"
            canonical = root / "canonical.csv"
            source.write_text(raw_text([raw_row(0, amount="not-a-number")]), encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
        self.assertIn("NONFINITE_OR_NONNUMERIC_MARKET_FIELD", receipt.blocked_reasons)
        self.assertFalse(canonical.exists())

    def test_blocked_source_never_overwrites_existing_canonical_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "bad.csv"
            canonical = root / "canonical.csv"
            canonical.write_text("KEEP_ME\n", encoding="utf-8")
            source.write_text("bad,header\n1,2\n", encoding="utf-8")
            receipt = adapt_mexc_bulk_csv(source, canonical)
            retained = canonical.read_text(encoding="utf-8")
        self.assertEqual(receipt.status, "BLOCKED_ADAPTER")
        self.assertEqual(retained, "KEEP_ME\n")

    def test_same_input_produces_same_canonical_sha_and_receipt_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "stable.csv"
            first = root / "first.csv"
            second = root / "second.csv"
            source.write_text(raw_text([raw_row(0), raw_row(1)]), encoding="utf-8")
            a = adapt_mexc_bulk_csv(source, first)
            b = adapt_mexc_bulk_csv(source, second)
            first_hash = sha256(first)
            second_hash = sha256(second)

        self.assertEqual(a.canonical_sha256, b.canonical_sha256)
        self.assertEqual(first_hash, second_hash)
        # File name is deliberately part of the receipt, so full receipt fingerprints differ.
        self.assertNotEqual(a.fingerprint, b.fingerprint)
        self.assertEqual(a.mapping_fingerprint, b.mapping_fingerprint)
        self.assertEqual(a.mapping_fingerprint, mapping_fingerprint())

    def test_adapter_source_has_no_network_or_p00_wiring(self):
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
