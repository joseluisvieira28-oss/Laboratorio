import unittest

from radar.models import Direction, MarketSnapshot, PromotionStatus
from radar.strategy import RawSignal, StrategyAdapter, enforce_promotion_gate


SNAPSHOT = MarketSnapshot(
    symbol="BTCUSDT",
    observed_at="2026-09-16T00:00:00Z",
    last_price=100000.0,
    bid_price=99999.0,
    ask_price=100001.0,
    quote_volume_24h=1_000_000_000.0,
)


class FakeAdapter(StrategyAdapter):
    strategy_id = "TEST-EDGE-001"

    def __init__(self, status: PromotionStatus, direction: Direction):
        self.promotion_status = status
        self._direction = direction

    def evaluate(self, snapshot: MarketSnapshot) -> RawSignal:
        return RawSignal(self._direction, "frozen test rule", {"test": True})


class PromotionGateTests(unittest.TestCase):
    def test_research_signal_is_blocked(self):
        decision = enforce_promotion_gate(
            FakeAdapter(PromotionStatus.RESEARCH, Direction.LONG), SNAPSHOT
        )
        self.assertFalse(decision.valid_signal)
        self.assertTrue(decision.reason.startswith("BLOCKED_NOT_PROMOTED"))

    def test_rejected_signal_is_blocked(self):
        decision = enforce_promotion_gate(
            FakeAdapter(PromotionStatus.REJECTED, Direction.SHORT), SNAPSHOT
        )
        self.assertFalse(decision.valid_signal)

    def test_promoted_directional_signal_is_valid(self):
        decision = enforce_promotion_gate(
            FakeAdapter(PromotionStatus.PROMOTED_SHADOW, Direction.LONG), SNAPSHOT
        )
        self.assertTrue(decision.valid_signal)

    def test_promoted_none_is_not_signal(self):
        decision = enforce_promotion_gate(
            FakeAdapter(PromotionStatus.PROMOTED_SHADOW, Direction.NONE), SNAPSHOT
        )
        self.assertFalse(decision.valid_signal)


if __name__ == "__main__":
    unittest.main()
