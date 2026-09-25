from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from .evidence import EvidenceStore
from .market import MEXCFuturesPublicFeed
from .mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from .mexc_auth_trade import MEXCFuturesMutationTransport
from .options_v21_futures_execution_signal import (
    build_futures_execution_signal,
    latest_due_parent_entry,
)
from .options_v21_live import BinanceBTCUSDTDailyFeed, DeribitBTCOptionTradeFeed
from .options_v21_watcher import OptionsV21ForwardShadowWatcher

MAX_NOTIONAL_USDT = 10.0
DAILY_LOSS_KILL_USDT = 2.0
ROLLING_7D_LOSS_KILL_USDT = 5.0
MAX_CLOCK_OFFSET_MS = 500.0
STATUS_VERSION = "OPTIONS_FUTURES_ONLY_AUTO_MICROLIVE_V0.2.1"
OFFICIAL_API_TAKER_FLOOR = 0.0005


class OptionsFuturesAutoLiveError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    out = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(out, dict):
        raise OptionsFuturesAutoLiveError(f"JSON object required: {path}")
    return out


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _exclusive_write(path: Path, payload: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return True


def _utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise OptionsFuturesAutoLiveError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def _oid(signal_key: str, leg: str) -> str:
    digest = hashlib.sha256(f"{signal_key}:{leg}:futures-v02".encode("utf-8")).hexdigest()[:18]
    return f"ov2-{leg}-{digest}"


def _session_name(signal_key: str) -> str:
    digest = hashlib.sha256(signal_key.encode("utf-8")).hexdigest()[:20]
    return f"options-futures-{digest}"


def _floor_step(value: float, step: float) -> float:
    if value <= 0 or step <= 0:
        return 0.0
    dv = Decimal(str(value))
    ds = Decimal(str(step))
    units = (dv / ds).to_integral_value(rounding=ROUND_DOWN)
    return float(units * ds)


def _fee(order: dict[str, Any]) -> float:
    if order.get("totalFee") is not None:
        try:
            return abs(float(order["totalFee"]))
        except (TypeError, ValueError):
            pass
    total = 0.0
    for key in ("takerFee", "makerFee"):
        try:
            total += abs(float(order.get(key, 0) or 0))
        except (TypeError, ValueError):
            pass
    return total


def _direction_meta(direction: str) -> dict[str, Any]:
    if direction == "LONG":
        return {
            "position_type": 1,
            "entry_side": 1,
            "exit_side": 4,
            "entry_semantics": "OPEN_LONG",
            "exit_semantics": "CLOSE_LONG",
        }
    if direction == "SHORT":
        return {
            "position_type": 2,
            "entry_side": 3,
            "exit_side": 2,
            "entry_semantics": "OPEN_SHORT",
            "exit_semantics": "CLOSE_SHORT",
        }
    raise OptionsFuturesAutoLiveError(f"unsupported direction: {direction}")


class OptionsV21FuturesAutoLiveEngine:
    def __init__(
        self,
        *,
        credentials: MEXCCredentials,
        db_path: str,
        receipt_root: str,
        armed_path: str,
        kill_switch_path: str,
        status_path: str,
        source_timeout: int = 15,
    ) -> None:
        self.store = EvidenceStore(db_path)
        self.receipt_root = Path(receipt_root)
        self.armed_path = Path(armed_path)
        self.kill_switch_path = Path(kill_switch_path)
        self.status_path = Path(status_path)
        self.futures_ro = MEXCFuturesAuthenticatedReadOnlyClient(credentials)
        self.futures_mut = MEXCFuturesMutationTransport(credentials)
        self.futures_public = MEXCFuturesPublicFeed(timeout=10)
        self.watcher = OptionsV21ForwardShadowWatcher(
            store=self.store,
            options_feed=DeribitBTCOptionTradeFeed(timeout=source_timeout),
            btc_feed=BinanceBTCUSDTDailyFeed(timeout=source_timeout),
        )

    def _status(self, status: str, **extra: Any) -> dict[str, Any]:
        payload = {
            "version": STATUS_VERSION,
            "status": status,
            "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
            if row.get("state") in {"FILLED", "EXIT_PENDING"} and not (path.parent / "POST_TRADE_RECONCILIATION.json").exists():
                out.append((path, row))
        return out

    def _loss_state(self, now: datetime) -> tuple[float, float]:
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        rolling_start = now - timedelta(days=7)
        daily = 0.0
        rolling = 0.0
        if not self.receipt_root.exists():
            return daily, rolling
        for path in self.receipt_root.rglob("POST_TRADE_RECONCILIATION.json"):
            try:
                row = _load(path)
                closed = _utc(str(row["closed_at_utc"]))
                pnl = float(row["realized_net_pnl_usdt"])
            except Exception:
                continue
            loss = max(0.0, -pnl)
            if closed >= rolling_start:
                rolling += loss
            if closed >= day_start:
                daily += loss
        return daily, rolling

    def _position(self, direction: str) -> dict[str, Any] | None:
        meta = _direction_meta(direction)
        rows = self.futures_ro.open_positions("BTC_USDT")
        matches = [
            row for row in rows
            if int(row.get("positionType", 0) or 0) == int(meta["position_type"])
            and float(row.get("holdVol", 0) or 0) > 0
        ]
        if len(matches) > 1:
            raise OptionsFuturesAutoLiveError(f"MULTIPLE_{direction}_POSITIONS_PRESENT")
        return matches[0] if matches else None

    def _global_gate(self, now: datetime) -> dict[str, Any]:
        blockers: list[str] = []
        if not self.armed_path.exists():
            blockers.append("AUTO_MICROLIVE_FUTURES_NOT_ARMED")
        if self.kill_switch_path.exists():
            blockers.append("KILL_SWITCH_PRESENT")

        daily_loss, rolling_loss = self._loss_state(now)
        if daily_loss >= DAILY_LOSS_KILL_USDT:
            blockers.append("DAILY_LOSS_KILL_ACTIVE")
        if rolling_loss >= ROLLING_7D_LOSS_KILL_USDT:
            blockers.append("ROLLING_7D_LOSS_KILL_ACTIVE")

        active = self._active_states()
        if active:
            blockers.append("LOCAL_MICROLIVE_POSITION_ALREADY_ACTIVE")

        try:
            positions = self.futures_ro.open_positions()
            if positions:
                blockers.append("OPEN_FUTURES_POSITION_PRESENT")
        except Exception as exc:
            positions = []
            blockers.append(f"FUTURES_POSITION_READ_FAILED:{type(exc).__name__}")

        try:
            orders = self.futures_ro.open_orders()
            if orders:
                blockers.append("OPEN_FUTURES_ORDER_PRESENT")
        except Exception as exc:
            orders = []
            blockers.append(f"FUTURES_ORDER_READ_FAILED:{type(exc).__name__}")

        return {
            "pass": not blockers,
            "blockers": blockers,
            "daily_realized_loss_usdt": daily_loss,
            "rolling_7d_realized_loss_usdt": rolling_loss,
            "active_local_trades": len(active),
            "open_futures_positions": len(positions),
            "open_futures_orders": len(orders),
        }

    def _clock_gate(self) -> dict[str, Any]:
        before = time.time_ns() / 1_000_000.0
        server_ms = float(self.futures_public.server_time_ms())
        after = time.time_ns() / 1_000_000.0
        midpoint = (before + after) / 2.0
        offset = server_ms - midpoint
        return {
            "pass": abs(offset) <= MAX_CLOCK_OFFSET_MS,
            "server_minus_local_midpoint_ms": offset,
            "request_rtt_ms": after - before,
            "max_abs_offset_ms": MAX_CLOCK_OFFSET_MS,
        }

    def _execution_gate(self, signal: dict[str, Any], now: datetime) -> dict[str, Any]:
        blockers: list[str] = []
        global_gate = self._global_gate(now)
        blockers.extend(global_gate["blockers"])

        direction = str(signal.get("signal_direction") or "")
        if direction not in {"LONG", "SHORT"}:
            blockers.append("INVALID_SIGNAL_DIRECTION")
        if not signal.get("source_healthy"):
            blockers.append("CANONICAL_SOURCE_NOT_HEALTHY")
        if not signal.get("entry_window_open"):
            blockers.append("ENTRY_WINDOW_CLOSED_NO_CHASE")
        if signal.get("route") != "MEXC_USDT_PERP_BTC_USDT":
            blockers.append("EXECUTION_FORK_ROUTE_MISMATCH")
        if signal.get("symbol") != "BTC_USDT":
            blockers.append("SYMBOL_MISMATCH")
        if int(signal.get("leverage") or 0) != 1:
            blockers.append("LEVERAGE_MISMATCH")
        if signal.get("margin_mode") != "ISOLATED":
            blockers.append("MARGIN_MODE_MISMATCH")

        try:
            clock = self._clock_gate()
            if not clock["pass"]:
                blockers.append("WINDOWS_CLOCK_OFFSET_OUTSIDE_500MS")
        except Exception as exc:
            clock = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
            blockers.append("MEXC_CLOCK_CHECK_FAILED")

        try:
            mode = self.futures_ro.position_mode()
            if mode != 1:
                blockers.append("FUTURES_POSITION_MODE_NOT_HEDGE")
        except Exception as exc:
            mode = None
            blockers.append(f"FUTURES_POSITION_MODE_READ_FAILED:{type(exc).__name__}")

        try:
            assets = self.futures_ro.assets()
            usdt = next(x for x in assets if str(x.get("currency", "")).upper() == "USDT")
            equity = float(usdt.get("equity"))
            available = float(usdt.get("availableBalance"))
            if equity <= 0 or available <= 0:
                blockers.append("FUTURES_USDT_BALANCE_INVALID")
        except Exception as exc:
            equity = None
            available = None
            blockers.append(f"FUTURES_ACCOUNT_READ_FAILED:{type(exc).__name__}")

        try:
            contract = self.futures_public.contract_row("BTC_USDT")
            snap = self.futures_public.all_market_snapshots()["BTCUSDT"]
            if contract.get("apiAllowed") is False or contract.get("state") not in (None, 0):
                blockers.append("BTC_USDT_CONTRACT_NOT_AVAILABLE")
            contract_size = float(contract["contractSize"])
            min_vol = float(contract["minVol"])
            step = float(contract["volUnit"])
            bid = float(snap.bid_price)
            ask = float(snap.ask_price)
            last = float(snap.last_price)
            conservative_price = max(last, ask)
            target = min(MAX_NOTIONAL_USDT, float(signal["planned_notional_usdt"]))
            max_contracts = target / (contract_size * conservative_price)
            volume = _floor_step(max_contracts, step)
            if volume < min_vol:
                blockers.append("VENUE_MINIMUM_EXCEEDS_WEIGHTED_MICROLIVE_BUDGET")
            if abs(volume - round(volume)) > 1e-9:
                blockers.append("NON_INTEGER_FUTURES_VOLUME_UNSUPPORTED")
            volume_int = int(round(volume)) if volume > 0 else 0
            estimated_notional = volume_int * contract_size * conservative_price
            if estimated_notional > target + 1e-9 or estimated_notional > MAX_NOTIONAL_USDT + 1e-9:
                blockers.append("FUTURES_NOTIONAL_EXCEEDS_CAP")
            mid = (bid + ask) / 2.0
            spread_bps = ((ask - bid) / mid) * 10000.0 if mid > 0 else 999999.0
        except Exception as exc:
            target = float(signal.get("planned_notional_usdt", 0) or 0)
            volume_int = 0
            estimated_notional = None
            bid = ask = last = spread_bps = None
            blockers.append(f"FUTURES_MARKET_METADATA_FAILED:{type(exc).__name__}")

        try:
            funding = self.futures_public.funding_rate("BTC_USDT")
            current_funding_rate = float(funding.get("fundingRate", 0) or 0)
            current_funding_abs_bps = abs(current_funding_rate) * 10000.0
        except Exception as exc:
            current_funding_rate = None
            current_funding_abs_bps = None
            blockers.append(f"FUNDING_READ_FAILED:{type(exc).__name__}")

        try:
            fees = self.futures_ro.fee_details("BTC_USDT")
            taker_raw = fees.get("realTakerFee")
            if taker_raw is None:
                taker_raw = fees.get("takerFee")
            taker = float(taker_raw)
            effective_taker = max(taker, OFFICIAL_API_TAKER_FLOOR)
            projected_round_trip_fee_bps = 2.0 * effective_taker * 10000.0
            projected_known_friction_bps = projected_round_trip_fee_bps + (2.0 * float(spread_bps or 0.0))
            if projected_known_friction_bps > 20.0:
                blockers.append("KNOWN_EXECUTION_FRICTION_EXCEEDS_STRESS20")
        except Exception as exc:
            taker = None
            projected_round_trip_fee_bps = None
            projected_known_friction_bps = None
            blockers.append(f"FUTURES_FEE_READ_FAILED:{type(exc).__name__}")

        return {
            "route": "MEXC_USDT_PERP_BTC_USDT",
            "direction": direction,
            "pass": not blockers,
            "blockers": blockers,
            "global_gate": global_gate,
            "clock": clock,
            "position_mode": mode,
            "futures_equity_usdt": equity,
            "futures_available_usdt": available,
            "target_notional_usdt": target,
            "volume_contracts": volume_int,
            "estimated_notional_usdt": estimated_notional,
            "bid": bid,
            "ask": ask,
            "last": last,
            "spread_bps": spread_bps,
            "account_taker_fee_fraction": taker,
            "official_api_taker_floor_fraction": OFFICIAL_API_TAKER_FLOOR,
            "projected_round_trip_fee_bps": projected_round_trip_fee_bps,
            "projected_known_friction_bps_ex_funding": projected_known_friction_bps,
            "current_funding_rate": current_funding_rate,
            "current_funding_abs_bps": current_funding_abs_bps,
        }

    def _wait_order(self, external_oid: str, timeout: float = 12.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            try:
                last = self.futures_ro.order_by_external(symbol="BTC_USDT", external_oid=external_oid)
            except Exception:
                time.sleep(0.5)
                continue
            if int(last.get("state", 0) or 0) in (3, 4, 5):
                return last
            time.sleep(0.5)
        if last is None:
            raise OptionsFuturesAutoLiveError("ACK_LOST_RECONCILIATION_REQUIRED")
        return last

    def _build_active(
        self,
        *,
        signal: dict[str, Any],
        gate: dict[str, Any],
        direction: str,
        order: dict[str, Any],
        position: dict[str, Any],
        external_oid: str,
        recovered: bool = False,
    ) -> dict[str, Any]:
        active = {
            "state": "EXIT_PENDING",
            "strategy_id": signal["strategy_id"],
            "execution_fork_id": signal["execution_fork_id"],
            "signal_identity": signal["immutable_signal_key"],
            "route": "MEXC_USDT_PERP_BTC_USDT",
            "direction": direction,
            "symbol": "BTC_USDT",
            "position_id": int(position["positionId"]),
            "volume_contracts": int(float(position["holdVol"])),
            "entry_price": float(order.get("dealAvgPrice") or position.get("openAvgPrice")),
            "entry_fee_usdt": _fee(order),
            "entry_target_utc": signal["entry_target_utc"],
            "exit_target_utc": signal["exit_target_utc"],
            "planned_notional_usdt": float(gate["estimated_notional_usdt"]),
            "entry_external_oid": external_oid,
            "promotion_credit_to_spot_parent": False,
        }
        if recovered:
            active["recovered_after_restart"] = True
        return active

    def _reconcile_entry(
        self,
        *,
        signal: dict[str, Any],
        session: Path,
        intent: dict[str, Any],
        gate: dict[str, Any],
    ) -> dict[str, Any]:
        active_path = session / "ACTIVE_TRADE_STATE.json"
        if active_path.exists():
            return {"status": "ALREADY_ACTIVE", "active": _load(active_path)}
        direction = str(intent["direction"])
        ext = str(intent["external_oid"])
        try:
            order = self.futures_ro.order_by_external(symbol="BTC_USDT", external_oid=ext)
            position = self._position(direction)
        except Exception as exc:
            return {
                "status": "ENTRY_RECONCILIATION_REQUIRED",
                "reason": f"{type(exc).__name__}: {exc}",
                "blind_resend_allowed": False,
            }
        if position is None or float(order.get("dealVol", 0) or 0) <= 0:
            return {
                "status": "ENTRY_RECONCILIATION_REQUIRED",
                "reason": "INTENT_EXISTS_BUT_NO_PROVABLE_FILL",
                "blind_resend_allowed": False,
            }
        active = self._build_active(
            signal=signal,
            gate=gate,
            direction=direction,
            order=order,
            position=position,
            external_oid=ext,
            recovered=True,
        )
        _atomic_write(active_path, active)
        return {"status": f"{direction}_RECOVERED", "active": active}

    def _enter(self, signal: dict[str, Any], session: Path, gate: dict[str, Any]) -> dict[str, Any]:
        direction = str(signal["signal_direction"])
        meta = _direction_meta(direction)
        signal_key = str(signal["immutable_signal_key"])
        ext = _oid(signal_key, "entry")
        intent = {
            "receipt_type": "ORDER_INTENT",
            "strategy_id": signal["strategy_id"],
            "execution_fork_id": signal["execution_fork_id"],
            "signal_identity": signal_key,
            "route": "MEXC_USDT_PERP_BTC_USDT",
            "direction": direction,
            "symbol": "BTC_USDT",
            "volume_contracts": int(gate["volume_contracts"]),
            "planned_notional_usdt": gate["estimated_notional_usdt"],
            "external_oid": ext,
            "entry_side": int(meta["entry_side"]),
            "entry_side_semantics": meta["entry_semantics"],
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        intent_path = session / "ORDER_INTENT.json"
        if not _exclusive_write(intent_path, intent):
            return self._reconcile_entry(signal=signal, session=session, intent=intent, gate=gate)

        self.futures_mut.configure_isolated_leverage(
            symbol="BTC_USDT",
            position_type=int(meta["position_type"]),
            leverage=1,
        )
        _atomic_write(
            session / "MARGIN_CONFIG_RECEIPT.json",
            {
                "symbol": "BTC_USDT",
                "direction": direction,
                "isolated": True,
                "leverage": 1,
                "position_type": int(meta["position_type"]),
            },
        )

        try:
            ack = self.futures_mut.submit_market_order(
                symbol="BTC_USDT",
                volume_contracts=int(gate["volume_contracts"]),
                side=int(meta["entry_side"]),
                external_oid=ext,
                position_mode=1,
            )
            _atomic_write(
                session / "EXCHANGE_ACK.json",
                {
                    "route": "MEXC_USDT_PERP_BTC_USDT",
                    "direction": direction,
                    "external_oid": ext,
                    "exchange_ack": ack,
                },
            )
        except Exception as exc:
            _atomic_write(
                session / "ENTRY_UNCERTAIN.json",
                {
                    "reason": f"{type(exc).__name__}: {exc}",
                    "external_oid": ext,
                    "blind_resend_allowed": False,
                },
            )
            raise

        order = self._wait_order(ext)
        _atomic_write(session / "FILL_RECEIPT.json", {"direction": direction, "order": order})
        position = self._position(direction)
        if position is None:
            raise OptionsFuturesAutoLiveError(f"NO_{direction}_POSITION_AFTER_ENTRY_ACK")

        try:
            if position.get("autoAddIm") is not False:
                self.futures_mut.set_auto_add_margin(position_id=int(position["positionId"]), enabled=False)
                time.sleep(0.25)
                position = self._position(direction) or position
            if (
                int(position.get("openType", 0) or 0) != 1
                or int(position.get("leverage", 0) or 0) != 1
                or position.get("autoAddIm") is not False
            ):
                raise OptionsFuturesAutoLiveError("POST_FILL_MARGIN_PROTECTION_NOT_VERIFIED")
        except Exception:
            try:
                hold_vol = int(float(position.get("holdVol", 0) or 0))
                if hold_vol > 0:
                    self.futures_mut.submit_market_order(
                        symbol="BTC_USDT",
                        volume_contracts=hold_vol,
                        side=int(meta["exit_side"]),
                        external_oid=_oid(signal_key, "emergency"),
                        position_mode=1,
                        position_id=int(position["positionId"]),
                    )
            finally:
                raise

        active = self._build_active(
            signal=signal,
            gate=gate,
            direction=direction,
            order=order,
            position=position,
            external_oid=ext,
        )
        _atomic_write(session / "ACTIVE_TRADE_STATE.json", active)
        return {"status": f"{direction}_ENTERED", "session": str(session), "active": active}

    def _exit(self, active_path: Path, active: dict[str, Any], now: datetime, emergency: bool) -> dict[str, Any]:
        session = active_path.parent
        direction = str(active["direction"])
        meta = _direction_meta(direction)
        signal_key = str(active["signal_identity"])
        oid = _oid(signal_key, "exit")
        position = self._position(direction)

        intent = {
            "receipt_type": "EXIT_INTENT",
            "strategy_id": active["strategy_id"],
            "execution_fork_id": active["execution_fork_id"],
            "signal_identity": signal_key,
            "route": active["route"],
            "direction": direction,
            "symbol": "BTC_USDT",
            "position_id": int(active["position_id"]),
            "exit_side": int(meta["exit_side"]),
            "exit_side_semantics": meta["exit_semantics"],
            "external_oid": oid,
            "reason": "KILL_SWITCH" if emergency else "SCHEDULED_24H_EXIT",
        }
        intent_path = session / "EXIT_INTENT.json"

        preclose_hold_fee = float(position.get("holdFee", 0) or 0) if position else 0.0

        if not _exclusive_write(intent_path, intent):
            try:
                order = self.futures_ro.order_by_external(symbol="BTC_USDT", external_oid=oid)
            except Exception as exc:
                return {
                    "status": "EXIT_RECONCILIATION_REQUIRED",
                    "reason": f"{type(exc).__name__}: {exc}",
                    "blind_resend_allowed": False,
                }
        else:
            if position is None:
                return {
                    "status": "EXIT_RECONCILIATION_REQUIRED",
                    "reason": "ACTIVE_RECEIPT_WITHOUT_MATCHING_OPEN_POSITION",
                    "blind_resend_allowed": False,
                }
            if int(position.get("positionId", 0) or 0) != int(active["position_id"]):
                return {"status": "FAIL_CLOSED", "reason": "POSITION_ID_MISMATCH"}

            ack = self.futures_mut.submit_market_order(
                symbol="BTC_USDT",
                volume_contracts=int(float(position["holdVol"])),
                side=int(meta["exit_side"]),
                external_oid=oid,
                position_mode=1,
                position_id=int(position["positionId"]),
            )
            _atomic_write(
                session / "EXIT_EXCHANGE_ACK.json",
                {"external_oid": oid, "direction": direction, "exchange_ack": ack},
            )
            order = self._wait_order(oid)

        if self._position(direction) is not None:
            return {
                "status": "EXIT_RECONCILIATION_REQUIRED",
                "reason": f"{direction}_POSITION_REMAINS",
                "blind_resend_allowed": False,
            }

        exit_fee = _fee(order)
        gross_profit = float(order.get("profit", 0) or 0)
        realized = gross_profit + preclose_hold_fee - float(active.get("entry_fee_usdt", 0) or 0) - exit_fee
        closed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        recon = {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "strategy_id": active["strategy_id"],
            "execution_fork_id": active["execution_fork_id"],
            "signal_identity": signal_key,
            "route": active["route"],
            "direction": direction,
            "closed_at_utc": closed,
            "gross_close_profit_usdt": gross_profit,
            "funding_hold_fee_usdt": preclose_hold_fee,
            "entry_fee_usdt": float(active.get("entry_fee_usdt", 0) or 0),
            "exit_fee_usdt": exit_fee,
            "realized_net_pnl_usdt": realized,
            "exit_reason": "KILL_SWITCH" if emergency else "SCHEDULED_24H_EXIT",
            "open_position_after_reconciliation": False,
            "promotion_credit_to_spot_parent": False,
        }
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", recon)
        active["state"] = "CLOSED"
        active["closed_at_utc"] = closed
        _atomic_write(active_path, active)
        return {"status": f"{direction}_CLOSED_RECONCILED", "realized_net_pnl_usdt": realized}

    def manage_active(self, now: datetime) -> dict[str, Any] | None:
        rows = self._active_states()
        if not rows:
            return None
        if len(rows) > 1:
            return self._status("FAIL_CLOSED", blockers=["MULTIPLE_LOCAL_ACTIVE_MICROLIVE_TRADES"])

        path, active = rows[0]
        exit_target = _utc(str(active["exit_target_utc"]))
        emergency = self.kill_switch_path.exists()
        if not emergency and now < exit_target:
            return self._status(
                "ACTIVE_WAITING_EXIT",
                route=active.get("route"),
                direction=active.get("direction"),
                signal_identity=active.get("signal_identity"),
                exit_target_utc=active.get("exit_target_utc"),
                seconds_to_exit=(exit_target - now).total_seconds(),
            )

        result = self._exit(path, active, now, emergency)
        return self._status(result.get("status", "FAIL_CLOSED"), result=result)

    def run_once(self, *, now_utc: datetime | None = None) -> dict[str, Any]:
        now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)

        active = self.manage_active(now)
        if active is not None:
            return active

        try:
            watcher_state = self.watcher.run_once(now_ms=int(now.timestamp() * 1000))
        except Exception as exc:
            return self._status("SOURCE_FAIL_CLOSED", blockers=[f"{type(exc).__name__}: {exc}"])

        entry = latest_due_parent_entry(self.store, now_utc=now)
        if entry is None:
            return self._status(
                "IDLE_WAITING_CANONICAL_OPTIONS_ENTRY",
                watcher_status=watcher_state.get("status"),
                latest_complete_signal_day=watcher_state.get("latest_complete_signal_day"),
            )

        signal = build_futures_execution_signal(
            entry,
            watcher_status=str(watcher_state.get("status") or ""),
            now_utc=now,
        )
        session = self.receipt_root / _session_name(str(signal["immutable_signal_key"]))
        session.mkdir(parents=True, exist_ok=True)
        _atomic_write(session / "CANONICAL_EXECUTION_SIGNAL.json", signal)

        if (session / "POST_TRADE_RECONCILIATION.json").exists():
            return self._status("SIGNAL_ALREADY_CONSUMED", signal_identity=signal["immutable_signal_key"])

        if not signal["source_healthy"]:
            return self._status("FAIL_CLOSED", blockers=["CANONICAL_SOURCE_NOT_HEALTHY"], signal=signal)

        if not signal["entry_window_open"]:
            missed = {
                "signal_identity": signal["immutable_signal_key"],
                "status": "MISSED_ENTRY_WINDOW_NO_CHASE",
                "seconds_from_entry_target": signal["seconds_from_entry_target"],
                "entry_ttl_seconds": signal["entry_ttl_seconds"],
            }
            _atomic_write(session / "MISSED_ENTRY_RECEIPT.json", missed)
            return self._status("MISSED_ENTRY_WINDOW_NO_CHASE", signal=signal)

        gate = self._execution_gate(signal, now)
        _atomic_write(session / "PRE_ORDER_GATE.json", gate)
        if not gate["pass"]:
            return self._status("FAIL_CLOSED", blockers=gate["blockers"], signal=signal, gate=gate)

        try:
            result = self._enter(signal, session, gate)
        except Exception as exc:
            return self._status(
                "ENTRY_FAIL_CLOSED",
                blockers=[f"{type(exc).__name__}: {exc}"],
                signal_identity=signal["immutable_signal_key"],
                session=str(session),
            )
        return self._status(result["status"], result=result)


__all__ = [
    "OptionsV21FuturesAutoLiveEngine",
    "OptionsFuturesAutoLiveError",
    "STATUS_VERSION",
    "_direction_meta",
    "_exclusive_write",
    "_floor_step",
]
