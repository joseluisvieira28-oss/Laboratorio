"""Outcome-blind contiguous coverage materializer for Cross-Venue Funding & Basis Lab.

Consumes only the V0.3 slot-occupancy receipt. It does not fetch market data and never
reads or summarizes funding-rate values. It freezes one continuous common-complete
replication partition ending 2025-12, with no interpolation across missing settlements.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
MATERIALIZER_ID = "CROSS_VENUE_FUNDING_BASIS_COVERAGE_MATERIALIZER_V04"
EXPECTED_SERIES = {
    "BINANCE_BTCUSDT",
    "BINANCE_ETHUSDT",
    "HYPERLIQUID_BTC",
    "HYPERLIQUID_ETH",
}
END_MONTH = "2025-12"


class CoverageFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CoverageFailure(message)


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def month_keys() -> list[str]:
    out: list[str] = []
    y, m = 2023, 1
    while (y, m) <= (2025, 12):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out


def validate_v03(v03: dict[str, Any]) -> None:
    require(v03.get("lab_id") == LAB_ID, "unexpected lab id")
    require(v03.get("diagnostic_id") == "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03", "unexpected V0.3 diagnostic")
    require(v03.get("status") == "DIAGNOSTIC_COMPLETE", "V0.3 incomplete")
    require(v03.get("classification") == "SLOT_OCCUPANCY_PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY", "unexpected V0.3 classification")
    for key in (
        "locked_2026_accessed",
        "mexc_accessed",
        "authenticated_account_data_used",
        "exchange_mutation_used",
        "funding_rate_values_summarized",
        "carry_computed",
        "apr_apy_computed",
        "pnl_computed",
        "signals_computed",
    ):
        require(v03.get(key) is False, f"V0.3 boundary marker not false: {key}")
    require(set(v03.get("series", {})) == EXPECTED_SERIES, "unexpected series set")


def materialize(v03: dict[str, Any]) -> dict[str, Any]:
    validate_v03(v03)
    months = month_keys()
    require(END_MONTH in months, "end month outside frozen range")

    common_complete: dict[str, bool] = {}
    for month in months:
        values = []
        for sid in sorted(EXPECTED_SERIES):
            month_obj = v03["series"][sid]["months"].get(month)
            require(isinstance(month_obj, dict), f"missing month object: {sid} {month}")
            values.append(month_obj.get("complete_by_unique_slot_occupancy") is True)
        common_complete[month] = all(values)

    end_idx = months.index(END_MONTH)
    require(common_complete[END_MONTH], "2025-12 is not common-complete; fail closed")

    failures = [i for i in range(end_idx + 1) if not common_complete[months[i]]]
    last_failure_idx = max(failures) if failures else -1
    start_idx = last_failure_idx + 1
    require(start_idx <= end_idx, "no continuous common-complete month remains")

    primary_months = months[start_idx : end_idx + 1]
    require(primary_months, "empty primary window")
    require(all(common_complete[m] for m in primary_months), "internal coverage failure in primary window")

    last_failure_month = months[last_failure_idx] if last_failure_idx >= 0 else None
    receipt = {
        "schema_version": "0.4",
        "lab_id": LAB_ID,
        "materializer_id": MATERIALIZER_ID,
        "classification": "CONTIGUOUS_COVERAGE_PARTITION_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "COVERAGE_PARTITION_MATERIALIZED",
        "source_v03_diagnostic_sha256": v03.get("diagnostic_sha256"),
        "selection_rule": "EARLIEST_MONTH_AFTER_LAST_COMMON_COVERAGE_FAILURE_THROUGH_2025_12",
        "last_common_coverage_failure_month": last_failure_month,
        "primary_start_month": primary_months[0],
        "primary_end_month": primary_months[-1],
        "primary_month_count": len(primary_months),
        "primary_months": primary_months,
        "common_complete_by_month": common_complete,
        "imputation_used": False,
        "economic_outcomes_used_for_selection": False,
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "discovery_authorized": False,
        "edge_status": "UNPROVEN",
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    return receipt


def main() -> None:
    source = Path(os.environ.get("PREFREEZE_SLOT_DIAGNOSTIC_RECEIPT", "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03_RECEIPT.json"))
    output = Path(os.environ.get("PREFREEZE_COVERAGE_V04_RECEIPT", "CROSS_VENUE_FUNDING_BASIS_COVERAGE_V04_RECEIPT.json"))
    require(source.exists(), f"V0.3 receipt not found: {source}")
    v03 = json.loads(source.read_text(encoding="utf-8"))
    receipt = materialize(v03)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "classification": receipt["classification"],
        "last_common_coverage_failure_month": receipt["last_common_coverage_failure_month"],
        "primary_start_month": receipt["primary_start_month"],
        "primary_end_month": receipt["primary_end_month"],
        "primary_month_count": receipt["primary_month_count"],
        "imputation_used": receipt["imputation_used"],
        "economic_outcomes_used_for_selection": receipt["economic_outcomes_used_for_selection"],
        "discovery_authorized": receipt["discovery_authorized"],
        "edge_status": receipt["edge_status"],
        "receipt_sha256": receipt["receipt_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
