import os
import tempfile
import unittest

from radar.evidence import EvidenceStore
from radar.market import MEXCFuturesPublicFeed
from radar.models import MarketSnapshot
from radar.preflight import local_node_preflight


class StubPreflightFeed(MEXCFuturesPublicFeed):
    def __init__(self, server_ms=1_100.0):
        super().__init__(timeout=1)
        self._server_ms = server_ms

    def server_time_ms(self):
        return self._server_ms

    def contract_row(self, symbol):
        self._validate_contract_symbol(symbol)
        return {
            "symbol": "BTC_USDT",
            "apiAllowed": True,
            "futureType": 1,
            "state": 0,
            "positionOpenType": 3,
        }

    def all_market_snapshots(self):
        return {
            "BTCUSDT": MarketSnapshot(
                symbol="BTCUSDT",
                observed_at="2026-09-17T16:00:00Z",
                last_price=100.0,
                bid_price=99.9,
                ask_price=100.1,
                quote_volume_24h=1_000_000.0,
            )
        }

    def funding_rate(self, symbol):
        self._validate_contract_symbol(symbol)
        return {"fundingRate": 0.0001, "nextSettleTime": 2_000.0}


class LocalNodePreflightTests(unittest.TestCase):
    def test_preflight_passes_with_clock_contract_market_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(os.path.join(tmp, "evidence.sqlite3"))
            times = iter([1_000.0, 1_200.0])
            result = local_node_preflight(
                feed=StubPreflightFeed(server_ms=1_100.0),
                store=store,
                clock_ms=lambda: next(times),
            )
            self.assertTrue(result["pass"], result)
            self.assertEqual(result["blockers"], [])
            self.assertTrue(result["evidence"]["chain_ok"])
            self.assertFalse(result["orders_created"])
            self.assertFalse(result["capital_enabled"])

    def test_preflight_fails_closed_on_clock_offset(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(os.path.join(tmp, "evidence.sqlite3"))
            times = iter([1_000.0, 1_200.0])
            result = local_node_preflight(
                feed=StubPreflightFeed(server_ms=2_000.0),
                store=store,
                clock_ms=lambda: next(times),
            )
            self.assertFalse(result["pass"])
            self.assertIn("CLOCK_OFFSET_OUTSIDE_OPERATOR_BUDGET", result["blockers"])
            self.assertTrue(result["evidence"]["chain_ok"])


if __name__ == "__main__":
    unittest.main()
