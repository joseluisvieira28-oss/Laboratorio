from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parent
FINAL_PROVENANCE_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_FINAL_CONSENSUS_PROVENANCE_FREEZE_V0.1.json"
PRE_DISCOVERY_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_PRE_DISCOVERY_SIGNAL_STATISTICAL_FREEZE_V0.1.json"

EXPECTED_FINAL_PROVENANCE_FINGERPRINT = "dbf8e972076fe98e90a6ed45dac5a091a557e2e24f6391ee790b6de2af49c0e4"
EXPECTED_PRE_DISCOVERY_FINGERPRINT = "945924528dde46a7e596ac77cec32e8deeff62adb42859f7e52abf63b6d5a37f"
EXPECTED_ORIGINAL_PROVENANCE_FINGERPRINT = "a78d4933663e687a61f91a548c074239b046c13e96dc059a73ba27828715ee7a"
EXPECTED_V09_MANIFEST_FINGERPRINT = "bb12b7798872b45be78aaf9aa10b53012327fda6399c8a77bd662576502f1a7d"
EXPECTED_V09_VALIDATION_FINGERPRINT = "dcf1be3085a3d04e6856da65698b25dfa9805291f07d095ac1e60a6b52b19d56"
EXPECTED_BOUNDARY_V07_BLOB_SHA = "521199c3bb57d627b08a7b3286ba57fd19b7b034"

EXPECTED_DISCOVERY_IDS = ['US_CPI_2022-02-10', 'US_CPI_2022-03-10', 'US_CPI_2022-05-11', 'US_CPI_2022-06-10', 'US_CPI_2022-07-13', 'US_CPI_2022-09-13', 'US_CPI_2022-11-10', 'US_CPI_2022-12-13', 'US_CPI_2023-01-12', 'US_CPI_2023-04-12', 'US_CPI_2023-06-13', 'US_CPI_2023-07-12', 'US_CPI_2023-08-10', 'US_CPI_2023-09-13', 'US_CPI_2023-11-14', 'US_CPI_2023-12-12', 'US_CPI_2024-01-11', 'US_CPI_2024-02-13', 'US_CPI_2024-03-12', 'US_CPI_2024-04-10', 'US_CPI_2024-05-15', 'US_CPI_2024-06-12', 'US_CPI_2024-07-11', 'US_CPI_2024-08-14', 'US_CPI_2024-09-11', 'US_CPI_2024-11-13', 'US_CPI_2024-12-11']
EXPECTED_VALIDATION_IDS = ['US_CPI_2025-01-15', 'US_CPI_2025-02-12', 'US_CPI_2025-03-12', 'US_CPI_2025-04-10', 'US_CPI_2025-05-13', 'US_CPI_2025-06-11', 'US_CPI_2025-07-15', 'US_CPI_2025-08-12']
EXPECTED_DISCOVERY_NEUTRALS = ['US_CPI_2022-03-10', 'US_CPI_2023-01-12', 'US_CPI_2023-06-13', 'US_CPI_2024-09-11', 'US_CPI_2024-11-13', 'US_CPI_2024-12-11']
EXPECTED_VALIDATION_NEUTRALS = ['US_CPI_2025-08-12']


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load_hashed(path: Path, expected: str, label: str) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    if supplied != expected:
        raise PermissionError(f"{label} supplied fingerprint drift: {supplied}")
    unsigned = deepcopy(raw)
    unsigned.pop("fingerprint", None)
    actual = canonical_hash(unsigned)
    if actual != expected:
        raise PermissionError(f"{label} canonical fingerprint drift: {actual}")
    return raw


def validate() -> dict:
    final = load_hashed(FINAL_PROVENANCE_PATH, EXPECTED_FINAL_PROVENANCE_FINGERPRINT, "final provenance")
    pre = load_hashed(PRE_DISCOVERY_PATH, EXPECTED_PRE_DISCOVERY_FINGERPRINT, "pre-discovery freeze")

    authority = final["authority_chain"]
    if authority["original_provenance_freeze_fingerprint"] != EXPECTED_ORIGINAL_PROVENANCE_FINGERPRINT:
        raise PermissionError("original provenance authority drift")
    if authority["v09_combined_manifest_fingerprint"] != EXPECTED_V09_MANIFEST_FINGERPRINT:
        raise PermissionError("V0.9 manifest authority drift")
    if authority["v09_validation_fingerprint"] != EXPECTED_V09_VALIDATION_FINGERPRINT:
        raise PermissionError("V0.9 validation authority drift")
    if authority["boundary_receipt_blob_sha"] != EXPECTED_BOUNDARY_V07_BLOB_SHA:
        raise PermissionError("boundary V0.7 blob authority drift")

    if final["corpus"]["events_total"] != 44:
        raise RuntimeError("final corpus total drift")
    if final["corpus"]["complete_a"] != 35 or final["corpus"]["complete_b"] != 0 or final["corpus"]["incomplete"] != 9:
        raise RuntimeError("final provenance count drift")
    if len(final["corpus"]["complete_a_event_ids"]) != 35:
        raise RuntimeError("final COMPLETE_A identity count drift")
    if len(final["corpus"]["incomplete_event_reasons"]) != 9:
        raise RuntimeError("final incomplete identity count drift")
    if final["bounded_sweep_decision"]["status"] != "EXHAUSTED_FOR_PRIMARY_DISCOVERY_COHORT":
        raise PermissionError("bounded provenance sweep is not final")
    if final["bounded_sweep_decision"]["after_market_outcome_access_historical_recoveries_may_not_modify_discovery_or_validation_cohorts"] is not True:
        raise PermissionError("post-outcome cohort immutability guard missing")

    for key, value in final["guards"].items():
        if key.endswith("_authorized"):
            if value is not False:
                raise PermissionError(f"final governance authorization drift: {key}")
        elif key.endswith("_accessed") or key in ("market_outcomes_accessed", "crypto_returns_computed", "profitability_computed"):
            if value is not False:
                raise PermissionError(f"final outcome boundary drift: {key}")

    if pre["authority_chain"]["final_provenance_freeze_fingerprint"] != EXPECTED_FINAL_PROVENANCE_FINGERPRINT:
        raise PermissionError("pre-discovery parent final provenance drift")
    if pre["authority_chain"]["original_provenance_freeze_fingerprint"] != EXPECTED_ORIGINAL_PROVENANCE_FINGERPRINT:
        raise PermissionError("pre-discovery original provenance drift")
    if pre["authority_chain"]["v09_combined_manifest_fingerprint"] != EXPECTED_V09_MANIFEST_FINGERPRINT:
        raise PermissionError("pre-discovery V0.9 manifest drift")
    if pre["authority_chain"]["v09_validation_fingerprint"] != EXPECTED_V09_VALIDATION_FINGERPRINT:
        raise PermissionError("pre-discovery V0.9 validation drift")
    if pre["authority_chain"]["boundary_receipt_v07_blob_sha"] != EXPECTED_BOUNDARY_V07_BLOB_SHA:
        raise PermissionError("pre-discovery boundary V0.7 drift")

    discovery = pre["cohorts"]["discovery"]
    validation = pre["cohorts"]["validation"]
    if discovery["event_ids"] != EXPECTED_DISCOVERY_IDS or discovery["event_count"] != 27:
        raise RuntimeError("Discovery cohort drift")
    if validation["event_ids"] != EXPECTED_VALIDATION_IDS or validation["event_count"] != 8:
        raise RuntimeError("Validation cohort drift")
    if discovery["market_outcomes_authorized_now"] is not False:
        raise PermissionError("Discovery outcomes prematurely authorized")
    if validation["market_outcomes_authorized_now"] is not False:
        raise PermissionError("Validation outcomes prematurely authorized")
    if pre["cohorts"]["mexc_2025_09_through_2025_12"] != "LOCKED_NOT_ACCESSED":
        raise PermissionError("MEXC 2025-09..12 unlocked")
    if pre["cohorts"]["holdout_2026"] != "LOCKED_NOT_ACCESSED":
        raise PermissionError("2026 unlocked")

    sig = pre["surprise_signal"]
    if sig["weights"] != {
        "headline_cpi_mom": "0.25", "headline_cpi_yoy": "0.25",
        "core_cpi_mom": "0.25", "core_cpi_yoy": "0.25"
    }:
        raise PermissionError("composite weights drift")
    if sig["standardization"] != "NONE" or sig["magnitude_threshold"] != "NONE":
        raise PermissionError("surprise transformation tuning introduced")
    if sig["directional_mapping"] != {"HOTTER": "CRYPTO_DOWN", "COOLER": "CRYPTO_UP", "NEUTRAL": "NO_DIRECTIONAL_TEST"}:
        raise PermissionError("directional mapping drift")
    labels = sig["frozen_event_labels"]
    if set(labels) != set(EXPECTED_DISCOVERY_IDS + EXPECTED_VALIDATION_IDS):
        raise RuntimeError("frozen signal label identity drift")

    disc_counts = pre["discovery_signal_counts"]
    if (disc_counts["total_grade_a_events"], disc_counts["directional_events"], disc_counts["hotter"], disc_counts["cooler"], disc_counts["neutral"]) != (27, 21, 11, 10, 6):
        raise RuntimeError("Discovery signal count drift")
    if disc_counts["neutral_event_ids"] != EXPECTED_DISCOVERY_NEUTRALS:
        raise RuntimeError("Discovery neutral IDs drift")
    if disc_counts["exact_label_permutation_count"] != 352716:
        raise RuntimeError("exact permutation count drift")

    val_counts = pre["validation_signal_counts"]
    if (val_counts["total_grade_a_events"], val_counts["directional_events"], val_counts["hotter"], val_counts["cooler"], val_counts["neutral"]) != (8, 7, 1, 6, 1):
        raise RuntimeError("Validation signal count drift")
    if val_counts["neutral_event_ids"] != EXPECTED_VALIDATION_NEUTRALS:
        raise RuntimeError("Validation neutral IDs drift")

    md = pre["market_data_contract"]
    if md["source"] != "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY" or md["market_type"] != "SPOT" or md["timeframe"] != "1m":
        raise PermissionError("market data contract drift")
    if md["symbols"] != ["BTCUSDT", "ETHUSDT"] or md["primary_inferential_asset"] != "BTCUSDT" or md["mandatory_cross_asset_replication"] != "ETHUSDT":
        raise PermissionError("asset contract drift")
    if md["validation_2025_access_now"] is not False or md["holdout_2026_access_now"] is not False or md["mexc_2025_09_through_2025_12_access_now"] is not False:
        raise PermissionError("protected market data prematurely unlocked")

    timing = pre["event_timing_contract"]
    if timing["primary_entry"] != "OPEN_OF_08:31_AMERICA_NEW_YORK_1M_CANDLE":
        raise PermissionError("primary entry drift")
    if timing["primary_exit"] != "OPEN_OF_08:45_AMERICA_NEW_YORK_1M_CANDLE":
        raise PermissionError("primary exit drift")
    if timing["alternate_primary_horizons"] != "FORBIDDEN":
        raise PermissionError("alternate primary horizon introduced")

    costs = pre["return_and_cost_contract"]
    if costs["fixed_round_trip_cost_bps"] != "10":
        raise PermissionError("cost hurdle drift")
    if costs["stop_loss"] != "NONE" or costs["take_profit"] != "NONE" or costs["position_sizing_optimization"] != "FORBIDDEN":
        raise PermissionError("execution parameter introduced")

    primary = pre["primary_discovery_test"]
    if primary["test"] != "EXACT_FIXED_COUNT_LABEL_PERMUTATION":
        raise PermissionError("primary test drift")
    if primary["unique_assignment_count"] != 352716 or primary["rng"] != "NONE":
        raise PermissionError("exact test implementation contract drift")
    if primary["alpha"] != "0.05":
        raise PermissionError("alpha drift")
    if primary["assets_tested"] != ["BTCUSDT", "ETHUSDT"]:
        raise PermissionError("asset testing drift")

    survival = pre["discovery_survival_criteria"]
    required = {
        "exact_one_sided_p_lte": "0.05",
        "mean_aligned_net_bps_gt": "0",
        "median_aligned_gross_bps_gt": "0",
        "every_leave_one_out_mean_aligned_net_bps_gt": "0",
    }
    if survival["BTCUSDT"] != required or survival["ETHUSDT"] != required:
        raise PermissionError("Discovery survival criteria drift")

    if len(pre["no_rescue_rules"]) < 10 or "PRIMARY_FAILURE_CLOSES_HYPOTHESIS_AS_NO_EDGE_UNDER_THIS_DEFINITION" not in pre["no_rescue_rules"]:
        raise PermissionError("no-rescue contract weakened")

    gov = pre["governance"]
    for key in ("research_only", "fail_closed", "no_tuning_after_outcomes", "no_cherry_picking"):
        if gov[key] is not True:
            raise PermissionError(f"governance weakened: {key}")
    for key in ("live_trading_authorized", "exchange_mutation_authorized", "main_merge_authorized", "render_deploy_authorized",
                "market_outcomes_accessed_at_freeze", "crypto_returns_computed_at_freeze", "profitability_computed_at_freeze"):
        if gov[key] is not False:
            raise PermissionError(f"forbidden authority/outcome drift: {key}")

    receipt = {
        "document_type": "NEWS_SHOCK_LAB_V03A_PRE_DISCOVERY_FREEZE_GATE_RECEIPT_V0.1",
        "version": "0.1",
        "status": "PRE_DISCOVERY_FREEZE_GATE_PASS",
        "final_provenance_freeze_fingerprint": EXPECTED_FINAL_PROVENANCE_FINGERPRINT,
        "pre_discovery_freeze_fingerprint": EXPECTED_PRE_DISCOVERY_FINGERPRINT,
        "v09_manifest_fingerprint": EXPECTED_V09_MANIFEST_FINGERPRINT,
        "v09_validation_fingerprint": EXPECTED_V09_VALIDATION_FINGERPRINT,
        "boundary_v07_blob_sha": EXPECTED_BOUNDARY_V07_BLOB_SHA,
        "corpus": {"total": 44, "complete_a": 35, "incomplete": 9, "complete_b": 0},
        "discovery": {"events": 27, "directional": 21, "hotter": 11, "cooler": 10, "neutral": 6, "exact_permutations": 352716},
        "validation": {"events": 8, "directional": 7, "hotter": 1, "cooler": 6, "neutral": 1, "outcomes_locked": True},
        "market_outcomes_accessed": False,
        "crypto_returns_computed": False,
        "profitability_computed": False,
        "holdout_2026_accessed": False,
        "mexc_2025_09_through_2025_12_accessed": False,
        "discovery_market_data_access_authorized_by_this_gate": False,
        "next_required_authority": "SEPARATE_DISCOVERY_DATA_ACCESS_AUTHORIZATION",
    }
    receipt["fingerprint"] = canonical_hash(receipt)
    return receipt


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_pre_discovery_gate_v01 <output_receipt.json>")
    output = Path(sys.argv[1])
    receipt = validate()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
