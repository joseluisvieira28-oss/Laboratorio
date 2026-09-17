from __future__ import annotations

from datetime import datetime
import time
from typing import Callable

from radar.models import Direction, MarketSnapshot, PromotionStatus
from radar.strategy import RawSignal, StrategyAdapter
from radar.timing import ExactTimingPolicy

from .etf_cme_instflow_001 import CFTCObservation, STRATEGY_ID
from .etf_cme_source import (
    fetch_latest_two,
    operational_signal_receipt_from_observations,
)


class ETFCMEInstFlowAdapter(StrategyAdapter):
    """Shadow-only adapter for the frozen ETF-CME institutional-flow signal."""

    strategy_id = STRATEGY_ID
    promotion_status = PromotionStatus.PROMOTED_SHADOW
    frozen_symbol = "BTCUSDT"

    def __init__(
        self,
        *,
        timeout: int = 30,
        source_refresh_seconds: float = 300.0,
        fetcher: Callable[[int], tuple[CFTCObservation, CFTCObservation]] = fetch_latest_two,
        monotonic: Callable[[], float] = time.monotonic,
        timing_policy: ExactTimingPolicy | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
        if source_refresh_seconds <= 0:
            raise ValueError("source_refresh_seconds must be > 0")
        self.timeout = timeout
        self.source_refresh_seconds = source_refresh_seconds
        self.timing_policy = timing_policy or ExactTimingPolicy()
        self._fetcher = fetcher
        self._monotonic = monotonic
        self._cached_observations: tuple[CFTCObservation, CFTCObservation] | None = None
        self._cached_at: float | None = None

    def _observations(self) -> tuple[CFTCObservation, CFTCObservation]:
        now_mono = self._monotonic()
        stale = (
            self._cached_observations is None
            or self._cached_at is None
            or now_mono - self._cached_at >= self.source_refresh_seconds
        )
        if stale:
            observations = self._fetcher(self.timeout)
            if len(observations) != 2:
                raise RuntimeError("ETF-CME source did not return two observations")
            self._cached_observations = observations
            self._cached_at = now_mono
        return self._cached_observations

    @staticmethod
    def _snapshot_time(snapshot: MarketSnapshot) -> datetime:
        raw = snapshot.observed_at.replace("Z", "+00:00")
        value = datetime.fromisoformat(raw)
        if value.tzinfo is None:
            raise ValueError("market snapshot observed_at must be timezone-aware")
        return value

    def timing_plan(self, now: datetime) -> dict:
        previous, current = self._observations()
        receipt = operational_signal_receipt_from_observations(
            previous,
            current,
            now,
            timing_policy=self.timing_policy,
        )
        return {
            "strategy_id": self.strategy_id,
            "direction": receipt["direction"],
            "state": receipt["state"],
            "entry_eligible_now": receipt["entry_eligible_now"],
            "exact_entry_time_utc": receipt["exact_entry_time_utc"],
            "exact_exit_time_utc": receipt["exact_exit_time_utc"],
            "operational_timing": receipt["operational_timing"],
            "scientific_target_unchanged": True,
        }

    def evaluate(self, snapshot: MarketSnapshot) -> RawSignal:
        if snapshot.symbol != self.frozen_symbol:
            return RawSignal(
                direction=Direction.NONE,
                reason="FROZEN_SYMBOL_NOT_ELIGIBLE",
                metadata={
                    "frozen_symbol": self.frozen_symbol,
                    "observed_symbol": snapshot.symbol,
                    "source_requested": False,
                    "shadow_only": True,
                },
            )

        previous, current = self._observations()
        receipt = operational_signal_receipt_from_observations(
            previous,
            current,
            self._snapshot_time(snapshot),
            timing_policy=self.timing_policy,
        )
        if receipt.get("strategy_id") != self.strategy_id:
            raise RuntimeError("ETF-CME source receipt strategy_id mismatch")
        if receipt.get("micro_live_eligible") is not False:
            raise RuntimeError("ETF-CME runtime unexpectedly marked micro-live eligible")
        if receipt.get("authenticated_exchange_api") is not False:
            raise RuntimeError("ETF-CME runtime unexpectedly used authenticated exchange API")
        if receipt.get("order_created") is not False:
            raise RuntimeError("ETF-CME runtime unexpectedly created an order")

        if receipt["entry_eligible_now"]:
            direction = Direction(receipt["direction"])
            reason = "FROZEN_EXACT_ENTRY_SHADOW_SIGNAL"
        else:
            direction = Direction.NONE
            reason = str(receipt["state"])

        metadata = dict(receipt)
        metadata.update(
            {
                "frozen_symbol": self.frozen_symbol,
                "source_refresh_seconds": self.source_refresh_seconds,
                "shadow_only": True,
            }
        )
        return RawSignal(direction=direction, reason=reason, metadata=metadata)
