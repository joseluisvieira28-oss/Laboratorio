from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from radar.market import MEXCFuturesPublicFeed
from radar.mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from radar.operator_futures_engine_v02 import (
    MAX_CLOCK_OFFSET_MS,
    OFFICIAL_API_TAKER_FLOOR,
    compute_contract_volume,
)
from radar.operator_risk_v02 import build_operator_risk_state

CANDIDATE_ID = "BNB-LAUNCHPOOL-DEMAND-001"
SYMBOL = "BNB_USDT"
FRICTION_CEILING_BPS = 30.0


def _write(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


def _load_policy(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("policy_id") != "CRYPTO-LAB-OPERATOR-GLOBAL-RISK-V0.2":
        raise RuntimeError("unexpected policy")
    return payload


def _clock_gate(public: MEXCFuturesPublicFeed) -> dict[str, Any]:
    before = time.time_ns() / 1_000_000.0
    server_ms = float(public.server_time_ms())
    after = time.time_ns() / 1_000_000.0
    midpoint = (before + after) / 2.0
    offset = server_ms - midpoint
    return {
        "pass": abs(offset) <= MAX_CLOCK_OFFSET_MS,
        "server_minus_local_midpoint_ms": offset,
        "request_rtt_ms": after - before,
        "max_abs_offset_ms": MAX_CLOCK_OFFSET_MS,
    }


def build_readiness(
    *,
    policy_path: str | Path,
    receipt_root: str | Path,
    credentials: MEXCCredentials,
) -> dict[str, Any]:
    policy = _load_policy(policy_path)
    private = MEXCFuturesAuthenticatedReadOnlyClient(credentials)
    public = MEXCFuturesPublicFeed(timeout=10)
    blockers: list[str] = []

    risk = build_operator_risk_state(
        private_client=private,
        receipt_root=receipt_root,
    )
    blockers.extend(risk["blockers"])

    try:
        mode = private.position_mode()
        if mode != 1:
            blockers.append("FUTURES_POSITION_MODE_NOT_HEDGE")
    except Exception as exc:
        mode = None
        blockers.append(f"POSITION_MODE_READ_FAILED:{type(exc).__name__}")

    try:
        clock = _clock_gate(public)
        if not clock["pass"]:
            blockers.append("WINDOWS_CLOCK_OFFSET_OUTSIDE_500MS")
    except Exception as exc:
        clock = {"pass": False, "error": f"{type(exc).__name__}:{exc}"}
        blockers.append("MEXC_CLOCK_CHECK_FAILED")

    try:
        contract = public.contract_row(SYMBOL)
        snapshots = public.all_market_snapshots()
        snap = snapshots[SYMBOL.replace("_", "")]
        price = max(float(snap.last_price), float(snap.ask_price))
        bid = float(snap.bid_price)
        ask = float(snap.ask_price)
        mid = (bid + ask) / 2.0
        spread_bps = ((ask - bid) / mid) * 10000.0 if mid > 0 else 999999.0
        sizing = compute_contract_volume(
            target_notional_usdt=50.0,
            price=price,
            contract_size=float(contract["contractSize"]),
            min_vol=float(contract["minVol"]),
            vol_unit=float(contract["volUnit"]),
        )
        if contract.get("apiAllowed") is False or contract.get("state") not in (None, 0):
            blockers.append("BNB_USDT_CONTRACT_NOT_API_ELIGIBLE")
    except Exception as exc:
        contract = {}
        sizing = None
        spread_bps = None
        blockers.append(f"BNB_USDT_MARKET_OR_SIZING_FAILED:{type(exc).__name__}:{exc}")

    try:
        fees = private.fee_details(SYMBOL)
        taker_raw = fees.get("realTakerFee")
        if taker_raw is None:
            taker_raw = fees.get("takerFee")
        account_taker = float(taker_raw)
        effective_taker = max(account_taker, OFFICIAL_API_TAKER_FLOOR)
        fee_rt_bps = 2.0 * effective_taker * 10000.0
    except Exception as exc:
        account_taker = None
        effective_taker = None
        fee_rt_bps = None
        blockers.append(f"BNB_USDT_FEE_READ_FAILED:{type(exc).__name__}")

    try:
        funding = public.funding_rate(SYMBOL)
        rate = abs(float(funding.get("fundingRate", 0) or 0))
        cycle = float(funding.get("collectCycle", 8) or 8)
        if cycle <= 0:
            cycle = 8.0
        settlements = max(1, int(math.ceil(24.0 / cycle)) + 1)
        funding_burden_bps = rate * 10000.0 * settlements
    except Exception as exc:
        funding = {}
        funding_burden_bps = None
        blockers.append(f"BNB_USDT_FUNDING_READ_FAILED:{type(exc).__name__}")

    projected = None
    if fee_rt_bps is not None and spread_bps is not None and funding_burden_bps is not None:
        projected = fee_rt_bps + 2.0 * spread_bps + funding_burden_bps
        if projected > FRICTION_CEILING_BPS:
            blockers.append("BNB_PROJECTED_FRICTION_EXCEEDS_STRESS30")

    if sizing is not None and risk.get("available_usdt") is not None:
        entry_fee_buffer = float(sizing["estimated_notional_usdt"]) * float(
            effective_taker or OFFICIAL_API_TAKER_FLOOR
        )
        if float(risk["available_usdt"]) + 1e-9 < (
            float(sizing["estimated_initial_margin_usdt"]) + entry_fee_buffer
        ):
            blockers.append("AVAILABLE_BALANCE_INSUFFICIENT_FOR_10_MARGIN_PLUS_ENTRY_FEE")

    return {
        "readiness_id": "MEXC-BNB-OPERATOR-READY-V0.2",
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_id": CANDIDATE_ID,
        "symbol": SYMBOL,
        "status": "PASS_READY_TO_ARM" if not blockers else "FAIL_CLOSED",
        "pass": not blockers,
        "blockers": blockers,
        "policy_id": policy["policy_id"],
        "risk_state": risk,
        "position_mode": mode,
        "clock": clock,
        "sizing": sizing,
        "account_taker_fee_fraction": account_taker,
        "effective_taker_fee_fraction": effective_taker,
        "round_trip_fee_bps": fee_rt_bps,
        "spread_bps": spread_bps,
        "conservative_24h_funding_burden_bps": funding_burden_bps,
        "projected_roundtrip_friction_bps": projected,
        "friction_ceiling_bps": FRICTION_CEILING_BPS,
        "execution_envelope": {
            "initial_isolated_margin_usdt": 10.0,
            "leverage": 5,
            "maximum_notional_usdt": 50.0,
            "max_simultaneous_positions": 1,
            "daily_realized_loss_kill_usdt": 5.0,
            "rolling_7d_realized_loss_kill_usdt": 5.0,
            "per_position_stop_loss": None,
        },
        "exchange_mutation_performed": False,
        "order_created": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--receipt-root", default="live_receipts/operator_futures_v02")
    ap.add_argument("--out", default="live_state/operator_ready_v02.json")
    ap.add_argument("--armed-path", default="OPERATOR_FUTURES_V02_ARMED.json")
    ap.add_argument("--arm", action="store_true")
    args = ap.parse_args()

    credentials = MEXCCredentials.from_env()
    ready = build_readiness(
        policy_path=args.policy,
        receipt_root=args.receipt_root,
        credentials=credentials,
    )
    _write(args.out, ready)

    armed = False
    if args.arm and ready["pass"]:
        policy_bytes = Path(args.policy).read_bytes()
        marker = {
            "authority": "OPERATOR-FUTURES-GLOBAL-V0.2",
            "armed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "policy_sha256": hashlib.sha256(policy_bytes).hexdigest(),
            "initial_isolated_margin_usdt": 10.0,
            "leverage": 5,
            "maximum_notional_usdt": 50.0,
            "daily_realized_loss_kill_usdt": 5.0,
            "max_simultaneous_positions": 1,
            "operator_acknowledgement": (
                "daily realized-loss kill is not an open-position stop; isolated margin "
                "is the per-position loss container"
            ),
        }
        _write(args.armed_path, marker)
        armed = True

    print(json.dumps({
        "status": ready["status"],
        "pass": ready["pass"],
        "blockers": ready["blockers"],
        "armed": armed,
        "out": str(Path(args.out).resolve()),
    }, indent=2))
    return 0 if ready["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
