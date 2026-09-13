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

FREEZE_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V03A_REUTERS_CONSENSUS_SEED_FREEZE_V0.1.json"
)
SEED_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V03A_REUTERS_CONSENSUS_SEED_V0.1.json"
)
EXPECTED_FREEZE_FINGERPRINT = (
    "1e99091766126fad3240e0e0cb7125fd191853ae97fdfe55b94d639adb99ee9b"
)
EXPECTED_SEED_FINGERPRINT = (
    "c0fdfc834cd4eb6c8f2186392de2175857c50e7ba71f4cd4bca820695ba79382"
)
EXPECTED_COMPLETE_A = 2
EXPECTED_INCOMPLETE = 42


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


def load_authority() -> tuple[dict, dict]:
    freeze = _load_hashed(FREEZE_PATH, EXPECTED_FREEZE_FINGERPRINT, "Reuters seed freeze")
    seed = _load_hashed(SEED_PATH, EXPECTED_SEED_FINGERPRINT, "Reuters seed")
    if freeze["status"] != "FROZEN_PRE_OUTCOME_CONSENSUS_ATTACHMENT":
        raise PermissionError("Reuters seed freeze status mismatch")
    if seed["freeze_fingerprint"] != freeze["fingerprint"]:
        raise PermissionError("Reuters seed parent freeze mismatch")
    if freeze["authority"]["may_compute_crypto_returns"] is not False:
        raise PermissionError("Reuters seed crypto-outcome guard drift")
    if freeze["authority"]["may_compute_profitability"] is not False:
        raise PermissionError("Reuters seed profitability guard drift")
    if freeze["authority"]["may_expand_event_scope"] is not False:
        raise PermissionError("Reuters seed event-scope guard drift")
    allowed = set(freeze["scope"]["event_ids"])
    supplied = set(seed["events"])
    if supplied != allowed:
        raise PermissionError(f"Reuters seed event scope mismatch: {supplied} != {allowed}")
    for event_id, event in seed["events"].items():
        if set(event["consensus"]) != set(FIELDS):
            raise PermissionError(f"{event_id}: seed must contain exactly four CPI fields")
        if event["source_published_at_utc"] >= event["release_at_utc"]:
            raise PermissionError(f"{event_id}: seed is not pre-release")
        for field in FIELDS:
            item = event["consensus"][field]
            if item["source_publisher"] != "Reuters":
                raise PermissionError(f"{event_id}/{field}: publisher drift")
            if item["provenance_grade"] != "A" or item["pre_release_gate_pass"] is not True:
                raise PermissionError(f"{event_id}/{field}: provenance-grade drift")
            if item["published_at_utc"] != event["source_published_at_utc"]:
                raise PermissionError(f"{event_id}/{field}: publication timestamp drift")
    return freeze, seed


def build_augmented_manifest(output_dir: Path) -> tuple[dict, dict]:
    freeze, seed = load_authority()
    output_dir.mkdir(parents=True, exist_ok=True)
    actual_manifest_path = output_dir / "cpi_actual_provenance_manifest.json"
    actual_validation_path = output_dir / "actuals_validation_receipt.json"

    actual_manifest, _ = bls.collect_actuals(actual_manifest_path, actual_validation_path)
    if actual_manifest["event_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("Reuters seed actual-manifest event count drift")
    for key, value in actual_manifest["guards"].items():
        if key in {
            "market_outcomes_accessed", "crypto_returns_computed", "profitability_computed",
            "holdout_2026_accessed", "mexc_2025_09_through_2025_12_accessed"
        } and value is not False:
            raise RuntimeError(f"Reuters seed inherited guard drift: {key}")

    records = deepcopy(actual_manifest["records"])
    by_id = {record["event_id"]: record for record in records}
    for event_id, event in seed["events"].items():
        if event_id not in by_id:
            raise RuntimeError(f"Reuters seed event missing from actual manifest: {event_id}")
        record = by_id[event_id]
        if record["release_at_utc"] != event["release_at_utc"]:
            raise RuntimeError(f"Reuters seed release timestamp mismatch: {event_id}")
        record["consensus"] = deepcopy(event["consensus"])

    augmented = {
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_CONSENSUS_AUGMENTED_MANIFEST",
        "version": "0.3A",
        "status": "REUTERS_SEED_ATTACHED_PROVENANCE_VALIDATION_REQUIRED",
        "provenance_freeze_fingerprint": actual_manifest["freeze_fingerprint"],
        "bls_parser_amendment_fingerprint": bls.EXPECTED_AMENDMENT_FINGERPRINT,
        "reuters_seed_freeze_fingerprint": freeze["fingerprint"],
        "reuters_seed_fingerprint": seed["fingerprint"],
        "actual_manifest_runtime_fingerprint": actual_manifest["fingerprint"],
        "records": records,
        "guards": deepcopy(actual_manifest["guards"]),
    }
    augmented["fingerprint"] = canonical_hash(augmented)

    validation = validate_manifest_records(augmented)
    counts = validation["status_counts"]
    if counts.get("COMPLETE_A", 0) != EXPECTED_COMPLETE_A:
        raise RuntimeError(f"Reuters seed COMPLETE_A count drift: {counts}")
    if counts.get("CONSENSUS_PROVENANCE_INCOMPLETE", 0) != EXPECTED_INCOMPLETE:
        raise RuntimeError(f"Reuters seed incomplete count drift: {counts}")
    if validation.get("complete_b_count", 0) != 0:
        raise RuntimeError(f"Reuters seed unexpected COMPLETE_B: {counts}")
    if validation["record_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("Reuters seed validation record count drift")

    complete = [r for r in validation["records"] if r["record_status"] == "COMPLETE_A"]
    if {r["event_id"] for r in complete} != set(seed["events"]):
        raise RuntimeError("Reuters seed COMPLETE_A identity drift")

    augmented["status"] = "REUTERS_SEED_VALIDATED_2_COMPLETE_A_42_INCOMPLETE"
    augmented["fingerprint"] = canonical_hash({k: v for k, v in augmented.items() if k != "fingerprint"})
    (output_dir / "consensus_augmented_manifest.json").write_text(
        json.dumps(augmented, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "consensus_validation_receipt.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = {
        "status": augmented["status"],
        "event_count": validation["record_count"],
        "status_counts": counts,
        "complete_a_event_ids": [r["event_id"] for r in complete],
        "raw_surprises": {r["event_id"]: r["raw_surprises"] for r in complete},
        "augmented_manifest_fingerprint": augmented["fingerprint"],
        "validation_fingerprint": validation["fingerprint"],
        "reuters_seed_fingerprint": seed["fingerprint"],
        "guards": validation["guards"],
    }
    (output_dir / "consensus_seed_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return augmented, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_reuters_consensus_seed <output_dir>")
    _, summary = build_augmented_manifest(Path(sys.argv[1]))
    print(json.dumps(summary, indent=2, sort_keys=True))
