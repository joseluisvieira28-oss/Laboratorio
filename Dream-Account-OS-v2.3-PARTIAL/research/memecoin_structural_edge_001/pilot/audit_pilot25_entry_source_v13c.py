#!/usr/bin/env python3
"""MSEL-001 Pilot25 entry-source coverage audit V13C.

LOCAL-ONLY / RESEARCH-ONLY / OUTCOME-BLIND.

Reads only frozen cohort + <=T+5 Pump TradeEvent evidence + V13B binding.
Does NOT open V13 future raw transactions and does NOT compute returns/labels.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import statistics

EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V03_MANIFEST_SHA = "107f6a8c7eff6d98db6af6916e531b0f43a001704898440904452956e9294cea"
EXPECTED_V03_EVENTS_SHA = "973798aa4b8a861aff60c7e73075c12e2bdf803fe56515d73f8ed76a9cda3c97"
EXPECTED_V13B_BINDING_SHA = "0dc255dae3c355b859f6a534aae3eae75a092c6e40bbd4ab458676ceafd18a97"
DECISION_SECONDS = 300
FROZEN_FRESHNESS = 60
FROZEN_MIN_QUOTE = 10_000_000
ECON = {"ECONOMIC_BUY_CANDIDATE", "ECONOMIC_SELL_CANDIDATE"}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: pathlib.Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def j(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dumpj(p: pathlib.Path, obj) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(p)


def dumpjl(p: pathlib.Path, rows) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return sha(p)


def age_stats(values):
    if not values:
        return None
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    cohort_p = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    d03 = here / "data" / "msel001_t5_forensics"
    v03m_p = d03 / "economic_manifest_v03.json"
    events_p = d03 / "trade_events_economic_v03.jsonl"
    bind_p = here / "data" / "msel001_pilot25_outcome_binding_v13b" / "outcome_input_binding_v13b.json"
    for p in (cohort_p, v03m_p, events_p, bind_p):
        if not p.exists():
            raise RuntimeError(f"MISSING_INPUT {p}")
    if sha(cohort_p) != EXPECTED_COHORT_SHA:
        raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha(v03m_p) != EXPECTED_V03_MANIFEST_SHA:
        raise RuntimeError("V03_MANIFEST_HASH_MISMATCH")
    if sha(events_p) != EXPECTED_V03_EVENTS_SHA:
        raise RuntimeError("V03_EVENTS_HASH_MISMATCH")
    if sha(bind_p) != EXPECTED_V13B_BINDING_SHA:
        raise RuntimeError("V13B_BINDING_HASH_MISMATCH")
    binding = j(bind_p)
    if binding.get("future_raw_transactions_opened_by_binder") is not False:
        raise RuntimeError("BINDING_OUTCOME_LOCK_FAILURE")

    cohort = jl(cohort_p)
    events = jl(events_p)
    by_mint = {r["mint"]: r for r in cohort}
    if len(by_mint) != 25:
        raise RuntimeError("COHORT_SIZE_FAILURE")

    rows = []
    fresh_covered = 0
    prior_buy_covered = 0
    any_trade_covered = 0
    reserve_state_covered = 0
    prior_buy_ages = []
    any_trade_ages = []
    reserve_ages = []

    for launch in sorted(cohort, key=lambda r: int(r["cohort_rank"])):
        mint = launch["mint"]
        decision = int(launch["block_time"]) + DECISION_SECONDS
        prior = [r for r in events if r.get("mint") == mint and int(r["block_time"]) <= decision and r.get("semantic_class") in ECON]
        prior.sort(key=lambda r: (int(r["block_time"]), int(r.get("slot", 0)), int(r.get("transaction_index", 0)), int(r.get("log_index", 0))))

        valid_buys = [r for r in prior if r.get("side") == "buy" and int(r.get("sol_amount_raw", 0)) >= FROZEN_MIN_QUOTE]
        fresh_buys = [r for r in valid_buys if decision - FROZEN_FRESHNESS <= int(r["block_time"]) <= decision]
        valid_any = [r for r in prior if int(r.get("sol_amount_raw", 0)) >= FROZEN_MIN_QUOTE]
        reserve_rows = [r for r in prior if int(r.get("virtual_sol_reserves_raw", 0)) > 0 and int(r.get("virtual_token_reserves_raw", 0)) > 0]

        latest_buy = valid_buys[-1] if valid_buys else None
        latest_any = valid_any[-1] if valid_any else None
        latest_reserve = reserve_rows[-1] if reserve_rows else None

        if fresh_buys:
            fresh_covered += 1
        if latest_buy:
            prior_buy_covered += 1
            prior_buy_ages.append(decision - int(latest_buy["block_time"]))
        if latest_any:
            any_trade_covered += 1
            any_trade_ages.append(decision - int(latest_any["block_time"]))
        if latest_reserve:
            reserve_state_covered += 1
            reserve_ages.append(decision - int(latest_reserve["block_time"]))

        rows.append({
            "cohort_rank": int(launch["cohort_rank"]),
            "mint": mint,
            "decision_time": decision,
            "frozen_v12_fresh_buy_covered": bool(fresh_buys),
            "frozen_v12_fresh_buy_rows": len(fresh_buys),
            "prior_valid_buy_available": latest_buy is not None,
            "prior_valid_buy_age_seconds": None if latest_buy is None else decision - int(latest_buy["block_time"]),
            "prior_valid_any_trade_available": latest_any is not None,
            "prior_valid_any_trade_age_seconds": None if latest_any is None else decision - int(latest_any["block_time"]),
            "prior_verified_reserve_state_available": latest_reserve is not None,
            "prior_verified_reserve_state_age_seconds": None if latest_reserve is None else decision - int(latest_reserve["block_time"]),
            "latest_reserve_virtual_sol_raw": None if latest_reserve is None else int(latest_reserve["virtual_sol_reserves_raw"]),
            "latest_reserve_virtual_token_raw": None if latest_reserve is None else int(latest_reserve["virtual_token_reserves_raw"]),
            "latest_reserve_real_sol_raw": None if latest_reserve is None else int(latest_reserve["real_sol_reserves_raw"]),
            "latest_reserve_real_token_raw": None if latest_reserve is None else int(latest_reserve["real_token_reserves_raw"]),
            "outcomes_opened": False,
        })

    if fresh_covered != int(binding.get("pre_outcome_mints_with_eligible_pump_entry", -1)):
        raise RuntimeError(f"V13B_FROZEN_RULE_RECONCILIATION_FAILURE {fresh_covered}")

    out = here / "data" / "msel001_pilot25_entry_audit_v13c"
    rows_p = out / "entry_source_coverage_v13c.jsonl"
    rows_sha = dumpjl(rows_p, rows)
    manifest = {
        "artifact": "MSEL_PILOT25_ENTRY_SOURCE_AUDIT_V13C",
        "pilot_only": True,
        "source_v13b_binding_sha256": EXPECTED_V13B_BINDING_SHA,
        "source_v03_manifest_sha256": EXPECTED_V03_MANIFEST_SHA,
        "source_v03_trade_events_sha256": EXPECTED_V03_EVENTS_SHA,
        "frozen_v12_entry_rule": "economic Pump BUY in final 60s before T+5 with sol_amount_raw >= 10,000,000",
        "frozen_v12_coverage_mints": fresh_covered,
        "prior_valid_buy_coverage_mints_diagnostic_only": prior_buy_covered,
        "prior_valid_any_trade_coverage_mints_diagnostic_only": any_trade_covered,
        "prior_verified_reserve_state_coverage_mints_diagnostic_only": reserve_state_covered,
        "prior_valid_buy_age_seconds": age_stats(prior_buy_ages),
        "prior_valid_any_trade_age_seconds": age_stats(any_trade_ages),
        "prior_verified_reserve_state_age_seconds": age_stats(reserve_ages),
        "required_entry_coverage_for_pilot25_evaluation": 25,
        "exact_v12_entry_gate_status": "PASS" if fresh_covered == 25 else "INSUFFICIENT_ENTRY_COVERAGE_PRE_OUTCOME",
        "v14_authorized": fresh_covered == 25,
        "future_raw_transactions_opened": False,
        "returns_computed": False,
        "labels_computed": False,
        "coverage_rows_sha256": rows_sha,
    }
    man_p = out / "entry_source_audit_manifest_v13c.json"
    man_sha = dumpj(man_p, manifest)

    print("PASS: Pilot25 entry-source coverage audit V13C complete")
    print(f"frozen V12 fresh-buy coverage: {fresh_covered}/25")
    print(f"prior valid BUY coverage (diagnostic only): {prior_buy_covered}/25")
    print(f"prior valid ANY economic trade coverage (diagnostic only): {any_trade_covered}/25")
    print(f"prior verified reserve-state coverage (diagnostic only): {reserve_state_covered}/25")
    print(f"prior BUY age stats seconds: {age_stats(prior_buy_ages)}")
    print(f"reserve-state age stats seconds: {age_stats(reserve_ages)}")
    print(f"manifest sha256: {man_sha}")
    if fresh_covered != 25:
        print("V14 BLOCKED UNDER EXACT V12 ENTRY RULE")
        print("PRE-OUTCOME ENTRY AUTHORITY AMENDMENT REQUIRED OR PILOT STOPS")
    else:
        print("V14 ENTRY COVERAGE GATE PASS")
    print("NO FUTURE RAW TRANSACTION DECODED")
    print("NO RETURNS OR LABELS COMPUTED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {type(exc).__name__}: {exc}")
        raise
