#!/usr/bin/env python3
"""MSEL-001 Pilot25 executable-entry candidate audit V13D.

LOCAL-ONLY / RESEARCH-ONLY / OUTCOME-BLIND / FAIL-CLOSED.

Purpose:
- bind the V13C pre-outcome entry-source audit;
- use ALL already-reconciled <=T+5 Pump TradeEvents, including rows that were
  excluded from economic-flow features, to identify the last verified bonding-
  curve reserve state at or before T+5 for each frozen launch;
- evaluate whether a deterministic gross 0.01 SOL Pump BUY quote can be
  mechanically reconstructed from that state with the exact historical helper
  formula published by pump-fun at commit
  e2b66e4fce2fc130955912315167dc41e56956ad;
- measure coverage only. This script does NOT amend V12 and does NOT authorize
  V14 by itself.

It does NOT open V13 future raw transactions, compute returns, labels, slice
statistics, or any edge verdict.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import statistics

EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V03_MANIFEST_SHA = "107f6a8c7eff6d98db6af6916e531b0f43a001704898440904452956e9294cea"
EXPECTED_V03_EVENTS_SHA = "973798aa4b8a861aff60c7e73075c12e2bdf803fe56515d73f8ed76a9cda3c97"
EXPECTED_V13C_MANIFEST_SHA = "1e57b54041a041225aba5b844a9a9e8555ed5f17e8b6471b98c1927683fc6491"
EXPECTED_TRADE_EVENTS = 1081
DECISION_SECONDS = 300
GROSS_BUY_LAMPORTS = 10_000_000
DEFAULT_PUBKEY = "11111111111111111111111111111111"

HISTORICAL_DOCS_COMMIT = "e2b66e4fce2fc130955912315167dc41e56956ad"
HISTORICAL_BONDING_CURVE_TS_GIT_BLOB = "7cb9774ee2d3e6b2620369892ad4df46b4eb53dc"
QUOTE_FORMULA_ID = "PUMP_BONDINGCURVE_TS_GET_BUY_TOKEN_AMOUNT_FROM_SOL_AMOUNT_2025-05-08"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: pathlib.Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def j(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dumpj(p: pathlib.Path, obj) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V13D_OUTPUT_ALREADY_EXISTS {p}; preserve prior audit")
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(p)


def dumpjl(p: pathlib.Path, rows) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V13D_OUTPUT_ALREADY_EXISTS {p}; preserve prior audit")
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return sha(p)


def age_stats(values):
    if not values:
        return None
    return {"min": min(values), "median": statistics.median(values), "max": max(values)}


def exact_historical_buy_quote(gross_sol_lamports: int, row: dict) -> dict:
    """Literal integer arithmetic from historical docs/bondingCurve.ts.

    Historical helper:
      totalFeeBps = feeBasisPoints + creatorFeeBasisPoints when creator != default
      inputAmount = amount * 10_000 / (totalFeeBps + 10_000)
      tokensReceived = inputAmount * vToken / (vSol + inputAmount)
      return min(tokensReceived, realTokenReserves)

    For a post-launch buy, `newCoin` is false. Creator-fee inclusion therefore
    follows whether the event-reported bonding-curve creator is the default key.
    """
    vsol = int(row.get("virtual_sol_reserves_raw", 0))
    vtok = int(row.get("virtual_token_reserves_raw", 0))
    rtok = int(row.get("real_token_reserves_raw", 0))
    fee_bps = int(row.get("fee_basis_points", 0))
    creator_fee_bps_reported = int(row.get("creator_fee_basis_points", 0))
    creator = row.get("creator")
    creator_fee_applies = bool(creator) and creator != DEFAULT_PUBKEY
    creator_fee_bps_applied = creator_fee_bps_reported if creator_fee_applies else 0
    total_fee_bps = fee_bps + creator_fee_bps_applied

    if gross_sol_lamports <= 0 or vsol <= 0 or vtok <= 0 or rtok <= 0:
        return {
            "quote_available": False,
            "input_amount_after_fee_denominator_raw": None,
            "tokens_uncapped_raw": None,
            "tokens_received_raw": 0,
            "real_reserve_cap_applied": False,
            "fee_basis_points": fee_bps,
            "creator_fee_basis_points_reported": creator_fee_bps_reported,
            "creator_fee_basis_points_applied": creator_fee_bps_applied,
            "total_fee_basis_points_applied": total_fee_bps,
            "creator_fee_applies_from_event_creator": creator_fee_applies,
        }

    input_amount = gross_sol_lamports * 10_000 // (total_fee_bps + 10_000)
    tokens_uncapped = input_amount * vtok // (vsol + input_amount)
    tokens_received = min(tokens_uncapped, rtok)
    return {
        "quote_available": tokens_received > 0,
        "input_amount_after_fee_denominator_raw": input_amount,
        "tokens_uncapped_raw": tokens_uncapped,
        "tokens_received_raw": tokens_received,
        "real_reserve_cap_applied": tokens_uncapped > rtok,
        "fee_basis_points": fee_bps,
        "creator_fee_basis_points_reported": creator_fee_bps_reported,
        "creator_fee_basis_points_applied": creator_fee_bps_applied,
        "total_fee_basis_points_applied": total_fee_bps,
        "creator_fee_applies_from_event_creator": creator_fee_applies,
    }


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    cohort_p = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    d03 = here / "data" / "msel001_t5_forensics"
    v03m_p = d03 / "economic_manifest_v03.json"
    events_p = d03 / "trade_events_economic_v03.jsonl"
    d13c = here / "data" / "msel001_pilot25_entry_audit_v13c"
    v13c_p = d13c / "entry_source_audit_manifest_v13c.json"

    for p in (cohort_p, v03m_p, events_p, v13c_p):
        if not p.exists():
            raise RuntimeError(f"MISSING_INPUT {p}")
    if sha(cohort_p) != EXPECTED_COHORT_SHA:
        raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha(v03m_p) != EXPECTED_V03_MANIFEST_SHA:
        raise RuntimeError("V03_MANIFEST_HASH_MISMATCH")
    if sha(events_p) != EXPECTED_V03_EVENTS_SHA:
        raise RuntimeError("V03_EVENTS_HASH_MISMATCH")
    if sha(v13c_p) != EXPECTED_V13C_MANIFEST_SHA:
        raise RuntimeError("V13C_MANIFEST_HASH_MISMATCH")

    v03m = j(v03m_p)
    v13c = j(v13c_p)
    if v03m.get("outcomes_opened") is not False:
        raise RuntimeError("V03_OUTCOME_LOCK_FAILURE")
    if v13c.get("future_raw_transactions_opened") is not False:
        raise RuntimeError("V13C_OUTCOME_LOCK_FAILURE")
    if v13c.get("exact_v12_entry_gate_status") != "INSUFFICIENT_ENTRY_COVERAGE_PRE_OUTCOME":
        raise RuntimeError("V13C_GATE_STATE_MISMATCH")

    cohort = jl(cohort_p)
    events = jl(events_p)
    if len(cohort) != 25 or len({r["mint"] for r in cohort}) != 25:
        raise RuntimeError("COHORT_SIZE_FAILURE")
    if len(events) != EXPECTED_TRADE_EVENTS:
        raise RuntimeError(f"V03_EVENT_COUNT_FAILURE {len(events)}/{EXPECTED_TRADE_EVENTS}")

    rows = []
    ages = []
    quote_covered = 0
    zero_real_reserve = 0
    cap_count = 0
    fee_totals = set()
    semantic_classes_latest = {}

    for launch in sorted(cohort, key=lambda r: int(r["cohort_rank"])):
        mint = launch["mint"]
        decision = int(launch["block_time"]) + DECISION_SECONDS
        prior = [
            r for r in events
            if r.get("mint") == mint and int(r.get("block_time", -1)) <= decision
        ]
        prior.sort(key=lambda r: (
            int(r.get("block_time", 0)), int(r.get("slot", 0)),
            int(r.get("transaction_index", 0)), int(r.get("log_index", 0)),
        ))
        latest = prior[-1] if prior else None

        if latest is None:
            row = {
                "cohort_rank": int(launch["cohort_rank"]),
                "mint": mint,
                "decision_time": decision,
                "latest_trade_event_available": False,
                "candidate_curve_quote_available": False,
                "candidate_curve_quote_reason": "NO_PRIOR_TRADE_EVENT_STATE",
                "outcomes_opened": False,
            }
            rows.append(row)
            continue

        state_age = decision - int(latest["block_time"])
        ages.append(state_age)
        q = exact_historical_buy_quote(GROSS_BUY_LAMPORTS, latest)
        if q["quote_available"]:
            quote_covered += 1
        if int(latest.get("real_token_reserves_raw", 0)) <= 0:
            zero_real_reserve += 1
        if q["real_reserve_cap_applied"]:
            cap_count += 1
        fee_totals.add(int(q["total_fee_basis_points_applied"]))
        sc = str(latest.get("semantic_class"))
        semantic_classes_latest[sc] = semantic_classes_latest.get(sc, 0) + 1

        rows.append({
            "cohort_rank": int(launch["cohort_rank"]),
            "mint": mint,
            "decision_time": decision,
            "latest_trade_event_available": True,
            "latest_trade_event_block_time": int(latest["block_time"]),
            "latest_trade_event_age_seconds": state_age,
            "latest_trade_event_semantic_class": latest.get("semantic_class"),
            "latest_trade_event_signature": latest.get("signature"),
            "latest_trade_event_side": latest.get("side"),
            "virtual_sol_reserves_raw": int(latest.get("virtual_sol_reserves_raw", 0)),
            "virtual_token_reserves_raw": int(latest.get("virtual_token_reserves_raw", 0)),
            "real_sol_reserves_raw": int(latest.get("real_sol_reserves_raw", 0)),
            "real_token_reserves_raw": int(latest.get("real_token_reserves_raw", 0)),
            "candidate_curve_completed_by_real_token_zero": int(latest.get("real_token_reserves_raw", 0)) == 0,
            "candidate_entry_gross_sol_lamports": GROSS_BUY_LAMPORTS,
            "candidate_entry_formula_id": QUOTE_FORMULA_ID,
            **q,
            "candidate_curve_quote_reason": "PASS" if q["quote_available"] else "NON_EXECUTABLE_CURVE_STATE",
            "outcomes_opened": False,
        })

    out = here / "data" / "msel001_pilot25_executable_entry_v13d"
    rows_p = out / "executable_entry_coverage_v13d.jsonl"
    rows_sha = dumpjl(rows_p, rows)
    status = "CANDIDATE_CURVE_ENTRY_COVERAGE_PASS" if quote_covered == 25 else "CANDIDATE_CURVE_ENTRY_COVERAGE_INCOMPLETE"
    manifest = {
        "artifact": "MSEL_PILOT25_EXECUTABLE_ENTRY_AUDIT_V13D",
        "pilot_only": True,
        "source_cohort_sha256": EXPECTED_COHORT_SHA,
        "source_v03_manifest_sha256": EXPECTED_V03_MANIFEST_SHA,
        "source_v03_trade_events_sha256": EXPECTED_V03_EVENTS_SHA,
        "source_v13c_manifest_sha256": EXPECTED_V13C_MANIFEST_SHA,
        "historical_docs_commit": HISTORICAL_DOCS_COMMIT,
        "historical_bonding_curve_ts_git_blob": HISTORICAL_BONDING_CURVE_TS_GIT_BLOB,
        "quote_formula_id": QUOTE_FORMULA_ID,
        "candidate_entry_gross_sol_lamports": GROSS_BUY_LAMPORTS,
        "candidate_entry_gross_sol": 0.01,
        "state_rule": "latest reconciled Pump TradeEvent at or before T+5, all semantic classes included; carry reserves forward only because no later reconciled Pump TradeEvent exists before decision",
        "candidate_curve_quote_coverage_mints": quote_covered,
        "zero_real_token_reserve_states": zero_real_reserve,
        "real_reserve_cap_applied_count": cap_count,
        "state_age_seconds": age_stats(ages),
        "total_fee_basis_points_values": sorted(fee_totals),
        "latest_state_semantic_class_counts": semantic_classes_latest,
        "candidate_status": status,
        "v12_amended": False,
        "v14_authorized": False,
        "future_raw_transactions_opened": False,
        "returns_computed": False,
        "labels_computed": False,
        "slice_statistics_computed": False,
        "verdict_computed": False,
        "coverage_rows_sha256": rows_sha,
    }
    man_p = out / "executable_entry_audit_manifest_v13d.json"
    man_sha = dumpj(man_p, manifest)

    print("PASS: Pilot25 executable-entry candidate audit V13D complete")
    print(f"all-event latest-state coverage: {sum(1 for r in rows if r.get('latest_trade_event_available'))}/25")
    print(f"0.01 SOL historical-curve quote coverage: {quote_covered}/25")
    print(f"zero real-token-reserve states at T+5 carry-forward: {zero_real_reserve}")
    print(f"real-reserve cap applied: {cap_count}")
    print(f"latest-state age stats seconds: {age_stats(ages)}")
    print(f"total fee bps values used: {sorted(fee_totals)}")
    print(f"latest-state semantic classes: {semantic_classes_latest}")
    print(f"manifest sha256: {man_sha}")
    print(f"candidate status: {status}")
    if quote_covered == 25:
        print("V12A ENTRY-AUTHORITY FREEZE MAY BE PREPARED; V14 STILL BLOCKED UNTIL THAT FREEZE")
    else:
        print("CURVE-ONLY ENTRY AMENDMENT DOES NOT COVER ALL 25; V14 REMAINS BLOCKED")
    print("NO FUTURE RAW TRANSACTION DECODED")
    print("NO RETURNS OR LABELS COMPUTED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {type(exc).__name__}: {exc}")
        raise
