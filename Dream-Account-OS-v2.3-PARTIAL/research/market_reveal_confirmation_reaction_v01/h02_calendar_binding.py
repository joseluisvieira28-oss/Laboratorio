"""H02-specific official calendar completeness and provenance gate.

This is a governance/provenance validator, not a scientific selector. It binds
the already-frozen H02 event families to a complete confirmed 2027 official
calendar and rejects partial, tentative, wrong-domain or wrong-year manifests.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import urlparse

from calendar_manifest import validate_calendar_manifest


EXPECTED_YEAR = 2027
EXPECTED_FAMILIES = (
    "US_CPI",
    "US_EMPLOYMENT_SITUATION",
    "FOMC_STATEMENT",
)
EXPECTED_COUNTS = {
    "US_CPI": 12,
    "US_EMPLOYMENT_SITUATION": 12,
    "FOMC_STATEMENT": 8,
}
EXPECTED_SOURCE = {
    "US_CPI": ("BLS", "bls.gov"),
    "US_EMPLOYMENT_SITUATION": ("BLS", "bls.gov"),
    "FOMC_STATEMENT": ("FEDERAL_RESERVE", "federalreserve.gov"),
}


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def _host_matches(url: Any, expected_host: str) -> bool:
    if not isinstance(url, str) or not url:
        return False
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host == expected_host or host.endswith("." + expected_host)


def validate_h02_calendar_manifest(
    manifest: Mapping[str, Any],
    *,
    ruleset: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    blockers: list[str] = []

    generic_ok, generic_blockers = validate_calendar_manifest(manifest)
    if not generic_ok:
        blockers.extend(generic_blockers)

    event_scope = ruleset.get("event_scope") or {}
    frozen_families = tuple(event_scope.get("event_families") or ())
    frozen_year = event_scope.get("calendar_year")

    if frozen_families != EXPECTED_FAMILIES:
        blockers.append("FROZEN_RULESET_EVENT_FAMILIES_UNEXPECTED")
    if frozen_year != EXPECTED_YEAR:
        blockers.append("FROZEN_RULESET_CALENDAR_YEAR_UNEXPECTED")

    if manifest.get("calendar_year") != EXPECTED_YEAR:
        blockers.append("H02_CALENDAR_YEAR_MUST_EQUAL_2027")
    if tuple(manifest.get("event_families") or ()) != EXPECTED_FAMILIES:
        blockers.append("H02_EVENT_FAMILIES_EXACT_SET_ORDER_REQUIRED")

    sources = manifest.get("official_sources")
    events = manifest.get("events")
    completeness = manifest.get("family_completeness")

    if not isinstance(completeness, Mapping):
        blockers.append("FAMILY_COMPLETENESS_MISSING")
        completeness = {}

    if not isinstance(sources, list):
        sources = []
    if not isinstance(events, list):
        events = []

    actual_counts: Counter[str] = Counter()
    seen_family_time: set[tuple[str, str]] = set()

    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            continue

        family = event.get("event_family")
        if family not in EXPECTED_COUNTS:
            blockers.append(f"EVENT_{index}_FAMILY_NOT_IN_FROZEN_SCOPE")
            continue

        actual_counts[str(family)] += 1

        scheduled = event.get("scheduled_time_utc")
        scheduled_dt = _parse_utc(scheduled)
        if scheduled_dt is None:
            blockers.append(f"EVENT_{index}_SCHEDULED_TIME_UTC_INVALID")
        elif scheduled_dt.year != EXPECTED_YEAR:
            blockers.append(f"EVENT_{index}_OUTSIDE_2027")

        if event.get("official_status") != "CONFIRMED":
            blockers.append(f"EVENT_{index}_NOT_CONFIRMED")

        key = (str(family), str(scheduled))
        if key in seen_family_time:
            blockers.append("DUPLICATE_FAMILY_SCHEDULED_TIME")
        seen_family_time.add(key)

        source_ref = event.get("official_source_ref")
        if isinstance(source_ref, bool) or not isinstance(source_ref, int):
            continue
        if not (0 <= source_ref < len(sources)):
            continue
        source = sources[source_ref]
        if not isinstance(source, Mapping):
            continue

        expected_authority, expected_host = EXPECTED_SOURCE[str(family)]
        if source.get("authority") != expected_authority:
            blockers.append(f"EVENT_{index}_OFFICIAL_AUTHORITY_MISMATCH")
        if not _host_matches(source.get("source_url"), expected_host):
            blockers.append(f"EVENT_{index}_OFFICIAL_DOMAIN_MISMATCH")
        if source.get("publication_status") != "OFFICIAL_COMPLETE":
            blockers.append(f"EVENT_{index}_SOURCE_NOT_OFFICIAL_COMPLETE")
        if _parse_utc(source.get("retrieved_at_utc")) is None:
            blockers.append(f"EVENT_{index}_SOURCE_RETRIEVED_AT_INVALID")

    for family in EXPECTED_FAMILIES:
        expected_count = EXPECTED_COUNTS[family]
        if actual_counts[family] != expected_count:
            blockers.append(
                f"{family}_EVENT_COUNT_{actual_counts[family]}_EXPECTED_{expected_count}"
            )

        row = completeness.get(family)
        if not isinstance(row, Mapping):
            blockers.append(f"{family}_COMPLETENESS_DECLARATION_MISSING")
            continue
        if row.get("status") != "COMPLETE_OFFICIAL_CONFIRMED":
            blockers.append(f"{family}_COMPLETENESS_NOT_CONFIRMED")
        if row.get("calendar_year") != EXPECTED_YEAR:
            blockers.append(f"{family}_COMPLETENESS_YEAR_MISMATCH")
        if row.get("expected_event_count") != expected_count:
            blockers.append(f"{family}_EXPECTED_COUNT_DECLARATION_MISMATCH")
        if row.get("confirmed_event_count") != expected_count:
            blockers.append(f"{family}_CONFIRMED_COUNT_DECLARATION_MISMATCH")

        expected_authority, expected_host = EXPECTED_SOURCE[family]
        if row.get("authority") != expected_authority:
            blockers.append(f"{family}_COMPLETENESS_AUTHORITY_MISMATCH")
        if not _host_matches(row.get("source_url"), expected_host):
            blockers.append(f"{family}_COMPLETENESS_DOMAIN_MISMATCH")

    if set(completeness.keys()) != set(EXPECTED_FAMILIES):
        blockers.append("FAMILY_COMPLETENESS_EXACT_SET_REQUIRED")

    if manifest.get("all_events_confirmed") is not True:
        blockers.append("ALL_EVENTS_CONFIRMED_FALSE")
    if manifest.get("tentative_events_allowed") is not False:
        blockers.append("TENTATIVE_EVENTS_MUST_BE_FALSE")

    return len(blockers) == 0, tuple(sorted(set(blockers)))
