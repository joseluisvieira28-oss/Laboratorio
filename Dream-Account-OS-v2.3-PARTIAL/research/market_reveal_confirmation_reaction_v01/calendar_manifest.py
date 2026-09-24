"""Official prospective calendar manifest validation for MRCR V0.1.

No calendar dates are embedded here. This validates provenance/completeness only.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def manifest_sha256(manifest: Mapping[str, Any]) -> str:
    clean = json.loads(json.dumps(manifest))
    clean["manifest_sha256"] = None
    return hashlib.sha256(canonical_json_bytes(clean)).hexdigest()


def validate_calendar_manifest(manifest: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    blockers: list[str] = []

    if manifest.get("document_type") != "MRCR_OFFICIAL_CALENDAR_MANIFEST_V01":
        blockers.append("DOCUMENT_TYPE_MISMATCH")
    if manifest.get("lab_id") != "MARKET-REVEAL-CONFIRMATION-REACTION-001":
        blockers.append("LAB_ID_MISMATCH")
    if str(manifest.get("calendar_year")) < "2027":
        blockers.append("CALENDAR_YEAR_BEFORE_2027")

    families = manifest.get("event_families")
    if not isinstance(families, list) or not families:
        blockers.append("EVENT_FAMILIES_MISSING")

    sources = manifest.get("official_sources")
    if not isinstance(sources, list) or not sources:
        blockers.append("OFFICIAL_SOURCES_MISSING")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, Mapping):
                blockers.append(f"SOURCE_{index}_INVALID")
                continue
            for field in ("authority", "source_url", "retrieved_at_utc"):
                if not source.get(field):
                    blockers.append(f"SOURCE_{index}_{field.upper()}_MISSING")

    events = manifest.get("events")
    if not isinstance(events, list) or not events:
        blockers.append("EVENTS_MISSING")
    else:
        identities: set[str] = set()
        for index, event in enumerate(events):
            if not isinstance(event, Mapping):
                blockers.append(f"EVENT_{index}_INVALID")
                continue
            for field in (
                "event_id",
                "event_family",
                "scheduled_time_utc",
                "official_source_ref",
            ):
                if not event.get(field):
                    blockers.append(f"EVENT_{index}_{field.upper()}_MISSING")
            event_id = event.get("event_id")
            if event_id in identities:
                blockers.append("DUPLICATE_EVENT_ID")
            identities.add(event_id)

    if manifest.get("complete_official_calendar") is not True:
        blockers.append("COMPLETE_OFFICIAL_CALENDAR_FALSE")

    claimed = manifest.get("manifest_sha256")
    if not claimed:
        blockers.append("MANIFEST_SHA256_MISSING")
    elif claimed != manifest_sha256(manifest):
        blockers.append("MANIFEST_SHA256_MISMATCH")

    return len(blockers) == 0, tuple(sorted(set(blockers)))
