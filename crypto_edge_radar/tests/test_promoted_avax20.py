import math
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from radar.config import CORE5, Settings
from radar.evidence import EvidenceStore
from radar.engine import RadarEngine
from radar.models import Direction, MarketSnapshot, PromotionStatus
from radar.promoted import CED1D0031AVAX20Adapter, build_promoted_registry
from radar.strategy import RawSignal, StrategyAdapter, StrategyRegistry

UTC = timezone.utc


def daily_rows(end_day: str, closes: dict[str, float]):
    rows = []
    for day_s in sorted(closes):
        d = datetime.fromisoformat(day_s).replace(tzinfo=UTC)
        open_ms = int(d.timestamp() * 1000)
        close_ms = open_ms + 86_400_000 - 1
        px = closes[day_s]
        rows.append([open_ms, str(px), str(px), str(px), str(px), "0", close_ms])
    return rows


class FakeUsdmFeed:
    provider = "BINANCE_USDM_PUBLIC"

    def __init__(self, observed_at="2026-09-19T00:00:30Z", positive=True):
        self.observed_at = observed_at
        self.daily_calls = 0
        start = datetime(2026, 8, 25, tzinfo=UTC)
        closes = {}
        for i in range(25):
            day = (start + timedelta(days=i)).date().isoformat()
            closes[day] = 10.0 + i
        if not positive:
            closes["2026-09-18"] = 5.0
        self.rows = daily_rows("2026-09-18", closes)

    def daily_klines(self, symbol, limit=40):
        self.daily_calls += 1
        self.last_daily_args = (symbol, limit)
        return self.rows

    def all_market_snapshots(self):
        symbols = (*CORE5, "AVAXUSDT")
        return {
            symbol: MarketSnapshot(
                symbol=symbol,
                observed_at=self.observed_at,
                last_price=20.0,
                bid_price=19.99,
                ask_price=20.01,
                quote_volume_24h=1_000_000_000.0,
            )
            for symbol in symbols
        }

    def subset(self, snapshots, symbols):
        return {s: snapshots[s] for s in symbols if s in snapshots}

    def eligible_usdt_perpetual_symbols(self):
        return set((*CORE5, "AVAXUSDT"))


class FakeSpotFeed(FakeUsdmFeed):
    provider = "BINANCE_SPOT_DATA_API_PUBLIC"


class FixedSignalAdapter(StrategyAdapter):
    strategy_id = "FIXED"
    promotion_status = PromotionStatus.PROMOTED_SHADOW
    symbols = ("AVAXUSDT",)

    def evaluate(self, snapshot):
        return RawSignal(
            Direction.LONG,
            "fixed",
            {"signal_key": "FIXED:2026-09-18"},
        )


class PromotedAVAXTests(unittest.TestCase):
    def test_exact_positive_momentum_emits_long(self):
        feed = FakeUsdmFeed()
        adapter = CED1D0031AVAX20Adapter(feed)
        snap = feed.all_market_snapshots()["AVAXUSDT"]
        raw = adapter.evaluate(snap)
        self.assertEqual(raw.direction, Direction.LONG)
        self.assertEqual(raw.metadata["signal_key"], "CED1D-0031:2026-09-18")
        self.assertEqual(raw.metadata["signal_day"], "2026-09-18")
        self.assertEqual(raw.metadata["lag_day"], "2026-08-29")
        self.assertGreater(raw.metadata["momentum_ln"], 0)
        self.assertEqual(feed.last_daily_args, ("AVAXUSDT", 40))

    def test_negative_momentum_emits_short(self):
        feed = FakeUsdmFeed(positive=False)
        adapter = CED1D0031AVAX20Adapter(feed)
        raw = adapter.evaluate(feed.all_market_snapshots()["AVAXUSDT"])
        self.assertEqual(raw.direction, Direction.SHORT)
        self.assertLess(raw.metadata["momentum_ln"], 0)

    def test_pre_activation_does_not_open_history(self):
        feed = FakeUsdmFeed(observed_at="2026-09-18T23:59:59Z")
        adapter = CED1D0031AVAX20Adapter(feed)
        raw = adapter.evaluate(feed.all_market_snapshots()["AVAXUSDT"])
        self.assertEqual(raw.direction, Direction.NONE)
        self.assertEqual(raw.reason, "PRE_ACTIVATION_BOUNDARY")
        self.assertEqual(feed.daily_calls, 0)

    def test_late_cycle_does_not_backfill_signal(self):
        feed = FakeUsdmFeed(observed_at="2026-09-19T00:01:00Z")
        adapter = CED1D0031AVAX20Adapter(feed)
        raw = adapter.evaluate(feed.all_market_snapshots()["AVAXUSDT"])
        self.assertEqual(raw.direction, Direction.NONE)
        self.assertEqual(raw.reason, "OUTSIDE_SIGNAL_EMISSION_WINDOW")
        self.assertEqual(feed.daily_calls, 0)

    def test_spot_provider_never_loads_promoted_usdm_adapter(self):
        registry = build_promoted_registry(FakeSpotFeed())
        self.assertEqual(registry.adapters, ())

    def test_signal_key_is_emitted_once_across_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed = FakeUsdmFeed()
            settings = Settings(db_path=os.path.join(tmp, "radar.sqlite3"))
            store = EvidenceStore(settings.db_path)
            engine = RadarEngine(
                settings=settings,
                feed=feed,
                store=store,
                registry=StrategyRegistry((FixedSignalAdapter(),)),
            )
            first = engine.run_cycle()
            second = engine.run_cycle()
            self.assertEqual(len(first["valid_signals"]), 1)
            self.assertEqual(first["duplicate_signal_count"], 0)
            self.assertEqual(len(second["valid_signals"]), 0)
            self.assertEqual(second["duplicate_signal_count"], 1)
            self.assertTrue(store.signal_key_seen("FIXED:2026-09-18"))
            ok, detail = store.verify_chain()
            self.assertTrue(ok, detail)


if __name__ == "__main__":
    unittest.main()
