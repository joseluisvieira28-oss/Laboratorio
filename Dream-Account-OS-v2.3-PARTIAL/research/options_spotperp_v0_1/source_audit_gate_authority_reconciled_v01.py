#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001 V0.1 — authority-reconciled final source/data gate.

Implementation-only correction layered over source_audit_gate.py.

Why this exists:
- The frozen signal eligibility rule accepts only rows with finite positive trade IV
  and index_price, then decides data adequacy via the frozen >=500 valid-day gate.
- The source-audit checklist records mark_price as "when present" and does not use it
  in signal construction.
- The first final wrapper counted invalid raw IV/index/mark values correctly but made
  any such raw row a structural/provenance failure. That was stricter than the frozen
  eligibility semantics and could turn ordinary rejected source rows into a false
  SOURCE_AUDIT_BLOCKED verdict.

This wrapper changes NO research parameter, bucket, DTE, date, source, aggregation,
coverage threshold, outcome rule, cost, or pass criterion. It computes NO skew,
signal, return, or PnL. 2025 and 2026 remain locked.
"""

from __future__ import annotations

from typing import Any

import source_audit_gate as base


# These are source/provenance integrity failures. Every one must remain zero.
STRUCTURAL_HARD_ZERO = (
    "missing_trade_id",
    "duplicate_trade_id",
    "page_nonmonotonic",
    "page_out_of_bounds",
    "timestamp_invalid",
    "instrument_parse_failure",
    "direction_invalid",
    "amount_invalid_when_present",
)

# These are counted and disclosed, but invalid IV/index rows are already rejected by
# source_audit.py before eligibility/coverage accumulation. mark_price is not used in
# the frozen signal. They therefore cannot by themselves override the frozen coverage
# gate into a provenance failure.
ELIGIBILITY_VALUE_REJECTION_COUNTERS = (
    "iv_invalid",
    "index_price_invalid",
    "mark_price_invalid",
)


def reclassify_raw_audit(audit: dict[str, Any]) -> dict[str, Any]:
    out = dict(audit)
    out["structural_hard_zero_fields"] = list(STRUCTURAL_HARD_ZERO)
    out["eligibility_value_rejection_fields"] = list(
        ELIGIBILITY_VALUE_REJECTION_COUNTERS
    )
    out["eligibility_value_rejections"] = {
        key: int(out.get(key, 0) or 0)
        for key in ELIGIBILITY_VALUE_REJECTION_COUNTERS
    }
    out["schema_and_provenance_pass"] = all(
        int(out.get(key, 0) or 0) == 0 for key in STRUCTURAL_HARD_ZERO
    )
    out["authority_reconciliation"] = (
        "Invalid IV/index rows remain rejected before frozen eligibility coverage; "
        "mark_price is audited but is not a frozen signal input. No threshold or "
        "research parameter changed."
    )
    return out


def audit_deribit_raw_reconciled(root, probe):
    return reclassify_raw_audit(base._ORIGINAL_AUDIT_DERIBIT_RAW(root, probe))


def main() -> int:
    # Preserve the original implementation for the patched wrapper and make the
    # correction explicit rather than silently editing scientific logic.
    if not hasattr(base, "_ORIGINAL_AUDIT_DERIBIT_RAW"):
        base._ORIGINAL_AUDIT_DERIBIT_RAW = base.audit_deribit_raw
    base.audit_deribit_raw = audit_deribit_raw_reconciled
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
