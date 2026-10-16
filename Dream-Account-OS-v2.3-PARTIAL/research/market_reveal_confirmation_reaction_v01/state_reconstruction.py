"""Decision-time MRCR state reconstruction from canonical offline observations.

No target outcomes, thresholds, labels, entries or exits are defined here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from decision_boundary import (
    assert_no_future,
    bounded_window,
    epoch_ms_to_ns,
    rfc3339_to_ns,
)
from measurements import ratio, state_vector
from order_book import BookMetrics
from source_adapters import CanonicalTrade


@dataclass(frozen=True)
class TimedBookMetrics:
    timestamp_ns: int
    metrics: BookMetrics


@dataclass(frozen=True)
class FlowSummary:
    buy_notional: Decimal
    sell_notional: Decimal
    buy_trade_count: int
    sell_trade_count: int


@dataclass(frozen=True)
class ReconstructedState:
    venue: str
    native_symbol: str
    anchor_ns: int
    decision_ns: int
    pre_book_sequence: int
    decision_book_sequence: int
    feature_trade_count: int
    state: dict[str, float | None]


def canonical_trade_time_ns(trade: CanonicalTrade) -> int:
    if trade.venue == "BINANCE_SPOT":
        return epoch_ms_to_ns(trade.trade_time)
    if trade.venue == "COINBASE_ADVANCED_SPOT":
        return rfc3339_to_ns(trade.trade_time)
    raise ValueError(f"unsupported venue: {trade.venue}")


def aggregate_aggressive_flow(
    trades: Sequence[CanonicalTrade],
    *,
    venue: str,
    native_symbol: str,
    anchor_ns: int,
    decision_ns: int,
) -> FlowSummary:
    for trade in trades:
        if trade.venue != venue or trade.native_symbol != native_symbol:
            raise ValueError("mixed venue/symbol in flow feature set")

    assert_no_future(
        trades,
        timestamp_ns=canonical_trade_time_ns,
        decision_ns=decision_ns,
    )
    window = bounded_window(
        trades,
        timestamp_ns=canonical_trade_time_ns,
        anchor_ns=anchor_ns,
        decision_ns=decision_ns,
    )

    buy = Decimal("0")
    sell = Decimal("0")
    buy_count = 0
    sell_count = 0
    for trade in window:
        if trade.aggressor_side == "BUY":
            buy += trade.quote_notional
            buy_count += 1
        elif trade.aggressor_side == "SELL":
            sell += trade.quote_notional
            sell_count += 1
        else:
            raise ValueError(f"invalid aggressor side: {trade.aggressor_side}")

    return FlowSummary(
        buy_notional=buy,
        sell_notional=sell,
        buy_trade_count=buy_count,
        sell_trade_count=sell_count,
    )


def reconstruct_state(
    *,
    venue: str,
    native_symbol: str,
    anchor_ns: int,
    decision_ns: int,
    book_observations: Sequence[TimedBookMetrics],
    trades: Sequence[CanonicalTrade],
) -> ReconstructedState:
    if decision_ns < anchor_ns:
        raise ValueError("decision must be >= anchor")
    if not book_observations:
        raise ValueError("book observations are empty")

    assert_no_future(
        book_observations,
        timestamp_ns=lambda row: row.timestamp_ns,
        decision_ns=decision_ns,
    )
    eligible = [
        row for row in book_observations
        if row.timestamp_ns <= decision_ns
    ]
    pre_candidates = [
        row for row in eligible
        if row.timestamp_ns <= anchor_ns
    ]
    decision_candidates = [
        row for row in eligible
        if row.timestamp_ns <= decision_ns
    ]
    if not pre_candidates:
        raise ValueError("no pre-anchor book state available")
    if not decision_candidates:
        raise ValueError("no decision-time book state available")

    pre = max(pre_candidates, key=lambda row: row.timestamp_ns)
    decision = max(decision_candidates, key=lambda row: row.timestamp_ns)

    in_window = [
        row for row in eligible
        if anchor_ns <= row.timestamp_ns <= decision_ns
    ]
    if not in_window:
        raise ValueError("no book observations in decision window")

    pre_mid = pre.metrics.mid
    decision_mid = decision.metrics.mid
    if decision_mid >= pre_mid:
        extreme_mid = max(row.metrics.mid for row in in_window)
    else:
        extreme_mid = min(row.metrics.mid for row in in_window)

    max_spread = max(row.metrics.spread_abs for row in in_window)
    flow = aggregate_aggressive_flow(
        trades,
        venue=venue,
        native_symbol=native_symbol,
        anchor_ns=anchor_ns,
        decision_ns=decision_ns,
    )

    state = state_vector(
        pre_mid=float(pre_mid),
        decision_mid=float(decision_mid),
        extreme_mid_to_decision=float(extreme_mid),
        buy_notional=float(flow.buy_notional),
        sell_notional=float(flow.sell_notional),
        spread_pre=float(pre.metrics.spread_abs),
        spread_now=float(decision.metrics.spread_abs),
        max_spread_to_decision=float(max_spread),
        depth_pre=float(pre.metrics.total_depth_quote),
        depth_now=float(decision.metrics.total_depth_quote),
    )

    pre_spread_bps = float(pre.metrics.spread_bps)
    if pre_spread_bps <= 0:
        raise ValueError("pre-anchor spread_bps must be > 0")
    decision_return_bps = state["decision_return_bps"]
    if decision_return_bps is None:
        raise ValueError("decision return unexpectedly missing")

    state["pre_spread_bps"] = pre_spread_bps
    state["displacement_in_pre_spreads"] = abs(
        float(decision_return_bps)
    ) / pre_spread_bps
    state["bid_depth_vs_pre"] = ratio(
        float(decision.metrics.bid_depth_quote),
        float(pre.metrics.bid_depth_quote),
    )
    state["ask_depth_vs_pre"] = ratio(
        float(decision.metrics.ask_depth_quote),
        float(pre.metrics.ask_depth_quote),
    )

    return ReconstructedState(
        venue=venue,
        native_symbol=native_symbol,
        anchor_ns=anchor_ns,
        decision_ns=decision_ns,
        pre_book_sequence=pre.metrics.sequence_last,
        decision_book_sequence=decision.metrics.sequence_last,
        feature_trade_count=flow.buy_trade_count + flow.sell_trade_count,
        state=state,
    )
