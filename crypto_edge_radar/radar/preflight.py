from __future__ import annotations

import time
from typing import Callable

from .evidence import EvidenceStore
from .market import MEXCFuturesPublicFeed, MarketDataError

MAX_ABS_CLOCK_OFFSET_MS = 500.0
MAX_PUBLIC_RTT_MS = 1000.0
REQUIRED_SYMBOL = "BTC_USDT"
REQUIRED_CANONICAL_SYMBOL = "BTCUSDT"


def local_node_preflight(
    *,
    feed,
    store,
    clock_ms: Callable[[], float] | None = None,
) -> dict:
    """Validate the public/operator prerequisites before a local node arms.

    This preflight is deliberately public/read-only. It does not inspect
    credentials, account balances, positions or orders. Authenticated transport
    has a separate future gate.
    """

    clock_ms = clock_ms or (lambda: time.time_ns() / 1_000_000.0)
    checks: dict[str, dict] = {}
    blockers: list[str] = []

    provider_ok = isinstance(feed, MEXCFuturesPublicFeed)
    checks["provider"] = {
        "pass": provider_ok,
        "observed": getattr(feed, "provider", type(feed).__name__),
        "required": "MEXC_FUTURES_PUBLIC",
    }
    if not provider_ok:
        blockers.append("LOCAL_OPERATOR_REQUIRES_MEXC_FUTURES_PUBLIC")

    if provider_ok:
        t0 = float(clock_ms())
        server_ms = float(feed.server_time_ms())
        t1 = float(clock_ms())
        rtt_ms = max(0.0, t1 - t0)
        midpoint_ms = (t0 + t1) / 2.0
        offset_ms = server_ms - midpoint_ms
        clock_ok = abs(offset_ms) <= MAX_ABS_CLOCK_OFFSET_MS
        rtt_ok = rtt_ms <= MAX_PUBLIC_RTT_MS
        checks["clock"] = {
            "pass": clock_ok and rtt_ok,
            "server_minus_local_midpoint_ms": offset_ms,
            "request_rtt_ms": rtt_ms,
            "max_abs_offset_ms": MAX_ABS_CLOCK_OFFSET_MS,
            "max_rtt_ms": MAX_PUBLIC_RTT_MS,
        }
        if not clock_ok:
            blockers.append("CLOCK_OFFSET_OUTSIDE_OPERATOR_BUDGET")
        if not rtt_ok:
            blockers.append("PUBLIC_RTT_OUTSIDE_OPERATOR_BUDGET")

        contract = feed.contract_row(REQUIRED_SYMBOL)
        contract_ok = (
            contract.get("apiAllowed") is True
            and contract.get("futureType") in (None, 1)
            and contract.get("state") in (None, 0)
        )
        isolated_supported = contract.get("positionOpenType") in (1, 3)
        checks["contract"] = {
            "pass": contract_ok and isolated_supported,
            "symbol": REQUIRED_SYMBOL,
            "api_allowed": contract.get("apiAllowed"),
            "future_type": contract.get("futureType"),
            "state": contract.get("state"),
            "position_open_type": contract.get("positionOpenType"),
            "isolated_supported": isolated_supported,
        }
        if not contract_ok:
            blockers.append("BTC_USDT_CONTRACT_NOT_EXECUTION_ELIGIBLE")
        if not isolated_supported:
            blockers.append("BTC_USDT_ISOLATED_MARGIN_NOT_SUPPORTED")

        snapshots = feed.all_market_snapshots()
        market_ok = REQUIRED_CANONICAL_SYMBOL in snapshots
        checks["market_data"] = {
            "pass": market_ok,
            "symbol": REQUIRED_CANONICAL_SYMBOL,
        }
        if not market_ok:
            blockers.append("BTC_USDT_PUBLIC_MARKET_DATA_MISSING")

        funding = feed.funding_rate(REQUIRED_SYMBOL)
        funding_ok = "fundingRate" in funding and "nextSettleTime" in funding
        checks["funding_data"] = {
            "pass": funding_ok,
            "funding_rate_present": "fundingRate" in funding,
            "next_settle_time_present": "nextSettleTime" in funding,
        }
        if not funding_ok:
            blockers.append("BTC_USDT_FUNDING_DATA_MISSING")

    result = {
        "preflight": "LOCAL_NODE_PREFLIGHT_V1",
        "pass": len(blockers) == 0,
        "blockers": blockers,
        "checks": checks,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "capital_enabled": False,
    }

    receipt = store.append("LOCAL_NODE_PREFLIGHT", result)
    chain_ok, chain_detail = store.verify_chain()
    result["evidence"] = {
        "append_receipt": receipt,
        "chain_ok": chain_ok,
        "chain_detail": chain_detail,
    }
    if not chain_ok:
        result["pass"] = False
        result["blockers"].append("EVIDENCE_CHAIN_VERIFY_FAIL")
    return result


def require_local_node_preflight(*, feed, store) -> dict:
    result = local_node_preflight(feed=feed, store=store)
    if not result["pass"]:
        raise RuntimeError(f"local node preflight failed: {result['blockers']}")
    return result
