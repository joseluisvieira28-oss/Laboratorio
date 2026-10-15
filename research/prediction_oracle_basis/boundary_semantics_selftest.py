#!/usr/bin/env python3
"""Synthetic boundary semantics test for POB hourly strike pairs.

No network, quotes, outcomes, credentials, PnL or economic outputs.
"""

from decimal import Decimal
import json
from pathlib import Path

OUT = Path("artifacts/prediction_oracle_basis/synthetic_safety")
NOMINAL = Decimal("67000.00")
KALSHI_ENCODED = NOMINAL - Decimal("0.01")


def poly_yes(reference: Decimal) -> bool:
    # Frozen authority: strict > nominal strike.
    return reference > NOMINAL


def kalshi_yes(reference: Decimal) -> bool:
    # Frozen authority: encoded threshold one cent below displayed nominal strike.
    return reference > KALSHI_ENCODED


def main() -> int:
    cases = [
        ("one_cent_below", Decimal("66999.99"), False, False),
        ("exact_nominal", Decimal("67000.00"), False, True),
        ("one_cent_above", Decimal("67000.01"), True, True),
    ]

    results = []
    ok = True
    for name, ref, expected_poly, expected_kalshi in cases:
        p = poly_yes(ref)
        k = kalshi_yes(ref)
        case_ok = (p == expected_poly) and (k == expected_kalshi)
        ok = ok and case_ok
        results.append({
            "case": name,
            "reference": str(ref),
            "poly_yes": p,
            "kalshi_yes": k,
            "expected_poly_yes": expected_poly,
            "expected_kalshi_yes": expected_kalshi,
            "pass": case_ok,
        })

    exact_nominal = next(x for x in results if x["case"] == "exact_nominal")
    mismatch_preserved = exact_nominal["poly_yes"] != exact_nominal["kalshi_yes"]
    ok = ok and mismatch_preserved

    receipt = {
        "schema": "POB_BOUNDARY_SEMANTICS_SELFTEST_V0.1",
        "classification": "BOUNDARY_SEMANTICS_SELF_TEST_PASS" if ok else "BOUNDARY_SEMANTICS_SELF_TEST_FAIL",
        "nominal_strike": str(NOMINAL),
        "kalshi_encoded_threshold": str(KALSHI_ENCODED),
        "one_cent_boundary_mismatch_at_exact_nominal_preserved": mismatch_preserved,
        "classification_must_not_be_exact_except_oracle": True,
        "required_pair_classification": "MATCHED_HOURLY_STRIKE_TIME_REFERENCE_DIFF_TIE_1C",
        "synthetic_only": True,
        "network_requests": False,
        "market_quotes_compared": False,
        "matured_outcomes_read": False,
        "economic_outputs_computed": False,
        "orders": False,
        "cases": results,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "boundary_semantics_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
