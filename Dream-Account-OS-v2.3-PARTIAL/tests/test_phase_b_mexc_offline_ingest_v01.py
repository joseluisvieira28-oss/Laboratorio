import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from research.phase_b_mexc_offline_ingest_v01 import (
    CANONICAL_SCHEMA,
    EXPECTED_HEADER,
    IDENTITY_ADAPTER,
    SIDECAR_SCHEMA,
    TIMEFRAME_MS,
    audit_canonical_dataset,
    probe_raw_source,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research" / "PHASE_B_OFFLINE_DATA_INGEST_FREEZE_V0.1.json"
SOURCE = ROOT / "research" / "phase_b_mexc_offline_ingest_v01.py"
START_2023_MS = 1672531200000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_text(rows, header=EXPECTED_HEADER):
    lines = [",".join(header)]
    lines.extend(",".join(str(value) for value in row) for row in rows)
    return "\n".join(lines) + "\n"


def row(index, *, start=START_2023_MS, open_=100.0, high=101.0, low=99.0, close=100.5, volume=10.0):
    open_time = start + index * TIMEFRAME_MS
    return (open_time, open_, high, low, close, volume, open_time + TIMEFRAME_MS - 1)


def write_sidecar(path: Path, data_file: Path, **changes):
    metadata = {
        "schema_version": SIDECAR_SCHEMA,
        "source_exchange": "MEXC",
        "market_type": "SPOT",
        "source_authority": "OFFICIAL_MEXC_SOURCE_ONLY",
        "stage": "DISCOVERY",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "declared_start_utc": "2023-01-01T00:00:00Z",
        "declared_end_utc": "2023-12-31T23:59:59.999Z",
        "raw_source_filename": data_file.name,
        "raw_source_sha256": sha256(data_file) if data_file.exists() else "0" * 64,
        "canonical_schema": CANONICAL_SCHEMA,
        "adapter_id": IDENTITY_ADAPTER,
    }
    metadata.update(changes)
    path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    return metadata


class PhaseBMEXCOfflineIngestTests(unittest.TestCase):
    def test_valid_canonical_discovery_csv_passes_and_returns_closed_candles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "btc.csv"
            data.write_text(csv_text([row(i) for i in range(4)]), encoding="utf-8")
            sidecar = root / "btc.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertEqual(package.manifest.status, "PASS")
        self.assertEqual(package.manifest.row_count, 4)
        self.assertEqual(package.manifest.returned_candle_count, 4)
        self.assertEqual(len(package.candles), 4)
        self.assertTrue(all(candle.closed for candle in package.candles))
        self.assertFalse(package.manifest.p00_evaluation_performed)
        self.assertFalse(package.manifest.network_access_performed)
        self.assertFalse(package.manifest.exchange_mutation_performed)

    def test_gap_is_reported_without_interpolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "gap.csv"
            data.write_text(csv_text([row(0), row(1), row(3)]), encoding="utf-8")
            sidecar = root / "gap.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertEqual(package.manifest.status, "PASS_WITH_GAPS")
        self.assertEqual(package.manifest.detected_gap_count, 1)
        self.assertEqual(package.manifest.missing_candle_count, 1)
        self.assertEqual(package.manifest.contiguous_segment_count, 2)
        self.assertEqual(len(package.candles), 3)

    def test_duplicate_timestamp_blocks_and_returns_no_candles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "dup.csv"
            data.write_text(csv_text([row(0), row(1), row(1)]), encoding="utf-8")
            sidecar = root / "dup.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertEqual(package.manifest.status, "BLOCKED_DATA_INTEGRITY")
        self.assertIn("DUPLICATE_OPEN_TIMES", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_out_of_order_timestamp_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "order.csv"
            data.write_text(csv_text([row(0), row(2), row(1)]), encoding="utf-8")
            sidecar = root / "order.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("OUT_OF_ORDER_ROWS", package.manifest.reasons)
        self.assertEqual(package.manifest.returned_candle_count, 0)

    def test_ohlc_violation_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "ohlc.csv"
            bad = row(0, open_=100.0, high=99.0, low=98.0, close=100.5)
            data.write_text(csv_text([bad]), encoding="utf-8")
            sidecar = root / "ohlc.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("OHLC_INTEGRITY_VIOLATIONS", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_negative_volume_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "volume.csv"
            data.write_text(csv_text([row(0, volume=-1.0)]), encoding="utf-8")
            sidecar = root / "volume.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("NEGATIVE_VOLUME", package.manifest.reasons)

    def test_non_finite_numeric_value_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "nan.csv"
            bad = list(row(0))
            bad[4] = "nan"
            data.write_text(csv_text([bad]), encoding="utf-8")
            sidecar = root / "nan.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("NON_FINITE_NUMERIC_VALUES", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_close_time_violation_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "close_time.csv"
            bad = list(row(0))
            bad[6] += 1
            data.write_text(csv_text([bad]), encoding="utf-8")
            sidecar = root / "close_time.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("CLOSE_TIME_VIOLATIONS", package.manifest.reasons)

    def test_open_time_alignment_violation_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "alignment.csv"
            bad = list(row(0))
            bad[0] += 1
            bad[6] += 1
            data.write_text(csv_text([bad]), encoding="utf-8")
            sidecar = root / "alignment.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("OPEN_TIME_ALIGNMENT_VIOLATIONS", package.manifest.reasons)

    def test_unknown_header_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "unknown.csv"
            data.write_text(csv_text([row(0)], header=("time", "o", "h", "l", "c", "v", "ct")), encoding="utf-8")
            sidecar = root / "unknown.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("UNKNOWN_OR_NONCANONICAL_CSV_SCHEMA", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_validation_stage_is_blocked_before_missing_market_file_is_opened(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "does_not_exist.csv"
            sidecar = root / "validation.json"
            write_sidecar(
                sidecar,
                missing,
                stage="VALIDATION",
                declared_start_utc="2025-01-01T00:00:00Z",
                declared_end_utc="2025-12-31T23:59:59.999Z",
            )
            package = audit_canonical_dataset(sidecar, missing)
        self.assertEqual(package.manifest.status, "BLOCKED_METADATA")
        self.assertIn("STAGE_NOT_UNLOCKED", package.manifest.reasons)
        self.assertIn("DECLARED_RANGE_OUTSIDE_DISCOVERY", package.manifest.reasons)
        self.assertNotIn("CANONICAL_OR_RAW_SOURCE_NOT_FOUND", package.manifest.reasons)

    def test_holdout_stage_is_blocked_before_missing_market_file_is_opened(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "holdout.csv"
            sidecar = root / "holdout.json"
            write_sidecar(
                sidecar,
                missing,
                stage="HOLDOUT",
                declared_start_utc="2026-01-01T00:00:00Z",
                declared_end_utc="2026-01-31T23:59:59.999Z",
            )
            package = audit_canonical_dataset(sidecar, missing)
        self.assertEqual(package.manifest.status, "BLOCKED_METADATA")
        self.assertIn("STAGE_NOT_UNLOCKED", package.manifest.reasons)
        self.assertNotIn("CANONICAL_OR_RAW_SOURCE_NOT_FOUND", package.manifest.reasons)

    def test_unknown_adapter_is_blocked_before_missing_market_file_is_opened(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "raw_mexc.csv"
            sidecar = root / "adapter.json"
            write_sidecar(sidecar, missing, adapter_id="MEXC_BULK_GUESSED_V99")
            package = audit_canonical_dataset(sidecar, missing)
        self.assertEqual(package.manifest.status, "BLOCKED_METADATA")
        self.assertIn("UNKNOWN_OR_UNFROZEN_ADAPTER", package.manifest.reasons)
        self.assertNotIn("CANONICAL_OR_RAW_SOURCE_NOT_FOUND", package.manifest.reasons)

    def test_symbol_outside_frozen_universe_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "ada.csv"
            sidecar = root / "ada.json"
            write_sidecar(sidecar, missing, symbol="ADAUSDT")
            package = audit_canonical_dataset(sidecar, missing)
        self.assertIn("SYMBOL_OUTSIDE_FROZEN_UNIVERSE", package.manifest.reasons)

    def test_timeframe_outside_frozen_universe_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "btc1m.csv"
            sidecar = root / "btc1m.json"
            write_sidecar(sidecar, missing, timeframe="1m")
            package = audit_canonical_dataset(sidecar, missing)
        self.assertIn("TIMEFRAME_OUTSIDE_FROZEN_UNIVERSE", package.manifest.reasons)

    def test_raw_source_hash_mismatch_blocks_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "hash.csv"
            data.write_text(csv_text([row(0)]), encoding="utf-8")
            sidecar = root / "hash.json"
            write_sidecar(sidecar, data, raw_source_sha256="f" * 64)
            package = audit_canonical_dataset(sidecar, data)
        self.assertEqual(package.manifest.status, "BLOCKED_PROVENANCE")
        self.assertIn("RAW_SOURCE_SHA256_MISMATCH", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_identity_adapter_refuses_different_raw_and_canonical_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw.csv"
            canonical = root / "canonical.csv"
            raw.write_text(csv_text([row(0)]), encoding="utf-8")
            canonical.write_text(csv_text([row(0), row(1)]), encoding="utf-8")
            sidecar = root / "identity.json"
            write_sidecar(sidecar, raw)
            package = audit_canonical_dataset(sidecar, canonical, raw_source_path=raw)
        self.assertIn("IDENTITY_ADAPTER_REQUIRES_IDENTICAL_RAW_AND_CANONICAL_FILE", package.manifest.reasons)

    def test_mislabeled_2025_timestamp_blocks_and_returns_no_market_candles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "mislabeled.csv"
            start_2025 = 1735689600000
            data.write_text(csv_text([row(0, start=start_2025)]), encoding="utf-8")
            sidecar = root / "mislabeled.json"
            write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)
        self.assertIn("FORBIDDEN_STAGE_TIMESTAMPS", package.manifest.reasons)
        self.assertEqual(package.manifest.stage_boundary_violation_count, 1)
        self.assertEqual(package.candles, ())

    def test_audit_fingerprint_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "stable.csv"
            data.write_text(csv_text([row(0), row(1)]), encoding="utf-8")
            sidecar = root / "stable.json"
            write_sidecar(sidecar, data)
            first = audit_canonical_dataset(sidecar, data).manifest
            second = audit_canonical_dataset(sidecar, data).manifest
        self.assertEqual(first.audit_fingerprint, second.audit_fingerprint)
        self.assertEqual(first, second)

    def test_file_change_changes_data_and_audit_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "change.csv"
            sidecar = root / "change.json"
            data.write_text(csv_text([row(0)]), encoding="utf-8")
            write_sidecar(sidecar, data)
            first = audit_canonical_dataset(sidecar, data).manifest
            data.write_text(csv_text([row(0), row(1)]), encoding="utf-8")
            write_sidecar(sidecar, data)
            second = audit_canonical_dataset(sidecar, data).manifest
        self.assertNotEqual(first.canonical_file_sha256, second.canonical_file_sha256)
        self.assertNotEqual(first.audit_fingerprint, second.audit_fingerprint)

    def test_safe_zip_probe_fingerprints_without_promoting_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "safe.zip"
            with ZipFile(archive, "w") as zf:
                zf.writestr("BTCUSDT/sample.csv", "untrusted raw layout")
            result = probe_raw_source(archive)
        self.assertEqual(result.status, "PASS_PROBE_ONLY")
        self.assertEqual(result.zip_entry_count, 1)
        self.assertEqual(result.zip_entries, ("BTCUSDT/sample.csv",))
        self.assertIsNotNone(result.sha256)

    def test_zip_path_traversal_blocks_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "unsafe.zip"
            with ZipFile(archive, "w") as zf:
                zf.writestr("../escape.csv", "x")
            result = probe_raw_source(archive)
        self.assertEqual(result.status, "BLOCKED_UNSAFE_ARCHIVE_PATH")
        self.assertIn("../escape.csv", result.unsafe_zip_entries)

    def test_missing_raw_source_probe_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = probe_raw_source(Path(tmp) / "missing.zip")
        self.assertEqual(result.status, "BLOCKED_SOURCE_NOT_FOUND")
        self.assertIsNone(result.sha256)

    def test_contract_freezes_stage_lock_no_interpolation_and_unknown_schema_block(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "FROZEN_BEFORE_FIRST_REAL_DATA_INGEST")
        self.assertEqual(data["stage_lock"]["currently_unlocked_stage"], "DISCOVERY")
        self.assertIn("PHYSICALLY_LOCKED", data["stage_lock"]["validation_2025_status"])
        self.assertIn("PHYSICALLY_LOCKED", data["stage_lock"]["holdout_2026_status"])
        self.assertFalse(data["source_policy"]["cross_exchange_backfill_allowed"])
        self.assertFalse(data["source_policy"]["interpolation_allowed"])
        self.assertEqual(data["source_policy"]["unknown_raw_schema_action"], "BLOCKED_UNKNOWN_SCHEMA")
        self.assertFalse(data["handoff_rule"]["p00_evaluator_wiring_in_this_release"])

    def test_contract_marks_mexc_2022_availability_unresolved_without_cross_exchange_rescue(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(data["mexc_2022_availability"]["status"], "UNRESOLVED")
        self.assertIn("Do not cross-exchange backfill", data["mexc_2022_availability"]["rule"])

    def test_ingest_source_has_no_network_or_p00_evaluator_wiring(self):
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
