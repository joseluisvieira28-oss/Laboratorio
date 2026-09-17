import unittest

from radar.models import Direction, MarketSnapshot
from radar.strategy import enforce_promotion_gate
from radar.strategies.etf_cme_adapter import ETFCMEInstFlowAdapter
from radar.strategies.etf_cme_instflow_001 import CFTCObservation


PREVIOUS = CFTCObservation("2026-09-01", 1000, 400, 300)
CURRENT = CFTCObservation("2026-09-08", 1000, 450, 300)


def snapshot(symbol: str, observed_at: str) -> MarketSnapshot:
    return MarketSnapshot(
        symbol=symbol,
        observed_at=observed_at,
        last_price=100000.0,
        bid_price=99999.0,
        ask_price=100001.0,
        quote_volume_24h=1_000_000_000.0,
    )


class FakeClock:
    def __init__(self, value: float = 100.0):
        self.value = value

    def __call__(self) -> float:
        return self.value


class ETFCMEAdapterTests(unittest.TestCase):
    def test_non_btc_symbols_never_request_cftc_source(self):
        calls = []

        def fetcher(timeout):
            calls.append(timeout)
            return PREVIOUS, CURRENT

        adapter = ETFCMEInstFlowAdapter(fetcher=fetcher)
        decision = enforce_promotion_gate(
            adapter,
            snapshot("ETHUSDT", "2026-09-16T00:00:00Z"),
        )
        self.assertFalse(decision.valid_signal)
        self.assertEqual(decision.direction, Direction.NONE)
        self.assertEqual(calls, [])
        self.assertFalse(decision.metadata["source_requested"])

    def test_exact_frozen_entry_time_emits_promoted_shadow_signal(self):
        adapter = ETFCMEInstFlowAdapter(fetcher=lambda timeout: (PREVIOUS, CURRENT))
        decision = enforce_promotion_gate(
            adapter,
            snapshot("BTCUSDT", "2026-09-16T00:00:00Z"),
        )
        self.assertTrue(decision.valid_signal)
        self.assertEqual(decision.direction, Direction.LONG)
        self.assertEqual(decision.reason, "FROZEN_EXACT_ENTRY_SHADOW_SIGNAL")
        self.assertFalse(decision.metadata["micro_live_eligible"])
        self.assertFalse(decision.metadata["authenticated_exchange_api"])
        self.assertFalse(decision.metadata["order_created"])

    def test_late_entry_is_never_chased(self):
        adapter = ETFCMEInstFlowAdapter(fetcher=lambda timeout: (PREVIOUS, CURRENT))
        decision = enforce_promotion_gate(
            adapter,
            snapshot("BTCUSDT", "2026-09-16T00:00:01Z"),
        )
        self.assertFalse(decision.valid_signal)
        self.assertEqual(decision.direction, Direction.NONE)
        self.assertEqual(decision.reason, "ENTRY_WINDOW_PASSED_DO_NOT_CHASE")
        self.assertFalse(decision.metadata["entry_eligible_now"])

    def test_public_cftc_rows_are_cached_but_time_gate_is_recomputed(self):
        calls = []
        clock = FakeClock()

        def fetcher(timeout):
            calls.append(timeout)
            return PREVIOUS, CURRENT

        adapter = ETFCMEInstFlowAdapter(
            fetcher=fetcher,
            monotonic=clock,
            source_refresh_seconds=300,
        )

        first = adapter.evaluate(snapshot("BTCUSDT", "2026-09-15T23:59:00Z"))
        second = adapter.evaluate(snapshot("BTCUSDT", "2026-09-16T00:00:00Z"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(first.reason, "WAITING_INFORMATION_SAFE_TIME")
        self.assertEqual(second.direction, Direction.LONG)
        self.assertEqual(second.reason, "FROZEN_EXACT_ENTRY_SHADOW_SIGNAL")

        clock.value += 301
        adapter.evaluate(snapshot("BTCUSDT", "2026-09-16T00:00:01Z"))
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
