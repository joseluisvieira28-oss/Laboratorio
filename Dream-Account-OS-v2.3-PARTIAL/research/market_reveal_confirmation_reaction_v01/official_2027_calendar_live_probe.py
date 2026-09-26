"""Official-source calendar status probe for MRCR H02.

Reads only public BLS/Federal Reserve calendar pages and emits a source-status
receipt. It never infers missing dates, never fabricates confirmation, and never
authorizes target observation.

This probe is diagnostic/pre-binding infrastructure only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import html
from html.parser import HTMLParser
import json
import re
import sys
from typing import Iterable
from urllib.request import Request, urlopen


BLS_CPI_URL = "https://www.bls.gov/schedule/news_release/cpi.htm"
BLS_EMPSIT_URL = "https://www.bls.gov/schedule/news_release/empsit.htm"
FED_FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

USER_AGENT = "MRCR-H02-Official-Calendar-Probe/0.1"

MONTHS = {
    "Jan.": 1, "Feb.": 2, "Mar.": 3, "Apr.": 4, "May": 5, "Jun.": 6,
    "Jul.": 7, "Aug.": 8, "Sep.": 9, "Oct.": 10, "Nov.": 11, "Dec.": 12,
}


@dataclass(frozen=True)
class BlsEvent:
    reference_month: str
    release_date: str
    release_time: str


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
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=15) as response:
        status = int(getattr(response, "status", 200))
        if status != 200:
            raise RuntimeError(f"HTTP_{status}")
        raw = response.read()
    parser = _TextExtractor()
    parser.feed(raw.decode("utf-8", errors="strict"))
    return parser.text()


def _parse_bls_rows(text: str) -> tuple[BlsEvent, ...]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    out: list[BlsEvent] = []
    date_re = re.compile(
        r"^(Jan\.|Feb\.|Mar\.|Apr\.|May|Jun\.|Jul\.|Aug\.|Sep\.|Oct\.|Nov\.|Dec\.)\s+(\d{1,2}),\s+(\d{4})$"
    )
    ref_re = re.compile(r"^[A-Z][a-z]+\s+\d{4}$")
    time_re = re.compile(r"^\d{1,2}:\d{2}\s+(?:AM|PM)$")

    i = 0
    while i + 2 < len(lines):
        ref = lines[i]
        date = lines[i + 1]
        time = lines[i + 2]
        if ref_re.match(ref) and date_re.match(date) and time_re.match(time):
            out.append(BlsEvent(ref, date, time))
            i += 3
        else:
            i += 1
    return tuple(out)


def _bls_2027_status(text: str, *, family: str) -> dict:
    rows = _parse_bls_rows(text)
    events = [row for row in rows if row.release_date.endswith("2027")]
    unique = {(row.reference_month, row.release_date, row.release_time) for row in events}
    confirmed_count = len(unique)
    complete = confirmed_count == 12

    latest = None
    if rows:
        latest = rows[-1]

    return {
        "authority": "BLS",
        "family": family,
        "source_url": BLS_CPI_URL if family == "US_CPI" else BLS_EMPSIT_URL,
        "status": (
            "COMPLETE_OFFICIAL_CONFIRMED"
            if complete else "INCOMPLETE_FOR_2027"
        ),
        "confirmed_2027_event_count": confirmed_count,
        "expected_2027_event_count": 12,
        "complete_2027_schedule_available": complete,
        "bindable": complete,
        "latest_visible_release_date": None if latest is None else latest.release_date,
        "latest_visible_reference_month": None if latest is None else latest.reference_month,
        "events_2027": [
            {
                "reference_month": row.reference_month,
                "release_date": row.release_date,
                "release_time": row.release_time,
                "official_status": "CONFIRMED",
            }
            for row in events
        ],
    }


def _extract_2027_fomc_section(text: str) -> str:
    marker = "2027 FOMC Meetings"
    start = text.find(marker)
    if start < 0:
        return ""
    tail = text[start + len(marker):]
    stop = tail.find("2028")
    return tail if stop < 0 else tail[:stop]


def _fed_2027_status(text: str) -> dict:
    section = _extract_2027_fomc_section(text)
    date_re = re.compile(
        r"(?m)^(January|February|March|April|May|June|July|August|September|October|November|December)\n(\d{1,2})-(\d{1,2})\*?$"
    )
    observed = [
        f"{month} {start}-{end}"
        for month, start, end in date_re.findall(section)
    ]
    tentative_note = (
        "Each meeting date is tentative until confirmed at the meeting immediately preceding it."
    )
    explicitly_tentative = tentative_note in text
    confirmed_count = 0 if explicitly_tentative else len(observed)
    complete_published_plan = len(observed) == 8
    complete_confirmed = complete_published_plan and confirmed_count == 8

    return {
        "authority": "FEDERAL_RESERVE",
        "family": "FOMC_STATEMENT",
        "source_url": FED_FOMC_URL,
        "status": (
            "COMPLETE_OFFICIAL_CONFIRMED"
            if complete_confirmed
            else (
                "EIGHT_2027_MEETINGS_PUBLISHED_BUT_TENTATIVE"
                if len(observed) == 8 and explicitly_tentative
                else "INCOMPLETE_OR_UNCONFIRMED_FOR_2027"
            )
        ),
        "observed_2027_meetings": observed,
        "observed_2027_meeting_count": len(observed),
        "confirmed_2027_event_count": confirmed_count,
        "expected_2027_event_count": 8,
        "official_tentative_note_present": explicitly_tentative,
        "complete_official_2027_plan_available": complete_published_plan,
        "complete_confirmed_2027_schedule_available": complete_confirmed,
        "annual_plan_bindable_v02": complete_published_plan,
        "all_events_confirmed_v01": complete_confirmed,
    }


def evaluate_official_calendar_status(
    *,
    cpi_text: str,
    empsit_text: str,
    fomc_text: str,
    checked_at_utc: str,
) -> dict:
    cpi = _bls_2027_status(cpi_text, family="US_CPI")
    empsit = _bls_2027_status(empsit_text, family="US_EMPLOYMENT_SITUATION")
    fomc = _fed_2027_status(fomc_text)
    annual_plan_ready = (
        cpi["bindable"]
        and empsit["bindable"]
        and fomc["annual_plan_bindable_v02"]
    )
    strict_v01_ready = (
        cpi["bindable"]
        and empsit["bindable"]
        and fomc["all_events_confirmed_v01"]
    )
    return {
        "document_type": "MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "checked_at_utc": checked_at_utc,
        "status": (
            "READY_FOR_V02_ANNUAL_PLAN"
            if annual_plan_ready
            else "BLOCKED"
        ),
        "sources": {
            "US_CPI": cpi,
            "US_EMPLOYMENT_SITUATION": empsit,
            "FOMC_STATEMENT": fomc,
        },
        "annual_plan_trigger_ready_v02": annual_plan_ready,
        "strict_v01_all_confirmed_trigger_ready": strict_v01_ready,
        "inferred_dates_used": False,
        "target_observation_authorized": False,
        "outcomes_authorized": False,
        "promotion_credit": "NONE",
    }


def main() -> int:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        receipt = evaluate_official_calendar_status(
            cpi_text=_fetch_text(BLS_CPI_URL),
            empsit_text=_fetch_text(BLS_EMPSIT_URL),
            fomc_text=_fetch_text(FED_FOMC_URL),
            checked_at_utc=now,
        )
    except Exception as exc:
        receipt = {
            "document_type": "MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01",
            "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
            "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
            "checked_at_utc": now,
            "status": "FAIL_CLOSED_SOURCE_PROBE",
            "error_class": type(exc).__name__,
            "annual_plan_trigger_ready_v02": False,
            "strict_v01_all_confirmed_trigger_ready": False,
            "inferred_dates_used": False,
            "target_observation_authorized": False,
            "outcomes_authorized": False,
            "promotion_credit": "NONE",
        }
        print(json.dumps(receipt, sort_keys=True))
        return 2

    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
