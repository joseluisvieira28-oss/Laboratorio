#!/usr/bin/env python3
"""Blind no-network preflight for SOURCE GATE SEMANTICS V2."""
from __future__ import annotations

import source_audit_gate_v2 as v2


def base_result():
    d = {k: 0 for k in v2.FATAL_SOURCE_INTEGRITY_FIELDS}
    d.update({k: 0 for k in v2.ELIGIBILITY_QUALITY_FIELDS})
    d.update({
        "schema_and_provenance_pass": True,
        "underlying_source_status": "SOURCE_AUDIT_PASS",
        "underlying_valid_signal_coverage_days": 1212,
        "underlying_min_required_valid_days": 500,
        "underlying_probe_mode": False,
        "outcomes_computed": False,
    })
    return d


# Case 1: eligibility-quality defects must remain visible but nonfatal.
case1 = base_result()
case1["iv_invalid"] = 35088
case1["mark_price_invalid"] = 8087
v2._ORIGINAL_AUDIT_DERIBIT_RAW = lambda root, probe: dict(case1)
r1 = v2.audit_deribit_raw_v2(None, False)
assert r1["schema_and_provenance_pass"] is True
assert r1["eligibility_quality_counts"]["iv_invalid"] == 35088
assert r1["eligibility_quality_counts"]["mark_price_invalid"] == 8087
assert r1["schema_and_provenance_pass_v1"] is True

# Case 2: index-price invalidity is an eligibility exclusion, not a lab-fatal blocker.
case2 = base_result()
case2["index_price_invalid"] = 17
v2._ORIGINAL_AUDIT_DERIBIT_RAW = lambda root, probe: dict(case2)
r2 = v2.audit_deribit_raw_v2(None, False)
assert r2["schema_and_provenance_pass"] is True

# Case 3: duplicate identity remains fatal.
case3 = base_result()
case3["duplicate_trade_id"] = 1
v2._ORIGINAL_AUDIT_DERIBIT_RAW = lambda root, probe: dict(case3)
r3 = v2.audit_deribit_raw_v2(None, False)
assert r3["schema_and_provenance_pass"] is False

# Case 4: timestamp boundary/provenance remains fatal.
case4 = base_result()
case4["page_out_of_bounds"] = 1
v2._ORIGINAL_AUDIT_DERIBIT_RAW = lambda root, probe: dict(case4)
r4 = v2.audit_deribit_raw_v2(None, False)
assert r4["schema_and_provenance_pass"] is False

assert v2.POLICY_ID == "SOURCE_GATE_SEMANTICS_V2_PROSPECTIVE_2026-09-14"
print("SOURCE_GATE_SEMANTICS_V2_PREFLIGHT_PASS")
print("ELIGIBILITY QUALITY != FATAL SOURCE INTEGRITY")
print("NO NETWORK | NO SKEW | NO SIGNALS | NO RETURNS | NO PNL | 2025 LOCKED | 2026 LOCKED")
