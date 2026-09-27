"""Live official Event Activation probe for MRCR H02 V0.2.

For a single event already present in the frozen annual plan:
- fetch official BLS/Federal Reserve evidence only;
- derive exact T0 through official_event_t0_extractor_v02;
- build a tamper-evident activation receipt;
- validate the receipt against the annual plan;
- optionally run the full event_capture_runtime_guard_v02 when protocol,
  implementation manifest and TARGET_OBSERVATION_OPEN authority are supplied.

It never opens target observation, computes outcomes, starts market-data capture,
or submits orders.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from event_activation_receipt_builder_v02 import (
    build_event_activation_receipt_v02,
)
from event_capture_runtime_guard_v02 import validate_event_capture_open_v02
from h02_calendar_binding_v02 import validate_event_activation_receipt
from official_event_t0_extractor_v02 import extract_bls_t0, extract_fomc_t0


BLS_CPI_URL = "https://www.bls.gov/schedule/news_release/cpi.htm"
BLS_EMPSIT_URL = "https://www.bls.gov/schedule/news_release/empsit.htm"
BLS_POLICY_URL = "https://www.bls.gov/about-bls/dissemination.htm"

FED_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FED_2027_ANNOUNCEMENT_URL = (
    "https://www.federalreserve.gov/newsevents/pressreleases/"
    "monetary20250905a.htm"
)
FED_MINUTES_BASE = "https://www.federalreserve.gov/monetarypolicy/"

USER_AGENT = "MRCR-H02-Event-Activation-Probe/0.2"

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


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = html.unescape(data)
        if text.strip():
            self.parts.append(text.strip())

    def text(self) -> str:
        return "\n".join(self.parts)


def _fetch_text(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html",
        },
    )
    with urlopen(request, timeout=15) as response:
        status = int(getattr(response, "status", 200))
        if status != 200:
            raise RuntimeError(f"HTTP_{status}")
        raw = response.read()
    parser = _TextExtractor()
    parser.feed(raw.decode("utf-8", errors="strict"))
    return parser.text()


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _find_event(annual_plan: Mapping[str, Any], event_id: str) -> dict[str, Any]:
    rows = [
        row
        for row in annual_plan.get("events", [])
        if isinstance(row, Mapping) and row.get("event_id") == event_id
    ]
    if len(rows) != 1:
        raise ValueError("EVENT_NOT_UNIQUELY_PRESENT_IN_ANNUAL_PLAN")
    return dict(rows[0])


def _extract_year_section(text: str, year: int) -> str:
    marker = f"{year} FOMC Meetings"
    start = text.find(marker)
    if start < 0:
        return ""
    tail = text[start + len(marker):]
    next_year = text.find(f"{year + 1} FOMC Meetings", start + len(marker))
    if next_year >= 0:
        return text[start + len(marker):next_year]
    return tail


def _parse_fomc_meetings(text: str, *, year: int) -> list[tuple[date, date]]:
    section = _extract_year_section(text, year)
    pattern = re.compile(
        r"(?m)^(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\n"
        r"(\d{1,2})-(\d{1,2})\*?$"
    )
    rows: list[tuple[date, date]] = []
    for month_name, start_day, end_day in pattern.findall(section):
        month = MONTHS[month_name]
        rows.append(
            (
                date(year, month, int(start_day)),
                date(year, month, int(end_day)),
            )
        )
    return rows


def _preceding_regular_meeting_end(
    *,
    calendar_text: str,
    target_start: date,
) -> date:
    meetings = [
        *_parse_fomc_meetings(calendar_text, year=target_start.year - 1),
        *_parse_fomc_meetings(calendar_text, year=target_start.year),
    ]
    candidates = [end for _, end in meetings if end < target_start]
    if not candidates:
        raise ValueError("PRECEDING_FOMC_MEETING_NOT_FOUND")
    return max(candidates)


def _minutes_url(end_date: date) -> str:
    return (
        FED_MINUTES_BASE
        + f"fomcminutes{end_date.strftime('%Y%m%d')}.htm"
    )


def _evaluate_receipt_only(
    *,
    annual_plan: Mapping[str, Any],
    event_id: str,
    retrieved_at_utc: str,
    bls_schedule_text: str | None = None,
    bls_policy_text: str | None = None,
    fomc_announcement_text: str | None = None,
    preceding_minutes_text: str | None = None,
    preceding_minutes_url: str | None = None,
) -> dict[str, Any]:
    event = _find_event(annual_plan, event_id)
    family = event.get("event_family")
    plan_date = str(event.get("scheduled_date"))

    if family == "US_CPI":
        if bls_schedule_text is None or bls_policy_text is None:
            raise ValueError("BLS_OFFICIAL_TEXTS_REQUIRED")
        evidence = extract_bls_t0(
            event_family="US_CPI",
            plan_date=plan_date,
            schedule_text=bls_schedule_text,
            dissemination_policy_text=bls_policy_text,
        )
        primary_url = BLS_CPI_URL
        supporting = [
            {
                "role": "BLS_RELEASE_SCHEDULE",
                "url": BLS_CPI_URL,
                "retrieved_at_utc": retrieved_at_utc,
            },
            {
                "role": "BLS_DISSEMINATION_POLICY",
                "url": BLS_POLICY_URL,
                "retrieved_at_utc": retrieved_at_utc,
            },
        ]
    elif family == "US_EMPLOYMENT_SITUATION":
        if bls_schedule_text is None or bls_policy_text is None:
            raise ValueError("BLS_OFFICIAL_TEXTS_REQUIRED")
        evidence = extract_bls_t0(
            event_family="US_EMPLOYMENT_SITUATION",
            plan_date=plan_date,
            schedule_text=bls_schedule_text,
            dissemination_policy_text=bls_policy_text,
        )
        primary_url = BLS_EMPSIT_URL
        supporting = [
            {
                "role": "BLS_RELEASE_SCHEDULE",
                "url": BLS_EMPSIT_URL,
                "retrieved_at_utc": retrieved_at_utc,
            },
            {
                "role": "BLS_DISSEMINATION_POLICY",
                "url": BLS_POLICY_URL,
                "retrieved_at_utc": retrieved_at_utc,
            },
        ]
    elif family == "FOMC_STATEMENT":
        if (
            fomc_announcement_text is None
            or preceding_minutes_text is None
            or preceding_minutes_url is None
        ):
            raise ValueError("FOMC_OFFICIAL_TEXTS_REQUIRED")
        start = event.get("meeting_start_date")
        end = event.get("meeting_end_date")
        if not isinstance(start, str) or not isinstance(end, str):
            raise ValueError("FOMC_ANNUAL_PLAN_MEETING_RANGE_MISSING")
        evidence = extract_fomc_t0(
            plan_start_date=start,
            plan_end_date=end,
            annual_schedule_announcement_text=fomc_announcement_text,
            preceding_meeting_minutes_text=preceding_minutes_text,
        )
        primary_url = FED_2027_ANNOUNCEMENT_URL
        supporting = [
            {
                "role": "FOMC_ANNUAL_SCHEDULE_ANNOUNCEMENT",
                "url": FED_2027_ANNOUNCEMENT_URL,
                "retrieved_at_utc": retrieved_at_utc,
            },
            {
                "role": "FOMC_PRECEDING_MEETING_MINUTES_CONFIRMATION",
                "url": preceding_minutes_url,
                "retrieved_at_utc": retrieved_at_utc,
            },
        ]
    else:
        raise ValueError("UNSUPPORTED_EVENT_FAMILY")

    receipt = build_event_activation_receipt_v02(
        event_id=event_id,
        evidence=evidence,
        confirmed_at_utc=retrieved_at_utc,
        primary_official_source_url=primary_url,
        supporting_official_sources=supporting,
    )
    ok, blockers = validate_event_activation_receipt(
        receipt,
        annual_plan=annual_plan,
        now_utc=retrieved_at_utc,
    )
    if not ok:
        raise RuntimeError(
            "ACTIVATION_RECEIPT_VALIDATION_FAILED:"
            + ",".join(blockers)
        )
    return receipt


def evaluate_event_activation_from_official_texts_v02(
    *,
    annual_plan: Mapping[str, Any],
    event_id: str,
    retrieved_at_utc: str,
    bls_schedule_text: str | None = None,
    bls_policy_text: str | None = None,
    fomc_announcement_text: str | None = None,
    preceding_minutes_text: str | None = None,
    preceding_minutes_url: str | None = None,
    protocol: Mapping[str, Any] | None = None,
    implementation_manifest: Mapping[str, Any] | None = None,
    target_open_authority: Mapping[str, Any] | None = None,
    ruleset: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    receipt = _evaluate_receipt_only(
        annual_plan=annual_plan,
        event_id=event_id,
        retrieved_at_utc=retrieved_at_utc,
        bls_schedule_text=bls_schedule_text,
        bls_policy_text=bls_policy_text,
        fomc_announcement_text=fomc_announcement_text,
        preceding_minutes_text=preceding_minutes_text,
        preceding_minutes_url=preceding_minutes_url,
    )

    runtime_inputs = (
        protocol,
        implementation_manifest,
        target_open_authority,
        ruleset,
    )
    supplied = [value is not None for value in runtime_inputs]
    if any(supplied) and not all(supplied):
        raise ValueError("PARTIAL_RUNTIME_GUARD_INPUTS_NOT_ALLOWED")

    if not all(supplied):
        return {
            "document_type": "MRCR_H02_LIVE_EVENT_ACTIVATION_STATUS_V02",
            "status": "ACTIVATION_RECEIPT_READY_TARGET_OBSERVATION_STILL_LOCKED",
            "event_id": event_id,
            "event_family": receipt["event_family"],
            "scheduled_time_utc": receipt["scheduled_time_utc"],
            "activation_receipt": receipt,
            "event_capture_runtime_ready": False,
            "target_observation_authorized": False,
            "outcomes_authorized": False,
            "orders_enabled": False,
            "promotion_credit": "NONE",
        }

    guard = validate_event_capture_open_v02(
        protocol=protocol,
        annual_plan=annual_plan,
        implementation_manifest=implementation_manifest,
        target_open_authority=target_open_authority,
        event_activation_receipt=receipt,
        ruleset=ruleset,
        now_utc=retrieved_at_utc,
    )
    return {
        "document_type": "MRCR_H02_LIVE_EVENT_ACTIVATION_STATUS_V02",
        "status": (
            "READY_FOR_EVENT_CAPTURE"
            if guard.ready
            else "BLOCKED_BY_RUNTIME_GUARD"
        ),
        "event_id": event_id,
        "event_family": receipt["event_family"],
        "scheduled_time_utc": receipt["scheduled_time_utc"],
        "activation_receipt": receipt,
        "event_capture_runtime_ready": guard.ready,
        "runtime_blockers": list(guard.blockers),
        "target_observation_authorized": (
            target_open_authority.get("authority_type")
            == "TARGET_OBSERVATION_OPEN"
        ),
        "outcomes_authorized": False,
        "orders_enabled": False,
        "promotion_credit": "NONE",
    }


def fetch_live_event_activation_v02(
    *,
    annual_plan: Mapping[str, Any],
    event_id: str,
    protocol: Mapping[str, Any] | None = None,
    implementation_manifest: Mapping[str, Any] | None = None,
    target_open_authority: Mapping[str, Any] | None = None,
    ruleset: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    event = _find_event(annual_plan, event_id)
    family = event.get("event_family")
    retrieved_at = _utc_now_z()

    try:
        if family == "US_CPI":
            return evaluate_event_activation_from_official_texts_v02(
                annual_plan=annual_plan,
                event_id=event_id,
                retrieved_at_utc=retrieved_at,
                bls_schedule_text=_fetch_text(BLS_CPI_URL),
                bls_policy_text=_fetch_text(BLS_POLICY_URL),
                protocol=protocol,
                implementation_manifest=implementation_manifest,
                target_open_authority=target_open_authority,
                ruleset=ruleset,
            )

        if family == "US_EMPLOYMENT_SITUATION":
            return evaluate_event_activation_from_official_texts_v02(
                annual_plan=annual_plan,
                event_id=event_id,
                retrieved_at_utc=retrieved_at,
                bls_schedule_text=_fetch_text(BLS_EMPSIT_URL),
                bls_policy_text=_fetch_text(BLS_POLICY_URL),
                protocol=protocol,
                implementation_manifest=implementation_manifest,
                target_open_authority=target_open_authority,
                ruleset=ruleset,
            )

        if family == "FOMC_STATEMENT":
            start = event.get("meeting_start_date")
            if not isinstance(start, str):
                raise ValueError("FOMC_ANNUAL_PLAN_MEETING_START_MISSING")
            target_start = date.fromisoformat(start)
            calendar_text = _fetch_text(FED_CALENDAR_URL)
            preceding_end = _preceding_regular_meeting_end(
                calendar_text=calendar_text,
                target_start=target_start,
            )
            minutes_url = _minutes_url(preceding_end)
            minutes_text = _fetch_text(minutes_url)
            return evaluate_event_activation_from_official_texts_v02(
                annual_plan=annual_plan,
                event_id=event_id,
                retrieved_at_utc=retrieved_at,
                fomc_announcement_text=_fetch_text(
                    FED_2027_ANNOUNCEMENT_URL
                ),
                preceding_minutes_text=minutes_text,
                preceding_minutes_url=minutes_url,
                protocol=protocol,
                implementation_manifest=implementation_manifest,
                target_open_authority=target_open_authority,
                ruleset=ruleset,
            )

        raise ValueError("UNSUPPORTED_EVENT_FAMILY")
    except HTTPError as exc:
        if exc.code == 404:
            return {
                "document_type": "MRCR_H02_LIVE_EVENT_ACTIVATION_STATUS_V02",
                "status": "EVIDENCE_NOT_READY",
                "event_id": event_id,
                "event_family": family,
                "http_status": 404,
                "error_class": type(exc).__name__,
                "event_capture_runtime_ready": False,
                "target_observation_authorized": False,
                "outcomes_authorized": False,
                "orders_enabled": False,
                "promotion_credit": "NONE",
            }
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annual-plan", type=Path, required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--implementation-manifest", type=Path)
    parser.add_argument("--target-open-authority", type=Path)
    parser.add_argument("--ruleset", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime_paths = (
        args.protocol,
        args.implementation_manifest,
        args.target_open_authority,
        args.ruleset,
    )
    supplied = [path is not None for path in runtime_paths]
    if any(supplied) and not all(supplied):
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "failure_reason": "PARTIAL_RUNTIME_GUARD_INPUTS_NOT_ALLOWED",
        }))
        return 2

    try:
        result = fetch_live_event_activation_v02(
            annual_plan=_load_json(args.annual_plan),
            event_id=args.event_id,
            protocol=_load_json(args.protocol) if args.protocol else None,
            implementation_manifest=(
                _load_json(args.implementation_manifest)
                if args.implementation_manifest else None
            ),
            target_open_authority=(
                _load_json(args.target_open_authority)
                if args.target_open_authority else None
            ),
            ruleset=_load_json(args.ruleset) if args.ruleset else None,
        )
    except (HTTPError, URLError, ValueError, RuntimeError) as exc:
        result = {
            "document_type": "MRCR_H02_LIVE_EVENT_ACTIVATION_STATUS_V02",
            "status": "FAIL_CLOSED",
            "event_id": args.event_id,
            "error_class": type(exc).__name__,
            "failure_reason": str(exc),
            "event_capture_runtime_ready": False,
            "target_observation_authorized": False,
            "outcomes_authorized": False,
            "orders_enabled": False,
            "promotion_credit": "NONE",
        }

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in {
        "ACTIVATION_RECEIPT_READY_TARGET_OBSERVATION_STILL_LOCKED",
        "READY_FOR_EVENT_CAPTURE",
        "EVIDENCE_NOT_READY",
    } else 2


if __name__ == "__main__":
    sys.exit(main())
