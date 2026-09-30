from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

MAX_INITIAL_MARGIN_USDT = 10.0
MAX_NOTIONAL_USDT = 50.0
REQUIRED_LEVERAGE = 5
MAX_SIMULTANEOUS_POSITIONS = 1
DAILY_REALIZED_LOSS_KILL_USDT = 5.0
ROLLING_7D_REALIZED_LOSS_KILL_USDT = 5.0


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _utc(value: Any) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def _finite_float(value: Any, *, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field} must be finite")
    return out


def _receipt_pnl(row: dict[str, Any]) -> float:
    """Prefer explicit corrected accounting when available; reject non-finite values."""
    for key in (
        "corrected_realized_net_pnl_usdt",
        "realized_net_pnl_usdt_corrected",
        "realized_net_pnl_usdt",
    ):
        if row.get(key) is not None:
            return _finite_float(row[key], field=key)
    raise ValueError("reconciliation missing realized net PnL")



def _load_correction_overlay() -> dict[str, dict[str, Any]]:
    raw = os.getenv("CRYPTO_LAB_PNL_CORRECTION_OVERLAY", "").strip()
    if not raw:
        return {}
    path = Path(raw)
    payload = _load(path)
    rows = payload.get("entries")
    if not isinstance(rows, list):
        raise ValueError("correction overlay entries must be a list")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("correction overlay row must be object")
        signal = str(row.get("signal_identity") or "")
        receipt_hash = str(row.get("original_receipt_sha256") or "")
        if not signal or len(receipt_hash) != 64:
            raise ValueError("correction overlay identity/hash missing")
        if signal in out:
            raise ValueError(f"duplicate correction overlay identity: {signal}")
        _finite_float(row.get("corrected_realized_net_pnl_usdt"), field="corrected_realized_net_pnl_usdt")
        out[signal] = row
    return out


def _pnl_with_overlay(
    *,
    path: Path,
    row: dict[str, Any],
    overlay: dict[str, dict[str, Any]],
) -> float:
    signal = str(row.get("signal_identity") or "")
    correction = overlay.get(signal)
    if correction is None:
        return _receipt_pnl(row)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != str(correction["original_receipt_sha256"]):
        raise ValueError(f"correction receipt hash mismatch for {signal}")
    expected_stored = _finite_float(
        correction.get("stored_net_pnl_usdt"),
        field="stored_net_pnl_usdt",
    )
    actual_stored = _finite_float(
        row.get("realized_net_pnl_usdt"),
        field="realized_net_pnl_usdt",
    )
    if abs(actual_stored - expected_stored) > 1e-12:
        raise ValueError(f"correction stored net mismatch for {signal}")
    return _finite_float(
        correction["corrected_realized_net_pnl_usdt"],
        field="corrected_realized_net_pnl_usdt",
    )


def _receipt_roots(receipt_root: str | Path) -> list[Path]:
    roots = [Path(receipt_root)]
    extra = os.getenv("CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS", "").strip()
    if extra:
        for raw in extra.split(os.pathsep):
            raw = raw.strip()
            if raw:
                roots.append(Path(raw))
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            key = str(root.resolve())
        except Exception:
            key = str(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def _unique_files(receipt_root: str | Path, filename: str) -> list[Path]:
    """Deduplicate physical files even when configured roots overlap."""
    out: list[Path] = []
    seen: set[str] = set()
    for root in _receipt_roots(receipt_root):
        if not root.exists():
            continue
        for path in root.rglob(filename):
            try:
                key = str(path.resolve())
            except Exception:
                key = str(path)
            if key in seen:
                continue
            seen.add(key)
            out.append(path)
    return sorted(out, key=lambda p: str(p))


def _local_receipt_uncertainty(receipt_root: str | Path) -> list[str]:
    blockers: list[str] = []

    for path in _unique_files(receipt_root, "POST_TRADE_RECONCILIATION.json"):
        try:
            row = _load(path)
            _utc(row["closed_at_utc"])
            _receipt_pnl(row)
        except Exception as exc:
            blockers.append(
                f"LOCAL_RECONCILIATION_INVALID:{path}:{type(exc).__name__}"
            )

    for path in _unique_files(receipt_root, "ACTIVE_TRADE_STATE.json"):
        try:
            _load(path)
        except Exception as exc:
            blockers.append(
                f"LOCAL_ACTIVE_STATE_INVALID:{path}:{type(exc).__name__}"
            )

    for path in _unique_files(receipt_root, "ORDER_INTENT.json"):
        try:
            _load(path)
        except Exception as exc:
            blockers.append(
                f"LOCAL_ORDER_INTENT_INVALID:{path}:{type(exc).__name__}"
            )
            continue
        session = path.parent
        if (session / "POST_TRADE_RECONCILIATION.json").exists():
            continue
        if (session / "ENTRY_NOT_SUBMITTED_FINAL.json").exists():
            continue
        if (session / "ENTRY_TERMINAL_NO_FILL_CONFIRMED.json").exists():
            continue
        # An intent without a terminal reconciliation or explicit pre-submit abort
        # reserves the only global slot indefinitely until reconciled.
        blockers.append(f"UNRESOLVED_ORDER_INTENT_RESERVES_GLOBAL_SLOT:{path}")

    return blockers


def local_active_trade_paths(receipt_root: str | Path) -> list[str]:
    out: list[str] = []
    for path in _unique_files(receipt_root, "ACTIVE_TRADE_STATE.json"):
        row = _load(path)
        if row.get("state") not in {"FILLED", "EXIT_PENDING"}:
            continue
        if (path.parent / "POST_TRADE_RECONCILIATION.json").exists():
            continue
        out.append(str(path))
    return sorted(out)


def realized_loss_state(
    receipt_root: str | Path,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    rolling_start = now - timedelta(days=7)
    daily = 0.0
    rolling = 0.0
    counted: list[str] = []
    invalid: list[str] = []
    try:
        overlay = _load_correction_overlay()
    except Exception as exc:
        overlay = {}
        invalid.append(f"CORRECTION_OVERLAY:{type(exc).__name__}:{exc}")

    for path in _unique_files(receipt_root, "POST_TRADE_RECONCILIATION.json"):
        try:
            row = _load(path)
            closed = _utc(row["closed_at_utc"])
            pnl = _pnl_with_overlay(path=path, row=row, overlay=overlay)
        except Exception as exc:
            invalid.append(f"{path}:{type(exc).__name__}")
            continue
        loss = max(0.0, -pnl)
        if closed >= rolling_start:
            rolling += loss
        if closed >= day_start:
            daily += loss
        counted.append(str(path))

    return {
        "daily_realized_loss_usdt": daily,
        "rolling_7d_realized_loss_usdt": rolling,
        "reconciliations_scanned": sorted(counted),
        "invalid_reconciliations": sorted(invalid),
    }


def build_operator_risk_state(
    *,
    private_client,
    receipt_root: str | Path,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    losses = realized_loss_state(receipt_root, now=now)
    blockers: list[str] = _local_receipt_uncertainty(receipt_root)

    try:
        local_active = local_active_trade_paths(receipt_root)
    except Exception as exc:
        local_active = []
        blockers.append(f"LOCAL_ACTIVE_STATE_SCAN_FAILED:{type(exc).__name__}")

    try:
        positions = private_client.open_positions()
    except Exception as exc:
        positions = []
        blockers.append(f"GLOBAL_POSITION_READ_FAILED:{type(exc).__name__}")

    try:
        orders = private_client.open_orders()
    except Exception as exc:
        orders = []
        blockers.append(f"GLOBAL_ORDER_READ_FAILED:{type(exc).__name__}")

    try:
        tpsl_orders = (
            private_client.open_tpsl_orders()
            if hasattr(private_client, "open_tpsl_orders")
            else []
        )
    except Exception as exc:
        tpsl_orders = []
        blockers.append(f"GLOBAL_TPSL_ORDER_READ_FAILED:{type(exc).__name__}")

    try:
        assets = private_client.assets()
        usdt = next(
            row for row in assets
            if str(row.get("currency", "")).upper() == "USDT"
        )
        equity = _finite_float(usdt.get("equity", 0), field="equity")
        available = _finite_float(
            usdt.get("availableBalance", 0), field="availableBalance"
        )
        if equity <= 0 or available < 0:
            blockers.append("FUTURES_ACCOUNT_BALANCE_INVALID")
    except Exception as exc:
        equity = None
        available = None
        blockers.append(f"FUTURES_ACCOUNT_READ_FAILED:{type(exc).__name__}")

    if losses["invalid_reconciliations"]:
        blockers.append("LOCAL_RECONCILIATION_ACCOUNTING_INVALID")

    exchange_open_count = len(positions)
    unresolved_intent = any(
        item.startswith("UNRESOLVED_ORDER_INTENT_RESERVES_GLOBAL_SLOT:")
        for item in blockers
    )
    effective_open = max(
        exchange_open_count,
        len(local_active),
        1 if unresolved_intent else 0,
    )

    if effective_open >= MAX_SIMULTANEOUS_POSITIONS:
        blockers.append("GLOBAL_POSITION_SLOT_OCCUPIED")
    if orders:
        blockers.append("GLOBAL_OPEN_ORDER_PRESENT")
    if tpsl_orders:
        blockers.append("GLOBAL_OPEN_TPSL_ORDER_PRESENT")
    if losses["daily_realized_loss_usdt"] >= DAILY_REALIZED_LOSS_KILL_USDT:
        blockers.append("DAILY_5_USDT_REALIZED_LOSS_KILL_ACTIVE")
    if losses["rolling_7d_realized_loss_usdt"] >= ROLLING_7D_REALIZED_LOSS_KILL_USDT:
        blockers.append("ROLLING_7D_5_USDT_REALIZED_LOSS_KILL_ACTIVE")

    # Preserve order while suppressing duplicates from overlapping diagnostics.
    blockers = list(dict.fromkeys(blockers))

    return {
        "risk_state_id": "CRYPTO-LAB-OPERATOR-GLOBAL-RISK-STATE-V0.2",
        "as_of_utc": now.isoformat().replace("+00:00", "Z"),
        "status": "PASS" if not blockers else "FAIL_CLOSED",
        "pass": not blockers,
        "blockers": blockers,
        "equity_usdt": equity,
        "available_usdt": available,
        "exchange_open_position_count": exchange_open_count,
        "exchange_open_order_count": len(orders),
        "exchange_open_tpsl_order_count": len(tpsl_orders),
        "local_active_trade_count": len(local_active),
        "local_active_trade_receipts": local_active,
        **losses,
        "policy": {
            "max_initial_margin_usdt_per_position": MAX_INITIAL_MARGIN_USDT,
            "max_notional_usdt_per_position": MAX_NOTIONAL_USDT,
            "leverage": REQUIRED_LEVERAGE,
            "margin_mode": "ISOLATED",
            "max_simultaneous_positions": MAX_SIMULTANEOUS_POSITIONS,
            "daily_realized_loss_kill_usdt": DAILY_REALIZED_LOSS_KILL_USDT,
            "rolling_7d_realized_loss_kill_usdt": ROLLING_7D_REALIZED_LOSS_KILL_USDT,
            "per_position_stop_loss": None,
            "daily_kill_is_not_open_position_stop": True,
        },
    }


__all__ = [
    "MAX_INITIAL_MARGIN_USDT",
    "MAX_NOTIONAL_USDT",
    "REQUIRED_LEVERAGE",
    "MAX_SIMULTANEOUS_POSITIONS",
    "DAILY_REALIZED_LOSS_KILL_USDT",
    "ROLLING_7D_REALIZED_LOSS_KILL_USDT",
    "realized_loss_state",
    "local_active_trade_paths",
    "build_operator_risk_state",
]
