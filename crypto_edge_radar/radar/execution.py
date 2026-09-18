from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Protocol

UTC = timezone.utc

CANDIDATE = "CED1D-0031"
SYMBOL = "AVAXUSDT"
PROVIDER = "BINANCE_USDM_PUBLIC"
AUTHORITY_COMMIT = "b0cea0fb9c47a3178599e93bde70c5e5a0207cc9"
ARM_TOKEN = "CED1D-0031-MICROLIVE-V0.1-ONE-EVENT"
EARLIEST_ENTRY_UTC = datetime(2026, 9, 21, 0, 1, tzinfo=UTC)
MAX_NOTIONAL_USDT = Decimal("25")
MAX_REAL_EVENTS = 1
ENTRY_GRACE_SECONDS = 5


class ExecutionBlocked(RuntimeError):
    pass


class TradingVenue(Protocol):
    name: str

    def preflight(self, symbol: str) -> dict[str, Any]: ...
    def market_rules(self, symbol: str) -> dict[str, Decimal]: ...
    def mark_or_last_price(self, symbol: str) -> Decimal: ...
    def submit_market(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        reduce_only: bool,
        client_order_id: str,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class MicroLiveSettings:
    enabled: bool
    arm_token: str
    venue: str
    state_path: str
    receipt_path: str

    @classmethod
    def from_env(cls) -> "MicroLiveSettings":
        enabled = os.getenv("MICROLIVE_EXECUTION_ENABLED", "0").strip() == "1"
        return cls(
            enabled=enabled,
            arm_token=os.getenv("MICROLIVE_ARM_TOKEN", "").strip(),
            venue=os.getenv("MICROLIVE_VENUE", "binance_usdm").strip().lower(),
            state_path=os.getenv("MICROLIVE_STATE", "microlive_state.json"),
            receipt_path=os.getenv("MICROLIVE_RECEIPTS", "microlive_receipts.jsonl"),
        )

    def assert_armed(self) -> None:
        if not self.enabled:
            raise ExecutionBlocked("MICROLIVE_EXECUTION_ENABLED is not 1")
        if self.arm_token != ARM_TOKEN:
            raise ExecutionBlocked("MICROLIVE_ARM_TOKEN mismatch")
        if self.venue != "binance_usdm":
            raise ExecutionBlocked(
                "CED1D-0031 is provider-bound to Binance USD-M; venue substitution is forbidden"
            )


@dataclass
class ExecutionState:
    status: str = "IDLE"
    signal_key: str | None = None
    entry_client_order_id: str | None = None
    exit_client_order_id: str | None = None
    quantity: str | None = None
    direction: str | None = None
    reference_exit: str | None = None
    entry_order: dict[str, Any] | None = None
    exit_order: dict[str, Any] | None = None
    completed_events: int = 0

    @classmethod
    def load(cls, path: str) -> "ExecutionState":
        p = Path(path)
        if not p.exists():
            return cls()
        return cls(**json.loads(p.read_text(encoding="utf-8")))

    def save(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(self), sort_keys=True, indent=2), encoding="utf-8")
        os.replace(tmp, p)


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ExecutionBlocked("timestamp must be timezone-aware")
    return dt.astimezone(UTC)


def client_id(signal_key: str, suffix: str) -> str:
    digest = hashlib.sha256(signal_key.encode("utf-8")).hexdigest()[:12]
    return f"ced0031-{digest}-{suffix}"


def append_receipt(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def inspect_signal_identity(signal: dict[str, Any]) -> dict[str, Any]:
    if signal.get("strategy_id") != CANDIDATE:
        raise ExecutionBlocked("wrong strategy_id")
    if signal.get("symbol") != SYMBOL:
        raise ExecutionBlocked("wrong symbol")
    if signal.get("market_provider") not in (None, PROVIDER):
        raise ExecutionBlocked("wrong market provider")

    direction = signal.get("direction")
    if direction not in {"LONG", "SHORT"}:
        raise ExecutionBlocked("direction must be LONG or SHORT")

    meta = signal.get("metadata") or {}
    signal_key = meta.get("signal_key")
    if not isinstance(signal_key, str) or not signal_key.startswith(CANDIDATE + ":"):
        raise ExecutionBlocked("invalid immutable signal_key")
    if meta.get("candidate") != CANDIDATE:
        raise ExecutionBlocked("candidate metadata mismatch")
    if meta.get("direction_rule") != "CONTINUATION_SIGN_LOG_CLOSE_RATIO":
        raise ExecutionBlocked("direction rule mismatch")
    if int(meta.get("lookback_calendar_days", -1)) != 20:
        raise ExecutionBlocked("lookback mismatch")
    if int(meta.get("horizon_calendar_days", -1)) != 1:
        raise ExecutionBlocked("horizon mismatch")
    if meta.get("provider") != PROVIDER:
        raise ExecutionBlocked("provider binding mismatch")

    reference_entry = parse_utc(meta["reference_entry"])
    reference_exit = parse_utc(meta["reference_exit"])
    if reference_entry < EARLIEST_ENTRY_UTC:
        raise ExecutionBlocked("pre micro-live activation boundary")
    if reference_exit <= reference_entry:
        raise ExecutionBlocked("invalid reference exit")

    return {
        "signal_key": signal_key,
        "direction": direction,
        "reference_entry": reference_entry,
        "reference_exit": reference_exit,
    }


def validate_signal(signal: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    resolved = inspect_signal_identity(signal)
    reference_entry = resolved["reference_entry"]
    deadline = reference_entry.replace(second=ENTRY_GRACE_SECONDS, microsecond=999999)
    if not (reference_entry <= now <= deadline):
        raise ExecutionBlocked("outside governed entry window")
    return resolved


def round_quantity(
    *,
    notional_usdt: Decimal,
    price: Decimal,
    step_size: Decimal,
    min_qty: Decimal,
) -> Decimal:
    if price <= 0 or step_size <= 0:
        raise ExecutionBlocked("invalid market rule")
    raw = notional_usdt / price
    units = (raw / step_size).to_integral_value(rounding=ROUND_DOWN)
    qty = units * step_size
    if qty < min_qty:
        raise ExecutionBlocked("25 USDT cap is below venue minimum quantity")
    if qty * price > MAX_NOTIONAL_USDT:
        raise ExecutionBlocked("rounded quantity exceeds 25 USDT cap")
    return qty


class MicroLiveCoordinator:
    def __init__(self, settings: MicroLiveSettings, venue: TradingVenue) -> None:
        self.settings = settings
        self.venue = venue

    def process_signal(self, signal: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
        now = (now or datetime.now(UTC)).astimezone(UTC)
        self.settings.assert_armed()
        if self.venue.name != "BINANCE_USDM":
            raise ExecutionBlocked("venue implementation does not match Binance USD-M authority")

        resolved = validate_signal(signal, now=now)
        state = ExecutionState.load(self.settings.state_path)
        if state.completed_events >= MAX_REAL_EVENTS:
            raise ExecutionBlocked("one-event V0.1 cap already consumed")
        if state.status != "IDLE":
            raise ExecutionBlocked(f"executor state is {state.status}, not IDLE")

        health = self.venue.preflight(SYMBOL)
        if health.get("ok") is not True:
            raise ExecutionBlocked(f"venue preflight failed: {health}")

        rules = self.venue.market_rules(SYMBOL)
        price = self.venue.mark_or_last_price(SYMBOL)
        qty = round_quantity(
            notional_usdt=MAX_NOTIONAL_USDT,
            price=price,
            step_size=rules["step_size"],
            min_qty=rules["min_qty"],
        )

        entry_side = "BUY" if resolved["direction"] == "LONG" else "SELL"
        entry_id = client_id(resolved["signal_key"], "e")
        order = self.venue.submit_market(
            symbol=SYMBOL,
            side=entry_side,
            quantity=qty,
            reduce_only=False,
            client_order_id=entry_id,
        )

        state.status = "OPEN"
        state.signal_key = resolved["signal_key"]
        state.entry_client_order_id = entry_id
        state.exit_client_order_id = client_id(resolved["signal_key"], "x")
        state.quantity = format(qty, "f")
        state.direction = resolved["direction"]
        state.reference_exit = resolved["reference_exit"].isoformat()
        state.entry_order = order
        state.save(self.settings.state_path)

        receipt = {
            "event": "MICROLIVE_ENTRY_SUBMITTED",
            "candidate": CANDIDATE,
            "authority_commit": AUTHORITY_COMMIT,
            "signal_key": resolved["signal_key"],
            "direction": resolved["direction"],
            "quantity": format(qty, "f"),
            "approx_notional_usdt": format(qty * price, "f"),
            "client_order_id": entry_id,
            "reference_exit": resolved["reference_exit"].isoformat(),
            "order": order,
        }
        append_receipt(self.settings.receipt_path, receipt)
        return receipt

    def maybe_exit_due(self, *, now: datetime | None = None) -> dict[str, Any] | None:
        now = (now or datetime.now(UTC)).astimezone(UTC)
        self.settings.assert_armed()
        state = ExecutionState.load(self.settings.state_path)
        if state.status != "OPEN":
            return None
        if not state.reference_exit or not state.quantity or not state.direction:
            raise ExecutionBlocked("open state is incomplete")

        due = parse_utc(state.reference_exit)
        if now < due:
            return None

        late_by_seconds = max(0.0, (now - due).total_seconds())
        side = "SELL" if state.direction == "LONG" else "BUY"
        order = self.venue.submit_market(
            symbol=SYMBOL,
            side=side,
            quantity=Decimal(state.quantity),
            reduce_only=True,
            client_order_id=state.exit_client_order_id or "ced0031-exit-missing",
        )
        state.status = "CLOSED_PENDING_RECONCILIATION"
        state.exit_order = order
        state.completed_events += 1
        state.save(self.settings.state_path)

        receipt = {
            "event": "MICROLIVE_EXIT_SUBMITTED",
            "candidate": CANDIDATE,
            "authority_commit": AUTHORITY_COMMIT,
            "signal_key": state.signal_key,
            "direction": state.direction,
            "quantity": state.quantity,
            "client_order_id": state.exit_client_order_id,
            "order": order,
            "late_exit_incident": late_by_seconds > ENTRY_GRACE_SECONDS,
            "late_by_seconds": late_by_seconds,
            "routing": "MANDATORY_RECONCILIATION_BEFORE_ANY_SECOND_REAL_EVENT",
        }
        append_receipt(self.settings.receipt_path, receipt)
        return receipt
