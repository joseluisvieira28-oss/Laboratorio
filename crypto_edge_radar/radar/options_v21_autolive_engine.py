from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

from .evidence import EvidenceStore
from .market import MEXCFuturesPublicFeed
from .mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from .mexc_auth_trade import MEXCFuturesMutationTransport
from .mexc_spot import MEXCSpotPublicFeed
from .mexc_spot_auth import MEXCSpotAuthenticatedClient
from .options_v21_execution_signal import build_execution_signal, latest_due_parent_entry
from .options_v21_live import BinanceBTCUSDTDailyFeed, DeribitBTCOptionTradeFeed
from .options_v21_watcher import OptionsV21ForwardShadowWatcher

MAX_NOTIONAL_USDT = 10.0
DAILY_LOSS_KILL_USDT = 2.0
ROLLING_7D_LOSS_KILL_USDT = 5.0
MAX_CLOCK_OFFSET_MS = 500.0
STATUS_VERSION = "OPTIONS_AUTO_MICROLIVE_V0.1"


class OptionsAutoLiveError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    out = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(out, dict):
        raise OptionsAutoLiveError(f"JSON object required: {path}")
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
        try:
            path.unlink(missing_ok=True)
        finally:
            raise
    return True


def _utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise OptionsAutoLiveError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def _oid(signal_key: str, leg: str) -> str:
    digest = hashlib.sha256(f"{signal_key}:{leg}".encode("utf-8")).hexdigest()[:20]
    return f"opt-{leg}-{digest}"


def _session_name(signal_key: str) -> str:
    digest = hashlib.sha256(signal_key.encode("utf-8")).hexdigest()[:20]
    return f"options-{digest}"


def _fee_from_futures_order(order: dict[str, Any]) -> float:
    if order.get("totalFee") is not None:
        try:
            return abs(float(order["totalFee"]))
        except (TypeError, ValueError):
            pass
    total = 0.0
    for field in ("takerFee", "makerFee"):
        try:
            total += abs(float(order.get(field, 0) or 0))
        except (TypeError, ValueError):
            pass
    return total


def _spot_balance(account: dict[str, Any], asset: str) -> tuple[float, float]:
    for row in account.get("balances") or []:
        if str(row.get("asset", "")).upper() == asset.upper():
            return float(row.get("free", 0) or 0), float(row.get("locked", 0) or 0)
    return 0.0, 0.0


def _floor_step(value: float, step: float) -> float:
    if value <= 0 or step <= 0:
        return 0.0
    dv = Decimal(str(value))
    ds = Decimal(str(step))
    units = (dv / ds).to_integral_value(rounding=ROUND_DOWN)
    return float(units * ds)


class OptionsV21AutoLiveEngine:
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
        self.spot_auth = MEXCSpotAuthenticatedClient(credentials)
        self.spot_public = MEXCSpotPublicFeed(timeout=10)
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

    def _global_gate(self, now: datetime) -> dict[str, Any]:
        blockers: list[str] = []
        if not self.armed_path.exists():
            blockers.append("AUTO_MICROLIVE_NOT_ARMED")
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
            fut_orders = self.futures_ro.open_orders()
            if fut_orders:
                blockers.append("OPEN_FUTURES_ORDER_PRESENT")
        except Exception as exc:
            fut_orders = []
            blockers.append(f"FUTURES_ORDER_READ_FAILED:{type(exc).__name__}")

        try:
            spot_orders = self.spot_auth.open_orders()
            if spot_orders:
                blockers.append("OPEN_SPOT_ORDER_PRESENT")
        except Exception as exc:
            spot_orders = []
            blockers.append(f"SPOT_ORDER_READ_FAILED:{type(exc).__name__}")

        return {
            "pass": not blockers,
            "blockers": blockers,
            "daily_realized_loss_usdt": daily_loss,
            "rolling_7d_realized_loss_usdt": rolling_loss,
            "active_local_trades": len(active),
            "open_futures_positions": len(positions),
            "open_futures_orders": len(fut_orders),
            "open_spot_orders": len(spot_orders),
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

    def _short_gate(self, signal: dict[str, Any], now: datetime) -> dict[str, Any]:
        blockers: list[str] = []
        global_gate = self._global_gate(now)
        blockers.extend(global_gate["blockers"])

        if not signal.get("source_healthy"):
            blockers.append("CANONICAL_SOURCE_NOT_HEALTHY")
        if not signal.get("entry_window_open"):
            blockers.append("ENTRY_WINDOW_CLOSED_NO_CHASE")
        if signal.get("signal_direction") != "SHORT":
            blockers.append("SIGNAL_NOT_SHORT")

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
            price = max(float(snap.last_price), float(snap.ask_price))
            target = min(MAX_NOTIONAL_USDT, float(signal["planned_notional_usdt"]))
            max_contracts = target / (contract_size * price)
            volume = _floor_step(max_contracts, step)
            if volume < min_vol:
                blockers.append("VENUE_MINIMUM_EXCEEDS_WEIGHTED_MICROLIVE_BUDGET")
            if abs(volume - round(volume)) > 1e-9:
                blockers.append("NON_INTEGER_FUTURES_VOLUME_UNSUPPORTED")
            volume_int = int(round(volume)) if volume > 0 else 0
            actual_notional = volume_int * contract_size * price
            if actual_notional > target + 1e-9 or actual_notional > MAX_NOTIONAL_USDT + 1e-9:
                blockers.append("FUTURES_NOTIONAL_EXCEEDS_CAP")
        except Exception as exc:
            contract = {}
            price = None
            target = float(signal.get("planned_notional_usdt", 0) or 0)
            volume_int = 0
            actual_notional = None
            blockers.append(f"FUTURES_MARKET_METADATA_FAILED:{type(exc).__name__}")

        try:
            fees = self.futures_ro.fee_details("BTC_USDT")
            taker = float(fees.get("realTakerFee") if fees.get("realTakerFee") is not None else fees.get("takerFee"))
            effective_taker = max(taker, 0.0008)
            projected_round_trip_bps = 2.0 * effective_taker * 10000.0
            if projected_round_trip_bps > 20.0:
                blockers.append("FUTURES_FEE_FLOOR_EXCEEDS_STRESS20")
        except Exception as exc:
            projected_round_trip_bps = None
            blockers.append(f"FUTURES_FEE_READ_FAILED:{type(exc).__name__}")

        return {
            "route": "MEXC_USDT_PERP_BTC_USDT",
            "pass": not blockers,
            "blockers": blockers,
            "global_gate": global_gate,
            "clock": clock,
            "position_mode": mode,
            "futures_equity_usdt": equity,
            "futures_available_usdt": available,
            "target_notional_usdt": target,
            "volume_contracts": volume_int,
            "estimated_notional_usdt": actual_notional,
            "reference_price": price,
            "projected_round_trip_fee_bps": projected_round_trip_bps,
        }

    def _spot_gate(self, signal: dict[str, Any], now: datetime) -> dict[str, Any]:
        blockers: list[str] = []
        global_gate = self._global_gate(now)
        blockers.extend(global_gate["blockers"])

        if not signal.get("source_healthy"):
            blockers.append("CANONICAL_SOURCE_NOT_HEALTHY")
        if not signal.get("entry_window_open"):
            blockers.append("ENTRY_WINDOW_CLOSED_NO_CHASE")
        if signal.get("signal_direction") != "LONG":
            blockers.append("SIGNAL_NOT_LONG")

        try:
            local_ms = time.time_ns() / 1_000_000.0
            server_ms = float(self.spot_public.server_time_ms())
            spot_clock_offset = server_ms - local_ms
            if abs(spot_clock_offset) > MAX_CLOCK_OFFSET_MS:
                blockers.append("SPOT_CLOCK_OFFSET_OUTSIDE_500MS")
        except Exception as exc:
            spot_clock_offset = None
            blockers.append(f"SPOT_CLOCK_CHECK_FAILED:{type(exc).__name__}")

        try:
            info = self.spot_public.exchange_info("BTCUSDT")
            order_types = set(info.get("orderTypes") or [])
            if info.get("isSpotTradingAllowed") is not True:
                blockers.append("BTCUSDT_SPOT_TRADING_NOT_ALLOWED")
            if info.get("quoteOrderQtyMarketAllowed") is not True:
                blockers.append("BTCUSDT_QUOTE_MARKET_NOT_ALLOWED")
            if "MARKET" not in order_types:
                blockers.append("BTCUSDT_MARKET_ORDER_NOT_ALLOWED")
            if str(info.get("tradeSideType", "1")) not in {"1", "2"}:
                blockers.append("BTCUSDT_BUY_SIDE_NOT_ALLOWED")
            min_market = float(info.get("quoteAmountPrecisionMarket") or info.get("quoteAmountPrecision") or 0)
            max_market = float(info.get("maxQuoteAmountMarket") or info.get("maxQuoteAmount") or 0)
        except Exception as exc:
            info = {}
            min_market = 0.0
            max_market = 0.0
            blockers.append(f"SPOT_EXCHANGE_INFO_FAILED:{type(exc).__name__}")

        target = min(MAX_NOTIONAL_USDT, float(signal["planned_notional_usdt"]))
        if min_market > 0 and target < min_market:
            blockers.append("SPOT_MINIMUM_EXCEEDS_WEIGHTED_MICROLIVE_BUDGET")
        if max_market > 0 and target > max_market:
            blockers.append("SPOT_TARGET_EXCEEDS_VENUE_MAX")

        try:
            account = self.spot_auth.account()
            if account.get("canTrade") is not True:
                blockers.append("SPOT_ACCOUNT_CANNOT_TRADE")
            free_usdt, locked_usdt = _spot_balance(account, "USDT")
            if free_usdt + 1e-12 < target:
                blockers.append("INSUFFICIENT_SPOT_USDT_FOR_LONG")
        except Exception as exc:
            free_usdt = None
            locked_usdt = None
            blockers.append(f"SPOT_ACCOUNT_READ_FAILED:{type(exc).__name__}")

        try:
            book = self.spot_public.book_ticker("BTCUSDT")
            depth = self.spot_public.depth("BTCUSDT", limit=20)
            bid = float(book["bidPrice"]); ask = float(book["askPrice"])
            if bid <= 0 or ask <= 0 or ask < bid:
                raise ValueError("invalid top of book")
            ask_capacity = sum(float(p) * float(q) for p, q, *_ in depth.get("asks") or [])
            if ask_capacity < target:
                blockers.append("SPOT_VISIBLE_ASK_DEPTH_BELOW_TARGET")
            spread_bps = (ask - bid) / ((ask + bid) / 2.0) * 10000.0
        except Exception as exc:
            bid = ask = spread_bps = ask_capacity = None
            blockers.append(f"SPOT_MARKET_DATA_FAILED:{type(exc).__name__}")

        return {
            "route": "MEXC_SPOT_BTCUSDT",
            "pass": not blockers,
            "blockers": blockers,
            "global_gate": global_gate,
            "spot_clock_offset_ms": spot_clock_offset,
            "target_notional_usdt": target,
            "spot_free_usdt": free_usdt,
            "spot_locked_usdt": locked_usdt,
            "minimum_market_quote_usdt": min_market,
            "maximum_market_quote_usdt": max_market,
            "bid": bid,
            "ask": ask,
            "spread_bps": spread_bps,
            "visible_ask_capacity_usdt": ask_capacity,
        }

    def _wait_futures_order(self, external_oid: str, timeout: float = 12.0) -> dict[str, Any]:
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
            raise OptionsAutoLiveError("FUTURES_ACK_LOST_RECONCILIATION_REQUIRED")
        return last

    def _short_position(self) -> dict[str, Any] | None:
        rows = self.futures_ro.open_positions("BTC_USDT")
        short = [
            x for x in rows
            if int(x.get("positionType", 0) or 0) == 2 and float(x.get("holdVol", 0) or 0) > 0
        ]
        if len(short) > 1:
            raise OptionsAutoLiveError("MULTIPLE_SHORT_POSITIONS_PRESENT")
        return short[0] if short else None

    def _spot_fill_summary(self, order: dict[str, Any]) -> dict[str, float]:
        order_id = str(order.get("orderId") or "")
        trades = self.spot_auth.my_trades(order_id=order_id) if order_id else []
        qty = 0.0
        quote = 0.0
        btc_commission = 0.0
        usdt_commission = 0.0
        for row in trades:
            q = float(row.get("qty", 0) or 0)
            qq = float(row.get("quoteQty", 0) or 0)
            qty += q
            quote += qq
            commission = abs(float(row.get("commission", 0) or 0))
            asset = str(row.get("commissionAsset", "")).upper()
            if asset == "BTC":
                btc_commission += commission
            elif asset == "USDT":
                usdt_commission += commission
        if qty <= 0:
            qty = float(order.get("executedQty", 0) or 0)
        if quote <= 0:
            quote = float(order.get("cummulativeQuoteQty", 0) or 0)
        return {
            "gross_btc": qty,
            "gross_quote_usdt": quote,
            "btc_commission": btc_commission,
            "usdt_commission": usdt_commission,
            "net_btc": max(0.0, qty - btc_commission),
        }

    def _wait_spot_order(self, client_oid: str, timeout: float = 12.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            try:
                last = self.spot_auth.order_by_client_id(symbol="BTCUSDT", client_order_id=client_oid)
            except Exception:
                time.sleep(0.5)
                continue
            if str(last.get("status", "")).upper() in {"FILLED", "CANCELED", "PARTIALLY_CANCELED"}:
                return last
            time.sleep(0.5)
        if last is None:
            raise OptionsAutoLiveError("SPOT_ACK_LOST_RECONCILIATION_REQUIRED")
        return last

    def _enter_short(self, signal: dict[str, Any], session: Path, gate: dict[str, Any]) -> dict[str, Any]:
        signal_key = str(signal["immutable_signal_key"])
        ext = _oid(signal_key, "entry")
        intent = {
            "receipt_type": "ORDER_INTENT",
            "strategy_id": signal["strategy_id"],
            "signal_identity": signal_key,
            "route": "MEXC_USDT_PERP_BTC_USDT",
            "direction": "SHORT",
            "symbol": "BTC_USDT",
            "volume_contracts": int(gate["volume_contracts"]),
            "planned_notional_usdt": gate["estimated_notional_usdt"],
            "external_oid": ext,
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        intent_path = session / "ORDER_INTENT.json"
        if not _exclusive_write(intent_path, intent):
            return self._reconcile_short_entry(signal, session, intent)

        self.futures_mut.configure_isolated_leverage(symbol="BTC_USDT", position_type=2, leverage=1)
        _atomic_write(session / "MARGIN_CONFIG_RECEIPT.json", {"isolated": True, "leverage": 1, "position_type": 2})

        try:
            ack = self.futures_mut.submit_market_order(
                symbol="BTC_USDT",
                volume_contracts=int(gate["volume_contracts"]),
                side=3,
                external_oid=ext,
                position_mode=1,
            )
            _atomic_write(session / "EXCHANGE_ACK.json", {"route": "FUTURES_SHORT", "external_oid": ext, "exchange_ack": ack})
        except Exception as exc:
            _atomic_write(session / "ENTRY_UNCERTAIN.json", {"reason": f"{type(exc).__name__}: {exc}", "external_oid": ext, "blind_resend_allowed": False})
            raise

        order = self._wait_futures_order(ext)
        _atomic_write(session / "FILL_RECEIPT.json", {"route": "FUTURES_SHORT", "order": order})
        position = self._short_position()
        if position is None:
            raise OptionsAutoLiveError("NO_SHORT_POSITION_AFTER_ENTRY_ACK")

        try:
            if position.get("autoAddIm") is not False:
                self.futures_mut.set_auto_add_margin(position_id=int(position["positionId"]), enabled=False)
                time.sleep(0.25)
                position = self._short_position() or position
            if int(position.get("openType", 0) or 0) != 1 or int(position.get("leverage", 0) or 0) != 1 or position.get("autoAddIm") is not False:
                raise OptionsAutoLiveError("POST_FILL_MARGIN_PROTECTION_NOT_VERIFIED")
        except Exception:
            try:
                self.futures_mut.submit_market_order(
                    symbol="BTC_USDT",
                    volume_contracts=int(float(position.get("holdVol", 0) or 0)),
                    side=2,
                    external_oid=_oid(signal_key, "emergency"),
                    position_mode=1,
                    position_id=int(position["positionId"]),
                )
            finally:
                raise

        active = {
            "state": "EXIT_PENDING",
            "strategy_id": signal["strategy_id"],
            "signal_identity": signal_key,
            "route": "MEXC_USDT_PERP_BTC_USDT",
            "direction": "SHORT",
            "position_id": int(position["positionId"]),
            "volume_contracts": int(float(position["holdVol"])),
            "entry_price": float(order.get("dealAvgPrice") or position.get("openAvgPrice")),
            "entry_fee_usdt": _fee_from_futures_order(order),
            "entry_target_utc": signal["entry_target_utc"],
            "exit_target_utc": signal["exit_target_utc"],
            "planned_notional_usdt": float(gate["estimated_notional_usdt"]),
            "entry_external_oid": ext,
        }
        _atomic_write(session / "ACTIVE_TRADE_STATE.json", active)
        return {"status": "SHORT_ENTERED", "session": str(session), "active": active}

    def _reconcile_short_entry(self, signal: dict[str, Any], session: Path, intent: dict[str, Any]) -> dict[str, Any]:
        active_path = session / "ACTIVE_TRADE_STATE.json"
        if active_path.exists():
            return {"status": "ALREADY_ACTIVE", "active": _load(active_path)}
        ext = str(intent["external_oid"])
        try:
            order = self.futures_ro.order_by_external(symbol="BTC_USDT", external_oid=ext)
            position = self._short_position()
        except Exception as exc:
            return {"status": "ENTRY_RECONCILIATION_REQUIRED", "reason": f"{type(exc).__name__}: {exc}", "blind_resend_allowed": False}
        if position is None or float(order.get("dealVol", 0) or 0) <= 0:
            return {"status": "ENTRY_RECONCILIATION_REQUIRED", "reason": "INTENT_EXISTS_BUT_NO_PROVABLE_FILL", "blind_resend_allowed": False}
        active = {
            "state": "EXIT_PENDING",
            "strategy_id": signal["strategy_id"],
            "signal_identity": signal["immutable_signal_key"],
            "route": "MEXC_USDT_PERP_BTC_USDT",
            "direction": "SHORT",
            "position_id": int(position["positionId"]),
            "volume_contracts": int(float(position["holdVol"])),
            "entry_price": float(order.get("dealAvgPrice") or position.get("openAvgPrice")),
            "entry_fee_usdt": _fee_from_futures_order(order),
            "entry_target_utc": signal["entry_target_utc"],
            "exit_target_utc": signal["exit_target_utc"],
            "planned_notional_usdt": float(intent["planned_notional_usdt"]),
            "entry_external_oid": ext,
            "recovered_after_restart": True,
        }
        _atomic_write(active_path, active)
        return {"status": "SHORT_RECOVERED", "active": active}

    def _enter_spot_long(self, signal: dict[str, Any], session: Path, gate: dict[str, Any]) -> dict[str, Any]:
        signal_key = str(signal["immutable_signal_key"])
        oid = _oid(signal_key, "entry")
        quote = float(gate["target_notional_usdt"])
        intent = {
            "receipt_type": "ORDER_INTENT",
            "strategy_id": signal["strategy_id"],
            "signal_identity": signal_key,
            "route": "MEXC_SPOT_BTCUSDT",
            "direction": "LONG",
            "symbol": "BTCUSDT",
            "quote_order_qty_usdt": quote,
            "planned_notional_usdt": quote,
            "client_order_id": oid,
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        intent_path = session / "ORDER_INTENT.json"
        if not _exclusive_write(intent_path, intent):
            return self._reconcile_spot_entry(signal, session, intent)

        try:
            ack = self.spot_auth.submit_market_buy_quote(quote_usdt=quote, client_order_id=oid)
            _atomic_write(session / "EXCHANGE_ACK.json", {"route": "SPOT_LONG", "client_order_id": oid, "exchange_ack": ack})
        except Exception as exc:
            _atomic_write(session / "ENTRY_UNCERTAIN.json", {"reason": f"{type(exc).__name__}: {exc}", "client_order_id": oid, "blind_resend_allowed": False})
            raise

        order = self._wait_spot_order(oid)
        fills = self._spot_fill_summary(order)
        if fills["net_btc"] <= 0:
            raise OptionsAutoLiveError("SPOT_MARKET_BUY_HAS_NO_PROVABLE_FILL")
        _atomic_write(session / "FILL_RECEIPT.json", {"route": "SPOT_LONG", "order": order, "fills": fills})

        active = {
            "state": "EXIT_PENDING",
            "strategy_id": signal["strategy_id"],
            "signal_identity": signal_key,
            "route": "MEXC_SPOT_BTCUSDT",
            "direction": "LONG",
            "entry_order_id": str(order.get("orderId") or ""),
            "entry_client_order_id": oid,
            "entry_btc_gross": fills["gross_btc"],
            "entry_btc_net": fills["net_btc"],
            "entry_quote_usdt": fills["gross_quote_usdt"],
            "entry_usdt_commission": fills["usdt_commission"],
            "entry_target_utc": signal["entry_target_utc"],
            "exit_target_utc": signal["exit_target_utc"],
            "planned_notional_usdt": quote,
        }
        _atomic_write(session / "ACTIVE_TRADE_STATE.json", active)
        return {"status": "SPOT_LONG_ENTERED", "session": str(session), "active": active}

    def _reconcile_spot_entry(self, signal: dict[str, Any], session: Path, intent: dict[str, Any]) -> dict[str, Any]:
        active_path = session / "ACTIVE_TRADE_STATE.json"
        if active_path.exists():
            return {"status": "ALREADY_ACTIVE", "active": _load(active_path)}
        oid = str(intent["client_order_id"])
        try:
            order = self.spot_auth.order_by_client_id(symbol="BTCUSDT", client_order_id=oid)
            fills = self._spot_fill_summary(order)
        except Exception as exc:
            return {"status": "ENTRY_RECONCILIATION_REQUIRED", "reason": f"{type(exc).__name__}: {exc}", "blind_resend_allowed": False}
        if fills["net_btc"] <= 0:
            return {"status": "ENTRY_RECONCILIATION_REQUIRED", "reason": "INTENT_EXISTS_BUT_NO_PROVABLE_FILL", "blind_resend_allowed": False}
        active = {
            "state": "EXIT_PENDING",
            "strategy_id": signal["strategy_id"],
            "signal_identity": signal["immutable_signal_key"],
            "route": "MEXC_SPOT_BTCUSDT",
            "direction": "LONG",
            "entry_order_id": str(order.get("orderId") or ""),
            "entry_client_order_id": oid,
            "entry_btc_gross": fills["gross_btc"],
            "entry_btc_net": fills["net_btc"],
            "entry_quote_usdt": fills["gross_quote_usdt"],
            "entry_usdt_commission": fills["usdt_commission"],
            "entry_target_utc": signal["entry_target_utc"],
            "exit_target_utc": signal["exit_target_utc"],
            "planned_notional_usdt": float(intent["planned_notional_usdt"]),
            "recovered_after_restart": True,
        }
        _atomic_write(active_path, active)
        return {"status": "SPOT_LONG_RECOVERED", "active": active}

    def _exit_short(self, active_path: Path, active: dict[str, Any], now: datetime, emergency: bool) -> dict[str, Any]:
        session = active_path.parent
        signal_key = str(active["signal_identity"])
        oid = _oid(signal_key, "exit")
        intent = {
            "receipt_type": "EXIT_INTENT",
            "signal_identity": signal_key,
            "route": active["route"],
            "position_id": int(active["position_id"]),
            "external_oid": oid,
            "reason": "KILL_SWITCH" if emergency else "SCHEDULED_24H_EXIT",
        }
        intent_path = session / "EXIT_INTENT.json"
        if not _exclusive_write(intent_path, intent):
            try:
                order = self.futures_ro.order_by_external(symbol="BTC_USDT", external_oid=oid)
            except Exception as exc:
                return {"status": "EXIT_RECONCILIATION_REQUIRED", "reason": f"{type(exc).__name__}: {exc}", "blind_resend_allowed": False}
        else:
            position = self._short_position()
            if position is None:
                return self._finalize_short_without_position(active_path, active, now, emergency)
            ack = self.futures_mut.submit_market_order(
                symbol="BTC_USDT",
                volume_contracts=int(float(position["holdVol"])),
                side=2,
                external_oid=oid,
                position_mode=1,
                position_id=int(position["positionId"]),
            )
            _atomic_write(session / "EXIT_EXCHANGE_ACK.json", {"external_oid": oid, "exchange_ack": ack})
            order = self._wait_futures_order(oid)

        if self._short_position() is not None:
            return {"status": "EXIT_RECONCILIATION_REQUIRED", "reason": "SHORT_POSITION_REMAINS", "blind_resend_allowed": False}

        exit_fee = _fee_from_futures_order(order)
        gross_profit = float(order.get("profit", 0) or 0)
        hold_fee = float(order.get("holdFee", 0) or 0)
        realized = gross_profit + hold_fee - float(active.get("entry_fee_usdt", 0) or 0) - exit_fee
        closed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        recon = {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "strategy_id": active["strategy_id"],
            "signal_identity": signal_key,
            "route": active["route"],
            "closed_at_utc": closed,
            "realized_net_pnl_usdt": realized,
            "exit_reason": "KILL_SWITCH" if emergency else "SCHEDULED_24H_EXIT",
            "open_position_after_reconciliation": False,
        }
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", recon)
        active["state"] = "CLOSED"; active["closed_at_utc"] = closed
        _atomic_write(active_path, active)
        return {"status": "SHORT_CLOSED_RECONCILED", "realized_net_pnl_usdt": realized}

    def _finalize_short_without_position(self, active_path: Path, active: dict[str, Any], now: datetime, emergency: bool) -> dict[str, Any]:
        session = active_path.parent
        if not (session / "EXIT_EXCHANGE_ACK.json").exists():
            return {"status": "EXIT_RECONCILIATION_REQUIRED", "reason": "ACTIVE_RECEIPT_BUT_NO_POSITION_AND_NO_EXIT_ACK", "blind_resend_allowed": False}
        recon = {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "strategy_id": active["strategy_id"],
            "signal_identity": active["signal_identity"],
            "route": active["route"],
            "closed_at_utc": now.isoformat().replace("+00:00", "Z"),
            "realized_net_pnl_usdt": 0.0,
            "exit_reason": "RECONCILED_ALREADY_CLOSED",
            "open_position_after_reconciliation": False,
            "pnl_requires_manual_audit": True,
        }
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", recon)
        active["state"] = "CLOSED"
        _atomic_write(active_path, active)
        return {"status": "SHORT_ALREADY_CLOSED_RECONCILED_WITH_PNL_AUDIT"}

    def _exit_spot(self, active_path: Path, active: dict[str, Any], now: datetime, emergency: bool) -> dict[str, Any]:
        session = active_path.parent
        signal_key = str(active["signal_identity"])
        oid = _oid(signal_key, "exit")
        intent_path = session / "EXIT_INTENT.json"

        account = self.spot_auth.account()
        free_btc, _ = _spot_balance(account, "BTC")
        intended = float(active.get("entry_btc_net", 0) or 0)
        if intended <= 0:
            raise OptionsAutoLiveError("ACTIVE_SPOT_ENTRY_QUANTITY_INVALID")
        info = self.spot_public.exchange_info("BTCUSDT")
        step = float(info.get("baseSizePrecision") or 0)
        if step <= 0:
            step = 10.0 ** (-int(info.get("baseAssetPrecision") or 8))
        qty = _floor_step(min(intended, free_btc), step)
        if qty <= 0:
            return {"status": "EXIT_RECONCILIATION_REQUIRED", "reason": "NO_SELLABLE_BTC_FOR_ACTIVE_MICROLIVE", "blind_resend_allowed": False}

        intent = {
            "receipt_type": "EXIT_INTENT",
            "signal_identity": signal_key,
            "route": active["route"],
            "quantity_btc": qty,
            "client_order_id": oid,
            "reason": "KILL_SWITCH" if emergency else "SCHEDULED_24H_EXIT",
        }

        if not _exclusive_write(intent_path, intent):
            try:
                order = self.spot_auth.order_by_client_id(symbol="BTCUSDT", client_order_id=oid)
            except Exception as exc:
                return {"status": "EXIT_RECONCILIATION_REQUIRED", "reason": f"{type(exc).__name__}: {exc}", "blind_resend_allowed": False}
        else:
            ack = self.spot_auth.submit_market_sell_quantity(quantity_btc=qty, client_order_id=oid)
            _atomic_write(session / "EXIT_EXCHANGE_ACK.json", {"client_order_id": oid, "exchange_ack": ack})
            order = self._wait_spot_order(oid)

        fills = self._spot_fill_summary(order)
        if fills["gross_quote_usdt"] <= 0:
            return {"status": "EXIT_RECONCILIATION_REQUIRED", "reason": "NO_PROVABLE_SPOT_EXIT_FILL", "blind_resend_allowed": False}

        entry_cost = float(active.get("entry_quote_usdt", 0) or 0) + float(active.get("entry_usdt_commission", 0) or 0)
        exit_proceeds = fills["gross_quote_usdt"] - fills["usdt_commission"]
        realized = exit_proceeds - entry_cost
        closed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        recon = {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "strategy_id": active["strategy_id"],
            "signal_identity": signal_key,
            "route": active["route"],
            "closed_at_utc": closed,
            "entry_cost_usdt": entry_cost,
            "exit_proceeds_usdt": exit_proceeds,
            "realized_net_pnl_usdt": realized,
            "exit_reason": "KILL_SWITCH" if emergency else "SCHEDULED_24H_EXIT",
            "open_position_after_reconciliation": False,
            "residual_btc_due_to_fee_or_step": max(0.0, intended - qty),
        }
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", recon)
        active["state"] = "CLOSED"; active["closed_at_utc"] = closed
        _atomic_write(active_path, active)
        return {"status": "SPOT_LONG_CLOSED_RECONCILED", "realized_net_pnl_usdt": realized}

    def manage_active(self, now: datetime) -> dict[str, Any] | None:
        active_rows = self._active_states()
        if not active_rows:
            return None
        if len(active_rows) > 1:
            return self._status("FAIL_CLOSED", blockers=["MULTIPLE_LOCAL_ACTIVE_MICROLIVE_TRADES"])
        path, active = active_rows[0]
        exit_target = _utc(str(active["exit_target_utc"]))
        emergency = self.kill_switch_path.exists()
        if not emergency and now < exit_target:
            return self._status(
                "ACTIVE_WAITING_EXIT",
                route=active.get("route"),
                signal_identity=active.get("signal_identity"),
                exit_target_utc=active.get("exit_target_utc"),
                seconds_to_exit=(exit_target - now).total_seconds(),
            )
        if active.get("route") == "MEXC_SPOT_BTCUSDT":
            result = self._exit_spot(path, active, now, emergency)
        elif active.get("route") == "MEXC_USDT_PERP_BTC_USDT":
            result = self._exit_short(path, active, now, emergency)
        else:
            result = {"status": "FAIL_CLOSED", "blockers": ["UNKNOWN_ACTIVE_ROUTE"]}
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

        signal = build_execution_signal(entry, watcher_status=str(watcher_state.get("status") or ""), now_utc=now)
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

        if signal["signal_direction"] == "SHORT":
            gate = self._short_gate(signal, now)
        else:
            gate = self._spot_gate(signal, now)
        _atomic_write(session / "PRE_ORDER_GATE.json", gate)
        if not gate["pass"]:
            return self._status("FAIL_CLOSED", blockers=gate["blockers"], signal=signal, gate=gate)

        try:
            if signal["signal_direction"] == "SHORT":
                result = self._enter_short(signal, session, gate)
            else:
                result = self._enter_spot_long(signal, session, gate)
        except Exception as exc:
            return self._status(
                "ENTRY_FAIL_CLOSED",
                blockers=[f"{type(exc).__name__}: {exc}"],
                signal_identity=signal["immutable_signal_key"],
                session=str(session),
            )
        return self._status(result["status"], result=result)


__all__ = ["OptionsV21AutoLiveEngine", "OptionsAutoLiveError", "STATUS_VERSION"]
