import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.phase_b_h01_mexc_discovery_access_v01 import (
    AUTHORIZATION_DOCUMENT_TYPE,
    AUTHORIZATION_STATUS,
    DISCOVERY_END_MONTH,
    DISCOVERY_START_MONTH,
    FAMILY_ID,
    FROZEN_UNIVERSE,
    HYPOTHESIS_ID,
    EXPECTED_MONTHS,
    intake_h01_discovery_downloads,
    validate_h01_discovery_access_request,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "research" / "phase_b_h01_mexc_discovery_access_v01.py"
P00_INTAKE = ROOT / "research" / "phase_b_mexc_download_intake_v01.py"
P00_CORPUS = ROOT / "research" / "phase_b_mexc_discovery_corpus_v01.py"


def canonical_hash(payload):
    clone = dict(payload)
    clone.pop("fingerprint", None)
    encoded = json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def authorization_payload(**overrides):
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
    payload.update(overrides)
    payload["fingerprint"] = canonical_hash(payload)
    return payload


def write_authorization(path, **overrides):
    payload = authorization_payload(**overrides)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


class PhaseBH01MEXCDiscoveryAccessTests(unittest.TestCase):
    def test_missing_authorization_blocks_before_market_bytes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = validate_h01_discovery_access_request(
                symbol="BTCUSDT",
                start_month="2025-01",
                end_month="2025-08",
                authorization_path=root / "missing.json",
            )
            self.assertEqual(receipt.status, "BLOCKED_H01_DISCOVERY_ACCESS")
            self.assertIn("H01_DISCOVERY_ACCESS_AUTHORIZATION_MISSING", receipt.reasons)
            self.assertFalse(receipt.source_market_bytes_read)
            self.assertFalse(receipt.validation_2025_market_bytes_read)
            self.assertFalse(receipt.holdout_2026_market_bytes_read)

    def test_validation_request_is_blocked_even_with_valid_authorization(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            receipt = validate_h01_discovery_access_request(
                symbol="BTCUSDT",
                start_month="2025-09",
                end_month="2025-12",
                authorization_path=auth,
            )
            self.assertEqual(receipt.status, "BLOCKED_H01_DISCOVERY_ACCESS")
            self.assertIn("H01_VALIDATION_2025_RANGE_BLOCKED", receipt.reasons)
            self.assertFalse(receipt.source_market_bytes_read)

    def test_2026_request_is_blocked_even_with_valid_authorization(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            receipt = validate_h01_discovery_access_request(
                symbol="BTCUSDT",
                start_month="2026-01",
                end_month="2026-08",
                authorization_path=auth,
            )
            self.assertEqual(receipt.status, "BLOCKED_H01_DISCOVERY_ACCESS")
            self.assertIn("H01_HOLDOUT_2026_RANGE_BLOCKED", receipt.reasons)
            self.assertFalse(receipt.source_market_bytes_read)

    def test_tampered_authorization_fails_closed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            payload = write_authorization(auth)
            payload["validation_2025_access_authorized"] = True
            auth.write_text(json.dumps(payload), encoding="utf-8")
            receipt = validate_h01_discovery_access_request(
                symbol="BTCUSDT",
                start_month="2025-01",
                end_month="2025-08",
                authorization_path=auth,
            )
            self.assertEqual(receipt.status, "BLOCKED_H01_DISCOVERY_ACCESS")
            self.assertIn("H01_DISCOVERY_ACCESS_AUTHORIZATION_FINGERPRINT_MISMATCH", receipt.reasons)
            self.assertIn("H01_DISCOVERY_ACCESS_AUTHORIZATION_VALIDATION_NOT_LOCKED", receipt.reasons)
            self.assertFalse(receipt.source_market_bytes_read)

    def test_valid_preflight_constructs_only_exact_discovery_filenames(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            write_authorization(auth)
            receipt = validate_h01_discovery_access_request(
                symbol="BTCUSDT",
                start_month="2025-01",
                end_month="2025-08",
                authorization_path=auth,
            )
            self.assertEqual(receipt.status, "PASS_H01_DISCOVERY_ACCESS_PREFLIGHT")
            self.assertTrue(receipt.authorization_verified)
            self.assertEqual(len(receipt.expected_file_names), 8)
            self.assertEqual(tuple(name.split("-Min15-")[1][:7] for name in receipt.expected_file_names), EXPECTED_MONTHS)
            self.assertFalse(any("2025-09" in name or "2025-10" in name or "2025-11" in name or "2025-12" in name for name in receipt.expected_file_names))
            self.assertFalse(any("2026-" in name for name in receipt.expected_file_names))
            self.assertFalse(receipt.source_directory_enumerated)
            self.assertFalse(receipt.source_market_bytes_read)

    def test_intake_reads_only_exact_expected_discovery_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "downloads"
            destination = root / "raw"
            source.mkdir()
            auth = root / "auth.json"
            write_authorization(auth)

            for month in EXPECTED_MONTHS:
                (source / f"BTC_USDT-Min15-{month}-01.csv").write_bytes((month + "\n").encode("ascii"))
            forbidden_validation = source / "BTC_USDT-Min15-2025-09-01.csv"
            forbidden_validation.write_bytes(b"DO_NOT_READ")
            forbidden_holdout = source / "BTC_USDT-Min15-2026-01-01.csv"
            forbidden_holdout.write_bytes(b"DO_NOT_READ")

            receipt = intake_h01_discovery_downloads(
                source,
                destination,
                symbol="BTCUSDT",
                start_month="2025-01",
                end_month="2025-08",
                authorization_path=auth,
            )
            self.assertEqual(receipt.status, "PASS_H01_DISCOVERY_INTAKE_COMPLETE")
            self.assertEqual(receipt.copied_count, 8)
            self.assertTrue(receipt.source_market_bytes_read)
            self.assertFalse(receipt.source_directory_enumerated)
            self.assertFalse(receipt.validation_2025_market_bytes_read)
            self.assertFalse(receipt.holdout_2026_market_bytes_read)
            self.assertFalse((destination / forbidden_validation.name).exists())
            self.assertFalse((destination / forbidden_holdout.name).exists())

    def test_blocked_validation_range_does_not_create_destination_or_read_source(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "downloads"
            destination = root / "raw"
            source.mkdir()
            auth = root / "auth.json"
            write_authorization(auth)
            forbidden = source / "BTC_USDT-Min15-2025-09-01.csv"
            forbidden.write_bytes(b"SENTINEL")

            receipt = intake_h01_discovery_downloads(
                source,
                destination,
                symbol="BTCUSDT",
                start_month="2025-09",
                end_month="2025-12",
                authorization_path=auth,
            )
            self.assertEqual(receipt.status, "BLOCKED_H01_DISCOVERY_ACCESS")
            self.assertFalse(receipt.source_market_bytes_read)
            self.assertFalse(destination.exists())

    def test_p00_ingestion_boundaries_are_not_modified(self):
        intake = P00_INTAKE.read_text(encoding="utf-8")
        corpus = P00_CORPUS.read_text(encoding="utf-8")
        self.assertIn('DISCOVERY_MAX_MONTH = "2024-12"', intake)
        self.assertIn('DISCOVERY_MAX_MONTH = "2024-12"', corpus)
        self.assertNotIn("H01_PROTECT_AFTER_TP1_NEXT_BAR", intake)
        self.assertNotIn("H01_PROTECT_AFTER_TP1_NEXT_BAR", corpus)

    def test_h01_access_module_has_no_network_or_exchange_route_and_no_directory_enumeration(self):
        text = MODULE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "mexc_client",
            "execution_layer",
            ".glob(",
            ".iterdir(",
            "os.listdir",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
