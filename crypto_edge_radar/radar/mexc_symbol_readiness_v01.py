from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

from .market import MEXCFuturesPublicFeed
from .mexc_auth_readonly import MEXCFuturesAuthenticatedReadOnlyClient


READINESS_ID = "MEXC_SYMBOL_READINESS_V0.1"


def _safe_float(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not numeric") from exc
    if not isfinite(out):
        raise ValueError(f"{field} is not finite")
    return out


def _canonical(symbol: str) -> str:
    return symbol.upper().replace("_", "")


def _min_notional(contract: dict[str, Any], price: float) -> dict[str, float]:
    min_vol = _safe_float(contract.get("minVol"), "minVol")
    contract_size = _safe_float(contract.get("contractSize"), "contractSize")
    vol_unit = _safe_float(contract.get("volUnit"), "volUnit")
    price_unit = _safe_float(contract.get("priceUnit"), "priceUnit")
    base_qty = min_vol * contract_size
    return {
        "min_contract_volume": min_vol,
        "contract_volume_step": vol_unit,
        "contract_size_base": contract_size,
        "price_tick": price_unit,
        "minimum_base_quantity_estimate": base_qty,
        "minimum_executable_notional_estimate_usdt": base_qty * price,
    }


def run_symbol_readiness(
    *,
    symbol: str,
    private_client: MEXCFuturesAuthenticatedReadOnlyClient,
    public_feed: MEXCFuturesPublicFeed | None = None,
    require_no_global_open_positions: bool = True,
) -> dict[str, Any]:
    """Read-only candidate-symbol readiness probe.

    It intentionally has no order, cancel, leverage mutation, transfer, or
    withdrawal capability. A PASS is technical readiness only and never
    authorizes capital or a candidate.
    """

    public_feed = public_feed or MEXCFuturesPublicFeed(timeout=10)
    symbol = symbol.upper()
    blockers: list[str] = []
    checks: dict[str, Any] = {}

    try:
        contract = public_feed.contract_row(symbol)
        snapshots = public_feed.all_market_snapshots()
        canonical = _canonical(symbol)
        if canonical not in snapshots:
            raise ValueError(f"{canonical} market snapshot missing")
        price = _safe_float(snapshots[canonical].last_price, "last_price")
        funding = public_feed.funding_rate(symbol)
        calc = _min_notional(contract, price)
        contract_ok = (
            contract.get("apiAllowed") is True
            and contract.get("state") in (None, 0)
            and contract.get("futureType") in (None, 1)
            and contract.get("positionOpenType") in (1, 3)
        )
        checks["contract"] = {
            "pass": contract_ok,
            "symbol": symbol,
            "reference_price": price,
            "api_allowed": contract.get("apiAllowed"),
            "state": contract.get("state"),
            "future_type": contract.get("futureType"),
            "position_open_type": contract.get("positionOpenType"),
            "min_leverage": contract.get("minLeverage"),
            "max_leverage": contract.get("maxLeverage"),
            **calc,
        }
        if not contract_ok:
            blockers.append(f"{symbol}_CONTRACT_NOT_API_ELIGIBLE")
        checks["funding"] = {
            "pass": all(
                key in funding
                for key in ("fundingRate", "nextSettleTime", "idxPrice", "fairPrice")
            ),
            "funding_rate": funding.get("fundingRate"),
            "next_settle_time_ms": funding.get("nextSettleTime"),
        }
        if not checks["funding"]["pass"]:
            blockers.append(f"{symbol}_FUNDING_DATA_INCOMPLETE")
    except Exception as exc:
        checks["contract"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append(f"{symbol}_PUBLIC_METADATA_FAILED")

    try:
        fees = private_client.fee_details(symbol)
        maker_raw = fees.get("realMakerFee", fees.get("makerFee"))
        taker_raw = fees.get("realTakerFee", fees.get("takerFee"))
        maker = _safe_float(maker_raw, "maker_fee")
        taker = _safe_float(taker_raw, "taker_fee")
        checks["fees"] = {
            "pass": maker >= 0 and taker >= 0,
            "maker_fee_fraction": maker,
            "taker_fee_fraction": taker,
            "maker_fee_bps": maker * 10000.0,
            "taker_fee_bps": taker * 10000.0,
        }
        if maker < 0 or taker < 0:
            blockers.append(f"{symbol}_FEE_RATE_INVALID")
    except Exception as exc:
        checks["fees"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append(f"{symbol}_FEE_READ_FAILED")

    try:
        symbol_positions = private_client.open_positions(symbol)
        checks["symbol_positions"] = {
            "pass": len(symbol_positions) == 0,
            "count": len(symbol_positions),
        }
        if symbol_positions:
            blockers.append(f"{symbol}_OPEN_POSITION_PRESENT")
    except Exception as exc:
        checks["symbol_positions"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append(f"{symbol}_POSITION_READ_FAILED")

    try:
        symbol_orders = private_client.open_orders(symbol)
        checks["symbol_orders"] = {
            "pass": len(symbol_orders) == 0,
            "count": len(symbol_orders),
        }
        if symbol_orders:
            blockers.append(f"{symbol}_OPEN_ORDER_PRESENT")
    except Exception as exc:
        checks["symbol_orders"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append(f"{symbol}_ORDER_READ_FAILED")

    try:
        leverage_rows = private_client.leverage(symbol)
        checks["leverage"] = {
            "pass": bool(leverage_rows),
            "rows": [
                {
                    "position_type": row.get("positionType"),
                    "open_type": row.get("openType"),
                    "leverage": row.get("leverage"),
                    "auto_add_im": row.get("autoAddIm"),
                }
                for row in leverage_rows
            ],
            "execution_requirement": "exactly 1x isolated and Auto Margin Add OFF before live order",
        }
        if not leverage_rows:
            blockers.append(f"{symbol}_LEVERAGE_STATE_EMPTY")
    except Exception as exc:
        checks["leverage"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append(f"{symbol}_LEVERAGE_READ_FAILED")

    try:
        risk = private_client.risk_limit(symbol)
        checks["risk_limit"] = {"pass": risk is not None}
        if risk is None:
            blockers.append(f"{symbol}_RISK_LIMIT_EMPTY")
    except Exception as exc:
        checks["risk_limit"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
        blockers.append(f"{symbol}_RISK_LIMIT_READ_FAILED")

    if require_no_global_open_positions:
        try:
            global_positions = private_client.open_positions()
            checks["global_positions"] = {
                "pass": len(global_positions) == 0,
                "count": len(global_positions),
                "symbols": [row.get("symbol") for row in global_positions],
            }
            if global_positions:
                blockers.append("GLOBAL_OPEN_FUTURES_POSITION_PRESENT")
        except Exception as exc:
            checks["global_positions"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
            blockers.append("GLOBAL_OPEN_POSITIONS_READ_FAILED")

    return {
        "readiness_id": READINESS_ID,
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "symbol": symbol,
        "status": "PASS_TECHNICAL_READINESS_ONLY" if not blockers else "FAIL_CLOSED",
        "pass": not blockers,
        "blockers": blockers,
        "checks": checks,
        "authority": {
            "live_activation_authorized": False,
            "scientific_credit": False,
            "note": "technical read-only probe only; candidate-specific operator authority is still required",
        },
    }


__all__ = ["READINESS_ID", "run_symbol_readiness"]
