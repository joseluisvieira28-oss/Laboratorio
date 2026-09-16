import json
import os
import tempfile
import unittest

from radar.config import CORE5, Settings
from radar.evidence import EvidenceStore
from radar.engine import RadarEngine
from radar.models import MarketSnapshot
from radar.service import PublicShadowService, read_status
from radar.strategy import StrategyRegistry


class FakeFeed:
    def all_market_snapshots(self):
        return {
            symbol: MarketSnapshot(
                symbol=symbol,
                observed_at="2026-09-16T00:00:00Z",
                last_price=100.0 + i,
                bid_price=99.9 + i,
                ask_price=100.1 + i,
                quote_volume_24h=1_000_000_000.0 - i,
            )
            for i, symbol in enumerate(CORE5)
        }

    def subset(self, snapshots, symbols):
        return {symbol: snapshots[symbol] for symbol in symbols if symbol in snapshots}

    def eligible_usdt_perpetual_symbols(self):
        return set(CORE5)


class BrokenFeed(FakeFeed):
    def all_market_snapshots(self):
        raise RuntimeError("synthetic market failure")


class ServiceTests(unittest.TestCase):
    def _engine(self, tmp, feed):
        settings = Settings(
            db_path=os.path.join(tmp, "radar.sqlite3"),
            status_path=os.path.join(tmp, "status.json"),
            notification_path=os.path.join(tmp, "notifications.jsonl"),
        )
        engine = RadarEngine(
            settings=settings,
            feed=feed,
            store=EvidenceStore(settings.db_path),
            registry=StrategyRegistry.empty(),
        )
        return engine, settings

    def test_heartbeat_persists_and_registry_stays_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, settings = self._engine(tmp, FakeFeed())
            service = PublicShadowService(engine, settings.status_path, settings.notification_path)
            code, status = service.run_cycle()
            self.assertEqual(code, 0)
            self.assertEqual(status["health"], "OK")
            self.assertEqual(status["registered_strategies"], 0)
            self.assertEqual(status["valid_signal_count"], 0)
            self.assertEqual(read_status(settings.status_path)["health"], "OK")
            ok, _ = engine.store.verify_chain()
            self.assertTrue(ok)

    def test_failure_is_fail_closed_and_notified(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, settings = self._engine(tmp, BrokenFeed())
            service = PublicShadowService(engine, settings.status_path, settings.notification_path)
            code, status = service.run_cycle()
            self.assertEqual(code, 2)
            self.assertEqual(status["health"], "FAIL_CLOSED")
            self.assertEqual(status["valid_signal_count"], 0)
            persisted = read_status(settings.status_path)
            self.assertEqual(persisted["health"], "FAIL_CLOSED")
            with open(settings.notification_path, "r", encoding="utf-8") as handle:
                records = [json.loads(line) for line in handle if line.strip()]
            self.assertEqual(records[-1]["event_type"], "SERVICE_FAIL_CLOSED")

    def test_bounded_service_runs_exact_cycle_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, settings = self._engine(tmp, FakeFeed())
            service = PublicShadowService(engine, settings.status_path, settings.notification_path)
            code = service.run(interval=5, max_cycles=3)
            self.assertEqual(code, 0)
            status = read_status(settings.status_path)
            self.assertEqual(status["cycle"], 3)

    def test_interval_under_five_seconds_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, settings = self._engine(tmp, FakeFeed())
            service = PublicShadowService(engine, settings.status_path, settings.notification_path)
            with self.assertRaises(ValueError):
                service.run(interval=1, max_cycles=1)


if __name__ == "__main__":
    unittest.main()
