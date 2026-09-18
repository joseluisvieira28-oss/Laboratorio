from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

from .market import MEXCFuturesPublicFeed
from .mexc_spot import MEXCSpotPublicFeed
from .spot_mapping import spot_perp_mapping_receipt
from .friction import MEXC_API_TAKER_ONE_WAY_FRACTION

BASE_BUDGET_BPS=10.0
STRESS_BUDGET_BPS=20.0
DAY_MS=86_400_000.0
SPOT_REFERENCE_TAKER_ONE_WAY_FRACTION=0.0005


def _require_nonnegative(x:float,name:str)->float:
    x=float(x)
    if not isfinite(x) or x<0:
        raise ValueError(f"invalid {name}")
    return x


def _trailing_24h_short_burden_bps(rows:list[dict],server_ms:float)->dict[str,Any]:
    start=server_ms-DAY_MS
    rates=[]
    settlements=[]
    for row in rows:
        try:
            ts=float(row["settleTime"])
            rate=float(row["fundingRate"])
        except (KeyError,TypeError,ValueError):
            continue
        if start<=ts<=server_ms:
            settlements.append(ts)
            rates.append(rate)
    signed_short_burden_bps=-sum(rates)*10_000.0
    conservative=max(0.0,signed_short_burden_bps)
    return {
        "window_start_ms":start,
        "window_end_ms":server_ms,
        "settlement_count":len(rates),
        "signed_short_burden_bps_proxy":signed_short_burden_bps,
        "conservative_nonnegative_short_burden_bps_proxy":conservative,
        "warning":"Trailing settled funding is a historical diagnostic, not a forecast."
    }


def evaluate_public_mapping(
    *,
    spot_receipt:dict,
    futures_spread_bps:float,
    short_funding_burden_bps:float,
)->dict[str,Any]:
    spot_spread=_require_nonnegative(
        spot_receipt["long_mapping_candidate"]["spread_bps"],"spot spread"
    )
    futures_spread=_require_nonnegative(futures_spread_bps,"futures spread")
    funding=_require_nonnegative(short_funding_burden_bps,"short funding burden")

    long_rt_fee=2*SPOT_REFERENCE_TAKER_ONE_WAY_FRACTION*10_000.0
    short_rt_fee=2*MEXC_API_TAKER_ONE_WAY_FRACTION*10_000.0
    long_proxy=long_rt_fee+spot_spread
    short_proxy=short_rt_fee+futures_spread+funding

    return {
        "long_spot":{
            "reference_taker_round_trip_fee_bps":long_rt_fee,
            "spread_bps":spot_spread,
            "public_proxy_round_trip_bps":long_proxy,
            "base10_compatible_public_proxy":long_proxy<=BASE_BUDGET_BPS,
            "stress20_compatible_public_proxy":long_proxy<=STRESS_BUDGET_BPS,
        },
        "short_perp":{
            "reference_taker_round_trip_fee_bps":short_rt_fee,
            "spread_bps":futures_spread,
            "conservative_nonnegative_trailing_24h_funding_burden_bps":funding,
            "public_proxy_round_trip_bps":short_proxy,
            "base10_compatible_public_proxy":short_proxy<=BASE_BUDGET_BPS,
            "stress20_compatible_public_proxy":short_proxy<=STRESS_BUDGET_BPS,
        },
        "account_specific_fee_verified":False,
        "authenticated_transport_verified":False,
        "execution_authority_present":False,
        "orders_created":False,
        "capital_enabled":False,
    }


def options_v21_exec_public_receipt(
    *,
    spot:MEXCSpotPublicFeed|None=None,
    futures:MEXCFuturesPublicFeed|None=None,
)->dict[str,Any]:
    spot=spot or MEXCSpotPublicFeed(timeout=10)
    futures=futures or MEXCFuturesPublicFeed(timeout=10)
    mapping=spot_perp_mapping_receipt(spot=spot,futures=futures)

    server_ms=float(futures.server_time_ms())
    snaps=futures.all_market_snapshots()
    snap=snaps["BTCUSDT"]
    bid=float(snap.bid_price); ask=float(snap.ask_price)
    if bid<=0 or ask<=0 or ask<bid:
        raise ValueError("invalid futures top of book")
    mid=(bid+ask)/2.0
    futures_spread=((ask-bid)/mid)*10_000.0

    rows=futures.funding_rate_history("BTC_USDT",page_num=1,page_size=100)
    funding=_trailing_24h_short_burden_bps(rows,server_ms)
    evaluation=evaluate_public_mapping(
        spot_receipt=mapping,
        futures_spread_bps=futures_spread,
        short_funding_burden_bps=funding["conservative_nonnegative_short_burden_bps_proxy"],
    )
    return {
        "receipt_type":"OPTIONS_V21_EXEC_MAPPING_PUBLIC_V0.1",
        "status":"PUBLIC_OBSERVATION_ONLY",
        "checked_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "mapping_contract":"OPTIONS_SPOTPERP_001_V21_EXEC_MAPPING_V0.1.json",
        "spot_perp_mapping":mapping,
        "short_trailing_24h_funding":funding,
        "evaluation":evaluation,
        "scientific_rule_changed":False,
        "authenticated_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
        "capital_enabled":False,
    }
