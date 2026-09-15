#!/usr/bin/env python3
"""MSEL-001 Pilot25 pre-evaluation input binder V13B.

LOCAL-ONLY / RESEARCH-ONLY / NO OUTCOME DECODING.

Purpose:
- bind the exact pre-outcome feature authority (V11), outcome schema (V12),
  sealed future-source manifest (V13), and pre-T+5 Pump execution source (V03)
  before any future transaction is decoded into returns or labels;
- freeze the historical PumpSwap May-2025 event/discriminator authority;
- write a deterministic binding artifact for V14.

This script deliberately does NOT open raw future transactions, compute prices,
returns, labels, slice statistics, or a verdict.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

EXPECTED_V11_MANIFEST_SHA = "ceec26d445a91c3a89721cd5ef3e7b774bbff5a620659c91486202e99134bae8"
EXPECTED_V11_MATRIX_SHA = "226c64d9683702e81c5f2b2b871b4d8971e761914c999a0d2e6c257328005d72"
EXPECTED_V11_RISK_SHA = "5857267a7d0203fa0e8e70eeafc34017d225a84a7809c97accce8bbb76f7fb8e"
EXPECTED_V12_PREFLIGHT_SHA = "9765330662b9003eca790a51f201b4f05c7d1f9bfa66daef83d1d3c2007c781b"
EXPECTED_V13_MANIFEST_SHA = "f2101ff97eb995f8f1df66ed9d11dd46b4bc24d558e67139b74df53a2a00cdde"
EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_PUMP_TRADE_EVENTS = 1081

HISTORICAL_IDL_COMMIT = "e2b66e4fce2fc130955912315167dc41e56956ad"
HISTORICAL_PUMPSWAP_IDL_BLOB = "7a1cf37270f6015f5af53b9ce58d8a6890254020"
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMPSWAP_PROGRAM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
WSOL_MINT = "So11111111111111111111111111111111111111112"
PUMP_MIGRATE_DISC = [155, 234, 231, 146, 236, 158, 162, 30]
PUMPSWAP_BUY_EVENT_DISC = [103, 244, 82, 31, 44, 245, 119, 119]
PUMPSWAP_SELL_EVENT_DISC = [62, 47, 55, 10, 165, 3, 220, 42]
PUMPSWAP_CREATE_POOL_EVENT_DISC = [177, 49, 12, 210, 160, 118, 167, 116]
PUMPSWAP_TRADE_EVENT_LEN = 360
PUMPSWAP_CREATE_POOL_EVENT_LEN = 333


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def j(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def jl(p: pathlib.Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def write_json(p: pathlib.Path, obj) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V13B_BINDING_ALREADY_EXISTS {p}; preserve prior binding")
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(p)


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    cohort_p = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    d11 = here / "data" / "msel001_pilot25_feature_v11"
    v11_manifest_p = d11 / "pilot25_feature_manifest_v11.json"
    v11_matrix_p = d11 / "pilot25_feature_matrix_v11.jsonl"
    v11_risk_p = d11 / "pilot25_primary_risk_order_v11.jsonl"
    v12_p = d11 / "pilot25_outcome_preflight_v12.json"
    d13 = here / "data" / "msel001_pilot25_outcome_source_v13"
    v13_manifest_p = d13 / "outcome_source_manifest_v13.json"
    d03 = here / "data" / "msel001_t5_forensics"
    v03_manifest_p = d03 / "economic_manifest_v03.json"
    v03_events_p = d03 / "trade_events_economic_v03.jsonl"

    required = [cohort_p, v11_manifest_p, v11_matrix_p, v11_risk_p, v12_p,
                v13_manifest_p, v03_manifest_p, v03_events_p]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"MISSING_BINDING_INPUTS {missing}")

    exact = {
        cohort_p: EXPECTED_COHORT_SHA,
        v11_manifest_p: EXPECTED_V11_MANIFEST_SHA,
        v11_matrix_p: EXPECTED_V11_MATRIX_SHA,
        v11_risk_p: EXPECTED_V11_RISK_SHA,
        v12_p: EXPECTED_V12_PREFLIGHT_SHA,
        v13_manifest_p: EXPECTED_V13_MANIFEST_SHA,
    }
    for p, expected in exact.items():
        actual = sha(p)
        if actual != expected:
            raise RuntimeError(f"EXACT_HASH_MISMATCH file={p.name} expected={expected} actual={actual}")

    v11 = j(v11_manifest_p)
    v12 = j(v12_p)
    v13 = j(v13_manifest_p)
    v03 = j(v03_manifest_p)

    if v11.get("outcomes_opened") is not False:
        raise RuntimeError("V11_OUTCOME_LOCK_FAILURE")
    if v12.get("outcomes_opened") is not False:
        raise RuntimeError("V12_OUTCOME_LOCK_FAILURE")
    if v13.get("returns_computed") is not False or v13.get("labels_computed") is not False:
        raise RuntimeError("V13_PRE_EVALUATION_STATE_FAILURE")
    if v13.get("slice_statistics_computed") is not False or v13.get("verdict_computed") is not False:
        raise RuntimeError("V13_PRE_EVALUATION_STATE_FAILURE")
    if v13.get("all_25_mint_histories_exhausted_to_create_boundary") is not True:
        raise RuntimeError("V13_SOURCE_COVERAGE_FAILURE")
    if int(v13.get("coverage_rows", 0)) != 25 or int(v13.get("raw_transaction_count", -1)) != 904:
        raise RuntimeError("V13_SHAPE_FAILURE")

    if v03.get("artifact") != "MSEL_TRADE_EVENT_ECONOMIC_V03":
        raise RuntimeError("V03_ARTIFACT_MISMATCH")
    if v03.get("outcomes_opened") is not False:
        raise RuntimeError("V03_OUTCOME_LOCK_FAILURE")
    if int(v03.get("trade_events_reconciled", -1)) != EXPECTED_PUMP_TRADE_EVENTS:
        raise RuntimeError("V03_TRADE_COUNT_FAILURE")
    v03_events_sha = sha(v03_events_p)
    if v03.get("trade_events_economic_v03_sha256") != v03_events_sha:
        raise RuntimeError("V03_EVENT_HASH_RECONCILIATION_FAILURE")
    v03_rows = jl(v03_events_p)
    if len(v03_rows) != EXPECTED_PUMP_TRADE_EVENTS:
        raise RuntimeError("V03_EVENT_ROW_COUNT_FAILURE")

    # Pre-outcome-only diagnostic: candidate entry rows are historical <=T+5 data.
    cohort = {r["mint"]: r for r in jl(cohort_p)}
    eligible_entry_rows = 0
    mints_with_eligible_pump_entry = set()
    for r in v03_rows:
        mint = r.get("mint")
        if mint not in cohort:
            continue
        decision = int(cohort[mint]["block_time"]) + 300
        bt = int(r["block_time"])
        if (r.get("side") == "buy" and r.get("semantic_class") == "ECONOMIC_BUY_CANDIDATE"
                and decision - 60 <= bt <= decision and int(r.get("sol_amount_raw", 0)) >= 10_000_000):
            eligible_entry_rows += 1
            mints_with_eligible_pump_entry.add(mint)

    binding = {
        "artifact": "MSEL_PILOT25_OUTCOME_INPUT_BINDING_V13B",
        "pilot_only": True,
        "full_mve_verdict_authorized": False,
        "source_cohort_sha256": EXPECTED_COHORT_SHA,
        "source_v11_manifest_sha256": EXPECTED_V11_MANIFEST_SHA,
        "source_v11_matrix_sha256": EXPECTED_V11_MATRIX_SHA,
        "source_v11_risk_order_sha256": EXPECTED_V11_RISK_SHA,
        "source_v12_preflight_sha256": EXPECTED_V12_PREFLIGHT_SHA,
        "source_v13_manifest_sha256": EXPECTED_V13_MANIFEST_SHA,
        "source_v03_manifest_sha256": sha(v03_manifest_p),
        "source_v03_trade_events_sha256": v03_events_sha,
        "source_v03_trade_events_rows": len(v03_rows),
        "pre_outcome_eligible_pump_entry_rows": eligible_entry_rows,
        "pre_outcome_mints_with_eligible_pump_entry": len(mints_with_eligible_pump_entry),
        "historical_idl_commit": HISTORICAL_IDL_COMMIT,
        "historical_pumpswap_idl_git_blob": HISTORICAL_PUMPSWAP_IDL_BLOB,
        "pump_program": PUMP_PROGRAM,
        "pumpswap_program": PUMPSWAP_PROGRAM,
        "required_quote_mint": WSOL_MINT,
        "pump_migrate_discriminator": PUMP_MIGRATE_DISC,
        "pumpswap_buy_event_discriminator": PUMPSWAP_BUY_EVENT_DISC,
        "pumpswap_sell_event_discriminator": PUMPSWAP_SELL_EVENT_DISC,
        "pumpswap_create_pool_event_discriminator": PUMPSWAP_CREATE_POOL_EVENT_DISC,
        "pumpswap_trade_event_encoded_length": PUMPSWAP_TRADE_EVENT_LEN,
        "pumpswap_create_pool_event_encoded_length": PUMPSWAP_CREATE_POOL_EVENT_LEN,
        "canonical_pool_rule": "same-successful-tx Pump migrate + historical PumpSwap CreatePoolEvent; target base mint; WSOL quote",
        "future_raw_transactions_opened_by_binder": False,
        "returns_computed": False,
        "labels_computed": False,
        "slice_statistics_computed": False,
        "verdict_computed": False,
    }

    out = here / "data" / "msel001_pilot25_outcome_binding_v13b" / "outcome_input_binding_v13b.json"
    bsha = write_json(out, binding)

    print("PASS: Pilot25 pre-evaluation input binding V13B complete")
    print(f"V03 manifest sha256: {binding['source_v03_manifest_sha256']}")
    print(f"V03 trade-events sha256: {v03_events_sha}")
    print(f"pre-outcome eligible Pump entry rows: {eligible_entry_rows}")
    print(f"pre-outcome mints with eligible Pump entry: {len(mints_with_eligible_pump_entry)}/25")
    print(f"V13 sealed manifest sha256: {EXPECTED_V13_MANIFEST_SHA}")
    print(f"binding sha256: {bsha}")
    print("NO FUTURE RAW TRANSACTION DECODED")
    print("NO RETURNS OR LABELS COMPUTED")
    print("READY FOR V14 ECONOMIC EVALUATION")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        raise
