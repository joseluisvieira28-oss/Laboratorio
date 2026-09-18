from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

from .market import MarketDataError
from .models import Direction, MarketSnapshot, PromotionStatus
from .strategy import RawSignal, StrategyAdapter, StrategyRegistry

UTC = timezone.utc


class CED1D0031AVAX20Adapter(StrategyAdapter):
    """Exact CED1D-0031 prospective shadow adapter.

    Research identity:
    AVAXUSDT USD-M, 20-calendar-day momentum, continuation, H1.
    Signal completion = UTC day boundary.
    Reference entry = completion + 1 minute.
    """

    strategy_id = "CED1D-0031"
    promotion_status = PromotionStatus.PROMOTED_SHADOW
    symbols = ("AVAXUSDT",)
    required_provider = "BINANCE_USDM_PUBLIC"

    activation_completion = datetime(2026, 9, 19, 0, 0, tzinfo=UTC)
    emission_window = timedelta(minutes=1)

    def __init__(self, feed) -> None:
        self.feed = feed

    @staticmethod
    def _parse_utc(value: str) -> datetime:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise MarketDataError("snapshot observed_at must be timezone-aware")
        return dt.astimezone(UTC)

    def evaluate(self, snapshot: MarketSnapshot) -> RawSignal:
        if snapshot.symbol != "AVAXUSDT":
            return RawSignal(
                Direction.NONE,
                "SYMBOL_NOT_AUTHORIZED",
                {"candidate": self.strategy_id, "expected_symbol": "AVAXUSDT"},
            )

        provider = getattr(self.feed, "provider", None)
        if provider != self.required_provider:
            return RawSignal(
                Direction.NONE,
                "PROVIDER_MISMATCH_FAIL_CLOSED",
                {
                    "candidate": self.strategy_id,
                    "required_provider": self.required_provider,
                    "observed_provider": provider,
                },
            )

        observed = self._parse_utc(snapshot.observed_at)
        completion = observed.replace(hour=0, minute=0, second=0, microsecond=0)
        reference_entry = completion + timedelta(minutes=1)

        if completion < self.activation_completion:
            return RawSignal(
                Direction.NONE,
                "PRE_ACTIVATION_BOUNDARY",
                {
                    "candidate": self.strategy_id,
                    "activation_completion": self.activation_completion.isoformat(),
                    "observed_at": observed.isoformat(),
                },
            )

        # A valid radar signal must exist before the exact 00:01 reference entry.
        # A late process restart cannot backfill a shadow signal.
        if not (completion <= observed < reference_entry):
            return RawSignal(
                Direction.NONE,
                "OUTSIDE_SIGNAL_EMISSION_WINDOW",
                {
                    "candidate": self.strategy_id,
                    "signal_completion": completion.isoformat(),
                    "reference_entry": reference_entry.isoformat(),
                    "observed_at": observed.isoformat(),
                    "late_backfill_forbidden": True,
                },
            )

        rows = self.feed.daily_klines("AVAXUSDT", limit=40)
        completion_ms = int(completion.timestamp() * 1000)
        closes_by_day: dict[str, float] = {}
        for row in rows:
            open_ms = int(row[0])
            close_px = float(row[4])
            close_ms = int(row[6])
            if close_ms >= completion_ms:
                continue
            day = datetime.fromtimestamp(open_ms / 1000, tz=UTC).date().isoformat()
            if day in closes_by_day:
                raise MarketDataError(f"duplicate daily candle for {day}")
            closes_by_day[day] = close_px

        signal_day = (completion.date() - timedelta(days=1))
        lag_day = signal_day - timedelta(days=20)
        sd = signal_day.isoformat()
        ld = lag_day.isoformat()
        if sd not in closes_by_day or ld not in closes_by_day:
            raise MarketDataError(
                f"exact 20-calendar-day path unavailable: signal_day={sd}, lag_day={ld}"
            )

        close_d = closes_by_day[sd]
        close_lag = closes_by_day[ld]
        momentum = math.log(close_d / close_lag)
        if momentum > 0:
            direction = Direction.LONG
        elif momentum < 0:
            direction = Direction.SHORT
        else:
            direction = Direction.NONE

        signal_key = f"{self.strategy_id}:{sd}"
        reference_exit = reference_entry + timedelta(days=1)
        reason = (
            "CED1D_0031_20D_CONTINUATION"
            if direction is not Direction.NONE
            else "ZERO_MOMENTUM_NO_SIGNAL"
        )
        return RawSignal(
            direction,
            reason,
            {
                "candidate": self.strategy_id,
                "signal_key": signal_key,
                "signal_day": sd,
                "lag_day": ld,
                "signal_completion": completion.isoformat(),
                "reference_entry": reference_entry.isoformat(),
                "reference_exit": reference_exit.isoformat(),
                "lookback_calendar_days": 20,
                "horizon_calendar_days": 1,
                "direction_rule": "CONTINUATION_SIGN_LOG_CLOSE_RATIO",
                "close_D": close_d,
                "close_D_minus_20": close_lag,
                "momentum_ln": momentum,
                "provider": provider,
                "research_notional_usdt": 100,
                "live_authorized": False,
                "orders_authorized": False,
                "authority": {
                    "promotion_record_commit": "3f207f0512015dfae12a0287f64516f425dd3d54",
                    "shadow_activation_commit": "211c392601f6c2ef602eaba9562560647aaad6fb",
                    "authority_reconciliation_head": "790236ed375b6842dc8ce26d1213d437435daaa3",
                },
            },
        )


def build_promoted_registry(feed) -> StrategyRegistry:
    """Load only adapters whose exact provider and shadow authority are active."""
    if getattr(feed, "provider", None) == "BINANCE_USDM_PUBLIC":
        return StrategyRegistry((CED1D0031AVAX20Adapter(feed),))
    return StrategyRegistry.empty()
