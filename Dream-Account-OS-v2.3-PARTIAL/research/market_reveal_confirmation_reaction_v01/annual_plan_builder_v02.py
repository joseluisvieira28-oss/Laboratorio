"""Deterministic real annual-plan builder for MRCR H02 V0.2.

Consumes only a READY live official-calendar status receipt produced by
official_2027_calendar_live_probe.py. It does not fetch data, infer dates,
authorize target observation, or compute outcomes.
"""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any, Mapping

from h02_calendar_binding_v02 import (
    annual_plan_sha256,
    validate_annual_plan_manifest,
)


MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def _parse_bls_release_date(value: str) -> date:
    for fmt in ("%b. %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    # May has no period in BLS abbreviation.
    try:
        return datetime.strptime(value, "%B %d, %Y").date()
    except ValueError as exc:
        raise ValueError(f"invalid BLS release date: {value}") from exc


def _parse_fomc_meeting(value: str, *, year: int) -> tuple[date, date]:
    match = re.fullmatch(r"([A-Z][a-z]+)\s+(\d{1,2})-(\d{1,2})", value.strip())
    if match is None:
        raise ValueError(f"invalid FOMC meeting range: {value}")
    month_name, start_day, end_day = match.groups()
    if month_name not in MONTHS:
        raise ValueError(f"invalid FOMC meeting month: {month_name}")
    month = MONTHS[month_name]
    return (
        date(year, month, int(start_day)),
        date(year, month, int(end_day)),
    )


def build_annual_plan_v02_from_live_status(
    *,
    live_status: Mapping[str, Any],
    ruleset: Mapping[str, Any],
) -> dict[str, Any]:
    if live_status.get("document_type") != "MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01":
        raise ValueError("LIVE_STATUS_DOCUMENT_TYPE_MISMATCH")
    if live_status.get("status") != "READY_FOR_V02_ANNUAL_PLAN":
        raise ValueError("LIVE_STATUS_NOT_READY_FOR_V02_ANNUAL_PLAN")
    if live_status.get("annual_plan_trigger_ready_v02") is not True:
        raise ValueError("ANNUAL_PLAN_TRIGGER_NOT_READY")
    if live_status.get("inferred_dates_used") is not False:
        raise ValueError("LIVE_STATUS_INFERRED_DATES_PRESENT")

    checked_at = live_status.get("checked_at_utc")
    if not isinstance(checked_at, str) or not checked_at:
        raise ValueError("LIVE_STATUS_CHECKED_AT_MISSING")

    sources = live_status.get("sources") or {}
    cpi = sources.get("US_CPI") or {}
    jobs = sources.get("US_EMPLOYMENT_SITUATION") or {}
    fomc = sources.get("FOMC_STATEMENT") or {}

    if cpi.get("confirmed_2027_event_count") != 12:
        raise ValueError("CPI_2027_COUNT_NOT_12")
    if jobs.get("confirmed_2027_event_count") != 12:
        raise ValueError("EMPLOYMENT_2027_COUNT_NOT_12")
    if fomc.get("observed_2027_meeting_count") != 8:
        raise ValueError("FOMC_2027_COUNT_NOT_8")
    if fomc.get("annual_plan_bindable_v02") is not True:
        raise ValueError("FOMC_ANNUAL_PLAN_NOT_BINDABLE")

    official_sources = [
        {
            "authority": "BLS",
            "source_url": str(cpi["source_url"]),
            "retrieved_at_utc": checked_at,
            "evidence_format": str(cpi.get("evidence_format") or ""),
            "extracted_text_sha256": str(cpi.get("extracted_text_sha256") or ""),
        },
        {
            "authority": "BLS",
            "source_url": str(jobs["source_url"]),
            "retrieved_at_utc": checked_at,
            "evidence_format": str(jobs.get("evidence_format") or ""),
            "extracted_text_sha256": str(jobs.get("extracted_text_sha256") or ""),
        },
        {
            "authority": "FEDERAL_RESERVE",
            "source_url": str(fomc["source_url"]),
            "retrieved_at_utc": checked_at,
            "evidence_format": str(fomc.get("evidence_format") or ""),
            "extracted_text_sha256": str(fomc.get("extracted_text_sha256") or ""),
        },
    ]

    events: list[dict[str, Any]] = []

    cpi_events = sorted(
        cpi.get("events_2027") or [],
        key=lambda row: _parse_bls_release_date(str(row["release_date"])),
    )
    jobs_events = sorted(
        jobs.get("events_2027") or [],
        key=lambda row: _parse_bls_release_date(str(row["release_date"])),
    )

    for index, row in enumerate(cpi_events, 1):
        release_date = _parse_bls_release_date(str(row["release_date"]))
        if release_date.year != 2027:
            raise ValueError("CPI_EVENT_OUTSIDE_2027")
        if row.get("official_status") != "CONFIRMED":
            raise ValueError("CPI_EVENT_NOT_CONFIRMED")
        events.append({
            "event_id": f"US_CPI-2027-{index:02d}",
            "event_family": "US_CPI",
            "scheduled_date": release_date.isoformat(),
            "official_plan_status": "OFFICIAL_CONFIRMED",
            "official_source_ref": 0,
            "reference_period": row.get("reference_month"),
        })

    for index, row in enumerate(jobs_events, 1):
        release_date = _parse_bls_release_date(str(row["release_date"]))
        if release_date.year != 2027:
            raise ValueError("EMPLOYMENT_EVENT_OUTSIDE_2027")
        if row.get("official_status") != "CONFIRMED":
            raise ValueError("EMPLOYMENT_EVENT_NOT_CONFIRMED")
        events.append({
            "event_id": f"US_EMPLOYMENT_SITUATION-2027-{index:02d}",
            "event_family": "US_EMPLOYMENT_SITUATION",
            "scheduled_date": release_date.isoformat(),
            "official_plan_status": "OFFICIAL_CONFIRMED",
            "official_source_ref": 1,
            "reference_period": row.get("reference_month"),
        })

    meetings = []
    for value in fomc.get("observed_2027_meetings") or []:
        start, end = _parse_fomc_meeting(str(value), year=2027)
        meetings.append((start, end))
    meetings.sort(key=lambda pair: pair[1])

    fomc_status = (
        "OFFICIAL_TENTATIVE"
        if fomc.get("official_tentative_note_present") is True
        else "OFFICIAL_CONFIRMED"
    )
    for index, (start, end) in enumerate(meetings, 1):
        events.append({
            "event_id": f"FOMC_STATEMENT-2027-{index:02d}",
            "event_family": "FOMC_STATEMENT",
            "scheduled_date": end.isoformat(),
            "meeting_start_date": start.isoformat(),
            "meeting_end_date": end.isoformat(),
            "official_plan_status": fomc_status,
            "official_source_ref": 2,
        })

    manifest: dict[str, Any] = {
        "document_type": "MRCR_H02_ANNUAL_PLAN_MANIFEST_V02",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "calendar_year": 2027,
        "complete_official_annual_plan": True,
        "event_families": [
            "US_CPI",
            "US_EMPLOYMENT_SITUATION",
            "FOMC_STATEMENT",
        ],
        "official_sources": official_sources,
        "events": events,
        "inferred_dates_used": False,
        "target_observation_authorized": False,
        "annual_plan_sha256": None,
    }
    manifest["annual_plan_sha256"] = annual_plan_sha256(manifest)

    ok, blockers = validate_annual_plan_manifest(manifest, ruleset=ruleset)
    if not ok:
        raise RuntimeError("BUILT_ANNUAL_PLAN_FAILED_VALIDATION:" + ",".join(blockers))
    return manifest
