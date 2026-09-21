#!/usr/bin/env python3
"""Fail-closed semantic validation beyond JSON Schema."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

UTC_SUFFIX = "Z"
ALLOWED_FIELDS = {
    "CPI": {"headline_cpi_mom", "headline_cpi_yoy", "core_cpi_mom", "core_cpi_yoy"},
    "EMPLOYMENT_SITUATION": {"nfp_change_k", "unemployment_rate", "ahe_mom", "ahe_yoy"},
}


def utc(value: str) -> datetime:
    if not value.endswith(UTC_SUFFIX):
        raise ValueError("UTC_Z_REQUIRED")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def validate_event(record: dict) -> list[str]:
    errors: list[str] = []
    release = utc(record["scheduled_release_utc"])
    cutoff = utc(record["cutoff_utc"])
    local = release.astimezone(ZoneInfo("America/New_York"))
    if local.strftime("%H:%M:%S") != "08:30:00":
        errors.append("RELEASE_CLOCK_NOT_0830_ET")
    year = local.year
    if year not in {2021, 2022, 2023, 2024}:
        errors.append("OUT_OF_SCOPE_BLOCKED")
    if record["release_timezone"] != "America/New_York":
        errors.append("TIMEZONE_INVALID")

    evidence = {e["evidence_id"]: e for e in record["evidence"]}
    seen = set()
    roles = {}
    for obs in record["observations"]:
        key = (obs["field"], obs["role"])
        if key in seen:
            errors.append("DUPLICATE_OBSERVATION")
        seen.add(key)
        if obs["field"] not in ALLOWED_FIELDS[record["event_family"]]:
            errors.append("FIELD_FAMILY_MISMATCH")
        if obs.get("value") is None:
            errors.append("MISSING_VALUE_NOT_COMPLETE")
        ev = evidence.get(obs.get("evidence_id"))
        if not ev:
            errors.append("EVIDENCE_MISSING")
            continue
        if obs["role"] == "consensus":
            published = ev.get("published_at_utc")
            if not published:
                errors.append("CONSENSUS_PUBLICATION_TIME_MISSING")
            elif not utc(published) < cutoff:
                errors.append("CONSENSUS_NOT_STRICTLY_PRE_T0")
            if ev.get("temporal_proof") not in {"PRE_T0_DIRECT", "PRE_T0_ARCHIVE"}:
                errors.append("CONSENSUS_TEMPORAL_PROOF_INVALID")
        roles.setdefault(obs["field"], set()).add(obs["role"])

    for field in ALLOWED_FIELDS[record["event_family"]]:
        if roles.get(field) != {"actual_first_release", "consensus"}:
            errors.append(f"FIELD_ROLE_INCOMPLETE:{field}")
    return sorted(set(errors))
