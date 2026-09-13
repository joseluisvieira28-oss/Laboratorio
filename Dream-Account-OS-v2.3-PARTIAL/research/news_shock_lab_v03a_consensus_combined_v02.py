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
FREEZE2_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_REUTERS_CONSENSUS_SEED_TRANCHE02_FREEZE_V0.1.json"
SEED2_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_REUTERS_CONSENSUS_SEED_TRANCHE02_V0.1.json"
FREEZE3_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE03_FREEZE_V0.1.json"
SEED3_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_CONSENSUS_SEED_TRANCHE03_V0.1.json"

EXPECTED_SEED1 = "c0fdfc834cd4eb6c8f2186392de2175857c50e7ba71f4cd4bca820695ba79382"
EXPECTED_FREEZE2 = "2f0ef842f242ec452b5dab7171ab7ce52eafc53494f2cd22131f5cbbd24ad471"
EXPECTED_SEED2 = "1260ea66f0e9296ac3b80dd272783b0a07a78cb31892c2d4011da9b8e3a4ec7d"
EXPECTED_FREEZE3 = "6ed43441957a31d3f3cff59a47174f69eb8af2e79d9e48001d6a1ddeaf9fc43a"
EXPECTED_SEED3 = "06b06d5d151f6fd66b916322dc42e380472acc78ca7eccbeff15b91ada8d70d6"
EXPECTED_PARENT_COMBINED = "6e8c0edb2a2a4448217f4bd49411c2804617730c7cc5db1d69e9cfdfb427dff7"
EXPECTED_PARENT_VALIDATION = "b0793e74d80076a8a376109676ca027caefcd14ae99dc38744c5ceb3cd19cf97"
EXPECTED_PROVENANCE_FREEZE = "a78d4933663e687a61f91a548c074239b046c13e96dc059a73ba27828715ee7a"
EXPECTED_COMPLETE_A = 11
EXPECTED_INCOMPLETE = 33


def _load_hashed(path: Path, expected: str, label: str) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = deepcopy(raw)
    unsigned.pop("fingerprint", None)
    calculated = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    if supplied != expected or calculated != supplied:
        raise PermissionError(f"{label} fingerprint mismatch supplied={supplied} calculated={calculated} expected={expected}")
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


def load_authority() -> tuple[dict, dict, dict, dict, dict]:
    seed1 = _load_hashed(SEED1_PATH, EXPECTED_SEED1, "seed1")
    freeze2 = _load_hashed(FREEZE2_PATH, EXPECTED_FREEZE2, "freeze2")
    seed2 = _load_hashed(SEED2_PATH, EXPECTED_SEED2, "seed2")
    freeze3 = _load_hashed(FREEZE3_PATH, EXPECTED_FREEZE3, "freeze3")
    seed3 = _load_hashed(SEED3_PATH, EXPECTED_SEED3, "seed3")

    if freeze2["parent_seed_fingerprint"] != seed1["fingerprint"]:
        raise PermissionError("freeze2 parent seed mismatch")
    if seed2["freeze_fingerprint"] != freeze2["fingerprint"]:
        raise PermissionError("seed2 freeze mismatch")

    if freeze3["parent_combined_manifest_fingerprint"] != EXPECTED_PARENT_COMBINED:
        raise PermissionError("freeze3 parent combined manifest mismatch")
    if freeze3["parent_validation_fingerprint"] != EXPECTED_PARENT_VALIDATION:
        raise PermissionError("freeze3 parent validation mismatch")
    if freeze3["parent_provenance_freeze_fingerprint"] != EXPECTED_PROVENANCE_FREEZE:
        raise PermissionError("freeze3 parent provenance freeze mismatch")
    if seed3["freeze_fingerprint"] != freeze3["fingerprint"]:
        raise PermissionError("seed3 freeze mismatch")

    for freeze, label in ((freeze2, "freeze2"), (freeze3, "freeze3")):
        auth = freeze["authority"]
        for key in (
            "may_access_holdout_2026",
            "may_access_mexc_2025_09_through_2025_12",
            "may_compute_crypto_returns",
            "may_compute_profitability",
            "may_trade_live",
        ):
            if auth.get(key) is not False:
                raise PermissionError(f"{label}: authority guard drift {key}")

    ids1, ids2, ids3 = set(seed1["events"]), set(seed2["events"]), set(seed3["events"])
    if ids1 & ids2 or ids1 & ids3 or ids2 & ids3:
        raise PermissionError("consensus seed tranches overlap")
    if ids2 != set(freeze2["scope"]["event_ids"]):
        raise PermissionError("seed2 scope mismatch")
    if ids3 != set(freeze3["scope"]["event_ids"]):
        raise PermissionError("seed3 scope mismatch")

    _validate_seed(seed1, "seed1")
    _validate_seed(seed2, "seed2")
    _validate_seed(seed3, "seed3")
    return seed1, freeze2, seed2, freeze3, seed3


def build_combined(output_dir: Path) -> tuple[dict, dict]:
    seed1, freeze2, seed2, freeze3, seed3 = load_authority()
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
    for seed in (seed1, seed2, seed3):
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
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_CONSENSUS_COMBINED_MANIFEST_V02",
        "version": "0.3A-v02",
        "status": "CONSENSUS_TRANCHE03_ATTACHED_VALIDATION_REQUIRED",
        "bls_parser_amendment_fingerprint": bls.EXPECTED_AMENDMENT_FINGERPRINT,
        "seed_v01_fingerprint": seed1["fingerprint"],
        "tranche02_freeze_fingerprint": freeze2["fingerprint"],
        "tranche02_seed_fingerprint": seed2["fingerprint"],
        "tranche03_freeze_fingerprint": freeze3["fingerprint"],
        "tranche03_seed_fingerprint": seed3["fingerprint"],
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

    manifest["status"] = "CONSENSUS_VALIDATED_11_COMPLETE_A_33_INCOMPLETE"
    unsigned = deepcopy(manifest)
    unsigned.pop("fingerprint", None)
    manifest["fingerprint"] = canonical_hash(unsigned)

    (output_dir / "combined_v02_consensus_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "combined_v02_validation_receipt.json").write_text(
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
        "tranche03_freeze_fingerprint": freeze3["fingerprint"],
        "tranche03_seed_fingerprint": seed3["fingerprint"],
        "guards": validation["guards"],
    }
    (output_dir / "combined_v02_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v03a_consensus_combined_v02 <output_dir>")
    _, summary = build_combined(Path(sys.argv[1]))
    print(json.dumps(summary, indent=2, sort_keys=True))
