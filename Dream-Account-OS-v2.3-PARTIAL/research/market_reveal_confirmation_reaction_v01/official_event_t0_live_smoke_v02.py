"""Live official-source format smoke test for MRCR H02 T0 extraction V0.2.

Uses already-public 2026 official BLS/Federal Reserve pages only. It validates
source-format compatibility; it is not target observation and has no outcome or
trading capability.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import sys
from urllib.request import Request, urlopen

from official_event_t0_extractor_v02 import extract_bls_t0, extract_fomc_t0


BLS_CPI_URL = "https://www.bls.gov/schedule/news_release/cpi.htm"
BLS_POLICY_URL = "https://www.bls.gov/about-bls/dissemination.htm"
FED_2026_ANNOUNCEMENT_URL = (
    "https://www.federalreserve.gov/newsevents/pressreleases/"
    "monetary20240809a.htm"
)
FED_2026_PRECEDING_MINUTES_URL = (
    "https://www.federalreserve.gov/monetarypolicy/"
    "fomcminutes20260729.htm"
)
USER_AGENT = "MRCR-H02-Official-T0-Live-Smoke/0.2"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = html.unescape(data)
        if value.strip():
            self.parts.append(value.strip())

    def text(self) -> str:
        return "\n".join(self.parts)


def _fetch_text(url: str) -> str:
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
    )
    with urlopen(request, timeout=15) as response:
        if int(getattr(response, "status", 200)) != 200:
            raise RuntimeError("OFFICIAL_SOURCE_HTTP_NON_200")
        raw = response.read()
    parser = _TextExtractor()
    parser.feed(raw.decode("utf-8", errors="strict"))
    return parser.text()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    checked = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        cpi_text = _fetch_text(BLS_CPI_URL)
        bls_policy = _fetch_text(BLS_POLICY_URL)
        fed_announcement = _fetch_text(FED_2026_ANNOUNCEMENT_URL)
        fed_minutes = _fetch_text(FED_2026_PRECEDING_MINUTES_URL)

        cpi = extract_bls_t0(
            event_family="US_CPI",
            plan_date="2026-10-14",
            schedule_text=cpi_text,
            dissemination_policy_text=bls_policy,
        )
        fomc = extract_fomc_t0(
            plan_start_date="2026-09-15",
            plan_end_date="2026-09-16",
            annual_schedule_announcement_text=fed_announcement,
            preceding_meeting_minutes_text=fed_minutes,
        )

        if cpi.scheduled_time_utc != "2026-10-14T12:30:00Z":
            raise RuntimeError("BLS_LIVE_T0_UNEXPECTED")
        if fomc.scheduled_time_utc != "2026-09-16T18:00:00Z":
            raise RuntimeError("FOMC_LIVE_T0_UNEXPECTED")

        receipt = {
            "document_type": "MRCR_H02_OFFICIAL_T0_LIVE_SMOKE_V02",
            "status": "PASS",
            "checked_at_utc": checked,
            "bls": {
                "event_family": "US_CPI",
                "plan_date": "2026-10-14",
                "scheduled_time_utc": cpi.scheduled_time_utc,
                "schedule_url": BLS_CPI_URL,
                "schedule_text_sha256": _sha(cpi_text),
                "policy_url": BLS_POLICY_URL,
                "policy_text_sha256": _sha(bls_policy),
            },
            "fomc": {
                "event_family": "FOMC_STATEMENT",
                "meeting_start_date": "2026-09-15",
                "meeting_end_date": "2026-09-16",
                "scheduled_time_utc": fomc.scheduled_time_utc,
                "announcement_url": FED_2026_ANNOUNCEMENT_URL,
                "announcement_text_sha256": _sha(fed_announcement),
                "preceding_minutes_url": FED_2026_PRECEDING_MINUTES_URL,
                "preceding_minutes_text_sha256": _sha(fed_minutes),
            },
            "target_observation_authorized": False,
            "outcomes_authorized": False,
            "orders_enabled": False,
            "promotion_credit": "NONE",
        }
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "document_type": "MRCR_H02_OFFICIAL_T0_LIVE_SMOKE_V02",
            "status": "FAIL_CLOSED",
            "checked_at_utc": checked,
            "error_class": type(exc).__name__,
            "failure_reason": str(exc),
            "target_observation_authorized": False,
            "outcomes_authorized": False,
            "orders_enabled": False,
            "promotion_credit": "NONE",
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
