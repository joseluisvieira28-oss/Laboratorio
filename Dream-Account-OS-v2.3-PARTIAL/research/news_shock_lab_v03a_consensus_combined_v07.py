from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from research import news_shock_lab_v03a_bls_actuals_amend03 as bls
from research.news_shock_lab_v03a_consensus_combined_v06 import load_authority as load_parent_authority
from research.news_shock_lab_v03a_consensus_combined_v03 import _load_hashed, _validate_seed
from research.news_shock_lab_v03a_provenance import EXPECTED_EVENT_COUNT, canonical_hash, validate_manifest_records

ROOT = Path(__file__).parent
FREEZE7_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE07_FREEZE_V0.1.json"
SEED7_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE07_V0.1.json"

EXPECTED_FREEZE7 = "15d20b6857622717cadb5e92d314ad6fb253b5ccb678f4359c23287c49582fc5"
EXPECTED_SEED7 = "392fd2d3e4c8935d2d3e23f7d5bcc35f04c2fa02b8618d85c8df34d3cbf5a7b7"
EXPECTED_PARENT_COMBINED = "5040b59e3d8f3f4aa769df8744357ee7a7d51d784f781ce28f6f059cc9c43777"
EXPECTED_PARENT_VALIDATION = "2263fad55efe19beede24cea448c13f1b39ae124e7fe07b77b05f066fca854e9"
EXPECTED_PROVENANCE_FREEZE = "a78d4933663e687a61f91a548c074239b046c13e96dc059a73ba27828715ee7a"
EXPECTED_COMPLETE_A = 30
EXPECTED_INCOMPLETE = 14


def load_authority():
    (
        seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4,
        freeze5, seed5, freeze6, seed6,
    ) = load_parent_authority()
    freeze7 = _load_hashed(FREEZE7_PATH, EXPECTED_FREEZE7, "freeze7")
    seed7 = _load_hashed(SEED7_PATH, EXPECTED_SEED7, "seed7")

    if freeze7["parent_combined_manifest_fingerprint"] != EXPECTED_PARENT_COMBINED:
        raise PermissionError("freeze7 parent combined manifest mismatch")
    if freeze7["parent_validation_fingerprint"] != EXPECTED_PARENT_VALIDATION:
        raise PermissionError("freeze7 parent validation mismatch")
    if freeze7["parent_provenance_freeze_fingerprint"] != EXPECTED_PROVENANCE_FREEZE:
        raise PermissionError("freeze7 parent provenance freeze mismatch")
    if seed7["freeze_fingerprint"] != freeze7["fingerprint"]:
        raise PermissionError("seed7 freeze mismatch")

    for key in (
        "may_access_holdout_2026", "may_access_mexc_2025_09_through_2025_12",
        "may_compute_crypto_returns", "may_compute_profitability", "may_trade_live",
    ):
        if freeze7["authority"].get(key) is not False:
            raise PermissionError(f"freeze7 authority guard drift {key}")
    for key, value in seed7.get("guards", {}).items():
        if value is not False:
            raise PermissionError(f"seed7 guard drift: {key}")

    prior_ids = (
        set(seed1["events"]) | set(seed2["events"]) | set(seed3["events"])
        | set(seed4["events"]) | set(seed5["events"]) | set(seed6["events"])
    )
    ids7 = set(seed7["events"])
    if prior_ids & ids7:
        raise PermissionError("tranche07 overlaps prior consensus seed tranches")
    if ids7 != set(freeze7["scope"]["event_ids"]):
        raise PermissionError("seed7 scope mismatch")
    _validate_seed(seed7, "seed7")
    return (
        seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4,
        freeze5, seed5, freeze6, seed6, freeze7, seed7,
    )


def build_combined(output_dir: Path):
    (
        seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4,
        freeze5, seed5, freeze6, seed6, freeze7, seed7,
    ) = load_authority()
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
    for seed in (seed1, seed2, seed3, seed4, seed5, seed6, seed7):
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
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_CONSENSUS_COMBINED_MANIFEST_V07",
        "version": "0.3A-v07",
        "status": "CONSENSUS_TRANCHE07_ATTACHED_VALIDATION_REQUIRED",
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
        "tranche06_freeze_fingerprint": freeze6["fingerprint"],
        "tranche06_seed_fingerprint": seed6["fingerprint"],
        "tranche07_freeze_fingerprint": freeze7["fingerprint"],
        "tranche07_seed_fingerprint": seed7["fingerprint"],
        "parent_combined_manifest_fingerprint": EXPECTED_PARENT_COMBINED,
        "parent_validation_fingerprint": EXPECTED_PARENT_VALIDATION,
        "records": records,
        "guards": deepcopy(actual_manifest["guards"]),
    }
    manifest["fingerprint"] = canonical_hash(manifest)
    validation = validate_manifest_records(manifest)
    counts = validation["status_counts"]
    expected_counts = {"COMPLETE_A": EXPECTED_COMPLETE_A, "CONSENSUS_PROVENANCE_INCOMPLETE": EXPECTED_INCOMPLETE}
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

    manifest["status"] = "CONSENSUS_VALIDATED_30_COMPLETE_A_14_INCOMPLETE"
    unsigned = deepcopy(manifest)
    unsigned.pop("fingerprint", None)
    manifest["fingerprint"] = canonical_hash(unsigned)
    (output_dir / "combined_v07_consensus_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "combined_v07_validation_receipt.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "status": manifest["status"], "event_count": validation["record_count"],
        "status_counts": counts, "complete_b_count": validation.get("complete_b_count", 0),
        "complete_a_event_ids": sorted(r["event_id"] for r in complete),
        "raw_surprises": {r["event_id"]: r["raw_surprises"] for r in complete},
        "combined_manifest_fingerprint": manifest["fingerprint"],
        "validation_fingerprint": validation["fingerprint"],
        "tranche07_freeze_fingerprint": freeze7["fingerprint"],
        "tranche07_seed_fingerprint": seed7["fingerprint"],
        "guards": validation["guards"],
    }
    (output_dir / "combined_v07_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_consensus_combined_v07 <output_dir>")
    _, summary = build_combined(Path(sys.argv[1]))
    print(json.dumps(summary, indent=2, sort_keys=True))
