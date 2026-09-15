#!/usr/bin/env python3
"""MSEL-001 Pilot25 V14 input binder V13F.

LOCAL-ONLY / RESEARCH-ONLY / FAIL-CLOSED.

Purpose:
- bind the exact pre-economic-evaluation authorities after the V12A entry-source amendment;
- verify that the V12A amendment is supported by V13D/V13E and that V13 future source remains sealed;
- do NOT open any V13 raw future transaction;
- authorize V14 Pilot25 economic evaluation only if every frozen hash/state matches.

This binder does not compute prices, returns, labels, slice statistics, or a verdict.

Technical note:
- repository Markdown authority is hashed in canonical LF-normalized UTF-8 form so
  Windows CRLF working-tree conversion cannot create a false scientific mismatch;
- generated local data artefacts retain exact byte-level hashing.
"""
from __future__ import annotations
import hashlib
import json
import pathlib

EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V11_MANIFEST_SHA = "ceec26d445a91c3a89721cd5ef3e7b774bbff5a620659c91486202e99134bae8"
EXPECTED_V11_MATRIX_SHA = "226c64d9683702e81c5f2b2b871b4d8971e761914c999a0d2e6c257328005d72"
EXPECTED_V11_RISK_SHA = "5857267a7d0203fa0e8e70eeafc34017d225a84a7809c97accce8bbb76f7fb8e"
EXPECTED_V12_PREFLIGHT_SHA = "9765330662b9003eca790a51f201b4f05c7d1f9bfa66daef83d1d3c2007c781b"
EXPECTED_V12A_DOC_SHA = "e8d319c6b5f89d99ac9265a9e4ec23b7cf5f87160dd27fdee4abce6d8e112aa7"
EXPECTED_V13_MANIFEST_SHA = "f2101ff97eb995f8f1df66ed9d11dd46b4bc24d558e67139b74df53a2a00cdde"
EXPECTED_V13D_MANIFEST_SHA = "0be1742b64425a1e2f5b4e15ad58ec0b4468af6d79b064f71579ad16d72c55e6"
EXPECTED_V13E_MANIFEST_SHA = "95a308535275680d16f5b5ddeff3f14d582b9d33838ba0ae9b7715c84288971f"
EXPECTED_FUTURE_TX = 904
EXPECTED_ENTRY_COVERAGE = 25

def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def canonical_lf_sha(p: pathlib.Path) -> str:
    # read_text uses universal-newline translation; re-encoding therefore hashes
    # the canonical LF text regardless of CRLF materialization in a Windows checkout.
    text = p.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def j(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))

def write_json(p: pathlib.Path, obj) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise RuntimeError(f"V13F_BINDING_ALREADY_EXISTS {p}; preserve prior binding")
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha(p)

def exact(p, expected, label):
    actual = sha(p)
    if actual != expected:
        raise RuntimeError(f"{label}_HASH_MISMATCH expected={expected} actual={actual}")

def exact_canonical_text_lf(p, expected, label):
    actual = canonical_lf_sha(p)
    if actual != expected:
        raise RuntimeError(f"{label}_CANONICAL_LF_HASH_MISMATCH expected={expected} actual={actual}")

def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    root = here.parent

    cohort_p = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    d11 = here / "data" / "msel001_pilot25_feature_v11"
    v11m_p = d11 / "pilot25_feature_manifest_v11.json"
    v11x_p = d11 / "pilot25_feature_matrix_v11.jsonl"
    v11r_p = d11 / "pilot25_primary_risk_order_v11.jsonl"
    v12_p = d11 / "pilot25_outcome_preflight_v12.json"
    v12a_p = root / "PILOT25_ENTRY_AUTHORITY_AMENDMENT_V12A.md"
    v13_p = here / "data" / "msel001_pilot25_outcome_source_v13" / "outcome_source_manifest_v13.json"
    v13d_p = here / "data" / "msel001_pilot25_executable_entry_v13d" / "executable_entry_audit_manifest_v13d.json"
    v13e_p = here / "data" / "msel001_pilot25_reserve_transition_v13e" / "reserve_transition_manifest_v13e.json"

    required = (cohort_p, v11m_p, v11x_p, v11r_p, v12_p, v12a_p, v13_p, v13d_p, v13e_p)
    for p in required:
        if not p.exists():
            raise RuntimeError(f"MISSING_INPUT {p}")

    exact(cohort_p, EXPECTED_COHORT_SHA, "COHORT")
    exact(v11m_p, EXPECTED_V11_MANIFEST_SHA, "V11_MANIFEST")
    exact(v11x_p, EXPECTED_V11_MATRIX_SHA, "V11_MATRIX")
    exact(v11r_p, EXPECTED_V11_RISK_SHA, "V11_RISK")
    exact(v12_p, EXPECTED_V12_PREFLIGHT_SHA, "V12_PREFLIGHT")
    exact_canonical_text_lf(v12a_p, EXPECTED_V12A_DOC_SHA, "V12A_DOC")
    exact(v13_p, EXPECTED_V13_MANIFEST_SHA, "V13_MANIFEST")
    exact(v13d_p, EXPECTED_V13D_MANIFEST_SHA, "V13D_MANIFEST")
    exact(v13e_p, EXPECTED_V13E_MANIFEST_SHA, "V13E_MANIFEST")

    v11 = j(v11m_p)
    v12 = j(v12_p)
    v13 = j(v13_p)
    v13d = j(v13d_p)
    v13e = j(v13e_p)

    if v11.get("outcomes_opened") is not False or v12.get("outcomes_opened") is not False:
        raise RuntimeError("PRE_EVALUATION_FEATURE_OR_SCHEMA_LOCK_FAILURE")
    for k in ("returns_computed", "labels_computed", "slice_statistics_computed", "verdict_computed"):
        if v13.get(k) is not False:
            raise RuntimeError(f"V13_ECONOMIC_STATE_ALREADY_OPEN field={k}")
    if v13.get("all_25_mint_histories_exhausted_to_create_boundary") is not True:
        raise RuntimeError("V13_SOURCE_COMPLETENESS_FAILURE")
    if int(v13.get("coverage_rows", 0)) != 25 or int(v13.get("raw_transaction_count", -1)) != EXPECTED_FUTURE_TX:
        raise RuntimeError("V13_SOURCE_SHAPE_FAILURE")

    if v13d.get("candidate_status") != "CANDIDATE_CURVE_ENTRY_COVERAGE_PASS":
        raise RuntimeError("V13D_STATUS_FAILURE")
    if int(v13d.get("candidate_curve_quote_coverage_mints", -1)) != EXPECTED_ENTRY_COVERAGE:
        raise RuntimeError("V13D_ENTRY_COVERAGE_FAILURE")
    if int(v13d.get("zero_real_token_reserve_states", -1)) != 0:
        raise RuntimeError("V13D_COMPLETED_CURVE_FAILURE")
    for k in ("future_raw_transactions_opened", "returns_computed", "labels_computed", "slice_statistics_computed", "verdict_computed"):
        if v13d.get(k) is not False:
            raise RuntimeError(f"V13D_OUTCOME_LOCK_FAILURE field={k}")

    if v13e.get("status") != "PASS_EXACT_RESERVE_TRANSITIONS":
        raise RuntimeError("V13E_STATUS_FAILURE")
    if int(v13e.get("mismatch_count", -1)) != 0 or int(v13e.get("exact_transitions", -1)) != int(v13e.get("consecutive_transitions_checked", -2)):
        raise RuntimeError("V13E_RESERVE_RECONCILIATION_FAILURE")
    if v13e.get("v12a_freeze_authorized") is not True:
        raise RuntimeError("V13E_V12A_AUTHORIZATION_FAILURE")
    for k in ("future_raw_transactions_opened", "returns_computed", "labels_computed", "slice_statistics_computed", "verdict_computed"):
        if v13e.get(k) is not False:
            raise RuntimeError(f"V13E_OUTCOME_LOCK_FAILURE field={k}")

    v12a_local_raw_sha = sha(v12a_p)
    v12a_canonical_sha = canonical_lf_sha(v12a_p)

    binding = {
        "artifact": "MSEL_PILOT25_V14_INPUT_BINDING_V13F",
        "pilot_only": True,
        "full_mve_verdict_authorized": False,
        "source_cohort_sha256": EXPECTED_COHORT_SHA,
        "source_v11_manifest_sha256": EXPECTED_V11_MANIFEST_SHA,
        "source_v11_matrix_sha256": EXPECTED_V11_MATRIX_SHA,
        "source_v11_risk_order_sha256": EXPECTED_V11_RISK_SHA,
        "source_v12_preflight_sha256": EXPECTED_V12_PREFLIGHT_SHA,
        "source_v12a_document_sha256": EXPECTED_V12A_DOC_SHA,
        "source_v12a_document_canonical_lf_sha256": v12a_canonical_sha,
        "source_v12a_document_local_bytes_sha256": v12a_local_raw_sha,
        "source_v13_manifest_sha256": EXPECTED_V13_MANIFEST_SHA,
        "source_v13d_manifest_sha256": EXPECTED_V13D_MANIFEST_SHA,
        "source_v13e_manifest_sha256": EXPECTED_V13E_MANIFEST_SHA,
        "entry_authority": "V12A_T5_PUMP_CURVE_GROSS_0.01_SOL",
        "entry_gross_lamports": 10000000,
        "entry_coverage_mints": 25,
        "future_raw_transactions_sealed": EXPECTED_FUTURE_TX,
        "future_raw_transactions_opened_by_binder": False,
        "returns_computed": False,
        "labels_computed": False,
        "slice_statistics_computed": False,
        "verdict_computed": False,
        "v14_pilot_economic_evaluation_authorized": True,
    }

    out = here / "data" / "msel001_pilot25_v14_binding_v13f" / "v14_input_binding_v13f.json"
    bsha = write_json(out, binding)

    print("PASS: Pilot25 V14 input binding V13F complete")
    print("entry authority: V12A T+5 Pump curve gross 0.01 SOL")
    print("entry coverage: 25/25")
    print(f"sealed future transactions: {EXPECTED_FUTURE_TX}")
    print(f"V12A canonical-LF sha256: {v12a_canonical_sha}")
    print(f"V12A local-byte sha256: {v12a_local_raw_sha}")
    print(f"V13D manifest sha256: {EXPECTED_V13D_MANIFEST_SHA}")
    print(f"V13E manifest sha256: {EXPECTED_V13E_MANIFEST_SHA}")
    print(f"binding sha256: {bsha}")
    print("NO FUTURE RAW TRANSACTION DECODED")
    print("NO RETURNS OR LABELS COMPUTED")
    print("V14 PILOT ECONOMIC EVALUATION AUTHORIZED")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {type(exc).__name__}: {exc}")
        raise
