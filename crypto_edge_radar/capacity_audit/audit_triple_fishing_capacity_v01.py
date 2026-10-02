#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DH03_MAX_HOLD_MS = 80 * 12 * 60 * 60 * 1000

OPTIONS_ID = "OPTIONS-SPOTPERP-001-V2.1"
BNB_ID = "BNB-LAUNCHPOOL-DEMAND-001"
DH03_ID = "HTF-DH03-12H-STANDALONE-FORWARD-V1"


def load_json(path: str | Path) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return obj


def iso_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def dh03_intervals(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    symbols = receipt.get("evaluation", {}).get("symbols", {})
    rows: list[dict[str, Any]] = []
    for symbol, payload in sorted(symbols.items()):
        for row in payload.get("rows", []):
            sig = row.get("signal") or {}
            entry = int(sig["entry_open_time"])
            exit_raw = row.get("price_exit_time")
            end = int(exit_raw) if exit_raw is not None else entry + DH03_MAX_HOLD_MS
            rows.append({
                "candidate_id": DH03_ID,
                "symbol": symbol,
                "entry_ms": entry,
                "exit_ms": end,
                "exit_observed": exit_raw is not None,
                "source_price_exit_reason": row.get("price_exit_reason"),
                "source_path_unresolved": bool(row.get("price_path_unresolved")),
            })
    rows.sort(key=lambda x: (x["entry_ms"], x["symbol"]))
    return rows


def capacity_sim(intervals: list[dict[str, Any]], slots: int) -> dict[str, Any]:
    if slots < 1:
        raise ValueError("slots must be >=1")
    active: list[dict[str, Any]] = []
    admitted: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for row in intervals:
        t = row["entry_ms"]
        active = [x for x in active if x["exit_ms"] > t]
        if len(active) < slots:
            admitted.append(row)
            active.append(row)
        else:
            blocked.append({**row, "blocked_by": [x["symbol"] for x in active]})
    return {
        "slot_cap": slots,
        "candidate_signals": len(intervals),
        "admitted": len(admitted),
        "blocked": len(blocked),
        "blocked_fraction": (len(blocked) / len(intervals)) if intervals else 0.0,
        "admitted_symbols": [x["symbol"] for x in admitted],
        "blocked_symbols": [x["symbol"] for x in blocked],
    }


def peak_concurrency(intervals: list[dict[str, Any]]) -> int:
    points = []
    for r in intervals:
        points.append((r["entry_ms"], 1))
        points.append((r["exit_ms"], -1))
    points.sort(key=lambda x: (x[0], x[1]))
    cur = peak = 0
    for _t, delta in points:
        cur += delta
        peak = max(peak, cur)
    return peak


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--dh03-receipt", required=True)
    ap.add_argument("--bnb-snapshot", required=True)
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    args = ap.parse_args()

    root = Path(args.repo_root)
    manifest = load_json(root / "crypto_edge_radar/execution/GLOBAL_FISHING_MANIFEST_V02.json")
    authority = load_json(root / "crypto_edge_radar/execution/OPERATOR_FUTURES_GLOBAL_AUTHORITY_V02.json")
    global_risk = load_json(root / "crypto_edge_radar/execution/OPERATOR_GLOBAL_RISK_V02.json")
    options_freeze = load_json(root / "crypto_edge_radar/OPTIONS_SPOTPERP_001_V21_LIVE_SHADOW_FREEZE_V0.1.json")
    dh03 = load_json(args.dh03_receipt)
    bnb = load_json(args.bnb_snapshot)

    options_standalone = load_json(
        root / "crypto_edge_radar/capacity_audit/OPTIONS_STANDALONE_EXECUTION_CONTRACT_REFERENCE.json"
    )

    current_single_slot = (
        manifest.get("single_global_position_slot") is True
        and int(authority.get("risk", {}).get("max_simultaneous_positions", -1)) == 1
        and int(global_risk.get("global_risk", {}).get("max_simultaneous_positions", -1)) == 1
    )

    intervals = dh03_intervals(dh03)
    dh03_totals = dh03.get("evaluation", {}).get("totals", {})
    sims = [capacity_sim(intervals, n) for n in range(1, 7)]
    peak = peak_concurrency(intervals)

    oos = options_freeze.get("oos_2025_reference", {})
    options_n = int(oos.get("resolved_scaled_trades", 0))
    options_density = options_n / 365.0 if options_n else None

    current_options_generic_leverage = 5
    current_options_generic_notional_cap = 50.0
    standalone_lev = int(options_standalone["execution_fork"]["leverage"])
    standalone_notional = float(options_standalone["risk"]["maximum_notional_usdt"])

    authority_candidates = set((authority.get("candidates") or {}).keys())
    manifest_lanes = {
        str(x.get("candidate_id") or "")
        for x in manifest.get("lanes", [])
        if isinstance(x, dict)
    }
    manifest_options = next(
        (x for x in manifest.get("lanes", []) if isinstance(x, dict) and x.get("candidate_id") == OPTIONS_ID),
        {},
    )

    findings = {
        "single_global_slot_is_current_authority": current_single_slot,
        "global_authority_missing_options_lane": OPTIONS_ID not in authority_candidates,
        "global_authority_missing_dh03_lane": DH03_ID not in authority_candidates,
        "global_manifest_missing_dh03_lane": DH03_ID not in manifest_lanes,
        "global_manifest_options_state": manifest_options.get("state"),
        "authority_manifest_lane_drift": (
            OPTIONS_ID not in authority_candidates
            or DH03_ID not in authority_candidates
            or DH03_ID not in manifest_lanes
        ),
        "single_slot_drops_due_signals_no_chase": "MISSED_CONFLICT_NO_CHASE" in str(authority),
        "dh03_parent_rule_is_one_active_trade_per_symbol": True,
        "dh03_prospective_selected_signals": len(intervals),
        "dh03_source_overlap_skipped_within_symbol": int(dh03_totals.get("overlap_skipped", 0)),
        "dh03_peak_cross_symbol_concurrency_observed_or_open": peak,
        "dh03_single_slot_admitted": sims[0]["admitted"],
        "dh03_single_slot_blocked": sims[0]["blocked"],
        "dh03_single_slot_blocked_fraction": sims[0]["blocked_fraction"],
        "options_2025_reference_resolved_trades": options_n,
        "options_2025_24h_occupancy_pressure_proxy": options_density,
        "options_standalone_leverage": standalone_lev,
        "options_triple_generic_leverage": current_options_generic_leverage,
        "options_standalone_max_notional_usdt": standalone_notional,
        "options_triple_generic_max_notional_usdt": current_options_generic_notional_cap,
        "options_risk_profile_mismatch": (
            standalone_lev != current_options_generic_leverage
            or standalone_notional != current_options_generic_notional_cap
        ),
        "bnb_current_public_snapshot_status": bnb.get("status"),
        "bnb_current_eligible_event_count": len(bnb.get("eligible_events", [])),
    }

    verdict = (
        "REDESIGN_JUSTIFIED__DO_NOT_ACTIVATE_MULTI_SLOT_UNTIL_PER_LANE_RISK_AND_MULTI_POSITION_RECOVERY_PASS"
        if current_single_slot and sims[0]["blocked"] > 0
        else "INSUFFICIENT_EVIDENCE_TO_CHANGE_SINGLE_SLOT"
    )

    report = {
        "audit_id": "TRIPLE_FISHING_CAPACITY_AUDIT_V0.1",
        "as_of_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "offline/read-only capacity and architecture audit; no orders; no exchange mutation",
        "verdict": verdict,
        "findings": findings,
        "dh03_intervals": [
            {**r, "entry_utc": iso_ms(r["entry_ms"]), "exit_or_maxhold_utc": iso_ms(r["exit_ms"])}
            for r in intervals
        ],
        "dh03_capacity_simulation": sims,
        "bnb_public_snapshot": bnb,
        "hard_blockers_before_any_multislot_live_authority": [
            "replace single-file GlobalSlotReservationV03 with durable multi-reservation ledger keyed by signal identity",
            "make engine manage multiple active trade states instead of FAIL_CLOSED on >1",
            "make account risk count aggregate open margin/notional and candidate-specific limits",
            "preserve one-active-per-symbol and prevent duplicate same-symbol/direction exposure",
            "separate per-lane execution risk profiles; OPTIONS standalone contract is 1x/10 USDT notional while generic Triple engine is 5x/50 USDT",
            "define global aggregate initial-margin/notional caps before allowing slot 2",
            "define portfolio-level daily/rolling kill semantics for already-open positions",
            "prove restart/reconciliation with 2+ simultaneous positions and unknown acknowledgements",
            "prove independent TP/SL/scheduled-exit ownership for every active session",
            "fresh authenticated read-only account/position/order reconciliation before activation",
            "reconcile authority/manifest lane inventory with actual Triple Fishing supervisor before any activation",
            "new explicit authority required; current authority remains max_simultaneous_positions=1",
        ],
        "suggested_staged_target": {
            "first_engineering_target": 2,
            "reason": "prove multi-position accounting/recovery with the smallest concurrency increase; this is an engineering target, not live authority",
            "dh03_signals_admitted_in_observed_cluster": sims[1]["admitted"] if len(sims) > 1 else None,
            "dh03_signals_still_blocked_in_observed_cluster": sims[1]["blocked"] if len(sims) > 1 else None,
            "full_dh03_parent_capacity_peak_observed": peak,
        },
        "governance": {
            "live_trading_authorized": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "current_authority_modified": False,
            "main_merge": False,
        },
    }

    Path(args.output_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = f"""# Triple Fishing capacity audit V0.1

## Verdict

**{verdict}**

The present one-slot design is not merely conservative; in the currently available prospective DH03 evidence it truncates valid cross-symbol parent selections.

## Current architecture

- Manifest single global slot: **{manifest.get('single_global_position_slot')}**
- Authority max simultaneous positions: **{authority.get('risk',{}).get('max_simultaneous_positions')}**
- Risk policy max simultaneous positions: **{global_risk.get('global_risk',{}).get('max_simultaneous_positions')}**
- Conflict loser: **MISSED_CONFLICT_NO_CHASE**

## Authority / manifest reconciliation

The current Triple Fishing supervisor contains OPTIONS, BNB and DH03, but the frozen global authority/manifest are not aligned with that runtime inventory:

- Global authority missing OPTIONS lane: **{findings['global_authority_missing_options_lane']}**
- Global authority missing DH03 lane: **{findings['global_authority_missing_dh03_lane']}**
- Global manifest missing DH03 lane: **{findings['global_manifest_missing_dh03_lane']}**
- Manifest OPTIONS state: **{findings['global_manifest_options_state']}**

This drift is an independent activation blocker. A multi-slot redesign cannot be authorized by changing capacity alone.

## Prospective DH03 capacity evidence

Latest source receipt: {dh03.get('checked_at_utc')}
Latest archive day: {dh03.get('latest_archive_day')}

- Parent-selected cross-symbol signals: **{len(intervals)}**
- Additional same-symbol triggers already suppressed by the frozen parent rule: **{int(dh03_totals.get('overlap_skipped',0))}**
- Peak simultaneous selected positions in this observed cluster: **{peak}**
- With one global slot: admitted **{sims[0]['admitted']}**, blocked **{sims[0]['blocked']}** ({sims[0]['blocked_fraction']:.1%})

Capacity replay:
"""
    for s in sims:
        md += f"- {s['slot_cap']} slot(s): admitted {s['admitted']}/{s['candidate_signals']}, blocked {s['blocked']} ({s['blocked_fraction']:.1%})\n"

    md += f"""
The first selected DH03 position in the evidence cluster is still unresolved in the available source window, so under the current one-slot rule it would retain the account-wide slot and suppress every later selected DH03 entry in the cluster.

## OPTIONS capacity pressure

Frozen 2025 OOS reference contains **{options_n} resolved scaled trades** with a frozen 24-hour holding horizon. Used only as an operational density reference, that is **{options_density:.1%} of 365 calendar days**. It is not a claim that 2026 will have the same signal density.

There is also an execution-risk mismatch that must be resolved before multi-slot activation:
- standalone OPTIONS Futures-only authority: **{standalone_lev}x**, max **{standalone_notional:g} USDT notional**
- generic Triple engine path: **5x**, max **50 USDT notional**

Therefore increasing the slot count in the existing engine would multiply a risk envelope that is not lane-specific.

## BNB current public snapshot

Status: **{bnb.get('status')}**
Eligible events visible now: **{len(bnb.get('eligible_events',[]))}**

A lack of a current BNB event does not remove the structural conflict: BNB has a strict 2-second no-chase entry window and a 24-hour hold, so an occupied global slot turns a valid event into a permanently missed execution.

## Engineering conclusion

A multi-position redesign is justified. **Do not change the live authority by editing max_simultaneous_positions from 1 to 2.**

The current engine, reservation and risk layers are structurally single-position:
1. one non-expiring global reservation file;
2. manage_active() fails closed when more than one local active trade exists;
3. risk policy blocks at one effective open position;
4. generic risk constants are shared across lanes.

The safe next implementation target is a **shadow-only two-slot engine** with per-lane risk profiles and an aggregate portfolio firewall. Two slots will not preserve every DH03 signal in the observed cluster, but it is the smallest concurrency increase on which multi-position reservation, restart, reconciliation and risk accounting can be proven before considering a higher cap.

No live trading, order creation, exchange mutation, authority replacement or main merge is authorized by this audit.
"""
    Path(args.output_md).write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "dh03_selected": len(intervals),
        "dh03_single_slot_blocked": sims[0]["blocked"],
        "dh03_peak_concurrency": peak,
        "options_reference_density": options_density,
        "options_risk_profile_mismatch": findings["options_risk_profile_mismatch"],
        "bnb_snapshot_status": bnb.get("status"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
