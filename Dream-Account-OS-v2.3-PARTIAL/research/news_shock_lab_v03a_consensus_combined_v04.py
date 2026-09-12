from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from research import news_shock_lab_v03a_bls_actuals_amend03 as bls
from research.news_shock_lab_v03a_consensus_combined_v02 import load_authority as load_parent_authority
from research.news_shock_lab_v03a_consensus_combined_v03 import _load_hashed, _validate_seed
from research.news_shock_lab_v03a_provenance import EXPECTED_EVENT_COUNT, canonical_hash, validate_manifest_records

ROOT = Path(__file__).parent
AMEND4_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE04_AMEND01_V0.1.json"
FREEZE4_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE04_FREEZE_V0.2.json"
SEED4_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE04_V0.2.json"

EXPECTED_AMEND4 = "74fa51103bc5fc40b633e154e1f7b88848f7c827ffb4cac7db9889f6f8efccc8"
EXPECTED_FREEZE4 = "5073bd6bc23d78bf44fd130c95b26ddfcff8a6b25f4cd34d31ad78f81a8aa748"
EXPECTED_SEED4 = "b3bb3450fa955252517bbb524abed32a3de88456bc420317941171476d75859b"
EXPECTED_PARENT_COMBINED = "bbe69cdf1909dda75343685ee62ef8173c7314067e1a07059ab22781692e1b89"
EXPECTED_PARENT_VALIDATION = "118980f25cb888423c9a50427be22891f6172cf489b7c7a15297b53a336ed881"
EXPECTED_PROVENANCE_FREEZE = "a78d4933663e687a61f91a548c074239b046c13e96dc059a73ba27828715ee7a"
EXPECTED_SUPERSEDED_FREEZE4 = "294680037de76d770c129fb0c6e3d2b903d43cda389dddcc2300c9fbe26688bf"
EXPECTED_SUPERSEDED_SEED4 = "0f43162e4b3b4f6155a8d0a642c2bc6c563ab94517a4334d293185c7a71f5997"
EXPECTED_COMPLETE_A = 15
EXPECTED_INCOMPLETE = 29


def load_authority():
    seed1, freeze2, seed2, freeze3, seed3 = load_parent_authority()
    amend4 = _load_hashed(AMEND4_PATH, EXPECTED_AMEND4, "amend4")
    freeze4 = _load_hashed(FREEZE4_PATH, EXPECTED_FREEZE4, "freeze4_v02")
    seed4 = _load_hashed(SEED4_PATH, EXPECTED_SEED4, "seed4_v02")

    if amend4["parent_tranche04_freeze_fingerprint"] != EXPECTED_SUPERSEDED_FREEZE4:
        raise PermissionError("amend4 superseded freeze mismatch")
    if amend4["parent_tranche04_seed_fingerprint"] != EXPECTED_SUPERSEDED_SEED4:
        raise PermissionError("amend4 superseded seed mismatch")
    if amend4["parent_combined_manifest_fingerprint"] != EXPECTED_PARENT_COMBINED:
        raise PermissionError("amend4 parent combined mismatch")
    if amend4["parent_validation_fingerprint"] != EXPECTED_PARENT_VALIDATION:
        raise PermissionError("amend4 parent validation mismatch")
    if amend4["parent_provenance_freeze_fingerprint"] != EXPECTED_PROVENANCE_FREEZE:
        raise PermissionError("amend4 provenance freeze mismatch")
    if amend4.get("market_outcomes_used_in_decision") is not False or amend4.get("consensus_values_changed") is not False:
        raise PermissionError("amend4 contamination or consensus mutation")

    if freeze4["amendment_fingerprint"] != amend4["fingerprint"]:
        raise PermissionError("freeze4 amendment mismatch")
    if freeze4["supersedes_tranche04_freeze_fingerprint"] != EXPECTED_SUPERSEDED_FREEZE4:
        raise PermissionError("freeze4 superseded freeze mismatch")
    if freeze4["supersedes_tranche04_seed_fingerprint"] != EXPECTED_SUPERSEDED_SEED4:
        raise PermissionError("freeze4 superseded seed mismatch")
    if freeze4["parent_combined_manifest_fingerprint"] != EXPECTED_PARENT_COMBINED:
        raise PermissionError("freeze4 parent combined mismatch")
    if freeze4["parent_validation_fingerprint"] != EXPECTED_PARENT_VALIDATION:
        raise PermissionError("freeze4 parent validation mismatch")
    if freeze4["parent_provenance_freeze_fingerprint"] != EXPECTED_PROVENANCE_FREEZE:
        raise PermissionError("freeze4 provenance freeze mismatch")

    if seed4["freeze_fingerprint"] != freeze4["fingerprint"] or seed4["amendment_fingerprint"] != amend4["fingerprint"]:
        raise PermissionError("seed4 authority chain mismatch")
    if seed4["supersedes_seed_fingerprint"] != EXPECTED_SUPERSEDED_SEED4:
        raise PermissionError("seed4 superseded seed mismatch")

    for doc, label in ((amend4, "amend4"), (seed4, "seed4")):
        for key, value in doc.get("guards", {}).items():
            if value is not False:
                raise PermissionError(f"{label} guard drift: {key}")
    for key in ("may_access_holdout_2026", "may_access_mexc_2025_09_through_2025_12", "may_compute_crypto_returns", "may_compute_profitability", "may_trade_live"):
        if freeze4["authority"].get(key) is not False:
            raise PermissionError(f"freeze4 authority drift: {key}")

    prior = set(seed1["events"]) | set(seed2["events"]) | set(seed3["events"])
    ids4 = set(seed4["events"])
    if prior & ids4 or ids4 != set(freeze4["scope"]["event_ids"]):
        raise PermissionError("tranche04 scope/overlap failure")
    if "US_CPI_2024-10-10" in ids4:
        raise PermissionError("ambiguous October event re-entered tranche04")
    _validate_seed(seed4, "seed4_v02")
    return seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4


def build_combined(output_dir: Path):
    seed1, freeze2, seed2, freeze3, seed3, amend4, freeze4, seed4 = load_authority()
    output_dir.mkdir(parents=True, exist_ok=True)
    actual_manifest, _ = bls.collect_actuals(output_dir / "cpi_actual_provenance_manifest.json", output_dir / "actuals_validation_receipt.json")
    if actual_manifest["event_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("event count drift")

    records = deepcopy(actual_manifest["records"])
    by_id = {r["event_id"]: r for r in records}
    combined_events = {}
    for seed in (seed1, seed2, seed3, seed4):
        combined_events.update(seed["events"])
    if len(combined_events) != EXPECTED_COMPLETE_A:
        raise RuntimeError(f"combined identity count drift: {len(combined_events)}")

    for event_id, event in combined_events.items():
        record = by_id.get(event_id)
        if record is None or record["release_at_utc"] != event["release_at_utc"]:
            raise RuntimeError(f"BLS identity/release mismatch: {event_id}")
        record["consensus"] = deepcopy(event["consensus"])

    manifest = {
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_CONSENSUS_COMBINED_MANIFEST_V04",
        "version": "0.3A-v04",
        "status": "CONSENSUS_TRANCHE04_V02_ATTACHED_VALIDATION_REQUIRED",
        "bls_parser_amendment_fingerprint": bls.EXPECTED_AMENDMENT_FINGERPRINT,
        "seed_v01_fingerprint": seed1["fingerprint"],
        "tranche02_freeze_fingerprint": freeze2["fingerprint"],
        "tranche02_seed_fingerprint": seed2["fingerprint"],
        "tranche03_freeze_fingerprint": freeze3["fingerprint"],
        "tranche03_seed_fingerprint": seed3["fingerprint"],
        "tranche04_amendment_fingerprint": amend4["fingerprint"],
        "tranche04_freeze_fingerprint": freeze4["fingerprint"],
        "tranche04_seed_fingerprint": seed4["fingerprint"],
        "parent_combined_manifest_fingerprint": EXPECTED_PARENT_COMBINED,
        "parent_validation_fingerprint": EXPECTED_PARENT_VALIDATION,
        "records": records,
        "guards": deepcopy(actual_manifest["guards"]),
    }
    manifest["fingerprint"] = canonical_hash(manifest)
    validation = validate_manifest_records(manifest)
    expected_counts = {"COMPLETE_A": EXPECTED_COMPLETE_A, "CONSENSUS_PROVENANCE_INCOMPLETE": EXPECTED_INCOMPLETE}
    if validation["status_counts"] != expected_counts or validation.get("complete_b_count", 0) != 0:
        raise RuntimeError(f"status count drift: {validation['status_counts']}")
    if validation["record_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("validation record count drift")
    complete = [r for r in validation["records"] if r["record_status"] == "COMPLETE_A"]
    if {r["event_id"] for r in complete} != set(combined_events):
        raise RuntimeError("COMPLETE_A identity drift")
    if any(value is not False for value in validation["guards"].values()):
        raise RuntimeError(f"outcome guard drift: {validation['guards']}")

    manifest["status"] = "CONSENSUS_VALIDATED_15_COMPLETE_A_29_INCOMPLETE"
    unsigned = deepcopy(manifest)
    unsigned.pop("fingerprint", None)
    manifest["fingerprint"] = canonical_hash(unsigned)
    (output_dir / "combined_v04_consensus_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "combined_v04_validation_receipt.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "status": manifest["status"],
        "event_count": validation["record_count"],
        "status_counts": validation["status_counts"],
        "complete_b_count": validation.get("complete_b_count", 0),
        "complete_a_event_ids": sorted(r["event_id"] for r in complete),
        "raw_surprises": {r["event_id"]: r["raw_surprises"] for r in complete},
        "combined_manifest_fingerprint": manifest["fingerprint"],
        "validation_fingerprint": validation["fingerprint"],
        "tranche04_amendment_fingerprint": amend4["fingerprint"],
        "tranche04_freeze_fingerprint": freeze4["fingerprint"],
        "tranche04_seed_fingerprint": seed4["fingerprint"],
        "guards": validation["guards"],
    }
    (output_dir / "combined_v04_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_consensus_combined_v04 <output_dir>")
    _, summary = build_combined(Path(sys.argv[1]))
    print(json.dumps(summary, indent=2, sort_keys=True))
