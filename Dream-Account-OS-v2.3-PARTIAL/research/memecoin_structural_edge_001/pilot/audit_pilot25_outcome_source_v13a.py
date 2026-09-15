#!/usr/bin/env python3
"""MSEL-001 Pilot25 V13 source integrity audit V13A.

LOCAL-ONLY / READ-ONLY WITH RESPECT TO RAW OUTCOME BYTES.

Purpose:
- verify an already-existing V13 outcome-source manifest and all referenced files;
- hash raw signature pages and raw transaction responses WITHOUT parsing trade outcomes;
- confirm source completeness and that returns/labels/slice statistics/verdict remain uncomputed;
- preserve the prior V13 run instead of overwriting it.

This script makes NO RPC calls and computes NO returns or labels.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any, Dict, List

EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V11_MANIFEST_SHA = "ceec26d445a91c3a89721cd5ef3e7b774bbff5a620659c91486202e99134bae8"
EXPECTED_V12_PREFLIGHT_SHA = "9765330662b9003eca790a51f201b4f05c7d1f9bfa66daef83d1d3c2007c781b"
EXPECTED_COVERAGE_ROWS = 25
VERSION = "MSEL_PILOT25_V13_SOURCE_INTEGRITY_AUDIT_V13A"


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: pathlib.Path) -> str:
    return sha_bytes(p.read_bytes())


def load_json(p: pathlib.Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def load_jsonl(p: pathlib.Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    out = here / "data" / "msel001_pilot25_outcome_source_v13"
    raw_pages = out / "raw_signature_pages"
    raw_txs = out / "raw_transactions"
    manifest_p = out / "outcome_source_manifest_v13.json"
    coverage_p = out / "mint_source_coverage_v13.jsonl"
    sig_index_p = out / "future_signature_index_v13.jsonl"
    receipts_p = out / "rpc_receipts_v13.jsonl"

    for p in (manifest_p, coverage_p, sig_index_p, receipts_p):
        if not p.exists():
            raise RuntimeError(f"V13_REQUIRED_ARTIFACT_MISSING {p}")

    manifest_sha = sha_file(manifest_p)
    m = load_json(manifest_p)

    if m.get("source_cohort_sha256") != EXPECTED_COHORT_SHA:
        raise RuntimeError("V13_SOURCE_COHORT_HASH_MISMATCH")
    if m.get("source_v11_manifest_sha256") != EXPECTED_V11_MANIFEST_SHA:
        raise RuntimeError("V13_SOURCE_V11_HASH_MISMATCH")
    if m.get("source_v12_preflight_sha256") != EXPECTED_V12_PREFLIGHT_SHA:
        raise RuntimeError("V13_SOURCE_V12_HASH_MISMATCH")
    if m.get("all_25_mint_histories_exhausted_to_create_boundary") is not True:
        raise RuntimeError("V13_HISTORY_COMPLETENESS_NOT_TRUE")
    if int(m.get("coverage_rows", -1)) != EXPECTED_COVERAGE_ROWS:
        raise RuntimeError(f"V13_COVERAGE_ROW_COUNT_FAILURE {m.get('coverage_rows')}")
    if m.get("outcome_source_bytes_acquired") is not True:
        raise RuntimeError("V13_SOURCE_BYTES_NOT_ACQUIRED")
    for flag in ("returns_computed", "labels_computed", "slice_statistics_computed", "verdict_computed"):
        if m.get(flag) is not False:
            raise RuntimeError(f"V13_PRE_EVALUATION_FLAG_FAILURE {flag}={m.get(flag)}")
    if m.get("live_trading") is not False or m.get("exchange_mutation") is not False:
        raise RuntimeError("V13_GOVERNANCE_FLAG_FAILURE")

    if sha_file(coverage_p) != m.get("mint_source_coverage_sha256"):
        raise RuntimeError("V13_COVERAGE_HASH_MISMATCH")
    if sha_file(sig_index_p) != m.get("future_signature_index_sha256"):
        raise RuntimeError("V13_SIGNATURE_INDEX_HASH_MISMATCH")
    if sha_file(receipts_p) != m.get("rpc_receipts_sha256"):
        raise RuntimeError("V13_RECEIPTS_HASH_MISMATCH")

    coverage = load_jsonl(coverage_p)
    sigs = load_jsonl(sig_index_p)
    receipts = load_jsonl(receipts_p)

    if len(coverage) != EXPECTED_COVERAGE_ROWS:
        raise RuntimeError(f"V13_COVERAGE_FILE_ROWS_FAILURE {len(coverage)}")
    if any(r.get("launch_boundary_exhausted") is not True for r in coverage):
        bad = [r.get("cohort_rank") for r in coverage if r.get("launch_boundary_exhausted") is not True]
        raise RuntimeError(f"V13_COVERAGE_BOUNDARY_FAILURE ranks={bad}")
    if len(sigs) != int(m.get("unique_future_signatures", -1)):
        raise RuntimeError(f"V13_SIGNATURE_COUNT_FAILURE {len(sigs)}/{m.get('unique_future_signatures')}")

    page_receipts = [r for r in receipts if r.get("method") == "getSignaturesForAddress"]
    tx_receipts = [r for r in receipts if r.get("method") == "getTransaction"]
    if len(page_receipts) != int(m.get("raw_signature_page_count", -1)):
        raise RuntimeError(f"V13_PAGE_RECEIPT_COUNT_FAILURE {len(page_receipts)}/{m.get('raw_signature_page_count')}")
    if len(tx_receipts) != int(m.get("raw_transaction_count", -1)):
        raise RuntimeError(f"V13_TX_RECEIPT_COUNT_FAILURE {len(tx_receipts)}/{m.get('raw_transaction_count')}")
    if len(sigs) != int(m.get("raw_transaction_count", -1)):
        raise RuntimeError(f"V13_SIG_TX_COUNT_FAILURE {len(sigs)}/{m.get('raw_transaction_count')}")

    checked_pages = 0
    checked_txs = 0
    for r in page_receipts:
        fn = r.get("raw_file")
        expected = r.get("response_sha256")
        if not fn or not expected:
            raise RuntimeError("V13_PAGE_RECEIPT_SHAPE_FAILURE")
        p = raw_pages / str(fn)
        if not p.exists():
            raise RuntimeError(f"V13_RAW_PAGE_MISSING {fn}")
        actual = sha_file(p)
        if actual != expected:
            raise RuntimeError(f"V13_RAW_PAGE_HASH_MISMATCH {fn}")
        checked_pages += 1

    tx_receipt_by_sig = {str(r.get("signature")): r for r in tx_receipts if r.get("signature")}
    if len(tx_receipt_by_sig) != len(tx_receipts):
        raise RuntimeError("V13_DUPLICATE_OR_MISSING_TX_RECEIPT_SIGNATURE")

    seen_sig = set()
    for row in sigs:
        sig = str(row.get("signature") or "")
        if not sig or sig in seen_sig:
            raise RuntimeError(f"V13_SIGNATURE_INDEX_DUPLICATE_OR_EMPTY {sig}")
        seen_sig.add(sig)
        fn = row.get("raw_transaction_file")
        expected = row.get("raw_transaction_sha256")
        if not fn or not expected:
            raise RuntimeError(f"V13_SIGNATURE_INDEX_TX_REF_FAILURE {sig}")
        p = raw_txs / str(fn)
        if not p.exists():
            raise RuntimeError(f"V13_RAW_TX_MISSING {fn}")
        actual = sha_file(p)
        if actual != expected:
            raise RuntimeError(f"V13_RAW_TX_HASH_MISMATCH {fn}")
        rr = tx_receipt_by_sig.get(sig)
        if rr is None:
            raise RuntimeError(f"V13_TX_RECEIPT_MISSING_FOR_SIG {sig}")
        if rr.get("raw_file") != fn or rr.get("response_sha256") != expected:
            raise RuntimeError(f"V13_TX_RECEIPT_RECONCILIATION_FAILURE {sig}")
        checked_txs += 1

    print("PASS: Pilot25 V13 source integrity audit V13A complete")
    print("existing V13 manifest preserved: YES")
    print(f"manifest sha256: {manifest_sha}")
    print(f"mint histories complete: {len(coverage)}/25")
    print(f"raw signature pages verified: {checked_pages}")
    print(f"unique future signatures sealed: {len(sigs)}")
    print(f"raw transactions verified: {checked_txs}")
    print(f"rpc calls recorded by V13: {m.get('rpc_calls')}")
    print("returns computed: FALSE")
    print("labels computed: FALSE")
    print("slice statistics computed: FALSE")
    print("verdict computed: FALSE")
    print("OUTCOME SOURCE BYTES ARE OPEN/SEALED; ECONOMIC EVALUATION NOT YET RUN")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        raise
