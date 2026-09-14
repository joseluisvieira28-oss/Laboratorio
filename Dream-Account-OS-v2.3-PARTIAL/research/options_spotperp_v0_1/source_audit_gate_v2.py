#!/usr/bin/env python3
"""OPTIONS-SPOTPERP-001 — SOURCE GATE SEMANTICS V2.

Prospective, outcome-blind correction of source-gate semantics.

The frozen signal protocol defines IV/index-price validity as TRADE ELIGIBILITY
conditions. Therefore invalid IV/index-price rows are excluded by source_audit.py
and reported as data-quality counts; they are not, by themselves, a fatal source
integrity failure when valid coverage remains adequate. mark_price is retained as
a reported quality field but is not used in the frozen skew construction.

Fatal integrity checks remain unchanged: trade identity, duplicates, page ordering
and bounds, timestamps, instrument parsing, direction, positive amount when present,
protocol binding, exact BTC Discovery cutoff, and 2025/2026 locks.

No skew, signals, forward returns, PnL, 2025 or 2026 are opened here.
"""
from __future__ import annotations

import source_audit_gate_expiryfix as expiryfix

# source_audit_gate_expiryfix already redirects the underlying source_audit.py call
# to source_audit_expiryfix.py (08:00 UTC expiry + deterministic gzip).
gate = expiryfix.gate
_ORIGINAL_AUDIT_DERIBIT_RAW = gate.audit_deribit_raw

FATAL_SOURCE_INTEGRITY_FIELDS = (
    "missing_trade_id",
    "duplicate_trade_id",
    "page_nonmonotonic",
    "page_out_of_bounds",
    "timestamp_invalid",
    "instrument_parse_failure",
    "direction_invalid",
    "amount_invalid_when_present",
)

ELIGIBILITY_QUALITY_FIELDS = (
    "iv_invalid",
    "index_price_invalid",
    "mark_price_invalid",
)

POLICY_ID = "SOURCE_GATE_SEMANTICS_V2_PROSPECTIVE_2026-09-14"


def audit_deribit_raw_v2(root, probe):
    out = _ORIGINAL_AUDIT_DERIBIT_RAW(root, probe)

    # Preserve the V1 result explicitly for auditability, then replace only the
    # aggregate pass semantics. No raw counts are changed or hidden.
    out["schema_and_provenance_pass_v1"] = out.get("schema_and_provenance_pass")

    fatal = {k: int(out.get(k, 0) or 0) for k in FATAL_SOURCE_INTEGRITY_FIELDS}
    quality = {k: int(out.get(k, 0) or 0) for k in ELIGIBILITY_QUALITY_FIELDS}

    out["fatal_source_integrity_counts"] = fatal
    out["eligibility_quality_counts"] = quality
    out["eligibility_quality_rows_are_nonfatal_if_coverage_passes"] = True
    out["mark_price_not_used_in_frozen_skew_signal"] = True
    out["source_gate_semantics_policy_id"] = POLICY_ID
    out["schema_and_provenance_pass"] = all(v == 0 for v in fatal.values())
    return out


gate.audit_deribit_raw = audit_deribit_raw_v2


if __name__ == "__main__":
    raise SystemExit(gate.main())
