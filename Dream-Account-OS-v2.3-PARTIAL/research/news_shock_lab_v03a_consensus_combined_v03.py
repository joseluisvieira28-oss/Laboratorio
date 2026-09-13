from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from research import news_shock_lab_v03a_bls_actuals_amend03 as bls
from research.news_shock_lab_v03a_consensus_combined_v02 import load_authority as load_parent_authority
from research.news_shock_lab_v03a_provenance import (
    EXPECTED_EVENT_COUNT,
    FIELDS,
    canonical_hash,
    validate_manifest_records,
)

ROOT = Path(__file__).parent
FREEZE4_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE04_FREEZE_V0.1.json"
SEED4_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE04_V0.1.json"

EXPECTED_FREEZE4 = "294680037de76d770c129fb0c6e3d2b903d43cda389dddcc2300c9fbe26688bf"
EXPECTED_SEED4 = "0f43162e4b3b4f6155a8d0a642c2bc6c563ab94517a4334d293185c7a71f5997"
EXPECTED_PARENT_COMBINED = "bbe69cdf1909dda75343685ee62ef8173c7314067e1a07059ab22781692e1b89"
EXPECTED_PARENT_VALIDATION = "118980f25cb888423c9a50427be22891f6172cf489b7c7a15297b53a336ed881"
EXPECTED_PROVENANCE_FREEZE = "a78d4933663e687a61f91a548c074239b046c13e96dc059a73ba27828715ee7a"
EXPECTED_COMPLETE_A = 16
EXPECTED_INCOMPLETE = 28


def _load_hashed(path: Path, expected: str, label: str) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = deepcopy(raw)
    unsigned.pop("fingerprint", None)
    calculated = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    if supplied != expected or calculated != supplied:
        raise PermissionError(
            f"{label} fingerprint mismatch supplied={supplied} calculated={calculated} expected={expected}"
        )
    return raw


def _validate_seed(seed: dict, label: str) -> None:
    for event_id, event in seed["events"].items():
        if set(event["consensus"]) != set(FIELDS):
            raise PermissionError(f"{label}/{event_id}: expected exactly four consensus fields")
        if event["source_published_at_utc"] >= event["release_at_utc"]:
            raise PermissionError(f"{label}/{event_id}: consensus source is not pre-release")
        for field in FIELDS:
            item = event["consensus"][field]
            if item["provenance_grade"] != "A" or item["pre_release_gate_pass"] is not True:
                raise PermissionError(f"{label}/{event_id}/{field}: provenance gate drift")
            if item["published_at_utc"] != event["source_published_at_utc"]:
                raise PermissionError(f"{label}/{event_id}/{field}: publication timestamp drift")
            if not item.get("source_url") or not item.get("source_publisher"):
                raise PermissionError(f"{label}/{event_id}/{field}: source provenance missing")


def load_authority() -> tuple[dict, dict, dict, dict, dict, dict, dict]:
    seed1, freeze2, seed2, freeze3, seed3 = load_parent_authority()
    freeze4 = _load_hashed(FREEZE4_PATH, EXPECTED_FREEZE4, "freeze4")
    seed4 = _load_hashed(SEED4_PATH, EXPECTED_SEED4, "seed4")

    if freeze4["parent_combined_manifest_fingerprint"] != EXPECTED_PARENT_COMBINED:
        raise PermissionError("freeze4 parent combined manifest mismatch")
    if freeze4["parent_validation_fingerprint"] != EXPECTED_PARENT_VALIDATION:
        raise PermissionError("freeze4 parent validation mismatch")
    if freeze4["parent_provenance_freeze_fingerprint"] != EXPECTED_PROVENANCE_FREEZE:
        raise PermissionError("freeze4 parent provenance freeze mismatch")
    if seed4["freeze_fingerprint"] != freeze4["fingerprint"]:
        raise PermissionError("seed4 freeze mismatch")

    auth = freeze4["authority"]
    for key in (
        "may_access_holdout_2026",
        "may_access_mexc_2025_09_through_2025_12",
        "may_compute_crypto_returns",
        "may_compute_profitability",
        "may_trade_live",
    ):
        if auth.get(key) is not False:
            raise PermissionError(f"freeze4: authority guard drift {key}")

    prior_ids = set(seed1["events"]) | set(seed2["events"]) | set(seed3["events"])
    ids4 = set(seed4["events"])
    if prior_ids & ids4:
        raise PermissionError("tranche04 overlaps prior consensus seed tranches")
    if ids4 != set(freeze4["scope"]["event_ids"]):
        raise PermissionError("seed4 scope mismatch")

    _validate_seed(seed4, "seed4")
    return seed1, freeze2, seed2, freeze3, seed3, freeze4, seed4


def build_combined(output_dir: Path) -> tuple[dict, dict]:
    seed1, freeze2, seed2, freeze3, seed3, freeze4, seed4 = load_authority()
    output_dir.mkdir(parents=True, exist_ok=True)

    actual_manifest, _ = bls.collect_actuals(
        output_dir / "cpi_actual_provenance_manifest.json",
        output_dir / "actuals_validation_receipt.json",
    )
    if actual_manifest["event_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("event count drift")

    records = deepcopy(actual_manifest["records"])
    by_id = {r["event_id"]: r for r in records}
    combined_events: dict[str, dict] = {}
    for seed in (seed1, seed2, seed3, seed4):
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
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_CONSENSUS_COMBINED_MANIFEST_V03",
        "version": "0.3A-v03",
        "status": "CONSENSUS_TRANCHE04_ATTACHED_VALIDATION_REQUIRED",
        "bls_parser_amendment_fingerprint": bls.EXPECTED_AMENDMENT_FINGERPRINT,
        "seed_v01_fingerprint": seed1["fingerprint"],
        "tranche02_freeze_fingerprint": freeze2["fingerprint"],
        "tranche02_seed_fingerprint": seed2["fingerprint"],
        "tranche03_freeze_fingerprint": freeze3["fingerprint"],
        "tranche03_seed_fingerprint": seed3["fingerprint"],
        "tranche04_freeze_fingerprint": freeze4["fingerprint"],
        "tranche04_seed_fingerprint": seed4["fingerprint"],
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

    manifest["status"] = "CONSENSUS_VALIDATED_16_COMPLETE_A_28_INCOMPLETE"
    unsigned = deepcopy(manifest)
    unsigned.pop("fingerprint", None)
    manifest["fingerprint"] = canonical_hash(unsigned)

    (output_dir / "combined_v03_consensus_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "combined_v03_validation_receipt.json").write_text(
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
        "tranche04_freeze_fingerprint": freeze4["fingerprint"],
        "tranche04_seed_fingerprint": seed4["fingerprint"],
        "guards": validation["guards"],
    }
    (output_dir / "combined_v03_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_consensus_combined_v03 <output_dir>")
    _, summary = build_combined(Path(sys.argv[1]))
    print(json.dumps(summary, indent=2, sort_keys=True))
