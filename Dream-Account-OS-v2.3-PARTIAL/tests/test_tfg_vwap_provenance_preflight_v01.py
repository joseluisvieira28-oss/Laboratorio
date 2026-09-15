from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from research.timeframe_gap.tfg_vwap_provenance_preflight_v01 import verify_discovery_source_identity


def make_fixture(root: Path, *, add_2026: bool = False, tamper: bool = False):
    symbols = ("BTCUSDT",)
    months = ("2022-01", "2022-02")
    files = []
    package = root / "H180-0001_NORMALIZED_BTCUSDT.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_STORED) as zf:
        for i, month in enumerate(months):
            member = f"BTCUSDT/1m/BTCUSDT-1m-{month}.normalized.csv.zst"
            expected_payload = f"authorized-{month}".encode()
            written_payload = expected_payload + (b"-tampered" if tamper and i == 0 else b"")
            zf.writestr(member, written_payload)
            files.append({
                "symbol": "BTCUSDT",
                "month": month,
                "rows": 1,
                "normalized_member": member,
                "normalized_compressed_sha256": hashlib.sha256(expected_payload).hexdigest(),
            })
        zf.writestr("BTCUSDT/1m/BTCUSDT-1m-2025-01.normalized.csv.zst", b"PROTECTED-CONTENT-NOT-TO-BE-OPENED")
        if add_2026:
            zf.writestr("BTCUSDT/1m/BTCUSDT-1m-2026-01.normalized.csv.zst", b"FORBIDDEN")

    manifest = {
        "experiment": "H180-0001",
        "run": "03C",
        "normalization_version": "H180-NORM-1.0.0",
        "provider": "Binance",
        "market": "USD-M Futures",
        "interval": "1m",
        "clock": "UTC",
        "monthly_raw_fingerprint": "e62523e28ab87da27e1aa0f992e94d1b4be461a00ef1d7a1ce807a3740348e8a",
        "files": files,
    }
    manifest_path = root / "H180-0001_PROVENANCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return package, manifest_path, manifest_sha, symbols, months


class ProvenancePreflightTests(unittest.TestCase):
    def test_passes_exact_discovery_members_without_opening_outcomes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, manifest, digest, symbols, months = make_fixture(root)
            result = verify_discovery_source_identity(
                root, manifest, symbols=symbols, months=months, expected_manifest_sha256=digest
            )
            self.assertEqual(result["status"], "PASS_DISCOVERY_SOURCE_IDENTITY_ONLY")
            self.assertEqual(result["discovery_members_verified"], 2)
            self.assertFalse(result["market_rows_decompressed"])
            self.assertFalse(result["signals_computed"])
            self.assertFalse(result["outcome_computation_authorized"])
            self.assertFalse(result["protected_2025_member_content_opened"])

    def test_manifest_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, manifest, _, symbols, months = make_fixture(root)
            with self.assertRaisesRegex(RuntimeError, "PROVENANCE_MANIFEST_SHA256_MISMATCH"):
                verify_discovery_source_identity(root, manifest, symbols=symbols, months=months, expected_manifest_sha256="0" * 64)

    def test_tampered_discovery_member_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, manifest, digest, symbols, months = make_fixture(root, tamper=True)
            with self.assertRaisesRegex(RuntimeError, "DISCOVERY_MEMBER_SHA256_MISMATCH"):
                verify_discovery_source_identity(root, manifest, symbols=symbols, months=months, expected_manifest_sha256=digest)

    def test_2026_member_presence_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, manifest, digest, symbols, months = make_fixture(root, add_2026=True)
            with self.assertRaisesRegex(RuntimeError, "FORBIDDEN_2026_MEMBER_PRESENT"):
                verify_discovery_source_identity(root, manifest, symbols=symbols, months=months, expected_manifest_sha256=digest)


if __name__ == "__main__":
    unittest.main()
