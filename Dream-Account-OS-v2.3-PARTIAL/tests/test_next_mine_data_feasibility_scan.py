import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "research" / "next_mine_data_feasibility_scan"
MATRIX = SCAN / "NEXT_MINE_DATA_FEASIBILITY_MATRIX.csv"
RECEIPT = SCAN / "receipts" / "NEXT_MINE_DATA_FEASIBILITY_SCAN_RECEIPT.json"
HASH_MANIFEST = SCAN / "receipts" / "NEXT_MINE_DATA_FEASIBILITY_HASH_MANIFEST.csv"

EXPECTED_HEADERS = [
    "candidate_id", "candidate_name", "family", "repo_location", "branch_if_any",
    "scientific_status", "duplication_status", "primary_source", "backup_source",
    "historical_start", "historical_end", "resolution", "timestamp_quality",
    "timezone_quality", "raw_data_available", "free_access", "credentials_required",
    "bulk_download", "api_available", "raw_preservation", "hashable", "revision_risk",
    "survivorship_risk", "lookahead_risk", "source_mutation_risk",
    "single_source_dependency", "point_in_time_capability",
    "discovery_oos_holdout_feasible", "source_complexity", "blocking_reason", "status",
    "smallest_authorized_next_step",
]

ALLOWED_STATUSES = {
    "DATA_READY", "DATA_READY_WITH_CONTROLS", "SOURCE_PROBE_REQUIRED", "DATA_FRAGILE",
    "SOURCE_BLOCKED", "SCIENTIFICALLY_CLOSED", "DUPLICATE",
}
ALLOWED_DUPLICATION = {
    "EXACT_DUPLICATE", "NEAR_DUPLICATE", "ECONOMICALLY_EQUIVALENT", "DISTINCT",
}


def load_rows():
    with MATRIX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == EXPECTED_HEADERS
        rows = list(reader)
    assert rows
    assert all(None not in row for row in rows)
    return rows


def test_matrix_schema_ids_and_classes():
    rows = load_rows()
    ids = [row["candidate_id"] for row in rows]
    assert len(rows) == 60
    assert len(ids) == len(set(ids))
    assert {row["status"] for row in rows} <= ALLOWED_STATUSES
    assert {row["duplication_status"] for row in rows} <= ALLOWED_DUPLICATION
    assert all(row["status"] for row in rows)


def test_frozen_statuses_and_recommendation_are_preserved():
    rows = {row["candidate_id"]: row for row in load_rows()}
    assert rows["NEWS-SHOCK-LAB-V0.3"]["status"] == "SOURCE_BLOCKED"
    assert rows["STETH-REDEMPTION-BASIS-001"]["status"] == "SOURCE_BLOCKED"
    assert rows["STETH-REDEMPTION-BASIS-002"]["status"] == "DATA_READY_WITH_CONTROLS"
    attack = (SCAN / "NEXT_AUTHORIZED_ATTACK.md").read_text(encoding="utf-8")
    assert "Candidate: `STETH-REDEMPTION-BASIS-002`" in attack
    assert attack.count("Candidate:") == 1


def test_matrix_is_outcome_blind_and_contains_no_protected_2026_window():
    rows = load_rows()
    text = MATRIX.read_text(encoding="utf-8").lower()
    forbidden_headers = {"pnl", "sharpe", "win_rate", "returns", "outcomes"}
    with MATRIX.open(newline="", encoding="utf-8") as handle:
        headers = set(csv.DictReader(handle).fieldnames or [])
    assert forbidden_headers.isdisjoint(headers)
    assert all("2026-" not in row["historical_start"] for row in rows)
    assert all("2026-" not in row["historical_end"] for row in rows)
    assert "btc_return" not in text
    assert "eth_return" not in text


def test_receipt_counts_and_governance():
    rows = load_rows()
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    actual = {status: 0 for status in ALLOWED_STATUSES}
    for row in rows:
        actual[row["status"]] += 1
    assert receipt["inventory"]["classification_counts"] == actual
    assert receipt["selection"]["performance_evidence_used"] is False
    assert all(value is False for value in receipt["governance"].values())


def test_hash_manifest():
    with HASH_MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    for row in rows:
        path = SCAN / row["relative_path"]
        assert path.is_file()
        data = path.read_bytes()
        assert len(data) == int(row["bytes"])
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
