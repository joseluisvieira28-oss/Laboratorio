from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from radar.market import MEXCFuturesPublicFeed
from radar.mexc_auth_readonly import (
    MEXCCredentials,
    MEXCFuturesAuthenticatedReadOnlyClient,
)
from radar.mexc_auth_trade import MEXCFuturesMutationTransport
from radar.mexc_live_gate import EXECUTION_TOKEN, validate_futures_short_execution


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _load(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload


def _safe_session_name(signal_key: str) -> str:
    digest = hashlib.sha256(signal_key.encode("utf-8")).hexdigest()[:16]
    return f"etf-cme-{digest}"


def _acquire_duplicate_lock(root: Path, key: str, payload: dict[str, Any]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(key.encode("utf-8")).hexdigest() + ".lock"
    path = root / name
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags)
    except FileExistsError as exc:
        raise RuntimeError("DUPLICATE_PROTECTION_KEY_ALREADY_CONSUMED") from exc
    try:
        os.write(
            fd,
            (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"),
        )
    finally:
        os.close(fd)
    return path


def _wait_order(
    client: MEXCFuturesAuthenticatedReadOnlyClient,
    *,
    symbol: str,
    external_oid: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        try:
            last = client.order_by_external(
                symbol=symbol,
                external_oid=external_oid,
            )
        except Exception:
            time.sleep(0.5)
            continue
        state = int(last.get("state", 0) or 0)
        if state in (3, 4, 5):
            return last
        time.sleep(0.5)
    if last is None:
        raise RuntimeError("ORDER_LOOKUP_TIMEOUT_NO_STATE")
    return last


def _wait_short_position(
    client: MEXCFuturesAuthenticatedReadOnlyClient,
    *,
    timeout_seconds: float = 5.0,
) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_seconds
    last = None
    while time.monotonic() < deadline:
        rows = client.open_positions("BTC_USDT")
        short = [
            row
            for row in rows
            if str(row.get("symbol", "")).upper() == "BTC_USDT"
            and int(row.get("positionType", 0) or 0) == 2
            and float(row.get("holdVol", 0) or 0) > 0
        ]
        if len(short) == 1:
            return short[0]
        if len(short) > 1:
            raise RuntimeError("MULTIPLE_SHORT_POSITIONS_PRESENT")
        last = None
        time.sleep(0.25)
    return last


def _fee_from_order(order: dict[str, Any]) -> float:
    total = order.get("totalFee")
    if total is not None:
        try:
            return abs(float(total))
        except (TypeError, ValueError):
            pass
    fee = 0.0
    for key in ("takerFee", "makerFee"):
        try:
            fee += abs(float(order.get(key, 0) or 0))
        except (TypeError, ValueError):
            continue
    return fee


def _short_slippage_bps(reference_price: float, fill_price: float) -> float:
    # For a SHORT entry, a fill below reference is adverse.
    return ((reference_price - fill_price) / reference_price) * 10_000.0


def _emergency_flatten(
    *,
    transport: MEXCFuturesMutationTransport,
    readonly: MEXCFuturesAuthenticatedReadOnlyClient,
    position: dict[str, Any],
    session_dir: Path,
    reason: str,
) -> dict[str, Any]:
    position_id = int(position["positionId"])
    hold_vol = int(float(position["holdVol"]))
    ext = f"emg-{hashlib.sha256((str(position_id)+reason).encode()).hexdigest()[:20]}"
    request = {
        "receipt_type": "EMERGENCY_EXIT_REQUEST",
        "reason": reason,
        "symbol": "BTC_USDT",
        "position_id": position_id,
        "volume_contracts": hold_vol,
        "side": 2,
        "side_semantics": "CLOSE_SHORT",
        "external_oid": ext,
    }
    _write(session_dir / "EMERGENCY_EXIT_REQUEST.json", request)
    ack = transport.submit_market_order(
        symbol="BTC_USDT",
        volume_contracts=hold_vol,
        side=2,
        external_oid=ext,
        position_mode=1,
        position_id=position_id,
    )
    _write(
        session_dir / "EMERGENCY_EXIT_ACK.json",
        {
            "receipt_type": "EMERGENCY_EXIT_ACK",
            "reason": reason,
            "exchange_ack": ack,
        },
    )
    final = _wait_order(
        readonly,
        symbol="BTC_USDT",
        external_oid=ext,
        timeout_seconds=10,
    )
    _write(
        session_dir / "EMERGENCY_EXIT_RECEIPT.json",
        {
            "receipt_type": "EMERGENCY_EXIT_RECEIPT",
            "reason": reason,
            "order": final,
            "execution_failure": True,
        },
    )
    return final


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--authority", required=True)
    p.add_argument("--standing-authority", required=True)
    p.add_argument("--preflight", required=True)
    p.add_argument("--signal", required=True)
    p.add_argument("--risk-state", required=True)
    p.add_argument("--receipt-root", default="live_receipts")
    p.add_argument("--duplicate-lock-root", default="live_state/duplicate_locks")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()

    authority = _load(args.authority)
    signal = _load(args.signal)
    signal_key = str(signal.get("immutable_signal_key") or "missing-signal")
    session_dir = Path(args.receipt_root) / _safe_session_name(signal_key)
    session_dir.mkdir(parents=True, exist_ok=True)

    kill_switch_path = str(authority.get("kill_switch_path") or "KILL_SWITCH")
    gate = validate_futures_short_execution(
        authority_path=args.authority,
        standing_authority_path=args.standing_authority,
        preflight_path=args.preflight,
        signal_path=args.signal,
        risk_state_path=args.risk_state,
        kill_switch_path=kill_switch_path,
    )
    _write(session_dir / "PRE_ORDER_GATE.json", gate)
    if not gate["pass"]:
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "blockers": gate["blockers"],
                    "session_dir": str(session_dir.resolve()),
                },
                indent=2,
            )
        )
        return 2

    if not args.execute:
        print(
            json.dumps(
                {
                    "status": "TRADE_READY_NOT_SUBMITTED",
                    "gate": gate,
                    "session_dir": str(session_dir.resolve()),
                },
                indent=2,
            )
        )
        return 0

    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN") != EXECUTION_TOKEN:
        fail = {
            **gate,
            "pass": False,
            "blockers": ["LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"],
        }
        _write(session_dir / "PRE_ORDER_GATE.json", fail)
        print(json.dumps({"status": "FAIL_CLOSED", "blockers": fail["blockers"]}, indent=2))
        return 3

    credentials = MEXCCredentials.from_env()
    readonly = MEXCFuturesAuthenticatedReadOnlyClient(credentials)
    transport = MEXCFuturesMutationTransport(credentials)
    public_feed = MEXCFuturesPublicFeed(timeout=10)

    # Last-moment live account reconciliation before any exchange mutation.
    live_positions = readonly.open_positions()
    live_orders = readonly.open_orders()
    live_mode = readonly.position_mode()
    if live_positions or live_orders or live_mode != 1:
        blockers = []
        if live_positions:
            blockers.append("LAST_MOMENT_OPEN_POSITION_PRESENT")
        if live_orders:
            blockers.append("LAST_MOMENT_OPEN_ORDER_PRESENT")
        if live_mode != 1:
            blockers.append("LAST_MOMENT_POSITION_MODE_NOT_HEDGE")
        fail = {**gate, "pass": False, "blockers": blockers}
        _write(session_dir / "PRE_ORDER_GATE.json", fail)
        print(json.dumps({"status": "FAIL_CLOSED", "blockers": blockers}, indent=2))
        return 4

    snapshots = public_feed.all_market_snapshots()
    snap = snapshots["BTCUSDT"]
    funding = public_feed.funding_rate("BTC_USDT")
    contract = public_feed.contract_row("BTC_USDT")
    live_assets = readonly.assets()
    usdt_asset = next(
        (row for row in live_assets if str(row.get("currency", "")).upper() == "USDT"),
        None,
    )
    if usdt_asset is None:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_USDT_ASSET_MISSING"]},indent=2))
        return 4
    live_equity = float(usdt_asset.get("equity", 0) or 0)
    if live_equity <= 0:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_EQUITY_INVALID"]},indent=2))
        return 4
    volume = int(authority["volume_contracts"])
    current_conservative_price = max(float(snap.last_price), float(snap.ask_price))
    current_notional = (
        volume
        * float(contract["contractSize"])
        * current_conservative_price
    )
    current_budget = live_equity * 0.001
    if current_notional > current_budget + 1e-12:
        print(json.dumps({
            "status":"FAIL_CLOSED",
            "blockers":["LAST_MOMENT_NOTIONAL_EXCEEDS_FROZEN_0_1PCT_BUDGET"],
            "current_notional_usdt":current_notional,
            "current_budget_usdt":current_budget
        },indent=2))
        return 4
    if Path(kill_switch_path).exists():
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["KILL_SWITCH_PRESENT_BEFORE_MUTATION"]},indent=2))
        return 4

    pre_order = {
        "receipt_type": "PRE_ORDER_RECEIPT",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "strategy_id": gate["strategy_id"],
        "signal_identity": gate["signal_identity"],
        "symbol": gate["symbol"],
        "direction": "SHORT",
        "requested_notional_usdt_at_gate": gate["requested_notional_usdt"],
        "requested_notional_usdt_last_moment": current_notional,
        "maximum_authorized_notional_usdt_at_gate": gate["maximum_authorized_notional_usdt"],
        "maximum_authorized_notional_usdt_last_moment": current_budget,
        "live_equity_usdt": live_equity,
        "minimum_notional_usdt": gate["minimum_notional_usdt"],
        "exchange": "MEXC",
        "margin_mode": "ISOLATED",
        "leverage": 1,
        "position_mode": "HEDGE",
        "order_type": "MARKET",
        "reference_entry_price": gate["reference_entry_price"],
        "market_snapshot": {
            "last_price": snap.last_price,
            "bid": snap.bid_price,
            "ask": snap.ask_price,
            "funding_rate": funding.get("fundingRate"),
            "next_settle_time_ms": funding.get("nextSettleTime"),
        },
        "projected_round_trip_bps": gate["projected_round_trip_bps"],
        "effective_taker_fee_bps": gate["effective_taker_fee_bps"],
    }
    _write(session_dir / "PRE_ORDER_RECEIPT.json", pre_order)

    # Configure isolated 1x and verify from a fresh authenticated read.
    leverage_ack = transport.configure_isolated_leverage(
        symbol="BTC_USDT",
        position_type=2,
        leverage=1,
    )
    _write(
        session_dir / "LEVERAGE_CONFIGURATION_ACK.json",
        {
            "receipt_type": "LEVERAGE_CONFIGURATION_ACK",
            "symbol": "BTC_USDT",
            "position_type": 2,
            "open_type": "ISOLATED",
            "leverage": 1,
            "exchange_ack": leverage_ack,
        },
    )
    leverage_rows = readonly.leverage("BTC_USDT")
    short_leverage = [
        row
        for row in leverage_rows
        if int(row.get("positionType", 0) or 0) == 2
    ]
    leverage_ok = (
        len(short_leverage) == 1
        and int(short_leverage[0].get("leverage", 0) or 0) == 1
        and int(short_leverage[0].get("openType", 0) or 0) == 1
    )
    _write(
        session_dir / "LEVERAGE_POST_VERIFY.json",
        {
            "receipt_type": "LEVERAGE_POST_VERIFY",
            "pass": leverage_ok,
            "rows": short_leverage,
        },
    )
    if not leverage_ok:
        print(json.dumps({"status": "FAIL_CLOSED", "blockers": ["ISOLATED_1X_POST_VERIFY_FAILED"]}, indent=2))
        return 5

    # Fresh conflict/kill-switch check after leverage configuration and before order/create.
    if Path(kill_switch_path).exists():
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["KILL_SWITCH_PRESENT_BEFORE_ORDER"]},indent=2))
        return 5
    if readonly.open_positions() or readonly.open_orders():
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_POSITION_OR_ORDER_CONFLICT"]},indent=2))
        return 5

    duplicate_key = str(authority["duplicate_protection_key"])
    try:
        lock = _acquire_duplicate_lock(
            Path(args.duplicate_lock_root),
            duplicate_key,
            {
                "signal_identity": signal_key,
                "strategy_id": gate["strategy_id"],
                "consumed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )
    except RuntimeError as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "blockers": [str(exc)]}, indent=2))
        return 6

    external_oid = str(authority["external_oid"])
    order_request = {
        "receipt_type": "ORDER_REQUEST",
        "symbol": "BTC_USDT",
        "api_path": "/api/v1/private/order/create",
        "side": 3,
        "side_semantics": "OPEN_SHORT",
        "type": 5,
        "type_semantics": "MARKET",
        "openType": 1,
        "open_type_semantics": "ISOLATED",
        "positionMode": 1,
        "leverage": 1,
        "volume_contracts": volume,
        "external_oid": external_oid,
        "signal_identity": authority["signal_identity"],
        "duplicate_lock": str(lock.resolve()),
    }
    _write(session_dir / "ORDER_REQUEST.json", order_request)

    ack = transport.submit_market_order(
        symbol="BTC_USDT",
        volume_contracts=volume,
        side=3,
        external_oid=external_oid,
        position_mode=1,
    )
    _write(
        session_dir / "EXCHANGE_ACK.json",
        {
            "receipt_type": "EXCHANGE_ACK",
            "order_id": ack.get("orderId"),
            "exchange_response_ts_ms": ack.get("ts"),
            "external_oid": external_oid,
            "exchange": "MEXC",
        },
    )

    order = _wait_order(
        readonly,
        symbol="BTC_USDT",
        external_oid=external_oid,
        timeout_seconds=10,
    )
    state = int(order.get("state", 0) or 0)
    deal_vol = float(order.get("dealVol", 0) or 0)

    if state not in (3, 4, 5):
        cancel_ack = transport.cancel_by_external(
            symbol="BTC_USDT",
            external_oid=external_oid,
        )
        _write(
            session_dir / "ORDER_TIMEOUT_CANCEL_ACK.json",
            {
                "receipt_type": "ORDER_TIMEOUT_CANCEL_ACK",
                "exchange_ack": cancel_ack,
                "last_order_state": order,
            },
        )
        order = _wait_order(
            readonly,
            symbol="BTC_USDT",
            external_oid=external_oid,
            timeout_seconds=3,
        )
        state = int(order.get("state", 0) or 0)
        deal_vol = float(order.get("dealVol", 0) or 0)

    if deal_vol <= 0:
        _write(
            session_dir / "EXECUTION_FAILURE.json",
            {
                "receipt_type": "EXECUTION_FAILURE",
                "reason": "ENTRY_ORDER_NOT_FILLED",
                "order": order,
                "trade_opened": False,
            },
        )
        print(json.dumps({"status": "FAIL_CLOSED", "blockers": ["ENTRY_ORDER_NOT_FILLED"]}, indent=2))
        return 7

    position = _wait_short_position(readonly, timeout_seconds=5)
    if position is None:
        _write(
            session_dir / "EXECUTION_FAILURE.json",
            {
                "receipt_type": "EXECUTION_FAILURE",
                "reason": "FILLED_ORDER_WITHOUT_RESOLVABLE_SHORT_POSITION",
                "order": order,
                "trade_opened": True,
            },
        )
        print(json.dumps({"status": "FAIL_CLOSED", "blockers": ["SHORT_POSITION_NOT_RESOLVED"]}, indent=2))
        return 8

    # Hard verify isolated 1x. If this is wrong after a fill, flatten immediately.
    if (
        int(position.get("openType", 0) or 0) != 1
        or int(position.get("leverage", 0) or 0) != 1
    ):
        _emergency_flatten(
            transport=transport,
            readonly=readonly,
            position=position,
            session_dir=session_dir,
            reason="POST_FILL_POSITION_NOT_ISOLATED_1X",
        )
        print(json.dumps({"status": "FAIL_CLOSED_FLATTENED", "blockers": ["POST_FILL_POSITION_NOT_ISOLATED_1X"]}, indent=2))
        return 9

    # MEXC's current API can toggle Auto-Add Margin only after a position exists.
    # Enforce OFF immediately after fill and flatten if OFF cannot be verified.
    if bool(position.get("autoAddIm")):
        transport.set_auto_add_margin(
            position_id=int(position["positionId"]),
            enabled=False,
        )
        time.sleep(0.25)
        refreshed = _wait_short_position(readonly, timeout_seconds=3)
        if refreshed is not None:
            position = refreshed

    auto_margin_off = position.get("autoAddIm") is False
    _write(
        session_dir / "POST_FILL_RISK_VERIFY.json",
        {
            "receipt_type": "POST_FILL_RISK_VERIFY",
            "pass": (
                int(position.get("openType", 0) or 0) == 1
                and int(position.get("leverage", 0) or 0) == 1
                and auto_margin_off
            ),
            "position_id": position.get("positionId"),
            "open_type": position.get("openType"),
            "leverage": position.get("leverage"),
            "auto_add_im": position.get("autoAddIm"),
        },
    )
    if not auto_margin_off:
        _emergency_flatten(
            transport=transport,
            readonly=readonly,
            position=position,
            session_dir=session_dir,
            reason="AUTO_MARGIN_ADD_OFF_NOT_VERIFIED",
        )
        print(json.dumps({"status": "FAIL_CLOSED_FLATTENED", "blockers": ["AUTO_MARGIN_ADD_OFF_NOT_VERIFIED"]}, indent=2))
        return 10

    fill_price = float(order.get("dealAvgPrice") or position.get("openAvgPrice"))
    reference_price = float(authority["reference_entry_price"])
    actual_fee = _fee_from_order(order)
    fill_receipt = {
        "receipt_type": "FILL_RECEIPT",
        "order_id": order.get("orderId"),
        "external_oid": external_oid,
        "position_id": position.get("positionId"),
        "deal_volume_contracts": deal_vol,
        "deal_average_price": fill_price,
        "order_state": state,
        "open_type": position.get("openType"),
        "leverage": position.get("leverage"),
        "auto_add_im": position.get("autoAddIm"),
        "filled_at_exchange_update_ms": order.get("updateTime"),
    }
    _write(session_dir / "FILL_RECEIPT.json", fill_receipt)

    preflight = _load(args.preflight)
    fees = (preflight.get("checks") or {}).get("fees") or {}
    _write(
        session_dir / "FEE_RECEIPT.json",
        {
            "receipt_type": "FEE_RECEIPT",
            "actual_entry_fee_usdt_from_order": actual_fee,
            "fee_currency": order.get("feeCurrency"),
            "order_taker_fee": order.get("takerFee"),
            "order_maker_fee": order.get("makerFee"),
            "order_total_fee": order.get("totalFee"),
            "effective_taker_fee_bps_model": fees.get(
                "effective_taker_fee_bps_for_execution_model"
            ),
            "official_api_fee_floor_bps": 8.0,
        },
    )

    signed_slippage = _short_slippage_bps(reference_price, fill_price)
    _write(
        session_dir / "SLIPPAGE_RECEIPT.json",
        {
            "receipt_type": "SLIPPAGE_RECEIPT",
            "direction": "SHORT",
            "reference_entry_price": reference_price,
            "fill_price": fill_price,
            "signed_adverse_slippage_bps": signed_slippage,
            "absolute_slippage_bps": abs(signed_slippage),
            "positive_signed_value_means_adverse": True,
        },
    )

    active = {
        "receipt_type": "ACTIVE_TRADE_STATE",
        "state": "EXIT_PENDING",
        "strategy_id": gate["strategy_id"],
        "signal_identity": signal_key,
        "position_id": int(position["positionId"]),
        "volume_contracts": int(float(position["holdVol"])),
        "entry_price": fill_price,
        "entry_order_external_oid": external_oid,
        "entry_order_id": order.get("orderId"),
        "entry_exchange_update_ms": order.get("updateTime"),
        "entry_target_utc": authority["entry_target_utc"],
        "exit_target_utc": authority["exit_target_utc"],
        "planned_risk_fraction_equity": 0.001,
        "authority_path": str(Path(args.authority).resolve()),
        "reference_entry_price": reference_price,
        "execution_failure": False,
    }
    _write(session_dir / "ACTIVE_TRADE_STATE.json", active)

    print(
        json.dumps(
            {
                "status": "FILLED_EXIT_PENDING",
                "session_dir": str(session_dir.resolve()),
                "position_id": active["position_id"],
                "exit_target_utc": active["exit_target_utc"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
