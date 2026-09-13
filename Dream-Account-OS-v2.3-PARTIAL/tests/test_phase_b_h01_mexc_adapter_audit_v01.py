import calendar
import csv
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.phase_b_h01_mexc_adapter_audit_v01 import (
    PASS_STATUSES,
    audit_h01_month,
    source_partition_bounds,
)
from research.phase_b_h01_mexc_discovery_access_v01 import (
    AUTHORIZATION_DOCUMENT_TYPE,
    AUTHORIZATION_STATUS,
    DISCOVERY_END_MONTH,
    DISCOVERY_START_MONTH,
    FAMILY_ID,
    FROZEN_UNIVERSE,
    HYPOTHESIS_ID,
)
from research.phase_b_mexc_bulk_csv_adapter_v01 import (
    RAW_HEADER,
    adapt_mexc_bulk_csv,
    write_receipt,
)
from research.phase_b_mexc_offline_ingest_v01 import TIMEFRAME_MS


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "research" / "phase_b_h01_mexc_adapter_audit_v01.py"
P00_AUDITOR = ROOT / "research" / "phase_b_mexc_adapter_audit_binding_v01.py"
P00_CONTRACT = ROOT / "research" / "PHASE_B_MEXC_ADAPTER_AUDIT_BINDING_V0.1.json"


def canonical_hash(payload):
    clone = dict(payload)
    clone.pop("fingerprint", None)
    encoded = json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_authorization(path):
    payload = {
        "document_type": AUTHORIZATION_DOCUMENT_TYPE,
        "version": "0.1",
        "status": AUTHORIZATION_STATUS,
        "hypothesis_id": HYPOTHESIS_ID,
        "family_id": FAMILY_ID,
        "source": "OFFICIAL_MEXC_SPOT_HISTORICAL_ONLY",
        "timeframe": "15m",
        "source_partition_timezone": "UTC+08:00",
        "allowed_start_month": DISCOVERY_START_MONTH,
        "allowed_end_month": DISCOVERY_END_MONTH,
        "universe": list(FROZEN_UNIVERSE),
        "cross_exchange_backfill_allowed": False,
        "interpolation_allowed": False,
        "validation_2025_access_authorized": False,
        "holdout_2026_access_authorized": False,
        "network_download_authorized": False,
        "exchange_mutation_authorized": False,
        "live_trading_authorized": False,
        "fingerprint": "",
    }
    payload["fingerprint"] = canonical_hash(payload)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return payload


def write_raw_month(path, month, *, skip_indexes=()):
    start, end = source_partition_bounds(month)
    count = calendar.monthrange(int(month[:4]), int(month[5:7]))[1] * 96
    start_ms = int(start.timestamp() * 1000)
    assert start_ms + count * TIMEFRAME_MS == int(end.timestamp() * 1000)
    skipped = set(skip_indexes)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RAW_HEADER)
        for index in range(count):
            if index in skipped:
                continue
            open_time = start_ms + index * TIMEFRAME_MS
            writer.writerow((open_time, "100", "101", "99", "100.5", "10", "1000", open_time + TIMEFRAME_MS))


def adapt_fixture(root, month="2025-01", *, skip_indexes=()):
    raw = root / f"BTC_USDT-Min15-{month}-01.csv"
    canonical = root / f"BTC_USDT-Min15-{month}-01.canonical.csv"
    receipt_path = root / f"BTC_USDT-Min15-{month}-01.adapter.json"
    write_raw_month(raw, month, skip_indexes=skip_indexes)
    receipt = adapt_mexc_bulk_csv(raw, canonical)
    if receipt.status != "PASS_ADAPTER_ONLY":
        raise AssertionError(receipt)
    write_receipt(receipt_path, receipt)
    return raw, canonical, receipt_path


class PhaseBH01MEXCAdapterAuditTests(unittest.TestCase):
    def test_missing_authorization_blocks_before_market_bytes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = audit_h01_month(
                root / "missing-raw.csv",
                root / "missing-canonical.csv",
                root / "missing-receipt.json",
                symbol="BTCUSDT",
                month="2025-01",
                authorization_path=root / "missing-auth.json",
            )
            self.assertEqual(package.manifest.status, "BLOCKED_H01_MONTH_AUTHORIZATION")
            self.assertFalse(package.manifest.source_market_bytes_read)
            self.assertEqual(package.candles, ())

    def test_validation_month_blocks_before_market_bytes_even_with_valid_authorization(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            package = audit_h01_month(
                root / "BTC_USDT-Min15-2025-09-01.csv",
                root / "BTC_USDT-Min15-2025-09-01.canonical.csv",
                root / "receipt.json",
                symbol="BTCUSDT",
                month="2025-09",
                authorization_path=auth,
            )
            self.assertEqual(package.manifest.status, "BLOCKED_H01_MONTH_METADATA")
            self.assertFalse(package.manifest.source_market_bytes_read)
            self.assertEqual(package.candles, ())

    def test_complete_authorized_month_passes_exact_integrity_boundary(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            raw, canonical, receipt = adapt_fixture(root)
            package = audit_h01_month(
                raw, canonical, receipt,
                symbol="BTCUSDT", month="2025-01", authorization_path=auth,
            )
            manifest = package.manifest
            self.assertEqual(manifest.status, "PASS_H01_MONTH")
            self.assertIn(manifest.status, PASS_STATUSES)
            self.assertTrue(manifest.authorization_verified)
            self.assertTrue(manifest.source_market_bytes_read)
            self.assertTrue(manifest.first_open_time_match)
            self.assertTrue(manifest.last_open_time_match)
            self.assertEqual(manifest.row_count, 31 * 96)
            self.assertEqual(manifest.returned_candle_count, 31 * 96)
            self.assertEqual(manifest.detected_gap_count, 0)
            self.assertEqual(manifest.missing_candle_count, 0)
            self.assertFalse(manifest.validation_2025_market_bytes_read)
            self.assertFalse(manifest.holdout_2026_market_bytes_read)
            self.assertFalse(manifest.network_access_performed)
            self.assertFalse(manifest.exchange_mutation_performed)
            self.assertFalse(manifest.submitted_to_exchange)

    def test_exact_15m_gap_passes_with_gap_and_never_interpolates(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            raw, canonical, receipt = adapt_fixture(root, skip_indexes=(100,))
            package = audit_h01_month(
                raw, canonical, receipt,
                symbol="BTCUSDT", month="2025-01", authorization_path=auth,
            )
            manifest = package.manifest
            self.assertEqual(manifest.status, "PASS_H01_MONTH_WITH_GAPS")
            self.assertEqual(manifest.row_count, 31 * 96 - 1)
            self.assertEqual(manifest.returned_candle_count, 31 * 96 - 1)
            self.assertEqual(manifest.detected_gap_count, 1)
            self.assertEqual(manifest.missing_candle_count, 1)
            self.assertEqual(len(package.candles), 31 * 96 - 1)

    def test_tampered_canonical_is_blocked_by_adapter_provenance(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            raw, canonical, receipt = adapt_fixture(root)
            with canonical.open("a", encoding="utf-8") as handle:
                handle.write("\n")
            package = audit_h01_month(
                raw, canonical, receipt,
                symbol="BTCUSDT", month="2025-01", authorization_path=auth,
            )
            self.assertEqual(package.manifest.status, "BLOCKED_H01_PROVENANCE")
            self.assertIn("CANONICAL_PROVENANCE_MISMATCH", package.manifest.reasons)
            self.assertEqual(package.candles, ())

    def test_month_boundaries_match_existing_utc_plus_8_semantics(self):
        start, end = source_partition_bounds("2025-01")
        self.assertEqual(start.isoformat(), "2024-12-31T16:00:00+00:00")
        self.assertEqual(end.isoformat(), "2025-01-31T16:00:00+00:00")
        august_start, august_end = source_partition_bounds("2025-08")
        self.assertEqual(august_start.isoformat(), "2025-07-31T16:00:00+00:00")
        self.assertEqual(august_end.isoformat(), "2025-08-31T16:00:00+00:00")

    def test_p00_auditor_and_contract_remain_2024_locked_and_h01_free(self):
        auditor = P00_AUDITOR.read_text(encoding="utf-8")
        contract = json.loads(P00_CONTRACT.read_text(encoding="utf-8"))
        self.assertNotIn(HYPOTHESIS_ID, auditor)
        self.assertEqual(contract["binding_rule"]["discovery_end_utc"], "2024-12-31T23:59:59.999Z")
        self.assertFalse(contract["authority_boundary"]["validation_2025_access_authorized"])
        self.assertFalse(contract["authority_boundary"]["holdout_2026_access_authorized"])

    def test_h01_auditor_has_no_network_exchange_or_classifier_route(self):
        text = MODULE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests", "import urllib", "import websockets", ".post(", ".put(",
            ".patch(", ".delete(", "mexc_client", "execution_layer", "classify_stage",
            "run_p00_discovery",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
