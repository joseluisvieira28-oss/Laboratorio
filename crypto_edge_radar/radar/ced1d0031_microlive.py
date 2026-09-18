from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
import os
import time
from typing import Any

from .binance_trading import BinanceTradingError, BinanceUSDMTradingClient
from .ced1d0031_public import (
    CANDIDATE,
    PROVIDER,
    SHADOW_EVENT_TYPE,
    SYMBOL,
    BinanceAVAXDailySource,
    maybe_emit_signal,
)
from .config import Settings
from .evidence import build_evidence_store

UTC = timezone.utc
AUTHORITY_COMMIT = "b0cea0fb9c47a3178599e93bde70c5e5a0207cc9"
ARM_TOKEN = "CED1D-0031-MICROLIVE-V0.1-ONE-EVENT"
FIRST_REAL_ENTRY = datetime(2026, 9, 21, 0, 1, tzinfo=UTC)
ENTRY_GRACE_SECONDS = 5
MAX_NOTIONAL_USDT = Decimal("25")
TARGET_NOTIONAL_USDT = Decimal("24")
PREFLIGHT_EVENT = "CED1D0031_MICROLIVE_PREFLIGHT"
ENTRY_EVENT = "CED1D0031_MICROLIVE_ENTRY"
EXIT_EVENT = "CED1D0031_MICROLIVE_EXIT"
RECON_EVENT = "CED1D0031_MICROLIVE_RECONCILIATION"
INCIDENT_EVENT = "CED1D0031_MICROLIVE_INCIDENT"
CHAIN_VERIFY_INTERVAL_SECONDS = 60.0
PREPARE_RETRY_SECONDS = 5.0


class MicroLiveBlocked(RuntimeError):
    pass


def _parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise MicroLiveBlocked("timestamp must be timezone-aware")
    return dt.astimezone(UTC)


def _client_id(signal_key: str, suffix: str) -> str:
    digest = hashlib.sha256(signal_key.encode("utf-8")).hexdigest()[:12]
    return f"ced0031-{digest}-{suffix}"


def _armed() -> bool:
    return (
        os.getenv("MICROLIVE_EXECUTION_ENABLED", "0").strip() == "1"
        and os.getenv("MICROLIVE_ARM_TOKEN", "").strip() == ARM_TOKEN
        and os.getenv("MICROLIVE_VENUE", "binance_usdm").strip().lower() == "binance_usdm"
    )


def _round_qty(
    *,
    price: Decimal,
    step_size: Decimal,
    min_qty: Decimal,
    min_notional: Decimal,
) -> Decimal:
    if price <= 0 or step_size <= 0:
        raise MicroLiveBlocked("invalid price/step")
    raw = TARGET_NOTIONAL_USDT / price
    units = (raw / step_size).to_integral_value(rounding=ROUND_DOWN)
    qty = units * step_size
    notional = qty * price
    if qty < min_qty:
        raise MicroLiveBlocked("24 USDT target is below venue minimum quantity")
    if notional < min_notional:
        raise MicroLiveBlocked("24 USDT target is below venue minimum notional")
    if notional > MAX_NOTIONAL_USDT:
        raise MicroLiveBlocked("rounded quantity exceeds 25 USDT hard cap")
    return qty


def _validate_signal_payload(signal: dict[str, Any]) -> dict[str, Any]:
    if signal.get("candidate") != CANDIDATE or signal.get("strategy_id") != CANDIDATE:
        raise MicroLiveBlocked("candidate identity mismatch")
    if signal.get("symbol") != SYMBOL or signal.get("provider") != PROVIDER:
        raise MicroLiveBlocked("symbol/provider mismatch")
    if signal.get("direction") not in {"LONG", "SHORT"}:
        raise MicroLiveBlocked("non-directional signal")
    if signal.get("direction_rule") != "CONTINUATION_SIGN_LOG_CLOSE_RATIO":
        raise MicroLiveBlocked("direction rule mismatch")
    if int(signal.get("lookback_calendar_days", -1)) != 20:
        raise MicroLiveBlocked("lookback mismatch")
    if int(signal.get("horizon_calendar_days", -1)) != 1:
        raise MicroLiveBlocked("horizon mismatch")

    entry = _parse_utc(signal["reference_entry"])
    exit_at = _parse_utc(signal["reference_exit"])
    if entry < FIRST_REAL_ENTRY:
        raise MicroLiveBlocked("pre real-money activation boundary")
    if exit_at != entry + timedelta(days=1):
        raise MicroLiveBlocked("H1 exit mismatch")
    return {"entry": entry, "exit": exit_at}


def _commission_breakdown(rows: list[dict[str, Any]]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for row in rows:
        asset = str(row.get("commissionAsset") or "UNKNOWN")
        out[asset] = out.get(asset, Decimal("0")) + Decimal(
            str(row.get("commission", "0"))
        )
    return out


class CED1D0031Runtime:
    """Restart-safe prospective shadow + one-event micro-live runtime.

    Scientific/execution state is reconstructed from the existing Radar evidence
    store. On the operational V0.9 path that store is PostgreSQL.
    """

    def __init__(self) -> None:
        self.settings = Settings.from_env()
        self.store = build_evidence_store(
            self.settings.db_path,
            self.settings.database_url,
        )
        self.source = BinanceAVAXDailySource(timeout=self.settings.http_timeout)
        self._client: BinanceUSDMTradingClient | None = None

        signals = self.store.read_payloads(SHADOW_EVENT_TYPE)
        preflights = self.store.read_payloads(PREFLIGHT_EVENT)
        entries = self.store.read_payloads(ENTRY_EVENT)
        exits = self.store.read_payloads(EXIT_EVENT)
        recons = self.store.read_payloads(RECON_EVENT)

        self.latest_signal: dict[str, Any] | None = signals[-1] if signals else None
        self.preflight: dict[str, Any] | None = preflights[-1] if preflights else None
        self.entry: dict[str, Any] | None = entries[0] if entries else None
        self.exit: dict[str, Any] | None = exits[0] if exits else None
        self.reconciliation: dict[str, Any] | None = recons[0] if recons else None

        self._last_prepare_attempt_monotonic = 0.0
        self._last_chain_check_monotonic = 0.0
        self._chain_ok, self._chain_detail = self.store.verify_chain()
        if not self._chain_ok:
            raise MicroLiveBlocked(
                f"evidence chain invalid at startup: {self._chain_detail}"
            )
        self._last_chain_check_monotonic = time.monotonic()

    def _client_or_create(self) -> BinanceUSDMTradingClient:
        if self._client is None:
            self._client = BinanceUSDMTradingClient(
                timeout=self.settings.http_timeout
            )
        return self._client

    def _append_incident(self, key: str, payload: dict[str, Any]) -> None:
        body = dict(payload)
        body.update(
            {
                "candidate": CANDIDATE,
                "authority_commit": AUTHORITY_COMMIT,
                "checked_at_utc": datetime.now(UTC).isoformat(),
            }
        )
        self.store.append_once(INCIDENT_EVENT, key, body)

    def _maybe_verify_chain(self) -> None:
        now_mono = time.monotonic()
        if (
            now_mono - self._last_chain_check_monotonic
            < CHAIN_VERIFY_INTERVAL_SECONDS
        ):
            return
        ok, detail = self.store.verify_chain()
        self._chain_ok, self._chain_detail = ok, detail
        self._last_chain_check_monotonic = now_mono
        if not ok:
            raise MicroLiveBlocked(f"evidence chain invalid: {detail}")

    def _maybe_emit_signal(self, now: datetime) -> dict[str, Any] | None:
        payload = maybe_emit_signal(
            now=now,
            store=self.store,
            source=self.source,
        )
        if payload is not None:
            self.latest_signal = payload
        return payload

    def _maybe_prepare(
        self,
        *,
        now: datetime,
        client: BinanceUSDMTradingClient,
    ) -> dict[str, Any] | None:
        if (
            not _armed()
            or self.entry is not None
            or self.latest_signal is None
        ):
            return None

        signal = self.latest_signal
        identity = _validate_signal_payload(signal)
        entry_at = identity["entry"]
        if now >= entry_at:
            return None

        if (
            self.preflight is not None
            and self.preflight.get("signal_key") == signal.get("signal_key")
            and self.preflight.get("ok") is True
        ):
            return None

        now_mono = time.monotonic()
        if (
            now_mono - self._last_prepare_attempt_monotonic
            < PREPARE_RETRY_SECONDS
        ):
            return None
        self._last_prepare_attempt_monotonic = now_mono

        try:
            health = client.preflight(SYMBOL)
            if health.get("ok") is not True:
                self._append_incident(
                    signal["signal_key"] + ":PREENTRY_PREFLIGHT",
                    {
                        "phase": "PREENTRY_PREFLIGHT",
                        "reason": "PREFLIGHT_FAIL",
                        "health": health,
                    },
                )
                return None

            rules = client.market_rules(SYMBOL)
            book = client.book_ticker(SYMBOL)
            checked = datetime.now(UTC)
            payload = {
                "candidate": CANDIDATE,
                "authority_commit": AUTHORITY_COMMIT,
                "signal_key": signal["signal_key"],
                "ok": True,
                "checked_at_utc": checked.isoformat(),
                "reference_entry": signal["reference_entry"],
                "health": health,
                "rules": {
                    key: format(value, "f")
                    for key, value in rules.items()
                },
                "book": {
                    key: format(value, "f")
                    for key, value in book.items()
                },
                "real_order_submitted": False,
            }
            self.store.append_once(
                PREFLIGHT_EVENT,
                signal["signal_key"],
                payload,
            )
            self.preflight = payload
            return payload
        except Exception as exc:
            self._append_incident(
                signal["signal_key"]
                + ":PREENTRY_PREFLIGHT:"
                + str(int(now.timestamp())),
                {
                    "phase": "PREENTRY_PREFLIGHT",
                    "reason": "PREFLIGHT_EXCEPTION",
                    "error": f"{type(exc).__name__}:{exc}",
                },
            )
            return None

    def _recover_entry_if_exchange_has_order(
        self,
        *,
        client: BinanceUSDMTradingClient,
        signal: dict[str, Any],
    ) -> dict[str, Any] | None:
        if self.entry is not None:
            return self.entry

        key = signal["signal_key"]
        client_id = _client_id(key, "e")
        order = client.query_order(SYMBOL, client_id)
        if order is None:
            return None

        payload = {
            "candidate": CANDIDATE,
            "authority_commit": AUTHORITY_COMMIT,
            "signal_key": key,
            "direction": signal["direction"],
            "reference_entry": signal["reference_entry"],
            "reference_exit": signal["reference_exit"],
            "client_order_id": client_id,
            "order": order,
            "recovered_after_process_or_network_ambiguity": True,
        }
        self.store.append_once(ENTRY_EVENT, key, payload)
        self.entry = payload
        return payload

    def _maybe_recover_entry_anytime(
        self,
        client: BinanceUSDMTradingClient,
    ) -> dict[str, Any] | None:
        if self.entry is not None or self.latest_signal is None:
            return None
        try:
            _validate_signal_payload(self.latest_signal)
        except MicroLiveBlocked:
            return None
        return self._recover_entry_if_exchange_has_order(
            client=client,
            signal=self.latest_signal,
        )

    def _quick_entry_guard(
        self,
        client: BinanceUSDMTradingClient,
    ) -> dict[str, Any]:
        positions = client.position_risk(SYMBOL)
        if len(positions) != 1:
            return {
                "ok": False,
                "reason": "POSITION_RISK_AMBIGUOUS",
                "rows": len(positions),
            }
        row = positions[0]
        leverage = int(row.get("leverage", -1))
        margin_type = str(row.get("marginType", "")).upper()
        position_amt = Decimal(str(row.get("positionAmt", "0")))
        if leverage != 1:
            return {
                "ok": False,
                "reason": "LEVERAGE_NOT_1X",
                "observed": leverage,
            }
        if margin_type != "ISOLATED":
            return {
                "ok": False,
                "reason": "MARGIN_NOT_ISOLATED",
                "observed": margin_type,
            }
        if position_amt != 0:
            return {
                "ok": False,
                "reason": "EXISTING_POSITION",
                "position_amt": format(position_amt, "f"),
            }
        orders = client.open_orders(SYMBOL)
        if orders:
            return {
                "ok": False,
                "reason": "EXISTING_OPEN_ORDERS",
                "count": len(orders),
            }
        return {
            "ok": True,
            "leverage": leverage,
            "margin_type": margin_type,
        }

    def _maybe_enter(
        self,
        *,
        now: datetime,
        client: BinanceUSDMTradingClient,
    ) -> dict[str, Any] | None:
        if self.entry is not None or not _armed() or self.latest_signal is None:
            return None

        signal = self.latest_signal
        identity = _validate_signal_payload(signal)
        entry_at = identity["entry"]
        deadline = entry_at.replace(
            second=ENTRY_GRACE_SECONDS,
            microsecond=999999,
        )

        recovered = self._recover_entry_if_exchange_has_order(
            client=client,
            signal=signal,
        )
        if recovered is not None:
            return recovered

        if not (entry_at <= now <= deadline):
            return None

        if (
            self.preflight is None
            or self.preflight.get("signal_key") != signal.get("signal_key")
            or self.preflight.get("ok") is not True
        ):
            self._append_incident(
                signal["signal_key"] + ":MISSING_PREFLIGHT",
                {
                    "phase": "ENTRY",
                    "reason": "MISSING_OR_INVALID_PREENTRY_PREFLIGHT",
                },
            )
            return None

        checked_at = _parse_utc(self.preflight["checked_at_utc"])
        preflight_age = (now - checked_at).total_seconds()
        if preflight_age < 0 or preflight_age > 90:
            self._append_incident(
                signal["signal_key"] + ":STALE_PREFLIGHT",
                {
                    "phase": "ENTRY",
                    "reason": "PREENTRY_PREFLIGHT_STALE",
                    "age_seconds": preflight_age,
                },
            )
            return None

        quick = self._quick_entry_guard(client)
        if quick.get("ok") is not True:
            self._append_incident(
                signal["signal_key"] + ":ENTRY_QUICK_GUARD",
                {
                    "phase": "ENTRY",
                    "reason": "QUICK_GUARD_FAIL",
                    "health": quick,
                },
            )
            return None

        rules = {
            key: Decimal(str(value))
            for key, value in self.preflight["rules"].items()
        }
        book = client.book_ticker(SYMBOL)
        qty = _round_qty(
            price=book["mid"],
            step_size=rules["step_size"],
            min_qty=rules["min_qty"],
            min_notional=rules["min_notional"],
        )
        side = "BUY" if signal["direction"] == "LONG" else "SELL"
        client_id = _client_id(signal["signal_key"], "e")

        order = client.submit_market(
            symbol=SYMBOL,
            side=side,
            quantity=qty,
            reduce_only=False,
            client_order_id=client_id,
        )

        payload = {
            "candidate": CANDIDATE,
            "authority_commit": AUTHORITY_COMMIT,
            "signal_key": signal["signal_key"],
            "direction": signal["direction"],
            "reference_entry": signal["reference_entry"],
            "reference_exit": signal["reference_exit"],
            "client_order_id": client_id,
            "requested_quantity": format(qty, "f"),
            "pretrade_mid": format(book["mid"], "f"),
            "pretrade_spread_bps": format(book["spread_bps"], "f"),
            "preentry_preflight": self.preflight,
            "entry_quick_guard": quick,
            "order": order,
            "target_notional_usdt": format(TARGET_NOTIONAL_USDT, "f"),
            "hard_cap_usdt": format(MAX_NOTIONAL_USDT, "f"),
        }
        self.store.append_once(ENTRY_EVENT, signal["signal_key"], payload)
        self.entry = payload
        return payload

    def _current_position_qty(
        self,
        client: BinanceUSDMTradingClient,
    ) -> Decimal:
        rows = client.position_risk(SYMBOL)
        if len(rows) != 1:
            raise MicroLiveBlocked(
                f"position risk ambiguous at exit: {len(rows)} rows"
            )
        return Decimal(str(rows[0].get("positionAmt", "0")))

    def _entry_signal(self) -> dict[str, Any]:
        if self.entry is None:
            raise MicroLiveBlocked("entry is missing")
        signal_key = self.entry.get("signal_key")
        if (
            self.latest_signal is not None
            and self.latest_signal.get("signal_key") == signal_key
        ):
            return self.latest_signal
        matches = [
            row
            for row in self.store.read_payloads(SHADOW_EVENT_TYPE)
            if row.get("signal_key") == signal_key
        ]
        if not matches:
            raise MicroLiveBlocked("entry signal missing from evidence store")
        return matches[-1]

    def _maybe_exit(
        self,
        *,
        now: datetime,
        client: BinanceUSDMTradingClient,
    ) -> dict[str, Any] | None:
        if self.entry is None or self.exit is not None:
            return None

        signal = self._entry_signal()
        exit_at = _parse_utc(signal["reference_exit"])
        if now < exit_at:
            return None

        position_amt = self._current_position_qty(client)
        client_id = _client_id(self.entry["signal_key"], "x")

        if position_amt == 0:
            existing = client.query_order(SYMBOL, client_id)
            payload = {
                "candidate": CANDIDATE,
                "authority_commit": AUTHORITY_COMMIT,
                "signal_key": self.entry["signal_key"],
                "direction": self.entry["direction"],
                "reference_exit": signal["reference_exit"],
                "client_order_id": client_id,
                "quantity": "0",
                "order": existing,
                "position_already_flat": True,
                "late_by_seconds": max(
                    0.0,
                    (now - exit_at).total_seconds(),
                ),
            }
            self.store.append_once(
                EXIT_EVENT,
                self.entry["signal_key"],
                payload,
            )
            self._append_incident(
                self.entry["signal_key"] + ":ALREADY_FLAT_AT_EXIT",
                {
                    "phase": "EXIT",
                    "reason": "POSITION_ALREADY_FLAT",
                    "known_exit_order": existing,
                },
            )
            self.exit = payload
            return payload

        actual_direction = "LONG" if position_amt > 0 else "SHORT"
        expected_direction = str(self.entry["direction"])
        mismatch = actual_direction != expected_direction
        qty = abs(position_amt)
        side = "SELL" if position_amt > 0 else "BUY"

        order = client.submit_market(
            symbol=SYMBOL,
            side=side,
            quantity=qty,
            reduce_only=True,
            client_order_id=client_id,
        )
        late_by = max(0.0, (now - exit_at).total_seconds())
        payload = {
            "candidate": CANDIDATE,
            "authority_commit": AUTHORITY_COMMIT,
            "signal_key": self.entry["signal_key"],
            "direction": expected_direction,
            "observed_position_direction": actual_direction,
            "direction_mismatch_incident": mismatch,
            "reference_exit": signal["reference_exit"],
            "client_order_id": client_id,
            "quantity": format(qty, "f"),
            "order": order,
            "late_by_seconds": late_by,
            "late_exit_incident": late_by > ENTRY_GRACE_SECONDS,
        }
        self.store.append_once(
            EXIT_EVENT,
            self.entry["signal_key"],
            payload,
        )
        self.exit = payload

        if mismatch:
            self._append_incident(
                self.entry["signal_key"] + ":POSITION_DIRECTION_MISMATCH",
                {
                    "phase": "EXIT",
                    "reason": "POSITION_DIRECTION_MISMATCH",
                    "expected_direction": expected_direction,
                    "observed_direction": actual_direction,
                    "action": "REDUCE_ONLY_CLOSE_ACTUAL_POSITION",
                },
            )
        if late_by > ENTRY_GRACE_SECONDS:
            self._append_incident(
                self.entry["signal_key"] + ":LATE_EXIT",
                {
                    "phase": "EXIT",
                    "reason": "LATE_EXIT",
                    "late_by_seconds": late_by,
                },
            )
        return payload

    def _maybe_reconcile(
        self,
        *,
        client: BinanceUSDMTradingClient,
    ) -> dict[str, Any] | None:
        if (
            self.entry is None
            or self.exit is None
            or self.reconciliation is not None
        ):
            return None

        signal = self._entry_signal()
        signal_key = self.entry["signal_key"]

        start = int(
            (
                _parse_utc(signal["reference_entry"])
                - timedelta(minutes=10)
            ).timestamp()
            * 1000
        )
        end = int(
            (datetime.now(UTC) + timedelta(minutes=10)).timestamp()
            * 1000
        )
        trades = client.user_trades(
            SYMBOL,
            start_ms=start,
            end_ms=end,
        )
        funding = client.funding_income(
            SYMBOL,
            start_ms=start,
            end_ms=end,
        )

        entry_order_id = str(
            (self.entry.get("order") or {}).get("orderId", "")
        )
        exit_order_id = str(
            (self.exit.get("order") or {}).get("orderId", "")
        )
        expected_ids = {
            order_id
            for order_id in (entry_order_id, exit_order_id)
            if order_id
        }
        relevant = [
            row
            for row in trades
            if str(row.get("orderId", "")) in expected_ids
        ]
        observed_ids = {
            str(row.get("orderId", ""))
            for row in relevant
        }

        if expected_ids and not expected_ids.issubset(observed_ids):
            return None

        commissions = _commission_breakdown(relevant)
        realized = sum(
            Decimal(str(row.get("realizedPnl", "0")))
            for row in relevant
        )
        funding_total = sum(
            Decimal(str(row.get("income", "0")))
            for row in funding
        )
        all_commission_usdt = set(commissions).issubset({"USDT"})
        if all_commission_usdt:
            commission_usdt = commissions.get("USDT", Decimal("0"))
            net_cashflow_usdt: str | None = format(
                realized + funding_total - commission_usdt,
                "f",
            )
        else:
            net_cashflow_usdt = None

        payload = {
            "candidate": CANDIDATE,
            "authority_commit": AUTHORITY_COMMIT,
            "signal_key": signal_key,
            "trade_rows": relevant,
            "funding_rows": funding,
            "commission_by_asset": {
                asset: format(amount, "f")
                for asset, amount in commissions.items()
            },
            "realized_pnl_usdt": format(realized, "f"),
            "funding_income_usdt": format(funding_total, "f"),
            "net_cashflow_usdt": net_cashflow_usdt,
            "net_cashflow_note": (
                "exact USDT cashflow"
                if all_commission_usdt
                else "not computed because one or more commissions were paid in a non-USDT asset"
            ),
            "reconciled_at_utc": datetime.now(UTC).isoformat(),
            "second_real_event_authorized": False,
        }
        self.store.append_once(
            RECON_EVENT,
            signal_key,
            payload,
        )
        self.reconciliation = payload
        return payload

    def cycle(
        self,
        *,
        now: datetime | None = None,
        allow_private: bool = True,
    ) -> dict[str, Any]:
        now = (now or datetime.now(UTC)).astimezone(UTC)
        result: dict[str, Any] = {
            "candidate": CANDIDATE,
            "checked_at_utc": now.isoformat(),
            "evidence_backend": self.store.backend,
            "armed": _armed(),
            "signal_key": (
                self.latest_signal.get("signal_key")
                if self.latest_signal
                else None
            ),
            "preflight_ready": (
                self.preflight is not None
                and self.latest_signal is not None
                and self.preflight.get("signal_key")
                == self.latest_signal.get("signal_key")
                and self.preflight.get("ok") is True
            ),
            "entry_exists": self.entry is not None,
            "exit_exists": self.exit is not None,
            "reconciliation_exists": self.reconciliation is not None,
        }

        signal = self._maybe_emit_signal(now)
        if signal is not None:
            result["signal"] = signal

        if allow_private and (_armed() or self.entry is not None):
            client = self._client_or_create()

            if self.entry is None and self.latest_signal is not None:
                try:
                    prepared = self._maybe_prepare(
                        now=now,
                        client=client,
                    )
                    if prepared is not None:
                        result["preflight"] = prepared
                except MicroLiveBlocked:
                    pass

            recovered = self._maybe_recover_entry_anytime(client)
            if recovered is not None:
                result["entry_recovery"] = recovered

            entry = self._maybe_enter(
                now=now,
                client=client,
            )
            if entry is not None:
                result["entry"] = entry

            exit_row = self._maybe_exit(
                now=now,
                client=client,
            )
            if exit_row is not None:
                result["exit"] = exit_row

            recon = self._maybe_reconcile(client=client)
            if recon is not None:
                result["reconciliation"] = recon

        self._maybe_verify_chain()
        result["evidence_chain_ok"] = self._chain_ok
        result["evidence_chain_detail"] = self._chain_detail
        return result


def run_cycle(
    *,
    now: datetime | None = None,
    allow_private: bool = True,
) -> dict[str, Any]:
    runtime = CED1D0031Runtime()
    return runtime.cycle(
        now=now,
        allow_private=allow_private,
    )


def _adaptive_sleep(runtime: CED1D0031Runtime, now: datetime) -> float:
    now = now.astimezone(UTC)
    midnight = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    seconds_of_day = (now - midnight).total_seconds()

    if seconds_of_day <= 75 or seconds_of_day >= 86390:
        return 0.25

    if runtime.entry is not None and runtime.exit is None:
        try:
            exit_at = _parse_utc(runtime._entry_signal()["reference_exit"])
            seconds_to_exit = (exit_at - now).total_seconds()
            if -10 <= seconds_to_exit <= 10:
                return 0.25
            if seconds_to_exit > 10:
                return min(10.0, max(1.0, seconds_to_exit - 5.0))
        except Exception:
            return 1.0

    return 10.0


def run_forever() -> int:
    runtime = CED1D0031Runtime()
    last_heartbeat = 0.0

    while True:
        started = time.monotonic()
        try:
            result = runtime.cycle()
            material = any(
                key in result
                for key in (
                    "signal",
                    "preflight",
                    "entry_recovery",
                    "entry",
                    "exit",
                    "reconciliation",
                )
            )
            if material or started - last_heartbeat >= 60.0:
                print(
                    json.dumps(result, sort_keys=True),
                    flush=True,
                )
                last_heartbeat = started
        except (MicroLiveBlocked, BinanceTradingError) as exc:
            print(
                json.dumps(
                    {
                        "candidate": CANDIDATE,
                        "status": "FAIL_CLOSED",
                        "error": f"{type(exc).__name__}:{exc}",
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "candidate": CANDIDATE,
                        "status": "UNEXPECTED_FAIL_CLOSED",
                        "error": f"{type(exc).__name__}:{exc}",
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

        sleep_for = _adaptive_sleep(runtime, datetime.now(UTC))
        elapsed = time.monotonic() - started
        time.sleep(max(0.05, sleep_for - elapsed))


if __name__ == "__main__":
    raise SystemExit(run_forever())
