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
ENTRY_EVENT = "CED1D0031_MICROLIVE_ENTRY"
EXIT_EVENT = "CED1D0031_MICROLIVE_EXIT"
RECON_EVENT = "CED1D0031_MICROLIVE_RECONCILIATION"
INCIDENT_EVENT = "CED1D0031_MICROLIVE_INCIDENT"


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


def _payloads(store, event_type: str) -> list[dict[str, Any]]:
    return store.read_payloads(event_type)


def _signal_by_key(store, signal_key: str) -> dict[str, Any] | None:
    for payload in reversed(_payloads(store, SHADOW_EVENT_TYPE)):
        if payload.get("signal_key") == signal_key:
            return payload
    return None


def _first_entry(store) -> dict[str, Any] | None:
    rows = _payloads(store, ENTRY_EVENT)
    return rows[0] if rows else None


def _first_exit(store) -> dict[str, Any] | None:
    rows = _payloads(store, EXIT_EVENT)
    return rows[0] if rows else None


def _append_incident(store, key: str, payload: dict[str, Any]) -> None:
    body = dict(payload)
    body.update(
        {
            "candidate": CANDIDATE,
            "authority_commit": AUTHORITY_COMMIT,
            "checked_at_utc": datetime.now(UTC).isoformat(),
        }
    )
    store.append_once(INCIDENT_EVENT, key, body)


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


def _recover_entry_if_exchange_has_order(
    *,
    store,
    client: BinanceUSDMTradingClient,
    signal: dict[str, Any],
) -> dict[str, Any] | None:
    existing_entry = _first_entry(store)
    if existing_entry is not None:
        return existing_entry

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
    store.append_once(ENTRY_EVENT, key, payload)
    return payload


def _maybe_enter(
    *,
    now: datetime,
    store,
    client: BinanceUSDMTradingClient,
) -> dict[str, Any] | None:
    if _first_entry(store) is not None:
        return None
    if not _armed():
        return None

    signals = _payloads(store, SHADOW_EVENT_TYPE)
    if not signals:
        return None
    signal = signals[-1]
    identity = _validate_signal_payload(signal)
    entry = identity["entry"]
    deadline = entry.replace(second=ENTRY_GRACE_SECONDS, microsecond=999999)

    recovered = _recover_entry_if_exchange_has_order(store=store, client=client, signal=signal)
    if recovered is not None:
        return recovered

    if not (entry <= now <= deadline):
        return None

    health = client.preflight(SYMBOL)
    if health.get("ok") is not True:
        _append_incident(
            store,
            signal["signal_key"] + ":ENTRY_PREFLIGHT",
            {"phase": "ENTRY", "reason": "PREFLIGHT_FAIL", "health": health},
        )
        return None

    rules = client.market_rules(SYMBOL)
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
        "preflight": health,
        "order": order,
        "target_notional_usdt": format(TARGET_NOTIONAL_USDT, "f"),
        "hard_cap_usdt": format(MAX_NOTIONAL_USDT, "f"),
    }
    store.append_once(ENTRY_EVENT, signal["signal_key"], payload)
    return payload


def _executed_qty(entry: dict[str, Any]) -> Decimal:
    order = entry.get("order") or {}
    raw = order.get("executedQty") or order.get("origQty") or entry.get("requested_quantity")
    qty = Decimal(str(raw))
    if qty <= 0:
        raise MicroLiveBlocked("entry has no positive executed quantity")
    return qty


def _maybe_exit(
    *,
    now: datetime,
    store,
    client: BinanceUSDMTradingClient,
) -> dict[str, Any] | None:
    entry = _first_entry(store)
    if entry is None or _first_exit(store) is not None:
        return None
    signal = _signal_by_key(store, entry["signal_key"])
    if signal is None:
        raise MicroLiveBlocked("entry signal missing from evidence store")
    exit_at = _parse_utc(signal["reference_exit"])
    if now < exit_at:
        return None

    qty = _executed_qty(entry)
    side = "SELL" if entry["direction"] == "LONG" else "BUY"
    client_id = _client_id(entry["signal_key"], "x")
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
        "signal_key": entry["signal_key"],
        "direction": entry["direction"],
        "reference_exit": signal["reference_exit"],
        "client_order_id": client_id,
        "quantity": format(qty, "f"),
        "order": order,
        "late_by_seconds": late_by,
        "late_exit_incident": late_by > ENTRY_GRACE_SECONDS,
    }
    store.append_once(EXIT_EVENT, entry["signal_key"], payload)
    if late_by > ENTRY_GRACE_SECONDS:
        _append_incident(
            store,
            entry["signal_key"] + ":LATE_EXIT",
            {"phase": "EXIT", "reason": "LATE_EXIT", "late_by_seconds": late_by},
        )
    return payload


def _maybe_reconcile(*, store, client: BinanceUSDMTradingClient) -> dict[str, Any] | None:
    entry = _first_entry(store)
    exit_row = _first_exit(store)
    if entry is None or exit_row is None:
        return None
    if _payloads(store, RECON_EVENT):
        return None

    signal = _signal_by_key(store, entry["signal_key"])
    if signal is None:
        raise MicroLiveBlocked("signal missing for reconciliation")

    start = int((_parse_utc(signal["reference_entry"]) - timedelta(minutes=10)).timestamp() * 1000)
    end = int((datetime.now(UTC) + timedelta(minutes=10)).timestamp() * 1000)
    trades = client.user_trades(SYMBOL, start_ms=start, end_ms=end)
    funding = client.funding_income(SYMBOL, start_ms=start, end_ms=end)

    entry_order_id = str((entry.get("order") or {}).get("orderId", ""))
    exit_order_id = str((exit_row.get("order") or {}).get("orderId", ""))
    relevant = [
        row for row in trades
        if str(row.get("orderId", "")) in {entry_order_id, exit_order_id}
    ]
    commissions = sum(Decimal(str(row.get("commission", "0"))) for row in relevant)
    realized = sum(Decimal(str(row.get("realizedPnl", "0"))) for row in relevant)
    funding_total = sum(Decimal(str(row.get("income", "0"))) for row in funding)

    payload = {
        "candidate": CANDIDATE,
        "authority_commit": AUTHORITY_COMMIT,
        "signal_key": entry["signal_key"],
        "trade_rows": relevant,
        "funding_rows": funding,
        "commission_total_asset_units": format(commissions, "f"),
        "realized_pnl_usdt": format(realized, "f"),
        "funding_income_usdt": format(funding_total, "f"),
        "net_cashflow_usdt_before_nontrade_account_items": format(
            realized + funding_total - commissions, "f"
        ),
        "reconciled_at_utc": datetime.now(UTC).isoformat(),
        "second_real_event_authorized": False,
    }
    store.append_once(RECON_EVENT, entry["signal_key"], payload)
    return payload


def run_cycle(*, now: datetime | None = None, allow_private: bool = True) -> dict[str, Any]:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    settings = Settings.from_env()
    store = build_evidence_store(settings.db_path, settings.database_url)
    source = BinanceAVAXDailySource(timeout=settings.http_timeout)

    result: dict[str, Any] = {
        "candidate": CANDIDATE,
        "checked_at_utc": now.isoformat(),
        "evidence_backend": store.backend,
        "armed": _armed(),
        "entry_exists": _first_entry(store) is not None,
        "exit_exists": _first_exit(store) is not None,
    }

    signal = maybe_emit_signal(now=now, store=store, source=source)
    if signal is not None:
        result["signal"] = signal

    if allow_private and (_armed() or _first_entry(store) is not None):
        client = BinanceUSDMTradingClient(timeout=settings.http_timeout)

        if _first_entry(store) is None:
            signals = _payloads(store, SHADOW_EVENT_TYPE)
            if signals:
                latest = signals[-1]
                try:
                    _validate_signal_payload(latest)
                    recovered = _recover_entry_if_exchange_has_order(
                        store=store, client=client, signal=latest
                    )
                    if recovered is not None:
                        result["entry_recovery"] = recovered
                except Exception as exc:
                    result["entry_recovery_error"] = f"{type(exc).__name__}:{exc}"

        entry = _maybe_enter(now=now, store=store, client=client)
        if entry is not None:
            result["entry"] = entry

        exit_row = _maybe_exit(now=now, store=store, client=client)
        if exit_row is not None:
            result["exit"] = exit_row

        recon = _maybe_reconcile(store=store, client=client)
        if recon is not None:
            result["reconciliation"] = recon

    chain_ok, detail = store.verify_chain()
    result["evidence_chain_ok"] = chain_ok
    result["evidence_chain_detail"] = detail
    return result


def run_forever() -> int:
    poll = max(float(os.getenv("CED1D0031_POLL_SECONDS", "0.5")), 0.25)
    while True:
        try:
            result = run_cycle()
            print(json.dumps(result, sort_keys=True), flush=True)
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
        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(run_forever())
