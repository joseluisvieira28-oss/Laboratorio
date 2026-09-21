from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Callable

from .market import MEXCFuturesPublicFeed, MarketDataError
from .mexc_auth_readonly import (
    MEXCAuthenticatedReadError,
    MEXCFuturesAuthenticatedReadOnlyClient,
)

PREFLIGHT_ID = "MEXC_FUTURES_AUTHENTICATED_READ_ONLY_PREFLIGHT_V0.1"
SYMBOL = "BTC_USDT"
CANONICAL_SYMBOL = "BTCUSDT"
MAX_ABS_CLOCK_OFFSET_MS = 500.0
MAX_PUBLIC_RTT_MS = 1500.0

# Frozen existing Crypto Lab execution-control value. This is not new science.
ETF_VALIDATION_ALLOCATION_FRACTION = 0.001

DOCUMENTED_RATE_LIMITS = {
    "contract_detail": "1 request / 5 seconds",
    "public_ping": "20 requests / 2 seconds",
    "private_read_endpoints": "20 requests / 2 seconds",
}


@dataclass(frozen=True)
class PreflightResult:
    preflight_id: str
    status: str
    pass_: bool
    checked_at_utc: str
    blockers: list[str]
    warnings: list[str]
    checks: dict[str, Any]
    security: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["pass"] = out.pop("pass_")
        return out


def _safe_float(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not numeric") from exc
    if not isfinite(out):
        raise ValueError(f"{field} is not finite")
    return out


def _find_usdt_asset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if str(row.get("currency", "")).upper() == "USDT":
            return row
    raise ValueError("USDT asset row missing")


def _market_price_from_snapshot(feed: MEXCFuturesPublicFeed) -> float:
    snapshots = feed.all_market_snapshots()
    if CANONICAL_SYMBOL not in snapshots:
        raise ValueError("BTCUSDT market snapshot missing")
    return _safe_float(snapshots[CANONICAL_SYMBOL].last_price, "last_price")


def _contract_min_notional_estimate_usdt(
    *,
    contract: dict[str, Any],
    reference_price: float,
) -> dict[str, Any]:
    min_vol = _safe_float(contract.get("minVol"), "minVol")
    vol_unit = _safe_float(contract.get("volUnit"), "volUnit")
    contract_size = _safe_float(contract.get("contractSize"), "contractSize")
    price_unit = _safe_float(contract.get("priceUnit"), "priceUnit")
    quantity_base = min_vol * contract_size
    notional = quantity_base * reference_price
    return {
        "min_contract_volume": min_vol,
        "contract_volume_step": vol_unit,
        "contract_size_base": contract_size,
        "minimum_base_quantity_estimate": quantity_base,
        "price_tick": price_unit,
        "reference_price": reference_price,
        "minimum_executable_notional_estimate_usdt": notional,
        "calculation": "minVol * contractSize * reference_price",
    }


def run_authenticated_preflight(
    *,
    private_client: MEXCFuturesAuthenticatedReadOnlyClient,
    public_feed: MEXCFuturesPublicFeed | None = None,
    clock_ms: Callable[[], float] | None = None,
) -> dict[str, Any]:
    public_feed = public_feed or MEXCFuturesPublicFeed(timeout=10)
    clock_ms = clock_ms or (lambda: time.time_ns() / 1_000_000.0)

    blockers: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    # Public clock and contract state.
    try:
        t0 = float(clock_ms())
        server_ms = float(public_feed.server_time_ms())
        t1 = float(clock_ms())
        rtt_ms = max(0.0, t1 - t0)
        midpoint = (t0 + t1) / 2.0
        offset_ms = server_ms - midpoint
        clock_ok = abs(offset_ms) <= MAX_ABS_CLOCK_OFFSET_MS
        rtt_ok = rtt_ms <= MAX_PUBLIC_RTT_MS
        checks["clock"] = {
            "pass": clock_ok and rtt_ok,
            "server_time_ms": server_ms,
            "server_minus_local_midpoint_ms": offset_ms,
            "request_rtt_ms": rtt_ms,
            "max_abs_offset_ms": MAX_ABS_CLOCK_OFFSET_MS,
            "max_rtt_ms": MAX_PUBLIC_RTT_MS,
        }
        if not clock_ok:
            blockers.append("WINDOWS_CLOCK_OFFSET_OUTSIDE_500MS")
        if not rtt_ok:
            blockers.append("MEXC_PUBLIC_RTT_OUTSIDE_1500MS")
    except Exception as exc:
        checks["clock"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append("MEXC_SERVER_CLOCK_CHECK_FAILED")

    try:
        contract = public_feed.contract_row(SYMBOL)
        market_price = _market_price_from_snapshot(public_feed)
        funding = public_feed.funding_rate(SYMBOL)
        contract_calc = _contract_min_notional_estimate_usdt(
            contract=contract,
            reference_price=market_price,
        )
        contract_ok = (
            contract.get("apiAllowed") is True
            and contract.get("state") in (None, 0)
            and contract.get("futureType") in (None, 1)
            and contract.get("positionOpenType") in (1, 3)
        )
        checks["contract"] = {
            "pass": contract_ok,
            "symbol": SYMBOL,
            "api_allowed": contract.get("apiAllowed"),
            "state": contract.get("state"),
            "future_type": contract.get("futureType"),
            "position_open_type": contract.get("positionOpenType"),
            "min_leverage": contract.get("minLeverage"),
            "max_leverage": contract.get("maxLeverage"),
            **contract_calc,
        }
        if not contract_ok:
            blockers.append("BTC_USDT_CONTRACT_NOT_MICROLIVE_ELIGIBLE")
        checks["funding"] = {
            "pass": "fundingRate" in funding and "nextSettleTime" in funding,
            "funding_rate": funding.get("fundingRate"),
            "collect_cycle_hours": funding.get("collectCycle"),
            "next_settle_time_ms": funding.get("nextSettleTime"),
            "fair_price": funding.get("fairPrice"),
            "index_price": funding.get("idxPrice"),
        }
        if not checks["funding"]["pass"]:
            blockers.append("BTC_USDT_FUNDING_DATA_INCOMPLETE")
    except Exception as exc:
        checks["contract"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append("BTC_USDT_PUBLIC_METADATA_FAILED")

    # Private account reads.
    try:
        assets = private_client.assets()
        usdt = _find_usdt_asset(assets)
        equity = _safe_float(usdt.get("equity"), "equity")
        available = _safe_float(usdt.get("availableBalance"), "availableBalance")
        checks["account"] = {
            "pass": equity >= 0 and available >= 0,
            "currency": "USDT",
            "equity_usdt": equity,
            "available_balance_usdt": available,
            "cash_balance_usdt": usdt.get("cashBalance"),
            "frozen_balance_usdt": usdt.get("frozenBalance"),
            "position_margin_usdt": usdt.get("positionMargin"),
            "unrealized_usdt": usdt.get("unrealized"),
            "operator_account_identity_confirmation_required": True,
        }
        if equity < 0 or available < 0:
            blockers.append("USDT_ACCOUNT_BALANCE_INVALID")
    except Exception as exc:
        checks["account"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append("AUTHENTICATED_ACCOUNT_BALANCE_READ_FAILED")
        equity = None

    try:
        positions = private_client.open_positions()
        checks["positions"] = {
            "pass": len(positions) == 0,
            "open_position_count": len(positions),
            "positions": [
                {
                    "symbol": row.get("symbol"),
                    "position_type": row.get("positionType"),
                    "open_type": row.get("openType"),
                    "hold_vol": row.get("holdVol"),
                    "leverage": row.get("leverage"),
                    "auto_add_im": row.get("autoAddIm"),
                }
                for row in positions
            ],
        }
        if positions:
            blockers.append("OPEN_FUTURES_POSITION_PRESENT")
    except Exception as exc:
        checks["positions"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append("AUTHENTICATED_OPEN_POSITIONS_READ_FAILED")
        positions = []

    try:
        orders = private_client.open_orders(SYMBOL)
        checks["orders"] = {
            "pass": len(orders) == 0,
            "open_order_count": len(orders),
            "orders": [
                {
                    "order_id": row.get("orderId"),
                    "symbol": row.get("symbol"),
                    "side": row.get("side"),
                    "order_type": row.get("orderType"),
                    "open_type": row.get("openType"),
                    "leverage": row.get("leverage"),
                    "state": row.get("state"),
                }
                for row in orders
            ],
        }
        if orders:
            blockers.append("OPEN_BTC_USDT_ORDER_PRESENT")
    except Exception as exc:
        checks["orders"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append("AUTHENTICATED_OPEN_ORDERS_READ_FAILED")

    try:
        fees = private_client.tiered_fee_rate(SYMBOL)
        maker = _safe_float(fees.get("makerFee"), "makerFee")
        taker = _safe_float(fees.get("takerFee"), "takerFee")
        checks["fees"] = {
            "pass": maker >= 0 and taker >= 0,
            "level": fees.get("level"),
            "maker_fee_fraction": maker,
            "taker_fee_fraction": taker,
            "maker_fee_bps": maker * 10_000.0,
            "taker_fee_bps": taker * 10_000.0,
            "source": "AUTHENTICATED_MEXC_ACCOUNT",
        }
        if maker < 0 or taker < 0:
            blockers.append("AUTHENTICATED_FEE_RATE_INVALID")
    except Exception as exc:
        checks["fees"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append("AUTHENTICATED_FEE_RATE_READ_FAILED")

    # These two read endpoints are documented by MEXC as requiring Trading permission.
    # The software remains GET-only even if the key permission is broader.
    try:
        leverage_rows = private_client.leverage(SYMBOL)
        checks["leverage"] = {
            "pass": bool(leverage_rows),
            "rows": [
                {
                    "position_type": row.get("positionType"),
                    "leverage": row.get("leverage"),
                    "risk_level": row.get("level"),
                    "imr": row.get("imr"),
                    "mmr": row.get("mmr"),
                }
                for row in leverage_rows
            ],
            "execution_requirement": "candidate-specific authority must require exactly 1x before a futures order",
        }
        if not leverage_rows:
            blockers.append("BTC_USDT_LEVERAGE_STATE_EMPTY")
    except Exception as exc:
        checks["leverage"] = {
            "pass": False,
            "error": f"{type(exc).__name__}: {exc}",
            "permission_note": "MEXC documents this GET as requiring Trading permission",
        }
        blockers.append("AUTHENTICATED_LEVERAGE_STATE_READ_FAILED")

    try:
        mode = private_client.position_mode()
        checks["position_mode"] = {
            "pass": True,
            "raw": mode,
            "mode": "HEDGE" if mode == 1 else "ONE_WAY",
        }
    except Exception as exc:
        checks["position_mode"] = {
            "pass": False,
            "error": f"{type(exc).__name__}: {exc}",
            "permission_note": "MEXC documents this GET as requiring Trading permission",
        }
        blockers.append("AUTHENTICATED_POSITION_MODE_READ_FAILED")

    try:
        risk_limit = private_client.risk_limit(SYMBOL)
        checks["risk_limit"] = {"pass": risk_limit is not None, "data": risk_limit}
        if risk_limit is None:
            blockers.append("AUTHENTICATED_RISK_LIMIT_EMPTY")
    except Exception as exc:
        checks["risk_limit"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append("AUTHENTICATED_RISK_LIMIT_READ_FAILED")

    # Existing ETF-CME V2 readiness budget feasibility diagnostic only.
    if equity is not None and "minimum_executable_notional_estimate_usdt" in checks.get("contract", {}):
        budget = equity * ETF_VALIDATION_ALLOCATION_FRACTION
        venue_min = float(checks["contract"]["minimum_executable_notional_estimate_usdt"])
        feasible = venue_min <= budget
        checks["etf_cme_existing_validation_budget"] = {
            "pass": feasible,
            "existing_frozen_fraction_of_equity": ETF_VALIDATION_ALLOCATION_FRACTION,
            "account_equity_usdt": equity,
            "maximum_validation_allocation_usdt": budget,
            "estimated_venue_minimum_notional_usdt": venue_min,
            "no_trade_if_minimum_exceeds_budget": True,
        }
        if not feasible:
            blockers.append("ETF_CME_VENUE_MIN_NOTIONAL_EXCEEDS_FROZEN_VALIDATION_BUDGET")

    # No open position means margin type and Auto Margin Add do not exist as active
    # position state. We refuse to convert the operator UI selector into account truth.
    if not positions:
        checks["active_margin_state"] = {
            "pass": True,
            "state": "NO_OPEN_POSITION",
            "margin_mode": "NOT_APPLICABLE_UNTIL_POSITION_EXISTS",
            "auto_margin_add": "NOT_APPLICABLE_UNTIL_POSITION_EXISTS",
            "execution_requirement": "future candidate-specific order path must set/verify ISOLATED, 1x and Auto Margin Add OFF where applicable",
        }

    checks["rate_limits"] = {
        "pass": True,
        "documented": DOCUMENTED_RATE_LIMITS,
        "client_policy": "single sequential preflight; no polling burst",
    }

    passed = len(blockers) == 0
    result = PreflightResult(
        preflight_id=PREFLIGHT_ID,
        status="PASS" if passed else "FAIL_CLOSED",
        pass_=passed,
        checked_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        blockers=blockers,
        warnings=warnings,
        checks=checks,
        security={
            "authenticated_exchange_api_used": True,
            "http_methods_allowed_by_client": ["GET"],
            "order_endpoint_implemented": False,
            "exchange_mutation_performed": False,
            "withdrawal_endpoint_implemented": False,
            "secret_persisted_by_python": False,
            "api_key_returned_in_receipt": False,
            "api_secret_returned_in_receipt": False,
        },
    )
    return result.to_dict()


def sanitized_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)


__all__ = [
    "PREFLIGHT_ID",
    "run_authenticated_preflight",
    "sanitized_json",
]
