import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "vault", "tradingview_evidence_vault/vault.py"
)
vault = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vault)


def receipt(bar_close=1790253600000, delta=4.0):
    payload = {
        "lab_id": vault.LAB_ID,
        "sensor_version": vault.SENSOR_VERSION,
        "symbol": vault.SYMBOL,
        "timeframe": vault.TIMEFRAME,
        "bar_open_ms": bar_close - vault.BAR_MS,
        "bar_close_ms": bar_close,
        "tv_delta": delta,
    }
    return {
        "record_type": "TVFP_RECEIPT",
        "evidence_key": f"{vault.LAB_ID}|{vault.SENSOR_VERSION}|{vault.SYMBOL}|{vault.TIMEFRAME}|{bar_close}",
        "payload_sha256": vault.payload_sha(payload),
        "received_at": "2026-09-24T12:40:06+00:00",
        "payload": payload,
        "trading_authority": "NONE",
    }


class VaultTests(unittest.TestCase):
    def test_validate(self):
        r = receipt()
        self.assertEqual(vault.validate_receipt(r), r)

    def test_duplicate_removed(self):
        r = receipt()
        rows, stats = vault.deduplicate([r, dict(r)])
        self.assertEqual(len(rows), 1)
        self.assertEqual(stats["exact_duplicates_removed"], 1)

    def test_conflict_fails_closed(self):
        a = receipt()
        b = receipt(delta=99.0)
        with self.assertRaises(vault.VaultError):
            vault.deduplicate([a, b])

    def test_continuity_gap(self):
        a = receipt(1790253600000)
        b = receipt(1790254200000)
        c = vault.continuity([a, b])
        self.assertEqual(c["missing_slots"], 1)
        self.assertEqual(c["missing_bar_close_ms"], [1790253900000])

    def test_manifest_hash_chain(self):
        rows = [receipt(1790253600000), receipt(1790253900000)]
        with tempfile.TemporaryDirectory() as td:
            m = vault.write_vault(rows, Path(td), "2026-09-24")
            self.assertEqual(m["unique_receipts"], 2)
            self.assertEqual(m["missing_slots"], 0)
            self.assertNotEqual(m["terminal_chain_sha256"], "0" * 64)
            self.assertTrue((Path(td) / "2026-09-24.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
