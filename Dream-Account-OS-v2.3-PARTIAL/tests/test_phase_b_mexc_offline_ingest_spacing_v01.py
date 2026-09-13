import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research.phase_b_mexc_offline_ingest_v01 import (
    CANONICAL_SCHEMA,
    IDENTITY_ADAPTER,
    SIDECAR_SCHEMA,
    TIMEFRAME_MS,
    audit_canonical_dataset,
)


START_2023_MS = 1672531200000
ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research" / "PHASE_B_OFFLINE_DATA_INGEST_FREEZE_V0.1.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _row(open_time: int):
    return (open_time, 100.0, 101.0, 99.0, 100.5, 10.0, open_time + TIMEFRAME_MS - 1)


def _write_csv(path: Path, rows) -> None:
    header = "open_time_ms,open,high,low,close,volume,close_time_ms\n"
    body = "".join(",".join(str(value) for value in row) + "\n" for row in rows)
    path.write_text(header + body, encoding="utf-8")


def _write_sidecar(path: Path, data_file: Path) -> None:
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
        "raw_source_sha256": _sha256(data_file),
        "canonical_schema": CANONICAL_SCHEMA,
        "adapter_id": IDENTITY_ADAPTER,
    }
    path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")


class PhaseBMEXCOfflineSpacingTests(unittest.TestCase):
    def test_twenty_minute_jump_is_irregular_not_valid_gap_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "irregular.csv"
            _write_csv(data, [_row(START_2023_MS), _row(START_2023_MS + 20 * 60 * 1000)])
            sidecar = root / "irregular.json"
            _write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)

        self.assertEqual(package.manifest.status, "BLOCKED_DATA_INTEGRITY")
        self.assertIn("IRREGULAR_INTERVAL_SPACING", package.manifest.reasons)
        self.assertEqual(package.manifest.irregular_interval_count, 1)
        self.assertEqual(package.manifest.detected_gap_count, 0)
        self.assertEqual(package.manifest.missing_candle_count, 0)
        self.assertEqual(package.candles, ())

    def test_exact_multiple_of_15_minutes_remains_a_reported_gap_not_irregular(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "gap.csv"
            _write_csv(data, [_row(START_2023_MS), _row(START_2023_MS + 45 * 60 * 1000)])
            sidecar = root / "gap.json"
            _write_sidecar(sidecar, data)
            package = audit_canonical_dataset(sidecar, data)

        self.assertEqual(package.manifest.status, "PASS_WITH_GAPS")
        self.assertEqual(package.manifest.irregular_interval_count, 0)
        self.assertEqual(package.manifest.detected_gap_count, 1)
        self.assertEqual(package.manifest.missing_candle_count, 2)
        self.assertEqual(len(package.candles), 2)

    def test_contract_explicitly_forbids_irregular_spacing(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        audit = contract["integrity_audit"]
        self.assertFalse(audit["irregular_interval_spacing_allowed"])
        self.assertIn("IRREGULAR_INTERVAL_SPACING", audit["irregular_interval_action"])
        self.assertIn("exactly divisible", audit["valid_gap_definition"])


if __name__ == "__main__":
    unittest.main()
