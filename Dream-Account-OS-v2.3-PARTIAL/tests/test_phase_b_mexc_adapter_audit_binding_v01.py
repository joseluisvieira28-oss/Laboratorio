import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research.phase_b_mexc_adapter_audit_binding_v01 import audit_adapter_bound_dataset
from research.phase_b_mexc_bulk_csv_adapter_v01 import RAW_HEADER, adapt_mexc_bulk_csv, write_receipt


START_2023_MS = 1672531200000
TIMEFRAME_MS = 900000


def raw_csv(rows):
    lines = [",".join(RAW_HEADER)]
    lines.extend(",".join(str(value) for value in row) for row in rows)
    return "\n".join(lines) + "\n"


def raw_row(index, *, open_=100.0, high=101.0, low=99.0, close=100.5, volume=10.0, amount=1000.0):
    open_time = START_2023_MS + index * TIMEFRAME_MS
    return (open_time, open_, high, low, close, volume, amount, open_time + TIMEFRAME_MS)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def resign_receipt(receipt):
    payload = dict(receipt)
    payload.pop("fingerprint", None)
    receipt["fingerprint"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return receipt


def prepare(root: Path, rows):
    raw = root / "BTC_USDT-Min15-2023-02-01.csv"
    canonical = root / "BTC_USDT-Min15-2023-02-01.canonical.csv"
    receipt_path = root / "adapter_receipt.json"
    raw.write_text(raw_csv(rows), encoding="utf-8")
    receipt = adapt_mexc_bulk_csv(raw, canonical)
    write_receipt(receipt_path, receipt)
    return raw, canonical, receipt_path


def audit(raw, canonical, receipt_path, **changes):
    kwargs = {
        "symbol": "BTCUSDT",
        "declared_start_utc": "2023-01-01T00:00:00Z",
        "declared_end_utc": "2023-12-31T23:59:59.999Z",
    }
    kwargs.update(changes)
    return audit_adapter_bound_dataset(raw, canonical, receipt_path, **kwargs)


class PhaseBMEXCAdapterAuditBindingTests(unittest.TestCase):
    def test_valid_adapter_receipt_binds_to_unchanged_base_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, canonical, receipt_path = prepare(Path(tmp), [raw_row(i) for i in range(4)])
            package = audit(raw, canonical, receipt_path)
        self.assertEqual(package.manifest.status, "PASS_ADAPTER_BOUND_AUDIT")
        self.assertEqual(package.manifest.base_audit_status, "PASS")
        self.assertEqual(package.manifest.row_count, 4)
        self.assertEqual(package.manifest.returned_candle_count, 4)
        self.assertEqual(len(package.candles), 4)
        self.assertFalse(package.manifest.p00_evaluation_performed)
        self.assertFalse(package.manifest.network_access_performed)
        self.assertFalse(package.manifest.exchange_mutation_performed)

    def test_exact_15m_gap_is_preserved_through_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, canonical, receipt_path = prepare(Path(tmp), [raw_row(0), raw_row(1), raw_row(3)])
            package = audit(raw, canonical, receipt_path)
        self.assertEqual(package.manifest.status, "PASS_WITH_GAPS_ADAPTER_BOUND_AUDIT")
        self.assertEqual(package.manifest.base_audit_status, "PASS_WITH_GAPS")
        self.assertEqual(package.manifest.detected_gap_count, 1)
        self.assertEqual(package.manifest.missing_candle_count, 1)
        self.assertEqual(len(package.candles), 3)

    def test_tampered_raw_file_blocks_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, canonical, receipt_path = prepare(root, [raw_row(i) for i in range(2)])
            raw.write_text(raw.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            package = audit(raw, canonical, receipt_path)
        self.assertEqual(package.manifest.status, "BLOCKED_PROVENANCE")
        self.assertIn("RAW_SOURCE_SHA256_MISMATCH", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_tampered_canonical_file_blocks_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, canonical, receipt_path = prepare(root, [raw_row(i) for i in range(2)])
            canonical.write_text(canonical.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            package = audit(raw, canonical, receipt_path)
        self.assertEqual(package.manifest.status, "BLOCKED_PROVENANCE")
        self.assertIn("CANONICAL_SHA256_MISMATCH", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_tampered_receipt_fingerprint_blocks_before_market_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, canonical, receipt_path = prepare(root, [raw_row(0)])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["fingerprint"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            package = audit(raw, canonical, receipt_path)
        self.assertEqual(package.manifest.status, "BLOCKED_ADAPTER_RECEIPT")
        self.assertIn("ADAPTER_RECEIPT_FINGERPRINT_MISMATCH", package.manifest.reasons)

    def test_wrong_mapping_fingerprint_blocks_even_with_resigned_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, canonical, receipt_path = prepare(root, [raw_row(0)])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["mapping_fingerprint"] = "f" * 64
            receipt_path.write_text(json.dumps(resign_receipt(receipt)), encoding="utf-8")
            package = audit(raw, canonical, receipt_path)
        self.assertEqual(package.manifest.status, "BLOCKED_ADAPTER_RECEIPT")
        self.assertIn("ADAPTER_MAPPING_FINGERPRINT_MISMATCH", package.manifest.reasons)

    def test_amount_semantics_cannot_be_authorized_by_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, canonical, receipt_path = prepare(root, [raw_row(0)])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["amount_semantics_authorized"] = True
            receipt_path.write_text(json.dumps(resign_receipt(receipt)), encoding="utf-8")
            package = audit(raw, canonical, receipt_path)
        self.assertIn("AMOUNT_SEMANTICS_UNEXPECTEDLY_AUTHORIZED", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_receipt_claiming_p00_network_or_mutation_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, canonical, receipt_path = prepare(root, [raw_row(0)])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["p00_evaluation_performed"] = True
            receipt["network_access_performed"] = True
            receipt["exchange_mutation_performed"] = True
            receipt_path.write_text(json.dumps(resign_receipt(receipt)), encoding="utf-8")
            package = audit(raw, canonical, receipt_path)
        self.assertIn("ADAPTER_RECEIPT_CLAIMS_P00", package.manifest.reasons)
        self.assertIn("ADAPTER_RECEIPT_CLAIMS_NETWORK_ACCESS", package.manifest.reasons)
        self.assertIn("ADAPTER_RECEIPT_CLAIMS_EXCHANGE_MUTATION", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_2025_validation_blocks_before_missing_market_files_or_receipt_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = audit_adapter_bound_dataset(
                root / "missing_raw.csv",
                root / "missing_canonical.csv",
                root / "missing_receipt.json",
                symbol="BTCUSDT",
                stage="VALIDATION",
                declared_start_utc="2025-01-01T00:00:00Z",
                declared_end_utc="2025-12-31T23:59:59.999Z",
            )
        self.assertEqual(package.manifest.status, "BLOCKED_METADATA")
        self.assertIn("STAGE_NOT_UNLOCKED", package.manifest.reasons)
        self.assertIn("DECLARED_RANGE_OUTSIDE_DISCOVERY", package.manifest.reasons)
        self.assertNotIn("INVALID_ADAPTER_RECEIPT", package.manifest.reasons)

    def test_2026_holdout_blocks_before_missing_market_files_or_receipt_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = audit_adapter_bound_dataset(
                root / "missing_raw.csv",
                root / "missing_canonical.csv",
                root / "missing_receipt.json",
                symbol="BTCUSDT",
                stage="HOLDOUT",
                declared_start_utc="2026-01-01T00:00:00Z",
                declared_end_utc="2026-01-31T23:59:59.999Z",
            )
        self.assertEqual(package.manifest.status, "BLOCKED_METADATA")
        self.assertIn("STAGE_NOT_UNLOCKED", package.manifest.reasons)
        self.assertNotIn("INVALID_ADAPTER_RECEIPT", package.manifest.reasons)

    def test_base_audit_integrity_failure_blocks_bound_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, canonical, receipt_path = prepare(
                Path(tmp),
                [raw_row(0, open_=100.0, high=99.0, low=98.0, close=100.5)],
            )
            package = audit(raw, canonical, receipt_path)
        self.assertEqual(package.manifest.status, "BLOCKED_BASE_AUDIT")
        self.assertIn("BASE_AUDIT:OHLC_INTEGRITY_VIOLATIONS", package.manifest.reasons)
        self.assertEqual(package.candles, ())

    def test_manifest_fingerprint_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, canonical, receipt_path = prepare(root, [raw_row(i) for i in range(2)])
            one = audit(raw, canonical, receipt_path).manifest
            two = audit(raw, canonical, receipt_path).manifest
        self.assertEqual(one.fingerprint, two.fingerprint)


if __name__ == "__main__":
    unittest.main()
