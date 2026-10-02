from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
from typing import Any

from radar.market import MEXCFuturesPublicFeed
from radar.mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from radar.multi_slot_reservation_v04 import MultiSlotReservationV04
from radar.operator_risk_v02 import realized_loss_state


CANDIDATES = (
    "OPTIONS-SPOTPERP-001-V2.1",
    "BNB-LAUNCHPOOL-DEMAND-001",
    "HTF-DH03-12H-STANDALONE-FORWARD-V1",
)
ALL_SYMBOLS = ("BTC_USDT","BNB_USDT","ETH_USDT","SOL_USDT","XRP_USDT","DOGE_USDT")
DH03_NONCONFLICT_SYMBOLS = ("ETH_USDT","SOL_USDT","XRP_USDT","DOGE_USDT")
MAX_CLOCK_OFFSET_MS = 500.0


def _load(path: str | Path) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        raise RuntimeError(f"JSON object required: {path}")
    return obj


def _finite(value: Any, field: str) -> float:
    x=float(value)
    if not math.isfinite(x):
        raise RuntimeError(f"{field} must be finite")
    return x


def evaluate_public_contracts(
    *,
    public: MEXCFuturesPublicFeed,
    lane_cap_usdt: float,
) -> dict[str, Any]:
    snapshots=public.all_market_snapshots()
    out={}
    feasible=set()
    for symbol in ALL_SYMBOLS:
        try:
            row=public.contract_row(symbol)
            canonical=symbol.replace("_","")
            snap=snapshots[canonical]
            contract_size=_finite(row.get("contractSize"),f"{symbol}.contractSize")
            min_vol=_finite(row.get("minVol"),f"{symbol}.minVol")
            vol_unit=_finite(row.get("volUnit"),f"{symbol}.volUnit")
            ask=_finite(snap.ask_price,f"{symbol}.ask")
            min_notional=contract_size*min_vol*ask
            ok=(
                row.get("apiAllowed") is not False
                and row.get("state") in (None,0)
                and row.get("futureType") in (None,1)
                and contract_size>0 and min_vol>0 and vol_unit>0 and ask>0
            )
            fits=ok and min_notional <= lane_cap_usdt + 1e-9
            if fits:
                feasible.add(symbol)
            out[symbol]={
                "pass_contract":bool(ok),
                "fits_lane_cap":bool(fits),
                "contract_size":contract_size,
                "min_vol":min_vol,
                "vol_unit":vol_unit,
                "ask_price":ask,
                "minimum_executable_notional_usdt":min_notional,
                "lane_cap_usdt":lane_cap_usdt,
            }
        except Exception as exc:
            out[symbol]={
                "pass_contract":False,
                "fits_lane_cap":False,
                "error":f"{type(exc).__name__}:{exc}",
                "lane_cap_usdt":lane_cap_usdt,
            }

    minimum_three_route_feasible=(
        "BTC_USDT" in feasible
        and "BNB_USDT" in feasible
        and any(symbol in feasible for symbol in DH03_NONCONFLICT_SYMBOLS)
    )
    return {
        "symbols":out,
        "feasible_symbols":sorted(feasible),
        "minimum_three_distinct_route_capacity_feasible":minimum_three_route_feasible,
        "required_for_three_distinct_routes":{
            "OPTIONS":"BTC_USDT",
            "BNB":"BNB_USDT",
            "DH03_one_of":list(DH03_NONCONFLICT_SYMBOLS),
        },
    }


def build_readiness(
    *,
    credentials: MEXCCredentials,
    policy_path: Path,
    ledger_path: Path,
    kill_switch_path: Path,
    receipt_root: Path,
    legacy_receipt_roots: list[Path] | None = None,
    correction_overlay: Path | None = None,
    legacy_v03_armed_path: Path | None = None,
    legacy_options_armed_path: Path | None = None,
    legacy_bnb_armed_path: Path | None = None,
) -> dict[str, Any]:
    checked=datetime.now(timezone.utc)
    blockers=[]
    policy=_load(policy_path)
    if policy.get("policy_id")!="TRIPLE_FISHING_MULTI_SLOT_SMALL_AGGRESSIVE_V0.4":
        blockers.append("POLICY_ID_MISMATCH")
    if int((policy.get("capacity") or {}).get("max_simultaneous_positions",0))!=3:
        blockers.append("POLICY_NOT_EXACTLY_THREE_SLOTS")
    if policy.get("status")!="ENGINEERING_FREEZE__LIVE_ACTIVATION_NOT_YET_AUTHORIZED":
        blockers.append("POLICY_STATUS_UNEXPECTED")

    global_cfg=policy.get("global_risk") or {}
    lane_cap=10.0

    receipt_root.mkdir(parents=True, exist_ok=True)
    legacy_receipt_roots = legacy_receipt_roots or []
    existing_roots = [str(p) for p in legacy_receipt_roots if p.exists()]
    if existing_roots:
        os.environ["CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS"] = os.pathsep.join(existing_roots)
    if correction_overlay is not None:
        if not correction_overlay.exists():
            blockers.append("CORRECTION_OVERLAY_MISSING")
        else:
            os.environ["CRYPTO_LAB_PNL_CORRECTION_OVERLAY"] = str(correction_overlay)

    try:
        losses = realized_loss_state(receipt_root, now=checked)
        if losses.get("invalid_reconciliations"):
            blockers.append("LEGACY_OR_LOCAL_RECONCILIATION_ACCOUNTING_INVALID")
        if float(losses.get("daily_realized_loss_usdt", 0)) >= float(global_cfg.get("daily_realized_loss_kill_usdt", 5)):
            blockers.append("DAILY_REALIZED_LOSS_KILL_ALREADY_ACTIVE")
        if float(losses.get("rolling_7d_realized_loss_usdt", 0)) >= float(global_cfg.get("rolling_7d_realized_loss_kill_usdt", 5)):
            blockers.append("ROLLING_7D_REALIZED_LOSS_KILL_ALREADY_ACTIVE")
    except Exception as exc:
        losses = {"error": f"{type(exc).__name__}:{exc}"}
        blockers.append("REALIZED_LOSS_CONTINUITY_CHECK_FAILED")

    private=MEXCFuturesAuthenticatedReadOnlyClient(credentials)
    public=MEXCFuturesPublicFeed(timeout=10)

    try:
        assets=private.assets()
        usdt=next(row for row in assets if str(row.get("currency","")).upper()=="USDT")
        equity=_finite(usdt.get("equity"),"equity")
        available=_finite(usdt.get("availableBalance"),"availableBalance")
        min_required=float(global_cfg.get("max_total_initial_margin_usdt",14))
        if equity < min_required or available < min_required:
            blockers.append("ACCOUNT_CANNOT_SUPPORT_FULL_THREE_SLOT_MARGIN_ENVELOPE")
        account={"pass":equity>=min_required and available>=min_required,"equity_usdt":equity,"available_usdt":available,"minimum_required_available_usdt":min_required}
    except Exception as exc:
        account={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("ACCOUNT_READ_FAILED")

    try:
        positions=private.open_positions()
        orders=private.open_orders()
        tpsl=private.open_tpsl_orders() if hasattr(private,"open_tpsl_orders") else []
        handover_clear=(len(positions)==0 and len(orders)==0 and len(tpsl)==0)
        if not handover_clear:
            blockers.append("INITIAL_HANDOVER_REQUIRES_ZERO_OPEN_POSITION_ORDER_TPSL")
        exchange_state={
            "pass":handover_clear,
            "open_position_count":len(positions),
            "open_order_count":len(orders),
            "open_tpsl_count":len(tpsl),
        }
    except Exception as exc:
        exchange_state={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("OPEN_STATE_READ_FAILED")

    try:
        mode=private.position_mode()
        if mode!=1:
            blockers.append("FUTURES_POSITION_MODE_NOT_HEDGE")
    except Exception as exc:
        mode=None
        blockers.append(f"POSITION_MODE_READ_FAILED:{type(exc).__name__}")

    try:
        before=time.time_ns()/1_000_000.0
        server=float(public.server_time_ms())
        after=time.time_ns()/1_000_000.0
        midpoint=(before+after)/2.0
        offset=server-midpoint
        clock={
            "pass":abs(offset)<=MAX_CLOCK_OFFSET_MS,
            "server_minus_local_midpoint_ms":offset,
            "request_rtt_ms":after-before,
        }
        if not clock["pass"]:
            blockers.append("CLOCK_OFFSET_OUTSIDE_500MS")
    except Exception as exc:
        clock={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("CLOCK_CHECK_FAILED")

    try:
        contracts=evaluate_public_contracts(public=public,lane_cap_usdt=lane_cap)
        if not contracts["minimum_three_distinct_route_capacity_feasible"]:
            blockers.append("TEN_USDT_CAP_CANNOT_CURRENTLY_SUPPORT_THREE_DISTINCT_ROUTES")
    except Exception as exc:
        contracts={"minimum_three_distinct_route_capacity_feasible":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("PUBLIC_CONTRACT_FEASIBILITY_FAILED")

    fee_checks={}
    for symbol in ALL_SYMBOLS:
        try:
            fee=private.fee_details(symbol)
            raw=fee.get("realTakerFee")
            if raw is None:
                raw=fee.get("takerFee")
            value=_finite(raw,f"{symbol}.takerFee")
            if value<0:
                raise RuntimeError("negative fee")
            fee_checks[symbol]={"pass":True,"account_taker_fee_fraction":value}
        except Exception as exc:
            fee_checks[symbol]={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
            blockers.append(f"FEE_READ_FAILED:{symbol}")

    try:
        ledger=MultiSlotReservationV04(ledger_path,capacity=3).current()
        if ledger.get("reservations"):
            blockers.append("MULTISLOT_LEDGER_NOT_EMPTY_AT_INITIAL_HANDOVER")
        ledger_check={"pass":not bool(ledger.get("reservations")),"ledger":ledger}
    except Exception as exc:
        ledger_check={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("MULTISLOT_LEDGER_INVALID")

    if kill_switch_path.exists():
        blockers.append("KILL_SWITCH_PRESENT")
    for name,path in (
        ("LEGACY_V03_STILL_ARMED",legacy_v03_armed_path),
        ("LEGACY_OPTIONS_STILL_ARMED",legacy_options_armed_path),
        ("LEGACY_BNB_STILL_ARMED",legacy_bnb_armed_path),
    ):
        if path is not None and path.exists():
            blockers.append(name)

    blockers=list(dict.fromkeys(blockers))
    return {
        "readiness_id":"MEXC-TRIPLE-FISHING-MULTISLOT-READY-V0.4",
        "checked_at_utc":checked.isoformat().replace("+00:00","Z"),
        "status":"PASS_PRELIVE_ACCOUNT_FEASIBILITY" if not blockers else "FAIL_CLOSED",
        "pass":not blockers,
        "blockers":blockers,
        "capacity_target":3,
        "policy_id":policy.get("policy_id"),
        "account":account,
        "exchange_state":exchange_state,
        "position_mode":mode,
        "clock":clock,
        "contracts":contracts,
        "fees":fee_checks,
        "ledger":ledger_check,
        "realized_loss_continuity":losses,
        "legacy_receipt_roots":[str(p) for p in legacy_receipt_roots if p.exists()],
        "correction_overlay":str(correction_overlay) if correction_overlay is not None and correction_overlay.exists() else None,
        "live_authority_created":False,
        "armed_marker_created":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
    }


def main()->int:
    ap=argparse.ArgumentParser(description="Read-only V0.4 three-slot handover readiness. Never arms or trades.")
    ap.add_argument("--policy",required=True)
    ap.add_argument("--ledger",required=True)
    ap.add_argument("--kill-switch",required=True)
    ap.add_argument("--receipt-root",required=True)
    ap.add_argument("--legacy-receipt-root",action="append",default=[])
    ap.add_argument("--correction-overlay")
    ap.add_argument("--out",required=True)
    ap.add_argument("--legacy-v03-armed-path")
    ap.add_argument("--legacy-options-armed-path")
    ap.add_argument("--legacy-bnb-armed-path")
    args=ap.parse_args()
    try:
        result=build_readiness(
            credentials=MEXCCredentials.from_env(),
            policy_path=Path(args.policy),
            ledger_path=Path(args.ledger),
            kill_switch_path=Path(args.kill_switch),
            receipt_root=Path(args.receipt_root),
            legacy_receipt_roots=[Path(x) for x in args.legacy_receipt_root],
            correction_overlay=Path(args.correction_overlay) if args.correction_overlay else None,
            legacy_v03_armed_path=Path(args.legacy_v03_armed_path) if args.legacy_v03_armed_path else None,
            legacy_options_armed_path=Path(args.legacy_options_armed_path) if args.legacy_options_armed_path else None,
            legacy_bnb_armed_path=Path(args.legacy_bnb_armed_path) if args.legacy_bnb_armed_path else None,
        )
    except Exception as exc:
        result={
            "readiness_id":"MEXC-TRIPLE-FISHING-MULTISLOT-READY-V0.4",
            "status":"FAIL_CLOSED",
            "pass":False,
            "blockers":[f"READINESS_EXCEPTION:{type(exc).__name__}:{exc}"],
            "live_authority_created":False,
            "armed_marker_created":False,
            "orders_created":False,
            "exchange_mutation_performed":False,
        }
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result.get("pass") else 2


if __name__=="__main__":
    raise SystemExit(main())
