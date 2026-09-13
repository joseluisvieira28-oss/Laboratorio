from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from research.news_shock_lab_v01_bls_schedule import build_manifest as build_v01_schedule_manifest

FREEZE_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V03A_CPI_SURPRISE_DATA_PROVENANCE_FREEZE.json"
)
EXPECTED_FREEZE_FINGERPRINT = (
    "a78d4933663e687a61f91a548c074239b046c13e96dc059a73ba27828715ee7a"
)
FIELDS = (
    "headline_cpi_mom",
    "headline_cpi_yoy",
    "core_cpi_mom",
    "core_cpi_yoy",
)
START_DATE = "2022-01-01"
END_DATE = "2025-08-31"
EXPECTED_EVENT_COUNT = 44
NY = ZoneInfo("America/New_York")


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def load_freeze() -> dict:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    if supplied != EXPECTED_FREEZE_FINGERPRINT:
        raise PermissionError("V0.3A freeze fingerprint mismatch")
    if canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.3A freeze canonical hash mismatch")
    if raw["analysis_authority"]["may_compute_crypto_returns_in_this_stage"] is not False:
        raise PermissionError("V0.3A outcome-access guard drift")
    if raw["governance"]["holdout_2026_authorized"] is not False:
        raise PermissionError("V0.3A 2026 guard drift")
    if raw["governance"]["mexc_2025_09_through_2025_12_authorized"] is not False:
        raise PermissionError("V0.3A MEXC holdout guard drift")
    return raw


def _parse_utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("UTC timestamp must end in Z")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _blank_consensus_field() -> None:
    return None


def _blank_record(event: dict) -> dict:
    record = {
        "event_id": f"US_CPI_{event['event_date']}",
        "event_type": "US_CPI",
        "reference_month": None,
        "release_date_local": event["event_date"],
        "release_timezone": "America/New_York",
        "release_at_utc": event["release_utc"],
        "actuals": {field: None for field in FIELDS},
        "actual_provenance": {
            "bls_release_url": None,
            "bls_retrieved_at_utc": None,
            "bls_content_sha256": None,
            "alfred_corroboration": {
                "status": "NOT_CHECKED",
                "source_url": None,
                "vintage_date": None,
                "evidence_note": None,
            },
        },
        "consensus": {field: _blank_consensus_field() for field in FIELDS},
        "raw_surprises": {field: None for field in FIELDS},
        "record_status": "ACTUAL_PROVENANCE_INCOMPLETE",
        "missing_reasons": [
            "BLS_ARCHIVED_RELEASE_NOT_YET_ATTACHED",
            "CONTEMPORANEOUS_CONSENSUS_NOT_YET_ATTACHED",
        ],
        "record_fingerprint": None,
    }
    record["record_fingerprint"] = record_fingerprint(record)
    return record


def record_fingerprint(record: dict) -> str:
    unsigned = deepcopy(record)
    unsigned["record_fingerprint"] = None
    return canonical_hash(unsigned)


def build_event_slot_manifest(output_path: Path | None = None) -> dict:
    load_freeze()
    parent = build_v01_schedule_manifest()
    events = [
        e for e in parent["events"]
        if e["event_type"] == "CPI"
        and START_DATE <= e["event_date"] <= END_DATE
    ]
    if len(events) != EXPECTED_EVENT_COUNT:
        raise RuntimeError(
            f"V0.3A CPI cardinality block: {len(events)} != {EXPECTED_EVENT_COUNT}"
        )
    if any(e["event_date"].startswith("2026-") for e in events):
        raise RuntimeError("V0.3A 2026 event guard violation")

    records = [_blank_record(e) for e in events]
    body = {
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_EVENT_SLOT_MANIFEST",
        "version": "0.3A",
        "status": "PROVENANCE_SLOTS_CREATED_NO_MARKET_OUTCOMES_ACCESSED",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "parent_bls_schedule_manifest_fingerprint": parent["fingerprint"],
        "selection": {
            "event_type": "CPI",
            "start_date_inclusive": START_DATE,
            "end_date_inclusive": END_DATE,
            "event_count": len(records),
            "no_outcome_based_selection": True,
        },
        "records": records,
        "guards": {
            "market_outcomes_accessed": False,
            "crypto_returns_computed": False,
            "profitability_computed": False,
            "holdout_2026_accessed": False,
            "mexc_2025_09_through_2025_12_accessed": False,
            "live_trading_authorized": False,
        },
    }
    body["fingerprint"] = canonical_hash(body)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(body, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return body


def _actual_provenance_complete(record: dict) -> bool:
    p = record["actual_provenance"]
    return bool(
        all(record["actuals"][field] is not None for field in FIELDS)
        and record["reference_month"]
        and p["bls_release_url"]
        and p["bls_retrieved_at_utc"]
        and p["bls_content_sha256"]
    )


def _consensus_field_valid(item: object, release_at: datetime) -> tuple[bool, str | None]:
    if not isinstance(item, dict):
        return False, "CONSENSUS_FIELD_MISSING"
    required = (
        "value", "unit", "source_publisher", "source_url", "source_title",
        "published_at_utc", "retrieved_at_utc", "consensus_statistic",
        "evidence_note", "pre_release_gate_pass", "provenance_grade",
    )
    missing = [key for key in required if key not in item]
    if missing:
        return False, f"CONSENSUS_KEYS_MISSING:{','.join(missing)}"
    if item["value"] is None:
        return False, "CONSENSUS_VALUE_MISSING"
    if not item["published_at_utc"]:
        return False, "CONSENSUS_PUBLISHED_AT_MISSING"
    published_at = _parse_utc(item["published_at_utc"])
    if not published_at < release_at:
        return False, "CONSENSUS_NOT_PRE_RELEASE"
    if item["pre_release_gate_pass"] is not True:
        return False, "CONSENSUS_PRE_RELEASE_GATE_FALSE"
    if item["provenance_grade"] not in {"A", "B"}:
        return False, "CONSENSUS_PROVENANCE_GRADE_INCOMPLETE"
    if not item["source_url"] or not item["source_publisher"]:
        return False, "CONSENSUS_SOURCE_IDENTITY_MISSING"
    return True, None


def validate_and_finalize_record(record: dict) -> dict:
    freeze = load_freeze()
    out = deepcopy(record)
    release_at = _parse_utc(out["release_at_utc"])
    local_release = release_at.astimezone(NY)

    errors: list[str] = []
    if out.get("event_type") != "US_CPI":
        errors.append("EVENT_TYPE_INVALID")
    if not START_DATE <= out.get("release_date_local", "") <= END_DATE:
        errors.append("EVENT_DATE_OUT_OF_SCOPE")
    if local_release.strftime("%H:%M:%S") != freeze["scope"]["expected_release_clock_time"]:
        errors.append("RELEASE_TIME_NOT_0830_ET")
    if local_release.date().isoformat() != out.get("release_date_local"):
        errors.append("RELEASE_LOCAL_DATE_MISMATCH")

    actual_ok = _actual_provenance_complete(out)
    if not actual_ok:
        errors.append("ACTUAL_PROVENANCE_INCOMPLETE")

    consensus_grades: list[str] = []
    field_error_prefixes = tuple(f"{field}:" for field in FIELDS)
    for field in FIELDS:
        ok, reason = _consensus_field_valid(out["consensus"].get(field), release_at)
        if not ok:
            errors.append(f"{field}:{reason}")
            out["raw_surprises"][field] = None
            continue
        item = out["consensus"][field]
        consensus_grades.append(item["provenance_grade"])
        if out["actuals"][field] is None:
            errors.append(f"{field}:ACTUAL_VALUE_MISSING")
            out["raw_surprises"][field] = None
        else:
            out["raw_surprises"][field] = (
                float(out["actuals"][field]) - float(item["value"])
            )

    if not actual_ok:
        status = "ACTUAL_PROVENANCE_INCOMPLETE"
    elif any(err.startswith(field_error_prefixes) for err in errors):
        status = "CONSENSUS_PROVENANCE_INCOMPLETE"
    elif consensus_grades and all(g == "A" for g in consensus_grades):
        status = "COMPLETE_A"
    elif consensus_grades and all(g in {"A", "B"} for g in consensus_grades):
        status = "COMPLETE_B"
    else:
        status = "REVIEW_REQUIRED"

    out["record_status"] = status
    out["missing_reasons"] = sorted(set(errors))
    out["record_fingerprint"] = record_fingerprint(out)
    return out


def validate_manifest_records(manifest: dict) -> dict:
    load_freeze()
    records = [validate_and_finalize_record(r) for r in manifest["records"]]
    ids = [r["event_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate V0.3A event_id")
    counts: dict[str, int] = {}
    for record in records:
        counts[record["record_status"]] = counts.get(record["record_status"], 0) + 1
    receipt = {
        "document_type": "NEWS_SHOCK_LAB_V03A_PROVENANCE_VALIDATION_RECEIPT",
        "version": "0.3A",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "record_count": len(records),
        "status_counts": counts,
        "complete_a_count": counts.get("COMPLETE_A", 0),
        "complete_b_count": counts.get("COMPLETE_B", 0),
        "guards": {
            "market_outcomes_accessed": False,
            "crypto_returns_computed": False,
            "profitability_computed": False,
            "holdout_2026_accessed": False,
            "mexc_2025_09_through_2025_12_accessed": False,
        },
        "records": records,
    }
    receipt["fingerprint"] = canonical_hash(receipt)
    return receipt


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_slots = sub.add_parser("slots")
    p_slots.add_argument("output")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("input")
    p_validate.add_argument("output")

    args = parser.parse_args()
    if args.command == "slots":
        manifest = build_event_slot_manifest(Path(args.output))
        print(json.dumps({
            "status": manifest["status"],
            "event_count": manifest["selection"]["event_count"],
            "fingerprint": manifest["fingerprint"],
            "guards": manifest["guards"],
        }, indent=2, sort_keys=True))
    elif args.command == "validate":
        source = json.loads(Path(args.input).read_text(encoding="utf-8"))
        receipt = validate_manifest_records(source)
        Path(args.output).write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "record_count": receipt["record_count"],
            "status_counts": receipt["status_counts"],
            "fingerprint": receipt["fingerprint"],
            "guards": receipt["guards"],
        }, indent=2, sort_keys=True))
