import importlib.util
import json
import os
import unittest

os.environ["TV_WEBHOOK_TOKEN"] = "unit-test-token-abcdefghijklmnopqrstuvwxyz"

spec = importlib.util.spec_from_file_location(
    "appmod", "tradingview_ingest/app.py"
)
appmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(appmod)


def valid_payload():
    return {
        "lab_id": "TV-FOOTPRINT-CALIBRATION-001",
        "sensor_version": "MM-V1",
        "symbol": "BINANCE:BTCUSDT",
        "timeframe": "5",
        "bar_open_ms": 1790247600000,
        "bar_close_ms": 1790247900000,
        "close": 83453.52,
        "tv_total_volume": 123.0,
        "tv_buy_volume": 70.0,
        "tv_sell_volume": 53.0,
        "tv_delta": 17.0,
        "tv_delta_pct": 0.138211,
        "poc_mid": 83450.0,
        "poc_migration_bps": -5.27,
        "vah": 83477.0,
        "val": 83435.0,
        "buy_imbalance_rows": 2,
        "sell_imbalance_rows": 1,
        "footprint_rows": 8,
        "ltf_intrabars": 5,
        "ltf_path_efficiency": 0.583,
        "ltf_signed_volume_pct": 0.11,
        "volume_z": 0.7,
        "bar_return_bps": -3.2,
        "eth_ret": 0.001,
        "sol_ret": -0.002,
        "cme_btc_ret": None,
        "ndx_ret": None,
        "dxy_ret": None,
    }


class ValidationTests(unittest.TestCase):
    def test_valid(self):
        p = valid_payload()
        self.assertEqual(appmod.validate_payload(p), p)

    def test_identity_mismatch(self):
        p = valid_payload()
        p["symbol"] = "BYBIT:BTCUSDT"
        with self.assertRaises(appmod.ValidationError):
            appmod.validate_payload(p)

    def test_pre_boundary_rejected(self):
        p = valid_payload()
        p["bar_open_ms"] = 1790247000000
        p["bar_close_ms"] = 1790247300000
        with self.assertRaises(appmod.ValidationError):
            appmod.validate_payload(p)

    def test_unknown_key_rejected(self):
        p = valid_payload()
        p["action"] = "BUY"
        with self.assertRaises(appmod.ValidationError):
            appmod.validate_payload(p)

    def test_interval_alignment(self):
        p = valid_payload()
        p["bar_close_ms"] += 1
        with self.assertRaises(appmod.ValidationError):
            appmod.validate_payload(p)

    def test_non_finite_rejected(self):
        p = valid_payload()
        p["tv_delta"] = float("nan")
        with self.assertRaises(appmod.ValidationError):
            appmod.validate_payload(p)

    def test_ltf_max_five(self):
        p = valid_payload()
        p["ltf_intrabars"] = 6
        with self.assertRaises(appmod.ValidationError):
            appmod.validate_payload(p)

    def test_receipt_is_deterministic(self):
        p = valid_payload()
        r1 = appmod.receipt_record(
            p, appmod.datetime(2026, 9, 24, 11, 5, tzinfo=appmod.timezone.utc)
        )
        r2 = appmod.receipt_record(
            p, appmod.datetime(2026, 9, 24, 11, 6, tzinfo=appmod.timezone.utc)
        )
        self.assertEqual(r1["evidence_key"], r2["evidence_key"])
        self.assertEqual(r1["payload_sha256"], r2["payload_sha256"])

    def test_http_accept_and_duplicate(self):
        appmod._recent.clear()
        appmod.accepted_in_process = 0
        appmod.duplicates_in_process = 0
        client = appmod.app.test_client()
        token = os.environ["TV_WEBHOOK_TOKEN"]
        p = valid_payload()

        r = client.post(f"/v1/tradingview/{token}", json=p)
        self.assertEqual(r.status_code, 202)
        self.assertEqual(r.get_json()["status"], "accepted")

        r = client.post(f"/v1/tradingview/{token}", json=p)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "duplicate_in_process")

    def test_http_rejects_execution_field(self):
        client = appmod.app.test_client()
        token = os.environ["TV_WEBHOOK_TOKEN"]
        p = valid_payload()
        p["side"] = "BUY"
        r = client.post(f"/v1/tradingview/{token}", json=p)
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
