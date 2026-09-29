import os
import tempfile
import unittest

from radar.config import CORE5, Settings
from radar.evidence import EvidenceStore
from radar.engine import RadarEngine
from radar.models import MarketSnapshot
from radar.strategy import StrategyRegistry


class FakeFeed:
    provider = "TEST_PUBLIC_PROVIDER"

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


class EngineTests(unittest.TestCase):
    def test_empty_registry_observes_without_inventing_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(db_path=os.path.join(tmp, "radar.sqlite3"))
            engine = RadarEngine(
                settings=settings,
                feed=FakeFeed(),
                store=EvidenceStore(settings.db_path),
                registry=StrategyRegistry.empty(),
            )
            result = engine.run_cycle()
            self.assertEqual(result["provider"], "TEST_PUBLIC_PROVIDER")
            self.assertEqual(result["universe"], list(CORE5))
            self.assertEqual(result["registered_strategies"], 0)
            self.assertEqual(result["valid_signals"], [])
            ok, _ = engine.store.verify_chain()
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
