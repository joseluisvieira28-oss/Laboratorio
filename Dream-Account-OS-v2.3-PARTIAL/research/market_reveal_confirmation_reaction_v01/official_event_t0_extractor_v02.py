"""Offline official T0 extraction for MRCR H02 event activation V0.2.

No network access. Callers must supply text fetched from official sources and
the source retrieval timestamps. This module normalizes those official texts
into exact UTC T0 evidence without using historical market outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any
from zoneinfo import ZoneInfo


EASTERN = ZoneInfo("America/New_York")

BLS_FAMILIES = {
    "US_CPI": "Consumer Price Index",
    "US_EMPLOYMENT_SITUATION": "Employment Situation",
}

BLS_MONTHS = {
    "Jan.": 1,
    "Feb.": 2,
    "Mar.": 3,
    "Apr.": 4,
    "May": 5,
    "Jun.": 6,
    "Jul.": 7,
    "Aug.": 8,
    "Sep.": 9,
    "Oct.": 10,
    "Nov.": 11,
    "Dec.": 12,
}

FED_STATEMENT_TIME_RULE = (
    "The Committee releases a policy statement at 2 p.m. Eastern Time "
    "on the second day of each regularly scheduled meeting"
)


@dataclass(frozen=True)
class OfficialT0Evidence:
    event_family: str
    scheduled_date: str
    scheduled_time_utc: str
    local_time_eastern: str
    confirmation_mode: str
    evidence_roles: tuple[str, ...]


def _utc_z(dt: datetime) -> str:
    return dt.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")


def _parse_iso_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("plan date must be YYYY-MM-DD") from exc
    return parsed


def _parse_bls_rows(text: str) -> list[tuple[str, date, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    date_re = re.compile(
        r"^(Jan\.|Feb\.|Mar\.|Apr\.|May|Jun\.|Jul\.|Aug\.|Sep\.|Oct\.|Nov\.|Dec\.)\s+(\d{1,2}),\s+(\d{4})$"
    )
    ref_re = re.compile(r"^[A-Z][a-z]+\s+\d{4}$")
    time_re = re.compile(r"^(\d{1,2}):(\d{2})\s+(AM|PM)$")

    rows: list[tuple[str, date, str]] = []
    for i in range(max(0, len(lines) - 2)):
        ref = lines[i]
        release_date = lines[i + 1]
        release_time = lines[i + 2]
        dm = date_re.match(release_date)
        tm = time_re.match(release_time)
        if not ref_re.match(ref) or dm is None or tm is None:
            continue
        month = BLS_MONTHS[dm.group(1)]
        rows.append(
            (
                ref,
                date(int(dm.group(3)), month, int(dm.group(2))),
                release_time,
            )
        )
    return rows


def extract_bls_t0(
    *,
    event_family: str,
    plan_date: str,
    schedule_text: str,
    dissemination_policy_text: str,
) -> OfficialT0Evidence:
    if event_family not in BLS_FAMILIES:
        raise ValueError("unsupported BLS event family")

    policy_required = (
        "All seven PFEIs are scheduled for release at 8:30 a.m. Eastern Time"
    )
    if policy_required not in dissemination_policy_text:
        raise ValueError("BLS_PFEI_EASTERN_TIME_POLICY_NOT_PROVEN")
    if BLS_FAMILIES[event_family] not in dissemination_policy_text:
        raise ValueError("BLS_FAMILY_NOT_LISTED_AS_PFEI")

    target = _parse_iso_date(plan_date)
    matches = [row for row in _parse_bls_rows(schedule_text) if row[1] == target]
    if len(matches) != 1:
        raise ValueError("BLS_PLAN_DATE_NOT_UNIQUELY_PRESENT")

    _, _, release_time = matches[0]
    if release_time != "08:30 AM":
        raise ValueError("BLS_RELEASE_TIME_NOT_0830_ET")

    local = datetime(
        target.year,
        target.month,
        target.day,
        8,
        30,
        tzinfo=EASTERN,
    )
    return OfficialT0Evidence(
        event_family=event_family,
        scheduled_date=plan_date,
        scheduled_time_utc=_utc_z(local),
        local_time_eastern=local.isoformat(),
        confirmation_mode="BLS_OFFICIAL_SCHEDULE_PLUS_PFEI_TIME_POLICY",
        evidence_roles=("BLS_RELEASE_SCHEDULE", "BLS_DISSEMINATION_POLICY"),
    )


def _normalize_space(value: str) -> str:
    return " ".join(value.replace("–", "-").replace("—", "-").split())


def _fomc_schedule_contains_meeting(
    text: str,
    *,
    start_date: date,
    end_date: date,
) -> bool:
    normalized = _normalize_space(text)
    start_month = start_date.strftime("%B")
    end_month = end_date.strftime("%B")
    start_day = str(start_date.day)
    end_day = str(end_date.day)

    same_month_candidates = (
        f"{start_month} {start_day}, and Wednesday, {end_month} {end_day}",
        f"{start_month} {start_day}, and {end_month} {end_day}",
    )
    if start_date.month == end_date.month and any(
        candidate in normalized for candidate in same_month_candidates
    ):
        return True

    cross_month = (
        f"{start_month} {start_day}, and Wednesday, {end_month} {end_day}"
    )
    return cross_month in normalized


def _preceding_minutes_confirm_next_meeting(
    text: str,
    *,
    start_date: date,
    end_date: date,
) -> bool:
    normalized = _normalize_space(text)
    # Minutes historically use wording such as:
    # "It was agreed that the next meeting of the Committee would be held on
    # Tuesday-Wednesday, October 27-28, 2015."
    if "It was agreed that the next meeting of the Committee would be held" not in normalized:
        return False

    month = start_date.strftime("%B")
    if start_date.month == end_date.month:
        patterns = (
            f"{month} {start_date.day}-{end_date.day}, {end_date.year}",
            f"{month} {start_date.day} - {end_date.day}, {end_date.year}",
        )
    else:
        patterns = (
            f"{start_date.strftime('%B')} {start_date.day}-{end_date.strftime('%B')} {end_date.day}, {end_date.year}",
            f"{start_date.strftime('%B')} {start_date.day} - {end_date.strftime('%B')} {end_date.day}, {end_date.year}",
        )
    return any(pattern in normalized for pattern in patterns)


def extract_fomc_t0(
    *,
    plan_start_date: str,
    plan_end_date: str,
    annual_schedule_announcement_text: str,
    preceding_meeting_minutes_text: str,
) -> OfficialT0Evidence:
    start = _parse_iso_date(plan_start_date)
    end = _parse_iso_date(plan_end_date)
    if end < start:
        raise ValueError("FOMC_END_BEFORE_START")
    if (end - start).days not in {1, 2}:
        raise ValueError("FOMC_REGULAR_MEETING_RANGE_INVALID")

    normalized_announcement = _normalize_space(
        annual_schedule_announcement_text
    )
    if FED_STATEMENT_TIME_RULE not in normalized_announcement:
        raise ValueError("FOMC_2PM_ET_STATEMENT_RULE_NOT_PROVEN")
    if not _fomc_schedule_contains_meeting(
        annual_schedule_announcement_text,
        start_date=start,
        end_date=end,
    ):
        raise ValueError("FOMC_MEETING_NOT_IN_OFFICIAL_ANNUAL_SCHEDULE")
    if not _preceding_minutes_confirm_next_meeting(
        preceding_meeting_minutes_text,
        start_date=start,
        end_date=end,
    ):
        raise ValueError("FOMC_NEXT_MEETING_NOT_CONFIRMED_BY_PRECEDING_MINUTES")

    local = datetime(
        end.year,
        end.month,
        end.day,
        14,
        0,
        tzinfo=EASTERN,
    )
    return OfficialT0Evidence(
        event_family="FOMC_STATEMENT",
        scheduled_date=end.isoformat(),
        scheduled_time_utc=_utc_z(local),
        local_time_eastern=local.isoformat(),
        confirmation_mode="FOMC_ANNUAL_SCHEDULE_TIME_RULE_PLUS_PRECEDING_MINUTES_CONFIRMATION",
        evidence_roles=(
            "FOMC_ANNUAL_SCHEDULE_ANNOUNCEMENT",
            "FOMC_PRECEDING_MEETING_MINUTES_CONFIRMATION",
        ),
    )
