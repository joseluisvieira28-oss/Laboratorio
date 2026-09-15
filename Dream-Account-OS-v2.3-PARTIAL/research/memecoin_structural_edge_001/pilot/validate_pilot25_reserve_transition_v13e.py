#!/usr/bin/env python3
"""MSEL-001 Pilot25 historical reserve-transition validation V13E.

LOCAL-ONLY / RESEARCH-ONLY / OUTCOME-BLIND / FAIL-CLOSED.

Purpose:
- bind the successful V13D executable-entry coverage audit;
- verify that consecutive <=T+5 historical Pump TradeEvents obey the published
  bonding-curve reserve transition semantics exactly;
- confirm that the event reserve fields used by the candidate T+5 curve entry
  are post-trade state and may be carried forward when no later reconciled Pump
  TradeEvent exists before T+5;
- do NOT amend V12, do NOT open V13 future transactions, and do NOT compute
  returns, labels, slice statistics, or any edge verdict.

Historical authority:
  pump-fun/pump-public-docs commit
  e2b66e4fce2fc130955912315167dc41e56956ad
  docs/PUMP_PROGRAM_README.md + docs/bondingCurve.ts
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from collections import defaultdict

EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V03_EVENTS_SHA = "973798aa4b8a861aff60c7e73075c12e2bdf803fe56515d73f8ed76a9cda3c97"
EXPECTED_V13D_MANIFEST_SHA = "0be1742b64425a1e2f5b4e15ad58ec0b4468af6d79b064f71579ad16d72c55e6"
EXPECTED_EVENTS = 1081
HISTORICAL_DOCS_COMMIT = "e2b66e4fce2fc130955912315167dc41e56956ad"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: pathlib.Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def j(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dumpj(p: pathlib.Path, obj) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V13E_OUTPUT_ALREADY_EXISTS {p}; preserve prior validation")
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(p)


def dumpjl(p: pathlib.Path, rows) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V13E_OUTPUT_ALREADY_EXISTS {p}; preserve prior validation")
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return sha(p)


def order_key(r: dict):
    return (
        int(r.get("block_time", 0)),
        int(r.get("slot", 0)),
        int(r.get("transaction_index", 0)),
        int(r.get("log_index", 0)),
    )


def expected_next_state(prev: dict, cur: dict) -> dict:
    pvs = int(prev["virtual_sol_reserves_raw"])
    pvt = int(prev["virtual_token_reserves_raw"])
    prs = int(prev["real_sol_reserves_raw"])
    prt = int(prev["real_token_reserves_raw"])
    sol = int(cur["sol_amount_raw"])
    tok = int(cur["token_amount_raw"])
    side = cur.get("side")
    if side == "buy":
        return {
            "virtual_sol_reserves_raw": pvs + sol,
            "virtual_token_reserves_raw": pvt - tok,
            "real_sol_reserves_raw": prs + sol,
            "real_token_reserves_raw": prt - tok,
        }
    if side == "sell":
        return {
            "virtual_sol_reserves_raw": pvs - sol,
            "virtual_token_reserves_raw": pvt + tok,
            "real_sol_reserves_raw": prs - sol,
            "real_token_reserves_raw": prt + tok,
        }
    raise RuntimeError(f"UNKNOWN_SIDE {side}")


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    cohort_p = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    events_p = here / "data" / "msel001_t5_forensics" / "trade_events_economic_v03.jsonl"
    v13d_p = here / "data" / "msel001_pilot25_executable_entry_v13d" / "executable_entry_audit_manifest_v13d.json"

    for p in (cohort_p, events_p, v13d_p):
        if not p.exists():
            raise RuntimeError(f"MISSING_INPUT {p}")
    if sha(cohort_p) != EXPECTED_COHORT_SHA:
        raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha(events_p) != EXPECTED_V03_EVENTS_SHA:
        raise RuntimeError("V03_EVENTS_HASH_MISMATCH")
    if sha(v13d_p) != EXPECTED_V13D_MANIFEST_SHA:
        raise RuntimeError("V13D_MANIFEST_HASH_MISMATCH")

    v13d = j(v13d_p)
    if v13d.get("candidate_status") != "CANDIDATE_CURVE_ENTRY_COVERAGE_PASS":
        raise RuntimeError("V13D_STATUS_MISMATCH")
    for k in ("future_raw_transactions_opened", "returns_computed", "labels_computed", "slice_statistics_computed", "verdict_computed"):
        if v13d.get(k) is not False:
            raise RuntimeError(f"V13D_OUTCOME_LOCK_FAILURE field={k}")

    cohort = jl(cohort_p)
    target = {r["mint"] for r in cohort}
    events = [r for r in jl(events_p) if r.get("mint") in target]
    if len(events) != EXPECTED_EVENTS:
        raise RuntimeError(f"EVENT_COUNT_MISMATCH {len(events)}/{EXPECTED_EVENTS}")

    by_mint = defaultdict(list)
    for r in events:
        by_mint[r["mint"]].append(r)
    if len(by_mint) != 25:
        raise RuntimeError(f"MINT_COVERAGE_MISMATCH {len(by_mint)}/25")

    checked = 0
    exact = 0
    mismatches = []
    side_counts = defaultdict(int)
    semantic_counts = defaultdict(int)

    for mint in sorted(by_mint):
        rows = sorted(by_mint[mint], key=order_key)
        for prev, cur in zip(rows, rows[1:]):
            checked += 1
            side_counts[str(cur.get("side"))] += 1
            semantic_counts[str(cur.get("semantic_class"))] += 1
            exp = expected_next_state(prev, cur)
            actual = {k: int(cur[k]) for k in exp}
            diffs = {k: actual[k] - exp[k] for k in exp}
            ok = all(v == 0 for v in diffs.values())
            if ok:
                exact += 1
            else:
                mismatches.append({
                    "mint": mint,
                    "prev_signature": prev.get("signature"),
                    "cur_signature": cur.get("signature"),
                    "cur_side": cur.get("side"),
                    "cur_semantic_class": cur.get("semantic_class"),
                    "prev_order": order_key(prev),
                    "cur_order": order_key(cur),
                    "expected": exp,
                    "actual": actual,
                    "diffs": diffs,
                })

    out = here / "data" / "msel001_pilot25_reserve_transition_v13e"
    mismatch_p = out / "reserve_transition_mismatches_v13e.jsonl"
    mismatch_sha = dumpjl(mismatch_p, mismatches)
    status = "PASS_EXACT_RESERVE_TRANSITIONS" if checked > 0 and exact == checked else "FAIL_RESERVE_TRANSITION_SEMANTICS"
    manifest = {
        "artifact": "MSEL_PILOT25_RESERVE_TRANSITION_VALIDATION_V13E",
        "pilot_only": True,
        "historical_docs_commit": HISTORICAL_DOCS_COMMIT,
        "source_cohort_sha256": EXPECTED_COHORT_SHA,
        "source_v03_trade_events_sha256": EXPECTED_V03_EVENTS_SHA,
        "source_v13d_manifest_sha256": EXPECTED_V13D_MANIFEST_SHA,
        "target_mints": len(by_mint),
        "trade_events": len(events),
        "consecutive_transitions_checked": checked,
        "exact_transitions": exact,
        "mismatch_count": len(mismatches),
        "side_counts": dict(sorted(side_counts.items())),
        "semantic_class_counts": dict(sorted(semantic_counts.items())),
        "mismatches_sha256": mismatch_sha,
        "status": status,
        "v12a_freeze_authorized": status == "PASS_EXACT_RESERVE_TRANSITIONS",
        "future_raw_transactions_opened": False,
        "returns_computed": False,
        "labels_computed": False,
        "slice_statistics_computed": False,
        "verdict_computed": False,
    }
    man_p = out / "reserve_transition_manifest_v13e.json"
    man_sha = dumpj(man_p, manifest)

    print("PASS: Pilot25 reserve-transition validation V13E complete")
    print(f"target mints: {len(by_mint)}/25")
    print(f"trade events: {len(events)}")
    print(f"consecutive reserve transitions checked: {checked}")
    print(f"exact reserve transitions: {exact}/{checked}")
    print(f"mismatches: {len(mismatches)}")
    print(f"side counts: {dict(sorted(side_counts.items()))}")
    print(f"manifest sha256: {man_sha}")
    print(f"status: {status}")
    if status == "PASS_EXACT_RESERVE_TRANSITIONS":
        print("V12A ENTRY-AUTHORITY FREEZE AUTHORIZED PRE-OUTCOME")
    else:
        print("V12A ENTRY-AUTHORITY FREEZE BLOCKED; RESERVE SEMANTICS REQUIRE RECONCILIATION")
    print("NO FUTURE RAW TRANSACTION DECODED")
    print("NO RETURNS OR LABELS COMPUTED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {type(exc).__name__}: {exc}")
        raise
