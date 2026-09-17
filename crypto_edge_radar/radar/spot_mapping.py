from __future__ import annotations

from datetime import datetime, timezone

from .market import MEXCFuturesPublicFeed
from .mexc_spot import MEXCSpotPublicFeed, MEXCSpotPublicError


def _f(value, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise MEXCSpotPublicError(f"invalid {name}") from exc
    if out <= 0:
        raise MEXCSpotPublicError(f"non-positive {name}")
    return out


def spot_perp_mapping_receipt(
    *,
    spot: MEXCSpotPublicFeed | None = None,
    futures: MEXCFuturesPublicFeed | None = None,
) -> dict:
    spot = spot or MEXCSpotPublicFeed(timeout=10)
    futures = futures or MEXCFuturesPublicFeed(timeout=10)

    supported = spot.default_symbols()
    if "BTCUSDT" not in supported:
        raise MEXCSpotPublicError("BTCUSDT absent from MEXC spot defaultSymbols")

    book = spot.book_ticker("BTCUSDT")
    depth = spot.depth("BTCUSDT", limit=20)
    last = spot.price("BTCUSDT")
    bid = _f(book["bidPrice"], "spot bid")
    ask = _f(book["askPrice"], "spot ask")
    if ask < bid:
        raise MEXCSpotPublicError("spot ask below bid")
    spot_mid = (bid + ask) / 2.0
    spot_spread_bps = (ask - bid) / spot_mid * 10_000.0

    futures_snapshots = futures.all_market_snapshots()
    if "BTCUSDT" not in futures_snapshots:
        raise MEXCSpotPublicError("BTCUSDT futures snapshot missing")
    perp = futures_snapshots["BTCUSDT"]
    perp_mid = (float(perp.bid_price) + float(perp.ask_price)) / 2.0
    if perp_mid <= 0:
        raise MEXCSpotPublicError("perpetual midpoint non-positive")
    perp_minus_spot_bps = (perp_mid - spot_mid) / spot_mid * 10_000.0

    return {
        "receipt_type": "ETF_CME_EXEC_V2_SPOT_PERP_MAPPING_SHADOW",
        "status": "PUBLIC_OBSERVATION_ONLY",
        "capital_enabled": False,
        "orders_created": False,
        "authenticated_api_used": False,
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "long_mapping_candidate": {
            "market": "MEXC_SPOT",
            "symbol": "BTCUSDT",
            "api_default_symbol_supported": True,
            "last_price": last,
            "bid": bid,
            "ask": ask,
            "mid": spot_mid,
            "spread_bps": spot_spread_bps,
            "depth_best_bid_raw": depth["bids"][0],
            "depth_best_ask_raw": depth["asks"][0],
            "funding_cost": "NONE_FOR_UNLEVERED_SPOT_HOLD",
            "general_mexc_spot_fee_reference": {
                "maker_fraction": 0.0,
                "taker_fraction": 0.0005,
                "status": "REFERENCE_ONLY_NOT_ACCOUNT_OR_API_CHANNEL_RECEIPT",
            },
        },
        "short_mapping_candidate": {
            "market": "MEXC_USDT_PERPETUAL",
            "symbol": "BTC_USDT",
            "mid": perp_mid,
            "funding_applies": True,
        },
        "cross_market": {
            "perp_minus_spot_mid_bps": perp_minus_spot_bps,
            "note": "Instantaneous basis diagnostic only; it is not a return forecast and does not justify changing the frozen signal."
        },
        "gates": {
            "spot_public_api_support": "PASS",
            "spot_account_api_fee": "UNVERIFIED_BLOCKER",
            "spot_authenticated_order_transport": "DISABLED",
            "short_perp_friction": "SEPARATE_GATE_REQUIRED",
            "capital": "BLOCKED",
        },
    }
