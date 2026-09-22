from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


PREFLIGHT_ID = "MEXC_FUTURES_AUTHENTICATED_READ_ONLY_PREFLIGHT_V0.1"
STANDING_AUTHORITY_ID = "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1"
ETF_ID = "ETF-CME-INSTFLOW-001"
OPTIONS_ID = "OPTIONS-SPOTPERP-001-V2.1"
REQUIRED_EXCHANGE_CHECKS = (
    "account", "clock", "contract", "fees", "funding", "orders",
    "positions", "rate_limits", "risk_limit",
)


def _fail(reason: str, *, receipt_version: str) -> dict[str, Any]:
    return {
        "status": "FAIL_CLOSED",
        "reason": reason,
        "receipt_version": receipt_version,
        "fresh": False,
        "provenance": None,
    }


def _freshness(age: float | None, maximum: float) -> tuple[bool, str | None]:
    if age is None:
        return False, "RECEIPT_TIMESTAMP_INVALID"
    if age < 0:
        return False, "RECEIPT_TIMESTAMP_IN_FUTURE"
    if age > maximum:
        return False, "RECEIPT_STALE"
    return True, None


def _read_receipt(path: Path, *, receipt_version: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON_OBJECT_REQUIRED")
    except FileNotFoundError:
        return None, _fail("RECEIPT_MISSING", receipt_version=receipt_version)
    except Exception as exc:
        return None, _fail(f"RECEIPT_INVALID:{type(exc).__name__}", receipt_version=receipt_version)
    return payload, {
        "receipt_version": receipt_version,
        "provenance": {
            "filename": path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        },
    }


def _age(value: Any, now: datetime) -> float | None:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return None
        return (now - dt.astimezone(timezone.utc)).total_seconds()
    except Exception:
        return None


def _contains_secret(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in {"api_key", "api_secret", "secret_key", "access_key"} and isinstance(value, str) and value:
                return True
            if _contains_secret(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_secret(value) for value in payload)
    return False


def read_mexc_local_state(
    *,
    data_dir: Path,
    standing_authority_path: Path,
    now_utc: datetime | None = None,
    max_preflight_age_seconds: float = 300.0,
    max_risk_age_seconds: float = 120.0,
) -> dict[str, Any]:
    """Consume sanitized local receipts without ever reading credentials.

    Exchange readiness, account risk, standing authority and candidate capital
    compatibility are intentionally independent states. Missing, malformed,
    future-dated or stale receipts fail closed.
    """
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    preflight, pre_meta = _read_receipt(
        data_dir / "mexc_authenticated_preflight_receipt.json",
        receipt_version=PREFLIGHT_ID,
    )
    risk, risk_meta = _read_receipt(
        data_dir / "mexc_account_risk_state.json",
        receipt_version="MEXC_ACCOUNT_RISK_STATE_V0.2",
    )
    standing, standing_meta = _read_receipt(
        standing_authority_path,
        receipt_version=STANDING_AUTHORITY_ID,
    )

    exchange = dict(pre_meta)
    capital = {ETF_ID: _fail("PREFLIGHT_UNAVAILABLE", receipt_version=PREFLIGHT_ID)}
    if preflight is not None:
        age = _age(preflight.get("checked_at_utc"), now)
        checks = preflight.get("checks") if isinstance(preflight.get("checks"), dict) else {}
        missing_or_failed = [name for name in REQUIRED_EXCHANGE_CHECKS if (checks.get(name) or {}).get("pass") is not True]
        security = preflight.get("security") or {}
        safe = (
            not _contains_secret(preflight)
            and security.get("api_key_returned_in_receipt") is False
            and security.get("api_secret_returned_in_receipt") is False
            and security.get("exchange_mutation_performed") is False
            and security.get("withdrawal_endpoint_implemented") is False
        )
        fresh, freshness_reason = _freshness(age, max_preflight_age_seconds)
        valid = preflight.get("preflight_id") == PREFLIGHT_ID and not missing_or_failed and safe and fresh
        exchange.update({
            "status": "PASS" if valid else "FAIL_CLOSED",
            "fresh": fresh,
            "age_seconds": age,
            "checked_at_utc": preflight.get("checked_at_utc"),
            "failed_checks": missing_or_failed,
            "sanitized": safe,
            "account_identity_pass": (checks.get("account") or {}).get("pass") is True,
            "open_position_count": (checks.get("positions") or {}).get("open_position_count"),
            "open_order_count": (checks.get("orders") or {}).get("open_order_count"),
            "reason": None if valid else (
                f"AUTHENTICATED_PREFLIGHT_{freshness_reason}" if not fresh else
                "AUTHENTICATED_PREFLIGHT_SCHEMA_OR_CHECK_FAILURE"
            ),
        })
        legacy = checks.get("etf_cme_existing_validation_budget") or {}
        explicit = ((preflight.get("candidate_feasibility") or {}).get(ETF_ID) or {})
        candidate_pass = explicit.get("pass") is True if explicit else legacy.get("pass") is True
        blockers = list(explicit.get("blockers") or preflight.get("blockers") or [])
        capital[ETF_ID] = {
            "status": "PASS" if candidate_pass else "BLOCKED",
            "pass": candidate_pass,
            "blockers": blockers,
            "maximum_validation_allocation_usdt": legacy.get("maximum_validation_allocation_usdt"),
            "minimum_executable_notional_usdt": legacy.get("estimated_venue_minimum_notional_usdt"),
            "receipt_version": PREFLIGHT_ID,
        }

    risk_state = dict(risk_meta)
    if risk is not None:
        age = _age(risk.get("as_of_utc"), now)
        fresh, freshness_reason = _freshness(age, max_risk_age_seconds)
        valid = risk.get("status") == "PASS" and fresh and not _contains_secret(risk)
        risk_state.update({
            "status": "PASS" if valid else "FAIL_CLOSED",
            "fresh": fresh,
            "age_seconds": age,
            "as_of_utc": risk.get("as_of_utc"),
            "daily_realized_loss_fraction_equity": risk.get("daily_realized_loss_fraction_equity"),
            "weekly_realized_loss_fraction_equity": risk.get("weekly_realized_loss_fraction_equity"),
            "concurrent_planned_risk_fraction_equity": risk.get("concurrent_planned_risk_fraction_equity"),
            "reason": None if valid else (
                f"ACCOUNT_RISK_STATE_{freshness_reason}" if not fresh else
                "ACCOUNT_RISK_STATE_INVALID"
            ),
        })

    authority = dict(standing_meta)
    routes: dict[str, dict[str, Any]] = {}
    if standing is not None:
        scope = standing.get("scope") or {}
        valid = (
            standing.get("authority_id") == STANDING_AUTHORITY_ID
            and standing.get("status") == "ACTIVE_STANDING_OPERATOR_AUTHORIZATION"
            and scope.get("exchange") == "MEXC"
            and scope.get("product") == "USDT_PERPETUAL_FUTURES"
            and scope.get("micro_live_only") is True
            and scope.get("per_trade_reconfirmation_required") is False
            and not _contains_secret(standing)
        )
        for route in standing.get("standing_authorized_routes") or []:
            if isinstance(route, dict) and route.get("strategy_id"):
                routes[str(route["strategy_id"])] = {
                    "operator_authorized": valid,
                    "direction": route.get("direction"),
                    "symbol": route.get("symbol"),
                    "scientific_tier": route.get("scientific_tier"),
                }
        authority.update({
            "status": "ACTIVE" if valid else "FAIL_CLOSED",
            "active": valid,
            "authority_id": standing.get("authority_id"),
            "routes": routes,
        })

    return {
        "schema_version": "RADAR_MEXC_LOCAL_STATE_V0.1",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "exchange_authenticated_preflight": exchange,
        "account_risk_firewall": risk_state,
        "standing_operator_authority": authority,
        "candidate_capital_feasibility": capital,
        "secrets_loaded": False,
        "exchange_mutation_performed": False,
    }
