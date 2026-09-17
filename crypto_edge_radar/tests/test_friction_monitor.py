import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from radar.friction_monitor import PublicFrictionMonitor


class DummyFeed:
    provider = "MEXC_FUTURES_PUBLIC"


class DummyStore:
    def __init__(self):
        self.rows = []

    def append(self, event_type, payload):
        self.rows.append((event_type, payload))
        return len(self.rows)


class DummyEngine:
    def __init__(self, provider="MEXC_FUTURES_PUBLIC"):
        self.feed = DummyFeed()
        self.feed.provider = provider
        self.store = DummyStore()


class FrictionMonitorTests(unittest.TestCase):
    def test_capture_persists_public_only_receipt_and_evidence(self):
        receipt = {
            "receipt_type": "MEXC_FRICTION_SHADOW_V1",
            "capital_enabled": False,
            "orders_created": False,
            "provider": "MEXC_FUTURES_PUBLIC",
        }
        with tempfile.TemporaryDirectory() as tmp, patch(
            "radar.friction_monitor.mexc_friction_shadow_receipt",
            return_value=receipt,
        ):
            engine = DummyEngine()
            path = Path(tmp) / "latest.json"
            monitor = PublicFrictionMonitor(engine=engine, latest_path=str(path))
            result = monitor.capture_once()
            self.assertEqual(result, receipt)
            self.assertEqual(json.loads(path.read_text()), receipt)
            self.assertEqual(engine.store.rows[-1][0], "MEXC_FRICTION_SHADOW")

    def test_non_mexc_provider_fails_closed(self):
        engine = DummyEngine(provider="BINANCE_SPOT_DATA_API_PUBLIC")
        monitor = PublicFrictionMonitor(engine=engine, latest_path="unused.json")
        with self.assertRaises(RuntimeError):
            monitor.capture_once()

    def test_receipt_cannot_enable_capital_or_orders(self):
        unsafe = {
            "capital_enabled": True,
            "orders_created": False,
        }
        with patch(
            "radar.friction_monitor.mexc_friction_shadow_receipt",
            return_value=unsafe,
        ):
            engine = DummyEngine()
            monitor = PublicFrictionMonitor(engine=engine, latest_path="unused.json")
            with self.assertRaises(RuntimeError):
                monitor.capture_once()

    def test_interval_under_one_minute_is_rejected(self):
        with self.assertRaises(ValueError):
            PublicFrictionMonitor(engine=DummyEngine(), latest_path="unused.json", interval_seconds=59)


if __name__ == "__main__":
    unittest.main()
