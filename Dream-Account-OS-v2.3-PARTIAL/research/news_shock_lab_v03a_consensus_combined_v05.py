from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from research import news_shock_lab_v03a_bls_actuals_amend03 as bls
from research.news_shock_lab_v03a_consensus_combined_v04 import load_authority as load_parent_authority
from research.news_shock_lab_v03a_consensus_combined_v03 import _load_hashed, _validate_seed
from research.news_shock_lab_v03a_provenance import EXPECTED_EVENT_COUNT, canonical_hash, validate_manifest_records

ROOT = Path(__file__).parent
FREEZE5_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE05_FREEZE_V0.1.json"
SEED5_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE05_V0.1.json"

EXPECTED_FREEZE5 = "b7a897c9e09df2302b1393d5bc9aa6ca45b8f910ccfc67f4f3b20e8ce2379a9b"
EXPECTED_SEED5 = "9ebc9d226792e7ee438b16edd133f3847f552d459dbc6bdbde0acdbb538d71e3"
EXPECTED_PARENT_COMBINED = "2b4090e9219a3ffd8a73304dd5b07ca8da640d8ed801ddb47649ad16d5186a58"
EXPECTED_PARENT_VALIDATION = "c9e3d6ae18323985a4e40f99a65c95b3cb7b562c7aad290320d0d0d428833495"
EXPECTED_PROVENANCE_FREEZE = "a78d4933663e687a61f91a548c074239b046c13e96dc059a73ba27828715ee7a"
EXPECTED_COMPLETE_A = 17
EXPECTED_INCOMPLETE = 27


def load_authority():
    seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4 = load_parent_authority()
    freeze5 = _load_hashed(FREEZE5_PATH, EXPECTED_FREEZE5, "freeze5")
    seed5 = _load_hashed(SEED5_PATH, EXPECTED_SEED5, "seed5")

    if freeze5["parent_combined_manifest_fingerprint"] != EXPECTED_PARENT_COMBINED:
        raise PermissionError("freeze5 parent combined manifest mismatch")
    if freeze5["parent_validation_fingerprint"] != EXPECTED_PARENT_VALIDATION:
        raise PermissionError("freeze5 parent validation mismatch")
    if freeze5["parent_provenance_freeze_fingerprint"] != EXPECTED_PROVENANCE_FREEZE:
        raise PermissionError("freeze5 parent provenance freeze mismatch")
    if seed5["freeze_fingerprint"] != freeze5["fingerprint"]:
        raise PermissionError("seed5 freeze mismatch")

    for key in (
        "may_access_holdout_2026",
        "may_access_mexc_2025_09_through_2025_12",
        "may_compute_crypto_returns",
        "may_compute_profitability",
        "may_trade_live",
    ):
        if freeze5["authority"].get(key) is not False:
            raise PermissionError(f"freeze5 authority guard drift {key}")

    for key, value in seed5.get("guards", {}).items():
        if value is not False:
            raise PermissionError(f"seed5 guard drift: {key}")

    prior_ids = set(seed1["events"]) | set(seed2["events"]) | set(seed3["events"]) | set(seed4["events"])
    ids5 = set(seed5["events"])
    if prior_ids & ids5:
        raise PermissionError("tranche05 overlaps prior consensus seed tranches")
    if ids5 != set(freeze5["scope"]["event_ids"]):
        raise PermissionError("seed5 scope mismatch")

    _validate_seed(seed5, "seed5")
    return seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4, freeze5, seed5


def build_combined(output_dir: Path):
    seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4, freeze5, seed5 = load_authority()
    output_dir.mkdir(parents=True, exist_ok=True)

    actual_manifest, _ = bls.collect_actuals(
        output_dir / "cpi_actual_provenance_manifest.json",
        output_dir / "actuals_validation_receipt.json",
    )
    if actual_manifest["event_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("event count drift")

    records = deepcopy(actual_manifest["records"])
    by_id = {r["event_id"]: r for r in records}
    combined_events = {}
    for seed in (seed1, seed2, seed3, seed4, seed5):
        combined_events.update(seed["events"])

    if len(combined_events) != EXPECTED_COMPLETE_A:
        raise RuntimeError(f"combined consensus identity count drift: {len(combined_events)}")

    for event_id, event in combined_events.items():
        record = by_id.get(event_id)
        if record is None:
            raise RuntimeError(f"event missing from BLS manifest: {event_id}")
        if record["release_at_utc"] != event["release_at_utc"]:
            raise RuntimeError(f"release timestamp mismatch: {event_id}")
        record["consensus"] = deepcopy(event["consensus"])

    manifest = {
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_CONSENSUS_COMBINED_MANIFEST_V05",
        "version": "0.3A-v05",
        "status": "CONSENSUS_TRANCHE05_ATTACHED_VALIDATION_REQUIRED",
        "bls_parser_amendment_fingerprint": bls.EXPECTED_AMENDMENT_FINGERPRINT,
        "seed_v01_fingerprint": seed1["fingerprint"],
        "tranche02_freeze_fingerprint": freeze2["fingerprint"],
        "tranche02_seed_fingerprint": seed2["fingerprint"],
        "tranche03_freeze_fingerprint": freeze3["fingerprint"],
        "tranche03_seed_fingerprint": seed3["fingerprint"],
        "tranche04_amendment_fingerprint": amend4["fingerprint"],
        "tranche04_freeze_fingerprint": freeze4["fingerprint"],
        "tranche04_seed_fingerprint": seed4["fingerprint"],
        "tranche05_freeze_fingerprint": freeze5["fingerprint"],
        "tranche05_seed_fingerprint": seed5["fingerprint"],
        "parent_combined_manifest_fingerprint": EXPECTED_PARENT_COMBINED,
        "parent_validation_fingerprint": EXPECTED_PARENT_VALIDATION,
        "records": records,
        "guards": deepcopy(actual_manifest["guards"]),
    }
    manifest["fingerprint"] = canonical_hash(manifest)

    validation = validate_manifest_records(manifest)
    counts = validation["status_counts"]
    expected_counts = {
        "COMPLETE_A": EXPECTED_COMPLETE_A,
        "CONSENSUS_PROVENANCE_INCOMPLETE": EXPECTED_INCOMPLETE,
    }
    if counts != expected_counts:
        raise RuntimeError(f"status count drift: {counts}")
    if validation.get("complete_b_count", 0) != 0:
        raise RuntimeError("unexpected COMPLETE_B")
    if validation["record_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("validation record count drift")

    complete = [r for r in validation["records"] if r["record_status"] == "COMPLETE_A"]
    if {r["event_id"] for r in complete} != set(combined_events):
        raise RuntimeError("COMPLETE_A event identity drift")

    for key, value in validation["guards"].items():
        if value is not False:
            raise RuntimeError(f"outcome guard drift: {key}")

    manifest["status"] = "CONSENSUS_VALIDATED_17_COMPLETE_A_27_INCOMPLETE"
    unsigned = deepcopy(manifest)
    unsigned.pop("fingerprint", None)
    manifest["fingerprint"] = canonical_hash(unsigned)

    (output_dir / "combined_v05_consensus_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "combined_v05_validation_receipt.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = {
        "status": manifest["status"],
        "event_count": validation["record_count"],
        "status_counts": counts,
        "complete_b_count": validation.get("complete_b_count", 0),
        "complete_a_event_ids": sorted(r["event_id"] for r in complete),
        "raw_surprises": {r["event_id"]: r["raw_surprises"] for r in complete},
        "combined_manifest_fingerprint": manifest["fingerprint"],
        "validation_fingerprint": validation["fingerprint"],
        "tranche05_freeze_fingerprint": freeze5["fingerprint"],
        "tranche05_seed_fingerprint": seed5["fingerprint"],
        "guards": validation["guards"],
    }
    (output_dir / "combined_v05_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_consensus_combined_v05 <output_dir>")
    _, summary = build_combined(Path(sys.argv[1]))
    print(json.dumps(summary, indent=2, sort_keys=True))
