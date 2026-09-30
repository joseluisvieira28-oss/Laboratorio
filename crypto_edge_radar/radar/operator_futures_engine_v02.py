from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

from .market import MEXCFuturesPublicFeed
from .mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from .global_slot_reservation_v03 import (
    GlobalSlotReservationError,
    GlobalSlotReservationV03,
)
from .mexc_operator_futures_transport_v02 import (
    MEXCOperatorFuturesTransportV02,
    OperatorFuturesPolicy,
    direction_meta,
)
from .operator_risk_v02 import (
    MAX_INITIAL_MARGIN_USDT,
    MAX_NOTIONAL_USDT,
    REQUIRED_LEVERAGE,
    build_operator_risk_state,
)

OFFICIAL_API_TAKER_FLOOR = 0.0008
MAX_CLOCK_OFFSET_MS = 500.0
STATUS_VERSION = "OPERATOR_FUTURES_ENGINE_V0.2"


class OperatorEngineError(RuntimeError):
    pass


def _load(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OperatorEngineError(f"JSON object required: {path}")
    return payload


def _atomic_write(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def _exclusive_write(path: str | Path, payload: dict[str, Any]) -> bool:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return True


def _utc(value: Any) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise OperatorEngineError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _floor_step(value: float, step: float) -> float:
    if value <= 0 or step <= 0:
        return 0.0
    dv = Decimal(str(value))
    ds = Decimal(str(step))
    units = (dv / ds).to_integral_value(rounding=ROUND_DOWN)
    return float(units * ds)



def _ceil_step(value: float, step: float) -> float:
    if value <= 0 or step <= 0:
        return 0.0
    dv = Decimal(str(value))
    ds = Decimal(str(step))
    units = (dv / ds).to_integral_value(rounding=ROUND_CEILING)
    return float(units * ds)


def protective_prices(
    *,
    entry_price: float,
    direction: str,
    stop_distance_fraction: float,
    take_profit_distance_fraction: float,
    price_unit: float,
) -> dict[str, float]:
    vals = (
        entry_price,
        stop_distance_fraction,
        take_profit_distance_fraction,
        price_unit,
    )
    if any(not math.isfinite(float(v)) or float(v) <= 0 for v in vals):
        raise OperatorEngineError("protective price inputs must be positive finite")
    direction = direction.upper()
    if direction == "LONG":
        stop_raw = entry_price * (1.0 - stop_distance_fraction)
        target_raw = entry_price * (1.0 + take_profit_distance_fraction)
        stop = _ceil_step(stop_raw, price_unit)
        target = _floor_step(target_raw, price_unit)
        if not 0 < stop < entry_price < target:
            raise OperatorEngineError("LONG protective geometry invalid after rounding")
    elif direction == "SHORT":
        stop_raw = entry_price * (1.0 + stop_distance_fraction)
        target_raw = entry_price * (1.0 - take_profit_distance_fraction)
        stop = _floor_step(stop_raw, price_unit)
        target = _ceil_step(target_raw, price_unit)
        if not 0 < target < entry_price < stop:
            raise OperatorEngineError("SHORT protective geometry invalid after rounding")
    else:
        raise OperatorEngineError("protective direction invalid")
    return {
        "stop_loss_price": stop,
        "take_profit_price": target,
        "price_unit": price_unit,
    }


def order_fee_usdt(order: dict[str, Any]) -> float:
    """MEXC may expose totalFee=0 while takerFee is non-zero."""
    total_fee: float | None = None
    if order.get("totalFee") is not None:
        try:
            total_fee = abs(float(order["totalFee"]))
            if total_fee > 0:
                return total_fee
        except (TypeError, ValueError):
            total_fee = None

    component_total = 0.0
    for key in ("takerFee", "makerFee"):
        try:
            component_total += abs(float(order.get(key, 0) or 0))
        except (TypeError, ValueError):
            pass
    if component_total > 0:
        return component_total
    return total_fee or 0.0


def timing_state(
    *,
    now: datetime,
    entry_target: datetime,
    max_late_seconds: float,
) -> str:
    now = now.astimezone(timezone.utc)
    entry_target = entry_target.astimezone(timezone.utc)
    delta = (now - entry_target).total_seconds()
    if delta < 0:
        return "WAITING"
    if delta <= max_late_seconds:
        return "DUE"
    return "MISSED_NO_CHASE"


def compute_contract_volume(
    *,
    target_notional_usdt: float,
    price: float,
    contract_size: float,
    min_vol: float,
    vol_unit: float,
    leverage: int = REQUIRED_LEVERAGE,
) -> dict[str, float | int]:
    values = (target_notional_usdt, price, contract_size, min_vol, vol_unit)
    if any(not math.isfinite(float(v)) or float(v) <= 0 for v in values):
        raise OperatorEngineError("positive finite sizing inputs required")
    if leverage != REQUIRED_LEVERAGE:
        raise OperatorEngineError("operator V0.2 sizing requires exactly 5x")

    raw = target_notional_usdt / (contract_size * price)
    volume = _floor_step(raw, vol_unit)
    if volume < min_vol:
        raise OperatorEngineError("VENUE_MINIMUM_EXCEEDS_OPERATOR_BUDGET")
    if abs(volume - round(volume)) > 1e-9:
        raise OperatorEngineError("NON_INTEGER_CONTRACT_VOLUME_UNSUPPORTED")
    volume_int = int(round(volume))
    notional = volume_int * contract_size * price
    margin = notional / leverage
    if notional > target_notional_usdt + 1e-9:
        raise OperatorEngineError("SIZING_ROUNDED_ABOVE_NOTIONAL_CAP")
    if notional > MAX_NOTIONAL_USDT + 1e-9:
        raise OperatorEngineError("SIZING_EXCEEDS_GLOBAL_NOTIONAL_CAP")
    if margin > MAX_INITIAL_MARGIN_USDT + 1e-9:
        raise OperatorEngineError("SIZING_EXCEEDS_GLOBAL_MARGIN_CAP")
    return {
        "volume_contracts": volume_int,
        "estimated_notional_usdt": notional,
        "estimated_initial_margin_usdt": margin,
    }


def _oid(signal_key: str, phase: str, attempt: int = 1) -> str:
    digest = hashlib.sha256(
        f"{signal_key}:{phase}:{attempt}:operator-v02".encode("utf-8")
    ).hexdigest()[:18]
    return f"op2-{phase[:3]}-{attempt}-{digest}"


def _session_name(candidate_id: str, signal_key: str) -> str:
    digest = hashlib.sha256(signal_key.encode("utf-8")).hexdigest()[:18]
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in candidate_id).strip("-")
    return f"{safe[:28]}-{digest}"


class OperatorFuturesEngineV02:
    def __init__(
        self,
        *,
        credentials: MEXCCredentials,
        receipt_root: str,
        armed_path: str,
        kill_switch_path: str,
        status_path: str,
    ) -> None:
        self.credentials = credentials
        self.receipt_root = Path(receipt_root)
        self.armed_path = Path(armed_path)
        self.kill_switch_path = Path(kill_switch_path)
        self.status_path = Path(status_path)
        self.global_slot = GlobalSlotReservationV03(
            self.receipt_root.parent / "live_state" / "GLOBAL_POSITION_SLOT_V03.json"
        )
        self.readonly = MEXCFuturesAuthenticatedReadOnlyClient(credentials)
        self.public = MEXCFuturesPublicFeed(timeout=10)

    def _status(self, status: str, **extra: Any) -> dict[str, Any]:
        payload = {
            "version": STATUS_VERSION,
            "status": status,
            "checked_at_utc": _iso(datetime.now(timezone.utc)),
            **extra,
        }
        _atomic_write(self.status_path, payload)
        return payload

    def _active_states(self) -> list[tuple[Path, dict[str, Any]]]:
        out: list[tuple[Path, dict[str, Any]]] = []
        if not self.receipt_root.exists():
            return out
        for path in self.receipt_root.rglob("ACTIVE_TRADE_STATE.json"):
            try:
                row = _load(path)
            except Exception:
                continue
            if row.get("state") in {"FILLED", "EXIT_PENDING"} and not (
                path.parent / "POST_TRADE_RECONCILIATION.json"
            ).exists():
                out.append((path, row))
        return out

    def _position(self, *, symbol: str, direction: str) -> dict[str, Any] | None:
        meta = direction_meta(direction)
        rows = self.readonly.open_positions(symbol)
        matches = [
            row for row in rows
            if int(row.get("positionType", 0) or 0) == meta["position_type"]
            and float(row.get("holdVol", 0) or 0) > 0
        ]
        if len(matches) > 1:
            raise OperatorEngineError("MULTIPLE_MATCHING_POSITIONS_PRESENT")
        return matches[0] if matches else None

    def _wait_order(
        self,
        *,
        symbol: str,
        external_oid: str,
        timeout: float = 12.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            try:
                last = self.readonly.order_by_external(
                    symbol=symbol,
                    external_oid=external_oid,
                )
            except Exception:
                time.sleep(0.5)
                continue
            if int(last.get("state", 0) or 0) in (3, 4, 5):
                return last
            time.sleep(0.5)
        if last is None:
            raise OperatorEngineError("ORDER_ACK_STATE_UNKNOWN")
        return last

    def _clock_gate(self) -> dict[str, Any]:
        before = time.time_ns() / 1_000_000.0
        server_ms = float(self.public.server_time_ms())
        after = time.time_ns() / 1_000_000.0
        midpoint = (before + after) / 2.0
        offset = server_ms - midpoint
        return {
            "pass": abs(offset) <= MAX_CLOCK_OFFSET_MS,
            "server_minus_local_midpoint_ms": offset,
            "request_rtt_ms": after - before,
            "max_abs_offset_ms": MAX_CLOCK_OFFSET_MS,
        }

    def _funding_burden_bps(
        self,
        *,
        funding: dict[str, Any],
        entry_target: datetime,
        exit_target: datetime,
    ) -> float:
        rate = abs(float(funding.get("fundingRate", 0) or 0))
        hold_hours = max(0.0, (exit_target - entry_target).total_seconds() / 3600.0)
        try:
            cycle = float(funding.get("collectCycle", 8) or 8)
        except (TypeError, ValueError):
            cycle = 8.0
        if cycle <= 0:
            cycle = 8.0
        # +1 is deliberately conservative for boundary alignment uncertainty.
        settlements = max(1, int(math.ceil(hold_hours / cycle)) + 1)
        return rate * 10000.0 * settlements

    def _entry_gate(self, signal: dict[str, Any], *, now: datetime) -> dict[str, Any]:
        blockers: list[str] = []
        candidate_id = str(signal.get("candidate_id") or signal.get("strategy_id") or "")
        signal_key = str(signal.get("immutable_signal_key") or "")
        symbol = str(signal.get("symbol") or "").upper()
        direction = str(signal.get("direction") or "").upper()

        if not candidate_id:
            blockers.append("CANDIDATE_ID_MISSING")
        if not signal_key:
            blockers.append("IMMUTABLE_SIGNAL_KEY_MISSING")
        if direction not in {"LONG", "SHORT"}:
            blockers.append("DIRECTION_INVALID")
        if not symbol.endswith("_USDT"):
            blockers.append("SYMBOL_INVALID")

        try:
            entry_target = _utc(signal["entry_target_utc"])
            exit_target = _utc(signal["exit_target_utc"])
        except Exception as exc:
            entry_target = now
            exit_target = now
            blockers.append(f"TIMING_PARSE_FAILED:{type(exc).__name__}")

        try:
            max_late = float(signal.get("max_late_seconds", 2.0) or 2.0)
            if not math.isfinite(max_late) or max_late < 0:
                raise ValueError("max_late_seconds must be finite and non-negative")
        except Exception as exc:
            max_late = 0.0
            blockers.append(f"MAX_LATE_INVALID:{type(exc).__name__}")
        timing = timing_state(
            now=now,
            entry_target=entry_target,
            max_late_seconds=max_late,
        )
        if timing == "WAITING":
            blockers.append("ENTRY_TARGET_NOT_DUE")
        elif timing == "MISSED_NO_CHASE":
            blockers.append("ENTRY_WINDOW_MISSED_NO_CHASE")

        protective = signal.get("protective_exit")
        protective_gate: dict[str, Any] | None = None
        if protective is not None:
            if not isinstance(protective, dict) or protective.get("required") is not True:
                blockers.append("PROTECTIVE_EXIT_SCHEMA_INVALID")
            else:
                try:
                    stop_fraction = float(protective["stop_distance_fraction"])
                    target_fraction = float(protective["take_profit_distance_fraction"])
                    if (
                        not math.isfinite(stop_fraction)
                        or not math.isfinite(target_fraction)
                        or stop_fraction <= 0
                        or target_fraction <= 0
                        or stop_fraction >= 1
                        or target_fraction >= 5
                    ):
                        raise ValueError("protective distances outside finite range")
                    if str(protective.get("trigger_basis")) != "LATEST_PRICE":
                        raise ValueError("only latest-price protection is supported")
                    protective_gate = {
                        "required": True,
                        "stop_distance_fraction": stop_fraction,
                        "take_profit_distance_fraction": target_fraction,
                        "trigger_basis": "LATEST_PRICE",
                    }
                except Exception as exc:
                    blockers.append(f"PROTECTIVE_EXIT_INVALID:{type(exc).__name__}:{exc}")

        if not self.armed_path.exists():
            blockers.append("OPERATOR_FUTURES_NOT_ARMED")
        if self.kill_switch_path.exists():
            blockers.append("KILL_SWITCH_PRESENT")

        risk = build_operator_risk_state(
            private_client=self.readonly,
            receipt_root=self.receipt_root,
            now=now,
        )
        blockers.extend(risk["blockers"])

        try:
            mode = self.readonly.position_mode()
            if mode != 1:
                blockers.append("FUTURES_POSITION_MODE_NOT_HEDGE")
        except Exception as exc:
            mode = None
            blockers.append(f"POSITION_MODE_READ_FAILED:{type(exc).__name__}")

        try:
            clock = self._clock_gate()
            if not clock["pass"]:
                blockers.append("WINDOWS_CLOCK_OFFSET_OUTSIDE_500MS")
        except Exception as exc:
            clock = {"pass": False, "error": f"{type(exc).__name__}:{exc}"}
            blockers.append("MEXC_CLOCK_CHECK_FAILED")

        try:
            contract = self.public.contract_row(symbol)
            snapshots = self.public.all_market_snapshots()
            canonical = symbol.replace("_", "")
            snap = snapshots[canonical]
            contract_ok = (
                contract.get("apiAllowed") is not False
                and contract.get("state") in (None, 0)
                and contract.get("futureType") in (None, 1)
            )
            if not contract_ok:
                blockers.append("CONTRACT_NOT_API_ELIGIBLE")

            contract_size = float(contract["contractSize"])
            min_vol = float(contract["minVol"])
            vol_unit = float(contract["volUnit"])
            price_unit = float(contract.get("priceUnit") or 0)
            if protective_gate is not None and (
                not math.isfinite(price_unit) or price_unit <= 0
            ):
                blockers.append("PROTECTIVE_PRICE_UNIT_UNAVAILABLE")
            conservative_price = max(float(snap.last_price), float(snap.ask_price))
            bid = float(snap.bid_price)
            ask = float(snap.ask_price)
            mid = (bid + ask) / 2.0
            spread_bps = ((ask - bid) / mid) * 10000.0 if mid > 0 else 999999.0

            requested_margin = min(
                float(signal.get("max_initial_margin_usdt", MAX_INITIAL_MARGIN_USDT)),
                MAX_INITIAL_MARGIN_USDT,
            )
            requested_notional = min(
                float(signal.get("max_notional_usdt", MAX_NOTIONAL_USDT)),
                requested_margin * REQUIRED_LEVERAGE,
                MAX_NOTIONAL_USDT,
            )
            sizing = compute_contract_volume(
                target_notional_usdt=requested_notional,
                price=conservative_price,
                contract_size=contract_size,
                min_vol=min_vol,
                vol_unit=vol_unit,
            )
        except Exception as exc:
            contract = {}
            snap = None
            contract_size = None
            price_unit = None
            spread_bps = None
            requested_margin = None
            requested_notional = None
            sizing = None
            blockers.append(f"MARKET_METADATA_OR_SIZING_FAILED:{type(exc).__name__}:{exc}")

        try:
            fees = self.readonly.fee_details(symbol)
            taker_raw = fees.get("realTakerFee")
            if taker_raw is None:
                taker_raw = fees.get("takerFee")
            account_taker = float(taker_raw)
            effective_taker = max(account_taker, OFFICIAL_API_TAKER_FLOOR)
            round_trip_fee_bps = 2.0 * effective_taker * 10000.0
        except Exception as exc:
            fees = {}
            account_taker = None
            effective_taker = None
            round_trip_fee_bps = None
            blockers.append(f"FEE_READ_FAILED:{type(exc).__name__}")

        try:
            funding = self.public.funding_rate(symbol)
            funding_burden_bps = self._funding_burden_bps(
                funding=funding,
                entry_target=entry_target,
                exit_target=exit_target,
            )
        except Exception as exc:
            funding = {}
            funding_burden_bps = None
            blockers.append(f"FUNDING_READ_FAILED:{type(exc).__name__}")

        projected = None
        if (
            round_trip_fee_bps is not None
            and spread_bps is not None
            and funding_burden_bps is not None
        ):
            projected = round_trip_fee_bps + 2.0 * spread_bps + funding_burden_bps
            ceiling = float(signal.get("max_projected_roundtrip_friction_bps", 0) or 0)
            if ceiling <= 0:
                blockers.append("FRICTION_CEILING_MISSING")
            elif projected > ceiling:
                blockers.append("PROJECTED_FRICTION_EXCEEDS_ROUTE_CEILING")

        if sizing is not None and risk.get("available_usdt") is not None:
            required_cash = float(sizing["estimated_initial_margin_usdt"])
            # Small buffer for entry fees; exit fees are realized later.
            entry_fee_buffer = (
                float(sizing["estimated_notional_usdt"]) * float(effective_taker or OFFICIAL_API_TAKER_FLOOR)
            )
            if float(risk["available_usdt"]) + 1e-9 < required_cash + entry_fee_buffer:
                blockers.append("AVAILABLE_BALANCE_INSUFFICIENT_FOR_MARGIN_AND_ENTRY_FEE")

        return {
            "pass": not blockers,
            "blockers": blockers,
            "candidate_id": candidate_id,
            "signal_identity": signal_key,
            "symbol": symbol,
            "direction": direction,
            "entry_target_utc": _iso(entry_target),
            "exit_target_utc": _iso(exit_target),
            "timing_state": timing,
            "max_late_seconds": max_late,
            "risk": risk,
            "position_mode": mode,
            "clock": clock,
            "contract": {
                "contract_size": contract_size,
                "min_vol": contract.get("minVol"),
                "vol_unit": contract.get("volUnit"),
                "price_unit": price_unit,
            },
            "protective_exit": protective_gate,
            "sizing": sizing,
            "account_taker_fee_fraction": account_taker,
            "effective_taker_fee_fraction": effective_taker,
            "round_trip_fee_bps": round_trip_fee_bps,
            "spread_bps": spread_bps,
            "conservative_funding_burden_bps": funding_burden_bps,
            "projected_roundtrip_friction_bps": projected,
            "friction_ceiling_bps": signal.get("max_projected_roundtrip_friction_bps"),
            "required_leverage": REQUIRED_LEVERAGE,
            "margin_mode": "ISOLATED",
        }

    def _ensure_position_risk(
        self,
        *,
        transport: MEXCOperatorFuturesTransportV02,
        symbol: str,
        direction: str,
        position: dict[str, Any],
        session: Path,
    ) -> dict[str, Any]:
        if int(position.get("openType", 0) or 0) != 1:
            raise OperatorEngineError("POST_FILL_NOT_ISOLATED")
        if int(position.get("leverage", 0) or 0) != REQUIRED_LEVERAGE:
            raise OperatorEngineError("POST_FILL_LEVERAGE_NOT_5X")

        if bool(position.get("autoAddIm")):
            transport.set_auto_add_margin(
                position_id=int(position["positionId"]),
                enabled=False,
            )
            time.sleep(0.25)
            refreshed = self._position(symbol=symbol, direction=direction)
            if refreshed is not None:
                position = refreshed

        if position.get("autoAddIm") is not False:
            raise OperatorEngineError("AUTO_MARGIN_ADD_OFF_NOT_VERIFIED")

        _atomic_write(session / "POST_FILL_RISK_VERIFY.json", {
            "receipt_type": "POST_FILL_RISK_VERIFY",
            "pass": True,
            "symbol": symbol,
            "direction": direction,
            "position_id": position.get("positionId"),
            "open_type": position.get("openType"),
            "leverage": position.get("leverage"),
            "auto_add_im": position.get("autoAddIm"),
        })
        return position

    def _install_position_protection(
        self,
        *,
        transport: MEXCOperatorFuturesTransportV02,
        position: dict[str, Any],
        direction: str,
        fill_price: float,
        protective: dict[str, Any],
        price_unit: float,
        session: Path,
    ) -> dict[str, Any]:
        prices = protective_prices(
            entry_price=fill_price,
            direction=direction,
            stop_distance_fraction=float(protective["stop_distance_fraction"]),
            take_profit_distance_fraction=float(
                protective["take_profit_distance_fraction"]
            ),
            price_unit=float(price_unit),
        )
        volume = int(float(position.get("holdVol", 0) or 0))
        position_id = int(position.get("positionId", 0) or 0)
        if volume <= 0 or position_id <= 0:
            raise OperatorEngineError("PROTECTIVE_POSITION_ID_OR_VOLUME_INVALID")

        ack = transport.place_position_tpsl(
            symbol=str(position.get("symbol") or "").upper(),
            direction=direction,
            position_id=position_id,
            volume_contracts=volume,
            stop_loss_price=prices["stop_loss_price"],
            take_profit_price=prices["take_profit_price"],
        )
        _atomic_write(session / "PROTECTIVE_TPSL_ACK.json", {
            "receipt_type": "PROTECTIVE_TPSL_ACK",
            "position_id": position_id,
            "volume_contracts": volume,
            "direction": direction,
            **prices,
            "exchange_ack": ack,
        })

        time.sleep(0.35)
        rows = self.readonly.open_tpsl_orders(
            str(position.get("symbol") or "").upper()
        )
        matches: list[dict[str, Any]] = []
        for row in rows:
            try:
                if int(row.get("positionId", 0) or 0) != position_id:
                    continue
                if int(row.get("state", 1) or 1) != 1:
                    continue
                row_stop = float(row.get("stopLossPrice", 0) or 0)
                row_target = float(row.get("takeProfitPrice", 0) or 0)
                row_vol = float(row.get("vol", 0) or 0)
                if abs(row_stop - prices["stop_loss_price"]) > float(price_unit) / 2.0:
                    continue
                if abs(row_target - prices["take_profit_price"]) > float(price_unit) / 2.0:
                    continue
                if abs(row_vol - volume) > 1e-9:
                    continue
            except (TypeError, ValueError):
                continue
            matches.append(row)

        if len(matches) != 1:
            raise OperatorEngineError(
                f"PROTECTIVE_TPSL_POST_VERIFY_FAILED:matches={len(matches)}"
            )
        order = matches[0]
        protective_id = int(order.get("id", 0) or 0)
        if protective_id <= 0:
            raise OperatorEngineError("PROTECTIVE_TPSL_ID_INVALID")

        receipt = {
            "receipt_type": "PROTECTIVE_TPSL_VERIFY",
            "pass": True,
            "position_id": position_id,
            "protective_order_id": protective_id,
            "volume_contracts": volume,
            "stop_loss_price": prices["stop_loss_price"],
            "take_profit_price": prices["take_profit_price"],
            "price_unit": prices["price_unit"],
            "trigger_basis": "LATEST_PRICE",
            "market_on_trigger": True,
            "exchange_row": order,
        }
        _atomic_write(session / "PROTECTIVE_TPSL_VERIFY.json", receipt)
        return receipt

    def _verify_active_protection(
        self,
        *,
        active: dict[str, Any],
    ) -> dict[str, Any]:
        symbol = str(active["symbol"]).upper()
        position_id = int(active["position_id"])
        protective_id = int(active.get("protective_tpsl_order_id", 0) or 0)
        if protective_id <= 0:
            raise OperatorEngineError("ACTIVE_PROTECTIVE_TPSL_ID_MISSING")
        rows = self.readonly.open_tpsl_orders(symbol)
        matches = [
            row for row in rows
            if int(row.get("id", 0) or 0) == protective_id
            and int(row.get("positionId", 0) or 0) == position_id
            and int(row.get("state", 1) or 1) == 1
        ]
        if len(matches) != 1:
            raise OperatorEngineError(
                f"ACTIVE_PROTECTIVE_TPSL_NOT_VERIFIED:matches={len(matches)}"
            )
        row = matches[0]
        unit = float(active.get("protective_price_unit", 0) or 0)
        if unit <= 0:
            raise OperatorEngineError("ACTIVE_PROTECTIVE_PRICE_UNIT_INVALID")
        stop = float(row.get("stopLossPrice", 0) or 0)
        target = float(row.get("takeProfitPrice", 0) or 0)
        if (
            abs(stop - float(active["protective_stop_loss_price"])) > unit / 2.0
            or abs(target - float(active["protective_take_profit_price"])) > unit / 2.0
        ):
            raise OperatorEngineError("ACTIVE_PROTECTIVE_TPSL_PRICE_DRIFT")
        return row

    def _historical_position(
        self,
        *,
        active: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any] | None:
        symbol = str(active["symbol"]).upper()
        direction = str(active["direction"]).upper()
        position_type = direction_meta(direction)["position_type"]
        opened = _utc(
            active.get("opened_at_utc")
            or active.get("entry_target_utc")
        )
        start_ms = int((opened.timestamp() - 3600.0) * 1000)
        end_ms = int((now.timestamp() + 60.0) * 1000)
        rows = self.readonly.historical_positions(
            symbol=symbol,
            position_type=position_type,
            start_time=start_ms,
            end_time=end_ms,
        )
        matches = [
            row for row in rows
            if int(row.get("positionId", 0) or 0) == int(active["position_id"])
        ]
        if len(matches) > 1:
            raise OperatorEngineError("MULTIPLE_HISTORICAL_POSITION_ID_MATCHES")
        return matches[0] if matches else None

    def _reconcile_protected_exchange_close(
        self,
        *,
        active_path: Path,
        active: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any]:
        session = active_path.parent
        symbol = str(active["symbol"]).upper()
        direction = str(active["direction"]).upper()
        signal_key = str(active["signal_identity"])
        hist = self._historical_position(active=active, now=now)
        if hist is None or int(hist.get("state", 0) or 0) != 3:
            return self._status(
                "PROTECTED_EXIT_RECONCILIATION_REQUIRED",
                candidate_id=active.get("candidate_id"),
                signal_identity=signal_key,
                reason="POSITION_MISSING_BUT_CLOSED_HISTORY_NOT_YET_PROVEN",
                session_dir=str(session),
            )

        opened = _utc(active.get("opened_at_utc") or active["entry_target_utc"])
        rows = self.readonly.tpsl_orders(
            symbol=symbol,
            is_finished=1,
            position_type=direction_meta(direction)["position_type"],
            start_time=int((opened.timestamp() - 3600.0) * 1000),
            end_time=int((now.timestamp() + 60.0) * 1000),
        )
        protective_id = int(active.get("protective_tpsl_order_id", 0) or 0)
        matches = [
            row for row in rows
            if int(row.get("id", 0) or 0) == protective_id
            and int(row.get("positionId", 0) or 0) == int(active["position_id"])
        ]
        if len(matches) != 1:
            return self._status(
                "PROTECTED_EXIT_RECONCILIATION_REQUIRED",
                candidate_id=active.get("candidate_id"),
                signal_identity=signal_key,
                reason=f"PROTECTIVE_HISTORY_MATCH_COUNT_{len(matches)}",
                session_dir=str(session),
            )
        tpsl = matches[0]
        if int(tpsl.get("state", 0) or 0) != 3:
            return self._status(
                "PROTECTED_EXIT_RECONCILIATION_REQUIRED",
                candidate_id=active.get("candidate_id"),
                signal_identity=signal_key,
                reason=f"PROTECTIVE_ORDER_NOT_EXECUTED_STATE_{tpsl.get('state')}",
                session_dir=str(session),
            )

        trigger_side = int(tpsl.get("triggerSide", 0) or 0)
        if trigger_side == 1:
            exit_reason = "MEXC_TAKE_PROFIT_TRIGGER"
        elif trigger_side == 2:
            exit_reason = "MEXC_STOP_LOSS_TRIGGER"
        else:
            return self._status(
                "PROTECTED_EXIT_RECONCILIATION_REQUIRED",
                candidate_id=active.get("candidate_id"),
                signal_identity=signal_key,
                reason="PROTECTIVE_TRIGGER_SIDE_UNKNOWN",
                session_dir=str(session),
            )

        def finite(name: str, default: Any = None) -> float:
            raw = hist.get(name, default)
            value = float(raw)
            if not math.isfinite(value):
                raise OperatorEngineError(f"HISTORICAL_POSITION_{name}_NONFINITE")
            return value

        try:
            gross = finite("closeProfitLoss", 0)
            funding = finite("holdFee", 0)
            total_fee = abs(finite("totalFee", hist.get("fee", 0) or 0))
            realized = finite("realised")
            exit_price = finite("closeAvgPrice")
            expected = gross + funding - total_fee
            if abs(realized - expected) > max(1e-6, abs(realized) * 1e-6):
                raise OperatorEngineError(
                    f"HISTORICAL_POSITION_ACCOUNTING_IDENTITY_MISMATCH:{realized}:{expected}"
                )
        except Exception as exc:
            return self._status(
                "PROTECTED_EXIT_RECONCILIATION_REQUIRED",
                candidate_id=active.get("candidate_id"),
                signal_identity=signal_key,
                reason=f"{type(exc).__name__}:{exc}",
                session_dir=str(session),
            )

        entry_fee = float(active.get("entry_fee_usdt", 0) or 0)
        exit_fee = max(0.0, total_fee - entry_fee)
        _atomic_write(session / "PROTECTIVE_TPSL_FINAL.json", {
            "receipt_type": "PROTECTIVE_TPSL_FINAL",
            "protective_order": tpsl,
            "historical_position": hist,
            "trigger_side": trigger_side,
            "exit_reason": exit_reason,
        })
        reconciliation = {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "candidate_id": active.get("candidate_id"),
            "strategy_id": active.get("strategy_id"),
            "signal_identity": signal_key,
            "closed_at_utc": _iso(now),
            "gross_close_profit_usdt": gross,
            "funding_hold_fee_usdt": funding,
            "entry_fee_usdt": entry_fee,
            "exit_fee_usdt": exit_fee,
            "total_position_fee_usdt": total_fee,
            "realized_net_pnl_usdt": realized,
            "entry_price": active.get("entry_price"),
            "exit_price": exit_price,
            "planned_notional_usdt": active.get("planned_notional_usdt"),
            "planned_initial_margin_usdt": active.get("planned_initial_margin_usdt"),
            "leverage": REQUIRED_LEVERAGE,
            "margin_mode": "ISOLATED",
            "scientific_credit": False,
            "exit_reason": exit_reason,
            "protective_order_id": protective_id,
            "open_position_after_reconciliation": False,
        }
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", reconciliation)
        active["state"] = "CLOSED"
        active["closed_at_utc"] = reconciliation["closed_at_utc"]
        active["exit_reason"] = exit_reason
        _atomic_write(active_path, active)
        try:
            release = self.global_slot.release(
                signal_identity=signal_key,
                reason="POST_TRADE_RECONCILIATION_CONFIRMED",
            )
        except Exception as exc:
            return self._status(
                "CLOSED_RECONCILED_SLOT_RELEASE_REQUIRED",
                candidate_id=active.get("candidate_id"),
                signal_identity=signal_key,
                realized_net_pnl_usdt=realized,
                error=f"{type(exc).__name__}:{exc}",
                session_dir=str(session),
            )
        return self._status(
            "CLOSED_RECONCILED",
            candidate_id=active.get("candidate_id"),
            signal_identity=signal_key,
            realized_net_pnl_usdt=realized,
            exit_reason=exit_reason,
            global_slot_release=release,
            session_dir=str(session),
        )

    def _flatten_position(
        self,
        *,
        transport: MEXCOperatorFuturesTransportV02,
        symbol: str,
        direction: str,
        position: dict[str, Any],
        signal_key: str,
        session: Path,
        reason: str,
    ) -> None:
        volume = int(float(position.get("holdVol", 0) or 0))
        if volume <= 0:
            return
        ext = _oid(signal_key, "emergency", 1)
        _atomic_write(session / "EMERGENCY_EXIT_INTENT.json", {
            "receipt_type": "EMERGENCY_EXIT_INTENT",
            "reason": reason,
            "symbol": symbol,
            "direction": direction,
            "position_id": int(position["positionId"]),
            "volume_contracts": volume,
            "external_oid": ext,
        })
        ack = transport.submit_market_order(
            symbol=symbol,
            direction=direction,
            phase="EXIT",
            volume_contracts=volume,
            external_oid=ext,
            position_id=int(position["positionId"]),
        )
        _atomic_write(session / "EMERGENCY_EXIT_ACK.json", {
            "receipt_type": "EMERGENCY_EXIT_ACK",
            "reason": reason,
            "exchange_ack": ack,
            "external_oid": ext,
        })

    def enter_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        candidate_id = str(signal.get("candidate_id") or signal.get("strategy_id") or "unknown")
        signal_key = str(signal.get("immutable_signal_key") or "unknown")
        symbol_hint = str(signal.get("symbol") or "").upper()
        direction_hint = str(signal.get("direction") or "").upper()
        ext = _oid(signal_key, "entry", 1)
        session = self.receipt_root / _session_name(candidate_id, signal_key)
        session.mkdir(parents=True, exist_ok=True)
        intent_path = session / "ORDER_INTENT.json"

        # Recovery takes precedence over timing. Once an intent exists, restart
        # must reconcile it by immutable externalOid instead of treating the
        # opportunity as late or blindly resending.
        if intent_path.exists():
            try:
                intent = _load(intent_path)
                symbol = str(intent["symbol"]).upper()
                direction = str(intent["direction"]).upper()
                ext = str(intent["external_oid"])
                claim = self.global_slot.claim(
                    candidate_id=str(intent.get("candidate_id") or candidate_id),
                    signal_identity=str(intent.get("signal_identity") or signal_key),
                    external_oid=ext,
                )
                if claim.get("claim_status") == "OCCUPIED_BY_OTHER_SIGNAL":
                    return self._status(
                        "FAIL_CLOSED",
                        candidate_id=candidate_id,
                        signal_identity=signal_key,
                        blockers=["GLOBAL_SLOT_OCCUPIED_BY_OTHER_SIGNAL"],
                        global_slot_owner=claim.get("owner"),
                        session_dir=str(session),
                    )
                order = self.readonly.order_by_external(
                    symbol=symbol,
                    external_oid=ext,
                )
                position = self._position(symbol=symbol, direction=direction)
            except Exception as exc:
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    error=f"{type(exc).__name__}:{exc}",
                    blind_resend_allowed=False,
                    session_dir=str(session),
                )

            deal_vol = float(order.get("dealVol", 0) or 0)
            terminal_state = int(order.get("state", 0) or 0) in (3, 4, 5)
            if deal_vol <= 0:
                if terminal_state and position is None:
                    marker = {
                        "receipt_type": "ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                        "signal_identity": signal_key,
                        "external_oid": ext,
                        "order": order,
                        "trade_opened": False,
                    }
                    _atomic_write(session / "ENTRY_TERMINAL_NO_FILL_CONFIRMED.json", marker)
                    try:
                        self.global_slot.release(
                            signal_identity=signal_key,
                            reason="ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                        )
                    except Exception as exc:
                        return self._status(
                            "FAIL_CLOSED",
                            candidate_id=candidate_id,
                            signal_identity=signal_key,
                            blockers=[f"GLOBAL_SLOT_RELEASE_FAILED:{type(exc).__name__}"],
                            session_dir=str(session),
                        )
                    return self._status(
                        "FAIL_CLOSED",
                        candidate_id=candidate_id,
                        signal_identity=signal_key,
                        blockers=["ENTRY_ORDER_TERMINAL_NO_FILL"],
                        session_dir=str(session),
                    )
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    reason="INTENT_EXISTS_BUT_NO_PROVABLE_FILL",
                    blind_resend_allowed=False,
                    session_dir=str(session),
                )
            if position is None:
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    reason="FILLED_ORDER_WITHOUT_MATCHING_POSITION",
                    blind_resend_allowed=False,
                    session_dir=str(session),
                )

            gate_path = session / "PRE_ORDER_GATE.json"
            if not gate_path.exists():
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    reason="RECOVERY_GATE_RECEIPT_MISSING",
                    blind_resend_allowed=False,
                    session_dir=str(session),
                )
            gate = _load(gate_path)
            sizing = gate.get("sizing")
            if not isinstance(sizing, dict):
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    reason="RECOVERY_SIZING_MISSING",
                    blind_resend_allowed=False,
                    session_dir=str(session),
                )
        else:
            gate = self._entry_gate(signal, now=now)
            candidate_id = gate["candidate_id"] or "unknown"
            signal_key = gate["signal_identity"] or "unknown"
            session = self.receipt_root / _session_name(candidate_id, signal_key)
            session.mkdir(parents=True, exist_ok=True)
            intent_path = session / "ORDER_INTENT.json"
            _atomic_write(session / "CANONICAL_OPERATOR_SIGNAL.json", signal)
            _atomic_write(session / "PRE_ORDER_GATE.json", gate)

            if not gate["pass"]:
                status = "WAITING_ENTRY_TARGET" if gate["timing_state"] == "WAITING" else "FAIL_CLOSED"
                return self._status(
                    status,
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    blockers=gate["blockers"],
                    session_dir=str(session),
                )

            symbol = gate["symbol"]
            direction = gate["direction"]
            sizing = gate["sizing"]
            if not isinstance(sizing, dict):
                raise OperatorEngineError("SIZING_MISSING_AFTER_PASS")
            ext = _oid(signal_key, "entry", 1)

            try:
                claim = self.global_slot.claim(
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    external_oid=ext,
                )
            except Exception as exc:
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    blockers=[f"GLOBAL_SLOT_RESERVATION_ERROR:{type(exc).__name__}:{exc}"],
                    session_dir=str(session),
                )
            if claim.get("claim_status") == "OCCUPIED_BY_OTHER_SIGNAL":
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    blockers=["GLOBAL_SLOT_OCCUPIED_BY_OTHER_SIGNAL"],
                    global_slot_owner=claim.get("owner"),
                    session_dir=str(session),
                )

            policy = OperatorFuturesPolicy(
                policy_id=f"{candidate_id}:OPERATOR-V0.3",
                symbol=symbol,
                allowed_directions=(direction,),
                required_leverage=REQUIRED_LEVERAGE,
            )
            transport = MEXCOperatorFuturesTransportV02(self.credentials, policy)

            try:
                configure_ack = transport.configure_isolated_leverage(
                    symbol=symbol,
                    direction=direction,
                )
                _atomic_write(session / "LEVERAGE_CONFIGURATION_ACK.json", {
                    "receipt_type": "LEVERAGE_CONFIGURATION_ACK",
                    "symbol": symbol,
                    "direction": direction,
                    "leverage": REQUIRED_LEVERAGE,
                    "margin_mode": "ISOLATED",
                    "exchange_ack": configure_ack,
                })

                meta = direction_meta(direction)
                lev = [
                    row for row in self.readonly.leverage(symbol)
                    if int(row.get("positionType", 0) or 0) == meta["position_type"]
                ]
                leverage_ok = (
                    len(lev) == 1
                    and int(lev[0].get("leverage", 0) or 0) == REQUIRED_LEVERAGE
                    and int(lev[0].get("openType", 0) or 0) == 1
                )
                _atomic_write(session / "LEVERAGE_POST_VERIFY.json", {
                    "receipt_type": "LEVERAGE_POST_VERIFY",
                    "pass": leverage_ok,
                    "rows": lev,
                })
                if not leverage_ok:
                    raise OperatorEngineError("ISOLATED_5X_POST_VERIFY_FAILED")

                # Last exchange/account check while the process owns the global
                # reservation. The reservation serializes competing executors.
                if self.readonly.open_positions() or self.readonly.open_orders():
                    raise OperatorEngineError("LAST_MOMENT_POSITION_OR_ORDER_CONFLICT")
            except Exception as exc:
                _atomic_write(session / "ENTRY_NOT_SUBMITTED_FINAL.json", {
                    "receipt_type": "ENTRY_NOT_SUBMITTED_FINAL",
                    "signal_identity": signal_key,
                    "external_oid": ext,
                    "reason": f"{type(exc).__name__}:{exc}",
                    "order_submitted": False,
                })
                try:
                    self.global_slot.release(
                        signal_identity=signal_key,
                        reason="PRE_SUBMIT_ABORT_CONFIRMED",
                    )
                except Exception as release_exc:
                    return self._status(
                        "FAIL_CLOSED",
                        candidate_id=candidate_id,
                        signal_identity=signal_key,
                        blockers=[
                            f"PRE_SUBMIT_ABORT:{type(exc).__name__}:{exc}",
                            f"GLOBAL_SLOT_RELEASE_FAILED:{type(release_exc).__name__}",
                        ],
                        session_dir=str(session),
                    )
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    blockers=[f"PRE_SUBMIT_ABORT:{type(exc).__name__}:{exc}"],
                    session_dir=str(session),
                )

            intent = {
                "receipt_type": "ORDER_INTENT",
                "candidate_id": candidate_id,
                "signal_identity": signal_key,
                "symbol": symbol,
                "direction": direction,
                "entry_target_utc": gate["entry_target_utc"],
                "exit_target_utc": gate["exit_target_utc"],
                "volume_contracts": int(sizing["volume_contracts"]),
                "estimated_notional_usdt": sizing["estimated_notional_usdt"],
                "estimated_initial_margin_usdt": sizing["estimated_initial_margin_usdt"],
                "leverage": REQUIRED_LEVERAGE,
                "margin_mode": "ISOLATED",
                "external_oid": ext,
            }
            if not _exclusive_write(intent_path, intent):
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    reason="ORDER_INTENT_RACE_DETECTED",
                    blind_resend_allowed=False,
                    session_dir=str(session),
                )

            # Close the race between validation and actual submission. If the
            # kill switch appears here, no order is sent and the reservation can
            # be released only after writing an explicit terminal marker.
            if self.kill_switch_path.exists():
                _atomic_write(session / "ENTRY_NOT_SUBMITTED_FINAL.json", {
                    "receipt_type": "ENTRY_NOT_SUBMITTED_FINAL",
                    "signal_identity": signal_key,
                    "external_oid": ext,
                    "reason": "KILL_SWITCH_PRESENT_AT_FINAL_SEND_GATE",
                    "order_submitted": False,
                })
                self.global_slot.release(
                    signal_identity=signal_key,
                    reason="PRE_SUBMIT_ABORT_CONFIRMED",
                )
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    blockers=["KILL_SWITCH_PRESENT_AT_FINAL_SEND_GATE"],
                    session_dir=str(session),
                )

            try:
                ack = transport.submit_market_order(
                    symbol=symbol,
                    direction=direction,
                    phase="ENTRY",
                    volume_contracts=int(sizing["volume_contracts"]),
                    external_oid=ext,
                )
            except Exception as exc:
                _atomic_write(session / "ENTRY_ACK_UNKNOWN.json", {
                    "receipt_type": "ENTRY_ACK_UNKNOWN",
                    "external_oid": ext,
                    "error": f"{type(exc).__name__}:{exc}",
                    "blind_resend_allowed": False,
                })
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    blind_resend_allowed=False,
                    global_slot_reserved=True,
                    session_dir=str(session),
                )
            _atomic_write(session / "ENTRY_EXCHANGE_ACK.json", {
                "receipt_type": "ENTRY_EXCHANGE_ACK",
                "external_oid": ext,
                "exchange_ack": ack,
            })
            order = self._wait_order(symbol=symbol, external_oid=ext)
            if int(order.get("state", 0) or 0) not in (3, 4, 5):
                cancel = transport.cancel_by_external(symbol=symbol, external_oid=ext)
                _atomic_write(session / "ENTRY_CANCEL_ACK.json", {
                    "receipt_type": "ENTRY_CANCEL_ACK",
                    "exchange_ack": cancel,
                    "last_order": order,
                })
                order = self._wait_order(symbol=symbol, external_oid=ext, timeout=3)
            if float(order.get("dealVol", 0) or 0) <= 0:
                _atomic_write(session / "ENTRY_TERMINAL_NO_FILL_CONFIRMED.json", {
                    "receipt_type": "ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                    "signal_identity": signal_key,
                    "external_oid": ext,
                    "order": order,
                    "trade_opened": False,
                })
                try:
                    self.global_slot.release(
                        signal_identity=signal_key,
                        reason="ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                    )
                except Exception as exc:
                    return self._status(
                        "FAIL_CLOSED",
                        candidate_id=candidate_id,
                        signal_identity=signal_key,
                        blockers=[f"GLOBAL_SLOT_RELEASE_FAILED:{type(exc).__name__}"],
                        session_dir=str(session),
                    )
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate_id,
                    signal_identity=signal_key,
                    blockers=["ENTRY_ORDER_NOT_FILLED"],
                    session_dir=str(session),
                )
            position = self._position(symbol=symbol, direction=direction)

        if position is None:
            return self._status(
                "ENTRY_RECONCILIATION_REQUIRED",
                candidate_id=candidate_id,
                signal_identity=signal_key,
                reason="FILLED_ORDER_WITHOUT_MATCHING_POSITION",
                blind_resend_allowed=False,
                global_slot_reserved=True,
                session_dir=str(session),
            )

        entry_fee = order_fee_usdt(order)
        fill_price = float(order.get("dealAvgPrice") or position.get("openAvgPrice"))
        if not math.isfinite(entry_fee) or not math.isfinite(fill_price) or fill_price <= 0:
            return self._status(
                "ENTRY_RECONCILIATION_REQUIRED",
                candidate_id=candidate_id,
                signal_identity=signal_key,
                reason="NONFINITE_ENTRY_ACCOUNTING",
                blind_resend_allowed=False,
                global_slot_reserved=True,
                session_dir=str(session),
            )
        _atomic_write(session / "FILL_RECEIPT.json", {
            "receipt_type": "FILL_RECEIPT",
            "order": order,
            "entry_fee_usdt": entry_fee,
            "position_id": position.get("positionId"),
            "external_oid": ext,
            "deal_average_price": fill_price,
            "deal_volume_contracts": order.get("dealVol"),
        })

        active = {
            "receipt_type": "ACTIVE_TRADE_STATE",
            "state": "EXIT_PENDING",
            "candidate_id": candidate_id,
            "strategy_id": candidate_id,
            "signal_identity": signal_key,
            "symbol": symbol,
            "direction": direction,
            "position_id": int(position["positionId"]),
            "volume_contracts": int(float(position["holdVol"])),
            "contract_size": gate["contract"]["contract_size"],
            "entry_price": fill_price,
            "entry_fee_usdt": entry_fee,
            "entry_external_oid": ext,
            "entry_order_id": order.get("orderId"),
            "entry_target_utc": gate["entry_target_utc"],
            "opened_at_utc": _iso(datetime.now(timezone.utc)),
            "exit_target_utc": gate["exit_target_utc"],
            "exit_tolerance_seconds": float(signal.get("exit_tolerance_seconds", signal.get("max_late_seconds", 2.0)) or 2.0),
            "planned_notional_usdt": sizing["estimated_notional_usdt"],
            "planned_initial_margin_usdt": sizing["estimated_initial_margin_usdt"],
            "leverage": REQUIRED_LEVERAGE,
            "margin_mode": "ISOLATED",
            "auto_margin_add": None,
            "post_fill_risk_verified": False,
            "scientific_credit": False,
            "execution_failure": False,
            "global_slot_reserved": True,
            "protective_tpsl_required": bool(gate.get("protective_exit")),
            "protective_tpsl_verified": False,
        }
        active_path = session / "ACTIVE_TRADE_STATE.json"
        _atomic_write(active_path, active)

        policy = OperatorFuturesPolicy(
            policy_id=f"{candidate_id}:OPERATOR-V0.3",
            symbol=symbol,
            allowed_directions=(direction,),
            required_leverage=REQUIRED_LEVERAGE,
        )
        transport = MEXCOperatorFuturesTransportV02(self.credentials, policy)

        try:
            position = self._ensure_position_risk(
                transport=transport,
                symbol=symbol,
                direction=direction,
                position=position,
                session=session,
            )
        except Exception as exc:
            active["execution_failure"] = True
            active["post_fill_risk_verified"] = False
            active["post_fill_risk_error"] = f"{type(exc).__name__}:{exc}"
            _atomic_write(active_path, active)
            return self._exit_active(
                active_path=active_path,
                active=active,
                reason="POST_FILL_RISK_FAILURE",
            )

        active["volume_contracts"] = int(float(position["holdVol"]))
        active["auto_margin_add"] = False
        active["post_fill_risk_verified"] = True
        _atomic_write(active_path, active)

        if gate.get("protective_exit"):
            try:
                protection = self._install_position_protection(
                    transport=transport,
                    position=position,
                    direction=direction,
                    fill_price=fill_price,
                    protective=gate["protective_exit"],
                    price_unit=float(gate["contract"]["price_unit"]),
                    session=session,
                )
                active["protective_tpsl_order_id"] = protection["protective_order_id"]
                active["protective_stop_loss_price"] = protection["stop_loss_price"]
                active["protective_take_profit_price"] = protection["take_profit_price"]
                active["protective_price_unit"] = protection["price_unit"]
                active["protective_trigger_basis"] = protection["trigger_basis"]
                active["protective_tpsl_verified"] = True
                _atomic_write(active_path, active)
            except Exception as exc:
                active["execution_failure"] = True
                active["protective_tpsl_verified"] = False
                active["protective_tpsl_error"] = f"{type(exc).__name__}:{exc}"
                _atomic_write(active_path, active)
                return self._exit_active(
                    active_path=active_path,
                    active=active,
                    reason="POST_FILL_PROTECTIVE_TPSL_FAILURE",
                )

        return self._status(
            "FILLED_EXIT_PENDING",
            candidate_id=candidate_id,
            signal_identity=signal_key,
            direction=direction,
            symbol=symbol,
            exit_target_utc=active["exit_target_utc"],
            planned_notional_usdt=active["planned_notional_usdt"],
            planned_initial_margin_usdt=active["planned_initial_margin_usdt"],
            global_slot_reserved=True,
            session_dir=str(session),
        )

    def _exit_active(
        self,
        *,
        active_path: Path,
        active: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        session = active_path.parent
        symbol = str(active["symbol"]).upper()
        direction = str(active["direction"]).upper()
        signal_key = str(active["signal_identity"])
        policy = OperatorFuturesPolicy(
            policy_id=f"{active.get('candidate_id')}:OPERATOR-V0.3",
            symbol=symbol,
            allowed_directions=(direction,),
            required_leverage=REQUIRED_LEVERAGE,
        )
        transport = MEXCOperatorFuturesTransportV02(self.credentials, policy)

        position = self._position(symbol=symbol, direction=direction)
        if position is None:
            return self._status(
                "EXIT_RECONCILIATION_REQUIRED",
                reason="LOCAL_ACTIVE_BUT_EXCHANGE_POSITION_MISSING",
                signal_identity=signal_key,
                session_dir=str(session),
            )
        if int(position.get("positionId", 0) or 0) != int(active["position_id"]):
            return self._status(
                "EXIT_RECONCILIATION_REQUIRED",
                reason="POSITION_IDENTITY_MISMATCH",
                signal_identity=signal_key,
                session_dir=str(session),
            )

        hold_fee = float(position.get("holdFee", 0) or 0)
        exit_orders: list[dict[str, Any]] = []
        for attempt in (1, 2):
            position = self._position(symbol=symbol, direction=direction)
            if position is None:
                break
            volume = int(float(position.get("holdVol", 0) or 0))
            if volume <= 0:
                break
            ext = _oid(signal_key, "exit", attempt)
            intent_path = session / f"EXIT_INTENT_{attempt}.json"

            if intent_path.exists():
                try:
                    order = self._wait_order(
                        symbol=symbol,
                        external_oid=ext,
                        timeout=5,
                    )
                except Exception as exc:
                    _atomic_write(session / f"EXIT_RECONCILIATION_REQUIRED_{attempt}.json", {
                        "receipt_type": "EXIT_RECONCILIATION_REQUIRED",
                        "attempt": attempt,
                        "external_oid": ext,
                        "reason": "PRIOR_EXIT_INTENT_EXISTS_BUT_STATE_UNKNOWN__NO_RESUBMIT",
                        "error": f"{type(exc).__name__}:{exc}",
                    })
                    return self._status(
                        "EXIT_RECONCILIATION_REQUIRED",
                        signal_identity=signal_key,
                        blind_resend_allowed=False,
                        session_dir=str(session),
                    )
            else:
                _atomic_write(intent_path, {
                    "receipt_type": "EXIT_INTENT",
                    "attempt": attempt,
                    "reason": reason,
                    "signal_identity": signal_key,
                    "symbol": symbol,
                    "direction": direction,
                    "position_id": int(position["positionId"]),
                    "volume_contracts": volume,
                    "external_oid": ext,
                })
                try:
                    ack = transport.submit_market_order(
                        symbol=symbol,
                        direction=direction,
                        phase="EXIT",
                        volume_contracts=volume,
                        external_oid=ext,
                        position_id=int(position["positionId"]),
                    )
                except Exception as exc:
                    _atomic_write(session / f"EXIT_ACK_UNKNOWN_{attempt}.json", {
                        "receipt_type": "EXIT_ACK_UNKNOWN",
                        "attempt": attempt,
                        "external_oid": ext,
                        "error": f"{type(exc).__name__}:{exc}",
                        "blind_resend_allowed": False,
                    })
                    return self._status(
                        "EXIT_RECONCILIATION_REQUIRED",
                        signal_identity=signal_key,
                        blind_resend_allowed=False,
                        session_dir=str(session),
                    )
                _atomic_write(session / f"EXIT_EXCHANGE_ACK_{attempt}.json", {
                    "receipt_type": "EXIT_EXCHANGE_ACK",
                    "attempt": attempt,
                    "external_oid": ext,
                    "exchange_ack": ack,
                })
                order = self._wait_order(symbol=symbol, external_oid=ext)

            if float(order.get("dealVol", 0) or 0) > 0:
                exit_orders.append(order)
            time.sleep(0.25)
            if self._position(symbol=symbol, direction=direction) is None:
                break

        if self._position(symbol=symbol, direction=direction) is not None:
            _atomic_write(session / "EXIT_FAILURE.json", {
                "receipt_type": "EXIT_FAILURE",
                "reason": "POSITION_REMAINS_AFTER_TWO_TERMINAL_EXIT_ATTEMPTS",
                "execution_failure": True,
            })
            return self._status(
                "FAIL_CLOSED_POSITION_REMAINS",
                signal_identity=signal_key,
                session_dir=str(session),
            )

        if not exit_orders:
            return self._status(
                "EXIT_RECONCILIATION_REQUIRED",
                reason="POSITION_CLOSED_BUT_NO_ATTRIBUTABLE_EXIT_FILL",
                signal_identity=signal_key,
                session_dir=str(session),
            )

        exit_fee = sum(order_fee_usdt(order) for order in exit_orders)
        gross = sum(float(order.get("profit", 0) or 0) for order in exit_orders)
        num = sum(
            float(order.get("dealAvgPrice", 0) or 0)
            * float(order.get("dealVol", 0) or 0)
            for order in exit_orders
        )
        den = sum(float(order.get("dealVol", 0) or 0) for order in exit_orders)
        exit_price = num / den if den > 0 else None
        entry_fee = float(active.get("entry_fee_usdt", 0) or 0)
        net = gross + hold_fee - entry_fee - exit_fee
        closed = datetime.now(timezone.utc)
        target = _utc(active["exit_target_utc"])
        late = max(0.0, (closed - target).total_seconds())
        execution_failure = (
            reason != "SCHEDULED_EXIT"
            or late > float(active.get("exit_tolerance_seconds", 2.0) or 2.0)
        )

        _atomic_write(session / "EXIT_FILL_RECEIPT.json", {
            "receipt_type": "EXIT_FILL_RECEIPT",
            "reason": reason,
            "orders": exit_orders,
            "exit_fee_usdt": exit_fee,
            "exit_fill_price": exit_price,
            "position_closed_verified": True,
        })
        reconciliation = {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "candidate_id": active.get("candidate_id"),
            "strategy_id": active.get("strategy_id"),
            "signal_identity": signal_key,
            "closed_at_utc": _iso(closed),
            "gross_close_profit_usdt": gross,
            "funding_hold_fee_usdt": hold_fee,
            "entry_fee_usdt": entry_fee,
            "exit_fee_usdt": exit_fee,
            "realized_net_pnl_usdt": net,
            "entry_price": active.get("entry_price"),
            "exit_price": exit_price,
            "planned_notional_usdt": active.get("planned_notional_usdt"),
            "planned_initial_margin_usdt": active.get("planned_initial_margin_usdt"),
            "leverage": REQUIRED_LEVERAGE,
            "margin_mode": "ISOLATED",
            "scientific_credit": False,
            "exit_reason": reason,
            "late_seconds": late,
            "execution_failure": execution_failure,
            "open_position_after_reconciliation": False,
        }
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", reconciliation)
        active["state"] = "CLOSED"
        active["closed_at_utc"] = reconciliation["closed_at_utc"]
        active["execution_failure"] = execution_failure
        _atomic_write(active_path, active)
        try:
            release = self.global_slot.release(
                signal_identity=signal_key,
                reason="POST_TRADE_RECONCILIATION_CONFIRMED",
            )
        except Exception as exc:
            _atomic_write(session / "GLOBAL_SLOT_RELEASE_REQUIRED.json", {
                "receipt_type": "GLOBAL_SLOT_RELEASE_REQUIRED",
                "signal_identity": signal_key,
                "reason": f"{type(exc).__name__}:{exc}",
                "new_entry_allowed": False,
            })
            return self._status(
                "CLOSED_RECONCILED_SLOT_RELEASE_REQUIRED",
                candidate_id=active.get("candidate_id"),
                signal_identity=signal_key,
                realized_net_pnl_usdt=net,
                entry_fee_usdt=entry_fee,
                exit_fee_usdt=exit_fee,
                funding_hold_fee_usdt=hold_fee,
                session_dir=str(session),
            )
        return self._status(
            "CLOSED_RECONCILED",
            candidate_id=active.get("candidate_id"),
            signal_identity=signal_key,
            realized_net_pnl_usdt=net,
            entry_fee_usdt=entry_fee,
            exit_fee_usdt=exit_fee,
            funding_hold_fee_usdt=hold_fee,
            global_slot_release=release,
            session_dir=str(session),
        )

    def manage_active(self) -> dict[str, Any]:
        active = self._active_states()
        if not active:
            try:
                reservation = self.global_slot.current()
            except Exception as exc:
                return self._status(
                    "FAIL_CLOSED",
                    blockers=[f"GLOBAL_SLOT_RESERVATION_INVALID:{type(exc).__name__}:{exc}"],
                )
            if reservation is not None:
                return self._status(
                    "GLOBAL_SLOT_RESERVED_RECONCILIATION_REQUIRED",
                    signal_identity=reservation.get("signal_identity"),
                    candidate_id=reservation.get("candidate_id"),
                    external_oid=reservation.get("external_oid"),
                    blind_resend_allowed=False,
                )
            return self._status("IDLE_NO_OPERATOR_POSITION")
        if len(active) > 1:
            return self._status(
                "FAIL_CLOSED",
                blockers=["MULTIPLE_LOCAL_OPERATOR_ACTIVE_TRADES"],
                active_count=len(active),
            )

        active_path, row = active[0]
        try:
            claim = self.global_slot.claim(
                candidate_id=str(row.get("candidate_id") or row.get("strategy_id") or "unknown"),
                signal_identity=str(row.get("signal_identity") or ""),
                external_oid=str(row.get("entry_external_oid") or ""),
            )
        except Exception as exc:
            return self._status(
                "FAIL_CLOSED",
                candidate_id=row.get("candidate_id"),
                signal_identity=row.get("signal_identity"),
                blockers=[f"GLOBAL_SLOT_RECOVERY_FAILED:{type(exc).__name__}:{exc}"],
                session_dir=str(active_path.parent),
            )
        if claim.get("claim_status") == "OCCUPIED_BY_OTHER_SIGNAL":
            return self._status(
                "FAIL_CLOSED",
                candidate_id=row.get("candidate_id"),
                signal_identity=row.get("signal_identity"),
                blockers=["GLOBAL_SLOT_OWNER_MISMATCH_WITH_ACTIVE_POSITION"],
                global_slot_owner=claim.get("owner"),
                session_dir=str(active_path.parent),
            )
        exit_target = _utc(row["exit_target_utc"])
        now = datetime.now(timezone.utc)
        symbol = str(row.get("symbol") or "").upper()
        direction = str(row.get("direction") or "").upper()

        # Exchange truth is checked on every active-management cycle. At 5x,
        # liquidation/manual closure or a risk-setting drift must never remain
        # invisible until the scheduled exit.
        try:
            position = self._position(symbol=symbol, direction=direction)
        except Exception as exc:
            return self._status(
                "ACTIVE_POSITION_READ_FAIL_CLOSED",
                candidate_id=row.get("candidate_id"),
                signal_identity=row.get("signal_identity"),
                error=f"{type(exc).__name__}:{exc}",
                session_dir=str(active_path.parent),
            )

        if position is None:
            _atomic_write(active_path.parent / "POSITION_MISSING_BEFORE_RECONCILIATION.json", {
                "receipt_type": "POSITION_MISSING_BEFORE_RECONCILIATION",
                "observed_at_utc": _iso(now),
                "candidate_id": row.get("candidate_id"),
                "signal_identity": row.get("signal_identity"),
                "reason": "EXCHANGE_POSITION_MISSING_WHILE_LOCAL_ACTIVE_STATE_EXISTS",
                "possible_causes": ["LIQUIDATION", "MANUAL_OR_EXTERNAL_CLOSE", "EXCHANGE_RECONCILIATION_GAP"],
                "new_entry_allowed": False,
            })
            return self._status(
                "EXTERNAL_OR_LIQUIDATION_RECONCILIATION_REQUIRED",
                candidate_id=row.get("candidate_id"),
                signal_identity=row.get("signal_identity"),
                session_dir=str(active_path.parent),
            )

        if int(position.get("positionId", 0) or 0) != int(row.get("position_id", 0) or 0):
            return self._status(
                "ACTIVE_POSITION_IDENTITY_MISMATCH",
                candidate_id=row.get("candidate_id"),
                signal_identity=row.get("signal_identity"),
                session_dir=str(active_path.parent),
            )

        invariant_breach = (
            int(position.get("openType", 0) or 0) != 1
            or int(position.get("leverage", 0) or 0) != REQUIRED_LEVERAGE
            or position.get("autoAddIm") is not False
        )
        if invariant_breach:
            return self._exit_active(
                active_path=active_path,
                active=row,
                reason="ACTIVE_POSITION_RISK_INVARIANT_BREACH",
            )

        if self.kill_switch_path.exists():
            return self._exit_active(
                active_path=active_path,
                active=row,
                reason="KILL_SWITCH_EMERGENCY_EXIT",
            )
        if now >= exit_target:
            return self._exit_active(
                active_path=active_path,
                active=row,
                reason="SCHEDULED_EXIT",
            )
        return self._status(
            "ACTIVE_WAITING_EXIT",
            candidate_id=row.get("candidate_id"),
            signal_identity=row.get("signal_identity"),
            symbol=symbol,
            direction=direction,
            position_id=position.get("positionId"),
            hold_volume_contracts=position.get("holdVol"),
            exit_target_utc=row.get("exit_target_utc"),
            seconds_to_exit=(exit_target - now).total_seconds(),
            planned_notional_usdt=row.get("planned_notional_usdt"),
            planned_initial_margin_usdt=row.get("planned_initial_margin_usdt"),
            leverage=REQUIRED_LEVERAGE,
            margin_mode="ISOLATED",
            auto_margin_add=False,
        )


__all__ = [
    "OperatorFuturesEngineV02",
    "OperatorEngineError",
    "OFFICIAL_API_TAKER_FLOOR",
    "order_fee_usdt",
    "timing_state",
    "compute_contract_volume",
]
