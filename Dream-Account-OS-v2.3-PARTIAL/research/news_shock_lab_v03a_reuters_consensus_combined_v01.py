from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from research import news_shock_lab_v03a_bls_actuals_amend03 as bls
from research.news_shock_lab_v03a_provenance import (
    EXPECTED_EVENT_COUNT,
    FIELDS,
    canonical_hash,
    validate_manifest_records,
)

ROOT = Path(__file__).parent
SEED1_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_REUTERS_CONSENSUS_SEED_V0.1.json"
SEED2_FREEZE_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_REUTERS_CONSENSUS_SEED_TRANCHE02_FREEZE_V0.1.json"
SEED2_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_REUTERS_CONSENSUS_SEED_TRANCHE02_V0.1.json"

EXPECTED_SEED1 = "c0fdfc834cd4eb6c8f2186392de2175857c50e7ba71f4cd4bca820695ba79382"
EXPECTED_SEED2_FREEZE = "2f0ef842f242ec452b5dab7171ab7ce52eafc53494f2cd22131f5cbbd24ad471"
EXPECTED_SEED2 = "7995e980a95ebb53656e02816c5606efe76c3ba140c756b3d22ac0b978025edb"
EXPECTED_COMPLETE_A = 5
EXPECTED_INCOMPLETE = 39


def _load_hashed(path: Path, expected: str, label: str) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = deepcopy(raw)
    unsigned.pop("fingerprint", None)
    calculated = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    if supplied != expected or calculated != supplied:
        raise PermissionError(f"{label} fingerprint mismatch")
    return raw


def load_authority() -> tuple[dict, dict, dict]:
    seed1 = _load_hashed(SEED1_PATH, EXPECTED_SEED1, "Reuters seed V0.1")
    freeze2 = _load_hashed(SEED2_FREEZE_PATH, EXPECTED_SEED2_FREEZE, "Reuters tranche02 freeze")
    seed2 = _load_hashed(SEED2_PATH, EXPECTED_SEED2, "Reuters tranche02 seed")

    if freeze2["parent_seed_fingerprint"] != seed1["fingerprint"]:
        raise PermissionError("Tranche02 parent seed mismatch")
    if seed2["freeze_fingerprint"] != freeze2["fingerprint"]:
        raise PermissionError("Tranche02 freeze mismatch")
    if freeze2["authority"]["may_mutate_parent_seed"] is not False:
        raise PermissionError("Tranche02 parent mutation guard drift")
    if freeze2["authority"]["may_compute_crypto_returns"] is not False:
        raise PermissionError("Tranche02 crypto outcome guard drift")
    if freeze2["authority"]["may_compute_profitability"] is not False:
        raise PermissionError("Tranche02 profitability guard drift")

    ids1 = set(seed1["events"])
    ids2 = set(seed2["events"])
    frozen2 = set(freeze2["scope"]["event_ids"])
    if ids1 & ids2:
        raise PermissionError("Reuters seed tranches overlap")
    if ids2 != frozen2:
        raise PermissionError("Tranche02 seed event scope mismatch")

    for seed in (seed1, seed2):
        for event_id, event in seed["events"].items():
            if set(event["consensus"]) != set(FIELDS):
                raise PermissionError(f"{event_id}: expected exactly four consensus fields")
            if event["source_published_at_utc"] >= event["release_at_utc"]:
                raise PermissionError(f"{event_id}: consensus source is not pre-release")
            for field in FIELDS:
                item = event["consensus"][field]
                if item["source_publisher"] != "Reuters":
                    raise PermissionError(f"{event_id}/{field}: publisher drift")
                if item["provenance_grade"] != "A" or item["pre_release_gate_pass"] is not True:
                    raise PermissionError(f"{event_id}/{field}: provenance gate drift")
                if item["published_at_utc"] != event["source_published_at_utc"]:
                    raise PermissionError(f"{event_id}/{field}: publication timestamp drift")
    return seed1, freeze2, seed2


def build_combined(output_dir: Path) -> tuple[dict, dict]:
    seed1, freeze2, seed2 = load_authority()
    output_dir.mkdir(parents=True, exist_ok=True)

    actual_manifest, _ = bls.collect_actuals(
        output_dir / "cpi_actual_provenance_manifest.json",
        output_dir / "actuals_validation_receipt.json",
    )
    if actual_manifest["event_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("Combined Reuters event count drift")

    records = deepcopy(actual_manifest["records"])
    by_id = {record["event_id"]: record for record in records}
    combined_events = {}
    combined_events.update(seed1["events"])
    combined_events.update(seed2["events"])

    for event_id, event in combined_events.items():
        record = by_id.get(event_id)
        if record is None:
            raise RuntimeError(f"Combined Reuters event missing from BLS manifest: {event_id}")
        if record["release_at_utc"] != event["release_at_utc"]:
            raise RuntimeError(f"Combined Reuters release time mismatch: {event_id}")
        record["consensus"] = deepcopy(event["consensus"])

    augmented = {
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_REUTERS_COMBINED_CONSENSUS_MANIFEST",
        "version": "0.3A",
        "status": "REUTERS_COMBINED_SEEDS_ATTACHED_VALIDATION_REQUIRED",
        "bls_parser_amendment_fingerprint": bls.EXPECTED_AMENDMENT_FINGERPRINT,
        "seed_v01_fingerprint": seed1["fingerprint"],
        "tranche02_freeze_fingerprint": freeze2["fingerprint"],
        "tranche02_seed_fingerprint": seed2["fingerprint"],
        "records": records,
        "guards": deepcopy(actual_manifest["guards"]),
    }
    augmented["fingerprint"] = canonical_hash(augmented)

    validation = validate_manifest_records(augmented)
    counts = validation["status_counts"]
    if counts.get("COMPLETE_A", 0) != EXPECTED_COMPLETE_A:
        raise RuntimeError(f"Combined Reuters COMPLETE_A count drift: {counts}")
    if counts.get("CONSENSUS_PROVENANCE_INCOMPLETE", 0) != EXPECTED_INCOMPLETE:
        raise RuntimeError(f"Combined Reuters incomplete count drift: {counts}")
    if validation.get("complete_b_count", 0) != 0:
        raise RuntimeError(f"Combined Reuters unexpected COMPLETE_B: {counts}")
    if validation["record_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("Combined Reuters record count drift")

    complete = [r for r in validation["records"] if r["record_status"] == "COMPLETE_A"]
    expected_ids = set(combined_events)
    if {r["event_id"] for r in complete} != expected_ids:
        raise RuntimeError("Combined Reuters COMPLETE_A identity drift")

    augmented["status"] = "REUTERS_COMBINED_VALIDATED_5_COMPLETE_A_39_INCOMPLETE"
    unsigned = deepcopy(augmented)
    unsigned.pop("fingerprint", None)
    augmented["fingerprint"] = canonical_hash(unsigned)

    (output_dir / "combined_consensus_manifest.json").write_text(
        json.dumps(augmented, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "combined_validation_receipt.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = {
        "status": augmented["status"],
        "event_count": validation["record_count"],
        "status_counts": counts,
        "complete_a_event_ids": sorted(r["event_id"] for r in complete),
        "raw_surprises": {r["event_id"]: r["raw_surprises"] for r in complete},
        "combined_manifest_fingerprint": augmented["fingerprint"],
        "validation_fingerprint": validation["fingerprint"],
        "seed_v01_fingerprint": seed1["fingerprint"],
        "tranche02_seed_fingerprint": seed2["fingerprint"],
        "guards": validation["guards"],
    }
    (output_dir / "combined_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return augmented, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_reuters_consensus_combined_v01 <output_dir>")
    _, summary = build_combined(Path(sys.argv[1]))
    print(json.dumps(summary, indent=2, sort_keys=True))
