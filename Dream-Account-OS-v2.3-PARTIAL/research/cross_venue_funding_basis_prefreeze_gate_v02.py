"""Evidence-linked final pre-freeze gate for Cross-Venue Funding & Basis Lab V0.2.

Consumes only pre-freeze, outcome-blind evidence:
- V0.2 raw provenance diagnostic receipt (raw-record hashes / duplicates / boundaries)
- V0.3 slot-occupancy receipt (timestamp normalization / missingness)
- V0.4 contiguous coverage partition receipt
- V0.5 dated funding-regime semantics freeze
- frozen cost/capital/execution policy

This gate NEVER computes or inspects funding carry, spread, APR/APY, PnL, rankings,
thresholds, or signals. A successful result means only that the lab is READY TO REQUEST
separate Discovery authorization. It does not authorize Discovery or trading.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import cross_venue_funding_basis_prefreeze_gate_v01 as v1

LAB_ID = v1.LAB_ID
EDGE_STATUS = "UNPROVEN"
EXPECTED_SERIES = {
    "BINANCE_BTCUSDT",
    "BINANCE_ETHUSDT",
    "HYPERLIQUID_BTC",
    "HYPERLIQUID_ETH",
}

class GateViolation(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateViolation(message)


def load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object: {path}")
    return value


def fingerprint(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def require_false_markers(obj: Mapping[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        require(obj.get(key) is False, f"boundary marker not false: {key}")


def validate_raw_v02(receipt: Mapping[str, Any]) -> None:
    require(receipt.get("lab_id") == LAB_ID, "V0.2 wrong lab")
    require(receipt.get("diagnostic_id") == "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_DIAGNOSTIC_V02", "wrong V0.2 receipt")
    require(receipt.get("classification") == "PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY", "wrong V0.2 classification")
    require(receipt.get("status") == "DIAGNOSTIC_COMPLETE", "V0.2 incomplete")
    require_false_markers(receipt, (
        "locked_2026_accessed", "mexc_accessed", "authenticated_account_data_used",
        "exchange_mutation_used", "funding_rate_values_summarized", "carry_computed",
        "apr_apy_computed", "pnl_computed", "signals_computed",
    ))
    require(receipt.get("v01_coverage_rule_changed") is False, "V0.2 silently changed V0.1 coverage rule")
    series = receipt.get("series", {})
    require(set(series) == EXPECTED_SERIES, "V0.2 series scope drift")
    for sid, s in series.items():
        require(int(s.get("record_count", 0)) > 0, f"V0.2 empty series: {sid}")
        require(int(s.get("unique_timestamp_count", -1)) == int(s.get("record_count", -2)), f"V0.2 duplicate timestamp count mismatch: {sid}")
        require(int(s.get("conflicting_duplicate_timestamp_count", -1)) == 0, f"V0.2 conflicting duplicates: {sid}")
        raw_hash = s.get("canonical_raw_records_sha256") or s.get("raw_sha256")
        require(isinstance(raw_hash, str) and len(raw_hash) == 64, f"V0.2 raw hash missing: {sid}")
        last = str(s.get("last_timestamp_utc") or "")
        require(last and not last.startswith("2026"), f"V0.2 timestamp reaches locked 2026: {sid}")


def validate_slot_v03(receipt: Mapping[str, Any], raw_v02: Mapping[str, Any]) -> None:
    require(receipt.get("lab_id") == LAB_ID, "V0.3 wrong lab")
    require(receipt.get("diagnostic_id") == "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03", "wrong V0.3 receipt")
    require(receipt.get("classification") == "SLOT_OCCUPANCY_PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY", "wrong V0.3 classification")
    require(receipt.get("status") == "DIAGNOSTIC_COMPLETE", "V0.3 incomplete")
    require_false_markers(receipt, (
        "locked_2026_accessed", "mexc_accessed", "authenticated_account_data_used",
        "exchange_mutation_used", "funding_rate_values_summarized", "carry_computed",
        "apr_apy_computed", "pnl_computed", "signals_computed",
    ))
    series = receipt.get("series", {})
    require(set(series) == EXPECTED_SERIES, "V0.3 series scope drift")
    for sid in EXPECTED_SERIES:
        s3 = series[sid]
        s2 = raw_v02["series"][sid]
        require(int(s3.get("record_count", -1)) == int(s2.get("record_count", -2)), f"V0.2/V0.3 record count mismatch: {sid}")
        require(int(s3.get("unique_timestamp_count", -1)) == int(s3.get("record_count", -2)), f"V0.3 raw duplicate timestamps: {sid}")
        require(int(s3.get("slot_collision_count_total", -1)) == 0, f"V0.3 slot collision: {sid}")
        require(int(s3.get("ambiguous_mapping_count_total", -1)) == 0, f"V0.3 ambiguous slot mapping: {sid}")
        months = s3.get("months", {})
        require(isinstance(months, dict) and "2025-12" in months, f"V0.3 missing terminal month: {sid}")
    require(isinstance(receipt.get("diagnostic_sha256"), str) and len(receipt["diagnostic_sha256"]) == 64, "V0.3 diagnostic fingerprint missing")


def validate_coverage_v04(receipt: Mapping[str, Any], slot_v03: Mapping[str, Any]) -> dict[str, Any]:
    require(receipt.get("lab_id") == LAB_ID, "V0.4 wrong lab")
    require(receipt.get("materializer_id") == "CROSS_VENUE_FUNDING_BASIS_COVERAGE_MATERIALIZER_V04", "wrong V0.4 receipt")
    require(receipt.get("classification") == "CONTIGUOUS_COVERAGE_PARTITION_ONLY_NOT_ECONOMIC_DISCOVERY", "wrong V0.4 classification")
    require(receipt.get("status") == "COVERAGE_PARTITION_MATERIALIZED", "V0.4 incomplete")
    require(receipt.get("source_v03_diagnostic_sha256") == slot_v03.get("diagnostic_sha256"), "V0.4 not linked to supplied V0.3")
    require(receipt.get("imputation_used") is False, "V0.4 used imputation")
    require(receipt.get("economic_outcomes_used_for_selection") is False, "V0.4 used economic outcomes")
    require(receipt.get("discovery_authorized") is False, "V0.4 pre-authorized Discovery")
    require(receipt.get("edge_status") == EDGE_STATUS, "V0.4 edge status drift")
    require_false_markers(receipt, (
        "locked_2026_accessed", "mexc_accessed", "authenticated_account_data_used",
        "exchange_mutation_used", "funding_rate_values_summarized", "carry_computed",
        "apr_apy_computed", "pnl_computed", "signals_computed",
    ))
    months = receipt.get("primary_months")
    require(isinstance(months, list) and months, "V0.4 primary months missing")
    require(receipt.get("primary_month_count") == len(months), "V0.4 month count mismatch")
    require(receipt.get("primary_start_month") == months[0], "V0.4 start mismatch")
    require(receipt.get("primary_end_month") == months[-1] == "2025-12", "V0.4 end must be 2025-12")
    require(all(slot_v03["series"][sid]["months"][m]["complete_by_unique_slot_occupancy"] is True for sid in EXPECTED_SERIES for m in months), "V0.4 includes incomplete slot month")
    all_months = sorted(slot_v03["series"][next(iter(EXPECTED_SERIES))]["months"].keys())
    failures = [m for m in all_months if m <= "2025-12" and not all(slot_v03["series"][sid]["months"][m]["complete_by_unique_slot_occupancy"] is True for sid in EXPECTED_SERIES)]
    expected_last_failure = failures[-1] if failures else None
    require(receipt.get("last_common_coverage_failure_month") == expected_last_failure, "V0.4 last failure inconsistent with V0.3")
    if expected_last_failure is not None:
        idx = all_months.index(expected_last_failure)
        require(idx + 1 < len(all_months), "no month after last failure")
        require(months[0] == all_months[idx + 1], "V0.4 did not start immediately after last coverage failure")
    return {
        "first_common_full_month": months[0],
        "last_common_full_month": months[-1],
        "common_full_month_count": len(months),
        "common_full_months": months,
        "selection_rule": receipt.get("selection_rule"),
    }


def validate_regime_v05(regime: Mapping[str, Any]) -> None:
    require(regime.get("lab_id") == LAB_ID, "V0.5 wrong lab")
    require(regime.get("freeze_id") == "CROSS_VENUE_FUNDING_BASIS_REGIME_SEMANTICS_FREEZE_V05", "wrong V0.5 freeze")
    require(regime.get("classification") == "REGIME_SEMANTICS_ONLY_NOT_ECONOMIC_DISCOVERY", "wrong V0.5 classification")
    require(regime.get("status") == "REGIME_SEMANTICS_FROZEN", "V0.5 incomplete")
    require(regime.get("economic_outcomes_inspected") is False, "V0.5 saw economic outcomes")
    require(regime.get("discovery_authorized") is False, "V0.5 pre-authorized Discovery")
    require(regime.get("trading_authorized") is False, "V0.5 authorized trading")
    require(regime.get("locked_2026_accessed") is False, "V0.5 accessed 2026")
    require(regime.get("mexc_accessed") is False, "V0.5 accessed MEXC")
    b = regime.get("binance_usdm", {})
    require(b.get("assets") == ["BTCUSDT", "ETHUSDT"], "V0.5 Binance scope drift")
    require(b.get("schedule_rule_change", {}).get("effective_utc") == "2025-05-02T08:00:00Z", "Binance schedule-rule date drift")
    require(b.get("formula_change", {}).get("effective_utc") == "2025-09-18T08:01:00Z", "Binance formula date drift")
    h = regime.get("hyperliquid", {})
    require(h.get("assets") == ["BTC", "ETH"], "V0.5 Hyperliquid scope drift")
    require(h.get("schedule") == "1H", "Hyperliquid schedule drift")
    require("one eighth" in h.get("formula_semantics", "").lower(), "Hyperliquid scaling semantics missing")


def evaluate(root: Path, raw_v02_path: Path, slot_v03_path: Path, coverage_v04_path: Path, regime_v05_path: Path) -> dict[str, Any]:
    policy = load(root / "CROSS_VENUE_FUNDING_BASIS_LAB_COST_CAPITAL_EXECUTION_FREEZE_V01.json")
    v1.validate_policy(policy)
    raw_v02 = load(raw_v02_path)
    slot_v03 = load(slot_v03_path)
    coverage_v04 = load(coverage_v04_path)
    regime_v05 = load(regime_v05_path)

    validate_raw_v02(raw_v02)
    validate_slot_v03(slot_v03, raw_v02)
    replication_window = validate_coverage_v04(coverage_v04, slot_v03)
    validate_regime_v05(regime_v05)

    gate_states = {
        "G03_FUNDING_REGIMES": "PASS_DATED_RULES_AND_OBSERVED_SETTLEMENT_SCHEDULE_AUDITED",
        "G04_RAW_PROVENANCE": "PASS_HASHED_RAW_RECORDS_AND_SLOT_COVERAGE_AUDITED",
        "G06_FEES": "PASS_POLICY_EXECUTABLE_CLAIM_BLOCKED_WITHOUT_DATE_MATCHED_FEE_PROVENANCE",
        "G07_EXECUTION_DATA": "UNOBSERVABLE_HISTORICALLY_FOR_EXECUTABLE_RETURN_CLAIM",
        "G08_MARGIN_CAPITAL": "PASS_SPEC_EXECUTABLE_LIQUIDATION_EXACTNESS_REQUIRES_DATE_MATCHED_MARGIN_PROVENANCE",
        "G09_OPPORTUNITY_COST": "PASS",
        "G10_REPLICATION_PARTITION": "PASS_PROVENANCE_ONLY_CONTIGUOUS_WINDOW_FROZEN",
        "G11_INDEPENDENT_VALIDATION": "PASS_POLICY_2026_LOCKED_2027_PLUS_REQUIRED",
        "G12_DISCOVERY_AUTHORIZATION": "BLOCKED_PENDING_SEPARATE_EXPLICIT_AUTHORIZATION",
    }

    return {
        "schema_version": "0.2",
        "lab_id": LAB_ID,
        "phase": "PRE_FREEZE",
        "status": "READY_TO_REQUEST_SEPARATE_DISCOVERY_AUTHORIZATION",
        "edge_status": EDGE_STATUS,
        "discovery_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "historical_executable_return_claim_authorized": False,
        "historical_mechanism_replication_classification": "ADVERSARIAL_REPLICATION_ONLY",
        "locked_2026": True,
        "mexc_2025_locked": True,
        "economic_outcomes_inspected_by_gate_engine": False,
        "gate_states": gate_states,
        "blockers_before_requesting_discovery_authorization": [],
        "replication_window_provenance_only": replication_window,
        "evidence_fingerprints": {
            "raw_v02_diagnostic_sha256": raw_v02.get("diagnostic_sha256"),
            "slot_v03_diagnostic_sha256": slot_v03.get("diagnostic_sha256"),
            "coverage_v04_receipt_sha256": coverage_v04.get("receipt_sha256"),
            "regime_v05_fingerprint": fingerprint(regime_v05),
            "policy_fingerprint": fingerprint(policy),
        },
        "next_action": "REQUEST_SEPARATE_EXPLICIT_DISCOVERY_AUTHORIZATION",
    }


def main() -> None:
    here = Path(__file__).resolve().parent
    root = here
    project = here.parent
    raw_v02 = project / "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_DIAGNOSTIC_V02_RECEIPT.json"
    slot_v03 = project / "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03_RECEIPT.json"
    coverage_v04 = project / "CROSS_VENUE_FUNDING_BASIS_COVERAGE_V04_RECEIPT.json"
    regime_v05 = here / "CROSS_VENUE_FUNDING_BASIS_REGIME_SEMANTICS_FREEZE_V05.json"
    for p in (raw_v02, slot_v03, coverage_v04, regime_v05):
        require(p.exists(), f"required pre-freeze evidence missing: {p}")
    result = evaluate(root, raw_v02, slot_v03, coverage_v04, regime_v05)
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
