"""MRCR H02 calendar binding V0.2.

Stage A validates the complete official annual plan by date/family provenance.
Stage B validates an exact official event activation receipt before T0.

This module does not authorize target observation and does not inspect outcomes.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from typing import Any, Mapping
from urllib.parse import urlparse


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
FOMC_ALLOWED_PLAN_STATUSES = {
    "OFFICIAL_CONFIRMED",
    "OFFICIAL_TENTATIVE",
}


def _host_matches(url: Any, expected_host: str) -> bool:
    if not isinstance(url, str) or not url:
        return False
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host == expected_host or host.endswith("." + expected_host)


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


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


def validate_annual_plan_manifest(
    manifest: Mapping[str, Any],
    *,
    ruleset: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    blockers: list[str] = []

    if manifest.get("document_type") != "MRCR_H02_ANNUAL_PLAN_MANIFEST_V02":
        blockers.append("DOCUMENT_TYPE_MISMATCH")
    if manifest.get("lab_id") != "MARKET-REVEAL-CONFIRMATION-REACTION-001":
        blockers.append("LAB_ID_MISMATCH")
    if manifest.get("h02_id") != "MRCR-H02-ACCEPTANCE-REJECTION-V01":
        blockers.append("H02_ID_MISMATCH")
    if manifest.get("calendar_year") != EXPECTED_YEAR:
        blockers.append("CALENDAR_YEAR_MISMATCH")

    scope = ruleset.get("event_scope") or {}
    if tuple(scope.get("event_families") or ()) != EXPECTED_FAMILIES:
        blockers.append("FROZEN_RULESET_FAMILY_MISMATCH")
    if scope.get("calendar_year") != EXPECTED_YEAR:
        blockers.append("FROZEN_RULESET_YEAR_MISMATCH")
    if scope.get("complete_official_calendar_required") is not True:
        blockers.append("FROZEN_RULESET_COMPLETE_CALENDAR_NOT_REQUIRED")

    if tuple(manifest.get("event_families") or ()) != EXPECTED_FAMILIES:
        blockers.append("ANNUAL_PLAN_FAMILIES_MISMATCH")

    sources = manifest.get("official_sources")
    events = manifest.get("events")
    if not isinstance(sources, list) or not sources:
        blockers.append("OFFICIAL_SOURCES_MISSING")
        sources = []
    if not isinstance(events, list):
        blockers.append("EVENTS_MISSING")
        events = []

    counts: Counter[str] = Counter()
    identities: set[str] = set()
    family_dates: set[tuple[str, str]] = set()

    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            blockers.append(f"EVENT_{index}_INVALID")
            continue

        event_id = event.get("event_id")
        family = event.get("event_family")
        event_date = event.get("scheduled_date")
        status = event.get("official_plan_status")
        source_ref = event.get("official_source_ref")

        if not isinstance(event_id, str) or not event_id:
            blockers.append(f"EVENT_{index}_ID_MISSING")
        elif event_id in identities:
            blockers.append("DUPLICATE_EVENT_ID")
        else:
            identities.add(event_id)

        if family not in EXPECTED_COUNTS:
            blockers.append(f"EVENT_{index}_FAMILY_INVALID")
            continue
        counts[str(family)] += 1

        parsed_date = _parse_date(event_date)
        if parsed_date is None or parsed_date.year != EXPECTED_YEAR:
            blockers.append(f"EVENT_{index}_DATE_INVALID")

        key = (str(family), str(event_date))
        if key in family_dates:
            blockers.append("DUPLICATE_FAMILY_DATE")
        family_dates.add(key)

        if family == "FOMC_STATEMENT":
            if status not in FOMC_ALLOWED_PLAN_STATUSES:
                blockers.append(f"EVENT_{index}_FOMC_PLAN_STATUS_INVALID")
        elif status != "OFFICIAL_CONFIRMED":
            blockers.append(f"EVENT_{index}_BLS_PLAN_STATUS_NOT_CONFIRMED")

        if isinstance(source_ref, bool) or not isinstance(source_ref, int):
            blockers.append(f"EVENT_{index}_SOURCE_REF_INVALID")
            continue
        if not (0 <= source_ref < len(sources)):
            blockers.append(f"EVENT_{index}_SOURCE_REF_OUT_OF_RANGE")
            continue

        source = sources[source_ref]
        if not isinstance(source, Mapping):
            blockers.append(f"EVENT_{index}_SOURCE_INVALID")
            continue
        authority, domain = EXPECTED_SOURCE[str(family)]
        if source.get("authority") != authority:
            blockers.append(f"EVENT_{index}_AUTHORITY_MISMATCH")
        if not _host_matches(source.get("source_url"), domain):
            blockers.append(f"EVENT_{index}_DOMAIN_MISMATCH")
        if _parse_utc(source.get("retrieved_at_utc")) is None:
            blockers.append(f"EVENT_{index}_SOURCE_RETRIEVED_AT_INVALID")

    for family, expected in EXPECTED_COUNTS.items():
        if counts[family] != expected:
            blockers.append(f"{family}_COUNT_{counts[family]}_EXPECTED_{expected}")

    if manifest.get("complete_official_annual_plan") is not True:
        blockers.append("COMPLETE_OFFICIAL_ANNUAL_PLAN_FALSE")
    if manifest.get("inferred_dates_used") is not False:
        blockers.append("INFERRED_DATES_MUST_BE_FALSE")
    if manifest.get("target_observation_authorized") is not False:
        blockers.append("ANNUAL_PLAN_CANNOT_AUTHORIZE_TARGET")

    return len(blockers) == 0, tuple(sorted(set(blockers)))


def validate_event_activation_receipt(
    receipt: Mapping[str, Any],
    *,
    annual_plan: Mapping[str, Any],
    now_utc: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    blockers: list[str] = []

    if receipt.get("document_type") != "MRCR_H02_EVENT_ACTIVATION_RECEIPT_V02":
        blockers.append("DOCUMENT_TYPE_MISMATCH")
    if receipt.get("lab_id") != "MARKET-REVEAL-CONFIRMATION-REACTION-001":
        blockers.append("LAB_ID_MISMATCH")
    if receipt.get("h02_id") != "MRCR-H02-ACCEPTANCE-REJECTION-V01":
        blockers.append("H02_ID_MISMATCH")

    event_id = receipt.get("event_id")
    family = receipt.get("event_family")
    t0 = _parse_utc(receipt.get("scheduled_time_utc"))
    confirmed_at = _parse_utc(receipt.get("confirmed_at_utc"))
    source_url = receipt.get("official_source_url")
    authority = receipt.get("official_authority")

    plan_rows = [
        row for row in annual_plan.get("events", [])
        if isinstance(row, Mapping) and row.get("event_id") == event_id
    ]
    if len(plan_rows) != 1:
        blockers.append("EVENT_NOT_UNIQUELY_BOUND_TO_ANNUAL_PLAN")
        plan_row = None
    else:
        plan_row = plan_rows[0]

    if family not in EXPECTED_SOURCE:
        blockers.append("EVENT_FAMILY_INVALID")
    elif plan_row is not None and plan_row.get("event_family") != family:
        blockers.append("EVENT_FAMILY_PLAN_MISMATCH")

    if t0 is None or t0.year != EXPECTED_YEAR:
        blockers.append("T0_INVALID_OR_WRONG_YEAR")
    if confirmed_at is None:
        blockers.append("CONFIRMED_AT_INVALID")
    if t0 is not None and confirmed_at is not None and confirmed_at >= t0:
        blockers.append("CONFIRMATION_NOT_BEFORE_T0")

    if receipt.get("official_status") != "OFFICIAL_CONFIRMED_FOR_CAPTURE":
        blockers.append("EVENT_NOT_CONFIRMED_FOR_CAPTURE")

    if family in EXPECTED_SOURCE:
        expected_authority, expected_domain = EXPECTED_SOURCE[str(family)]
        if authority != expected_authority:
            blockers.append("OFFICIAL_AUTHORITY_MISMATCH")
        if not _host_matches(source_url, expected_domain):
            blockers.append("OFFICIAL_DOMAIN_MISMATCH")

    if plan_row is not None and t0 is not None:
        plan_date = _parse_date(plan_row.get("scheduled_date"))
        if plan_date is None or t0.date() != plan_date:
            blockers.append("T0_DATE_DIFFERS_FROM_ANNUAL_PLAN")

    if now_utc is not None:
        now = _parse_utc(now_utc)
        if now is None:
            blockers.append("NOW_UTC_INVALID")
        elif t0 is not None and now >= t0:
            blockers.append("ACTIVATION_CHECK_AT_OR_AFTER_T0")

    if receipt.get("target_observation_authorized") is not False:
        blockers.append("EVENT_RECEIPT_CANNOT_SELF_AUTHORIZE_TARGET")
    if receipt.get("outcomes_authorized") is not False:
        blockers.append("EVENT_RECEIPT_CANNOT_AUTHORIZE_OUTCOMES")

    return len(blockers) == 0, tuple(sorted(set(blockers)))
