from __future__ import annotations

from datetime import datetime, timezone
import time

from .market import MEXCFuturesPublicFeed, MarketDataError

MEXC_API_MAKER_ONE_WAY_FRACTION = 0.0006
MEXC_API_TAKER_ONE_WAY_FRACTION = 0.0008
ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS = 21.2
ETF_CME_HOLD_DAYS = 7
FEE_SOURCE = "MEXC_OFFICIAL_API_FUTURES_FEE_UPDATE_2026-05-28_EFFECTIVE_2026-06-01"


def _bps(value: float) -> float:
    return value * 10_000.0


def _float(value, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise MarketDataError(f"invalid numeric field {name}") from exc
    return out


def mexc_friction_shadow_receipt(
    *,
    symbol: str = "BTC_USDT",
    feed: MEXCFuturesPublicFeed | None = None,
) -> dict:
    """Capture public-only execution-friction observables.

    This is deliberately not an execution simulator. It records observable
    components without inventing future exit liquidity, fill probability or
    future funding. Any projections are labelled as scenarios only.
    """

    feed = feed or MEXCFuturesPublicFeed(timeout=10)

    local_before_ms = time.time_ns() / 1_000_000.0
    server_ms = float(feed.server_time_ms())
    local_after_ms = time.time_ns() / 1_000_000.0
    request_rtt_ms = local_after_ms - local_before_ms
    local_midpoint_ms = (local_before_ms + local_after_ms) / 2.0
    clock_offset_ms = server_ms - local_midpoint_ms

    canonical = symbol.replace("_", "").upper()
    snapshots = feed.all_market_snapshots()
    if canonical not in snapshots:
        raise MarketDataError(f"ticker snapshot missing {canonical}")
    snap = snapshots[canonical]

    contract = feed.contract_row(symbol)
    if contract.get("apiAllowed") is False:
        raise MarketDataError(f"API trading not allowed for {symbol}")
    if contract.get("futureType") not in (None, 1):
        raise MarketDataError(f"contract is not perpetual: {symbol}")
    if contract.get("state") not in (None, 0):
        raise MarketDataError(f"contract is not enabled: {symbol}")

    depth = feed.order_book_depth(symbol, limit=20)
    funding = feed.funding_rate(symbol)
    trades = feed.recent_trades(symbol, limit=20)

    bid = _float(snap.bid_price, "bid")
    ask = _float(snap.ask_price, "ask")
    if bid <= 0 or ask <= 0 or ask < bid:
        raise MarketDataError("invalid top of book")
    mid = (bid + ask) / 2.0
    spread_bps = ((ask - bid) / mid) * 10_000.0
    long_entry_cross_bps = ((ask - mid) / mid) * 10_000.0
    short_entry_cross_bps = ((mid - bid) / mid) * 10_000.0

    funding_rate = _float(funding["fundingRate"], "fundingRate")
    collect_cycle_hours = int(funding["collectCycle"])
    if collect_cycle_hours <= 0:
        raise MarketDataError("collectCycle must be positive")
    idx_price = _float(funding["idxPrice"], "idxPrice")
    fair_price = _float(funding["fairPrice"], "fairPrice")
    if idx_price <= 0 or fair_price <= 0:
        raise MarketDataError("funding price fields must be positive")
    fair_index_basis_bps = ((fair_price - idx_price) / idx_price) * 10_000.0

    maker_rt_fee_bps = _bps(2.0 * MEXC_API_MAKER_ONE_WAY_FRACTION)
    taker_rt_fee_bps = _bps(2.0 * MEXC_API_TAKER_ONE_WAY_FRACTION)
    same_book_taker_proxy_bps = taker_rt_fee_bps + spread_bps
    fee_only_headroom_bps = ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS - taker_rt_fee_bps
    observable_proxy_headroom_bps = ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS - same_book_taker_proxy_bps

    settlements_if_constant = (ETF_CME_HOLD_DAYS * 24.0) / float(collect_cycle_hours)
    constant_rate_7d_magnitude_bps = abs(funding_rate) * settlements_if_constant * 10_000.0

    best_ask = depth.get("asks", [None])[0]
    best_bid = depth.get("bids", [None])[0]

    return {
        "receipt_type": "MEXC_FRICTION_SHADOW_V1",
        "status": "PUBLIC_OBSERVATION_ONLY",
        "capital_enabled": False,
        "orders_created": False,
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "provider": feed.provider,
        "symbol": symbol,
        "canonical_symbol": canonical,
        "contract": {
            "api_allowed": contract.get("apiAllowed"),
            "future_type": contract.get("futureType"),
            "state": contract.get("state"),
            "contract_size": contract.get("contractSize"),
            "min_vol": contract.get("minVol"),
            "vol_unit": contract.get("volUnit"),
            "position_open_type": contract.get("positionOpenType"),
        },
        "clock": {
            "server_time_ms": server_ms,
            "request_rtt_ms": request_rtt_ms,
            "estimated_server_minus_local_ms": clock_offset_ms,
            "note": "Offset uses the request midpoint and is diagnostic, not an NTP substitute.",
        },
        "top_of_book": {
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "spread_bps": spread_bps,
            "long_entry_cross_bps_vs_mid": long_entry_cross_bps,
            "short_entry_cross_bps_vs_mid": short_entry_cross_bps,
            "depth_best_bid_raw": best_bid,
            "depth_best_ask_raw": best_ask,
        },
        "fees": {
            "source": FEE_SOURCE,
            "maker_one_way_fraction": MEXC_API_MAKER_ONE_WAY_FRACTION,
            "taker_one_way_fraction": MEXC_API_TAKER_ONE_WAY_FRACTION,
            "maker_round_trip_bps": maker_rt_fee_bps,
            "taker_round_trip_bps": taker_rt_fee_bps,
            "must_revalidate_before_capital": True,
        },
        "funding_and_basis": {
            "current_funding_rate": funding_rate,
            "current_funding_rate_bps_per_settlement": funding_rate * 10_000.0,
            "collect_cycle_hours": collect_cycle_hours,
            "next_settle_time_ms": funding.get("nextSettleTime"),
            "index_price": idx_price,
            "fair_price": fair_price,
            "fair_minus_index_bps": fair_index_basis_bps,
            "constant_current_rate_7d_absolute_magnitude_bps_scenario": constant_rate_7d_magnitude_bps,
            "scenario_warning": "Not a forecast. Future funding and direction of payment are not inferred by this receipt.",
        },
        "edge_budget": {
            "historical_estimated_break_even_round_trip_bps": ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS,
            "taker_fee_only_headroom_bps": fee_only_headroom_bps,
            "same_book_taker_round_trip_proxy_bps": same_book_taker_proxy_bps,
            "headroom_after_fee_plus_current_spread_proxy_bps": observable_proxy_headroom_bps,
            "interpretation": "Proxy excludes future exit-book changes, market impact beyond best quote, realized funding and spot-perpetual mapping drift.",
        },
        "recent_trade_sample": {
            "count": len(trades),
            "latest": trades[0] if trades else None,
        },
        "unresolved_for_capital": [
            "prospective realized entry slippage",
            "prospective realized exit slippage",
            "realized 7-day funding path",
            "maker fill-selection risk if maker semantics are considered",
            "authenticated order acknowledgement/fill latency",
            "partial-fill/rejection behavior",
            "strategy-specific exposure-loss model",
        ],
    }
