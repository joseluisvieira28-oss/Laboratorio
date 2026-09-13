#!/usr/bin/env python3
"""Outcome-blind unit checks for the authority-reconciled Options source gate."""

from source_audit_gate_authority_reconciled_v01 import reclassify_raw_audit


def sample(**overrides):
    x = {
        "missing_trade_id": 0,
        "duplicate_trade_id": 0,
        "page_nonmonotonic": 0,
        "page_out_of_bounds": 0,
        "timestamp_invalid": 0,
        "instrument_parse_failure": 0,
        "direction_invalid": 0,
        "amount_invalid_when_present": 0,
        "iv_invalid": 0,
        "index_price_invalid": 0,
        "mark_price_invalid": 0,
    }
    x.update(overrides)
    return x


def main():
    # Eligibility-value rejections are disclosed, not converted into structural fail.
    a = reclassify_raw_audit(sample(iv_invalid=32, mark_price_invalid=2))
    assert a["schema_and_provenance_pass"] is True
    assert a["eligibility_value_rejections"] == {
        "iv_invalid": 32,
        "index_price_invalid": 0,
        "mark_price_invalid": 2,
    }

    # Every actual source/provenance violation remains fail-closed.
    for key in a["structural_hard_zero_fields"]:
        b = reclassify_raw_audit(sample(**{key: 1}))
        assert b["schema_and_provenance_pass"] is False, key

    print("AUTHORITY_RECONCILIATION_TESTS_PASS")
    print("NO OUTCOMES / NO SKEW / NO RETURNS / NO PNL")


if __name__ == "__main__":
    main()
