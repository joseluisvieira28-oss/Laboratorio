from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from research.news_shock_lab_v03a_provenance import (
    EXPECTED_EVENT_COUNT,
    EXPECTED_FREEZE_FINGERPRINT,
    FIELDS,
    build_event_slot_manifest,
    validate_manifest_records,
)

ARCHIVE_TEMPLATE = "https://www.bls.gov/news.release/archives/cpi_{mmddyyyy}.htm"
MONTHS = {
    "JANUARY": "01", "FEBRUARY": "02", "MARCH": "03", "APRIL": "04",
    "MAY": "05", "JUNE": "06", "JULY": "07", "AUGUST": "08",
    "SEPTEMBER": "09", "OCTOBER": "10", "NOVEMBER": "11", "DECEMBER": "12",
}


def fetch_bytes(url: str) -> bytes:
    last: Exception | None = None
    for attempt in range(1, 5):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "DreamAccountOS-NewsShockV03A/0.3 research-only",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            with urlopen(req, timeout=45) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                raw = response.read()
            if not raw:
                raise RuntimeError("empty BLS archive response")
            return raw
        except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
            last = exc
            if attempt < 4:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"BLS archive fetch failed: {url}: {last}")


def _normalize_text(raw: bytes) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def _signed_change(verb: str, value: str) -> float:
    number = float(value)
    verb = verb.lower()
    if verb in {"decreased", "declined", "fell", "dropped"}:
        return -number
    if verb in {"increased", "rose", "advanced", "gained", "was unchanged", "unchanged"}:
        return 0.0 if "unchanged" in verb else number
    raise ValueError(f"unsupported change verb: {verb}")


def _one(pattern: str, text: str, label: str, flags: int = re.I) -> re.Match[str]:
    matches = list(re.finditer(pattern, text, flags))
    if len(matches) != 1:
        raise ValueError(f"{label}: expected exactly one match, got {len(matches)}")
    return matches[0]


def parse_release(raw: bytes, expected_release_date: str) -> dict:
    text = _normalize_text(raw)
    local_date = datetime.strptime(expected_release_date, "%Y-%m-%d")
    expected_long = local_date.strftime("%B %d, %Y").replace(" 0", " ")

    # The archive itself must prove the embargo clock time and release date.
    embargo = _one(
        r"embargoed until\s+8:30 a\.m\.\s*\(ET\)\s+([A-Za-z]+),\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        text,
        "embargo",
    )
    if embargo.group(2) != expected_long:
        raise ValueError(
            f"embargo release-date mismatch: {embargo.group(2)!r} != {expected_long!r}"
        )

    title = _one(
        r"CONSUMER PRICE INDEX\s*-\s*([A-Z]+)\s+(20\d{2})",
        text,
        "reference month title",
    )
    month_name, year = title.group(1), title.group(2)
    if month_name not in MONTHS:
        raise ValueError(f"unknown reference month: {month_name}")
    reference_month = f"{year}-{MONTHS[month_name]}"

    # Headline MoM, constrained to the opening CPI-U sentence before the prior-month clause.
    hm = _one(
        r"Consumer Price Index for All Urban Consumers \(CPI-U\)\s+"
        r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+on a seasonally adjusted basis\s+in\s+"
        r"[A-Za-z]+",
        text,
        "headline_cpi_mom",
    )
    headline_mom = _signed_change(hm.group(1), hm.group(2))

    # Headline YoY from the first 12-month statement.
    hy = _one(
        r"Over the last 12 months,\s+the all items index\s+"
        r"(increased|decreased|declined|fell|rose)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+percent",
        text,
        "headline_cpi_yoy",
    )
    headline_yoy = _signed_change(hy.group(1), hy.group(2))

    # Core MoM opening summary sentence.
    cm = _one(
        r"The index for all items less food and energy\s+"
        r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+in\s+[A-Za-z]+",
        text,
        "core_cpi_mom",
    )
    core_mom = _signed_change(cm.group(1), cm.group(2))

    # Core YoY. Limit to wording that explicitly says 12 months / last year.
    core_patterns = [
        r"all items less food and energy index\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the last 12 months",
        r"index for all items less food and energy\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the last 12 months",
        r"all items less food and energy index\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the past 12 months",
        r"index for all items less food and energy\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the past 12 months",
    ]
    core_matches: list[re.Match[str]] = []
    for pattern in core_patterns:
        core_matches.extend(list(re.finditer(pattern, text, re.I)))
    # Deduplicate exact spans in case equivalent patterns overlap.
    unique = {(m.start(), m.end(), m.group(1), m.group(2)): m for m in core_matches}
    if len(unique) != 1:
        raise ValueError(f"core_cpi_yoy: expected exactly one match, got {len(unique)}")
    cy = next(iter(unique.values()))
    core_yoy = _signed_change(cy.group(1), cy.group(2))

    return {
        "reference_month": reference_month,
        "actuals": {
            "headline_cpi_mom": headline_mom,
            "headline_cpi_yoy": headline_yoy,
            "core_cpi_mom": core_mom,
            "core_cpi_yoy": core_yoy,
        },
        "embargo_proof": {
            "release_date_text": embargo.group(2),
            "release_time_et": "08:30:00",
        },
    }


def collect_actuals(output_path: Path, validation_path: Path) -> tuple[dict, dict]:
    slots = build_event_slot_manifest()
    records = deepcopy(slots["records"])
    retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipts: list[dict] = []

    if len(records) != EXPECTED_EVENT_COUNT:
        raise RuntimeError("V0.3A actual collector event count drift")

    for i, record in enumerate(records, start=1):
        release_date = record["release_date_local"]
        d = datetime.strptime(release_date, "%Y-%m-%d")
        mmddyyyy = d.strftime("%m%d%Y")
        url = ARCHIVE_TEMPLATE.format(mmddyyyy=mmddyyyy)
        raw = fetch_bytes(url)
        digest = hashlib.sha256(raw).hexdigest()
        parsed = parse_release(raw, release_date)

        record["reference_month"] = parsed["reference_month"]
        record["actuals"] = parsed["actuals"]
        record["actual_provenance"]["bls_release_url"] = url
        record["actual_provenance"]["bls_retrieved_at_utc"] = retrieved_at
        record["actual_provenance"]["bls_content_sha256"] = digest
        record["actual_provenance"]["alfred_corroboration"] = {
            "status": "NOT_CHECKED",
            "source_url": None,
            "vintage_date": None,
            "evidence_note": "BLS archived release is primary; ALFRED corroboration is a later optional audit layer.",
        }
        receipts.append({
            "event_id": record["event_id"],
            "release_url": url,
            "content_sha256": digest,
            "reference_month": parsed["reference_month"],
            "actuals": parsed["actuals"],
            "embargo_proof": parsed["embargo_proof"],
        })
        if i % 10 == 0 or i == len(records):
            print(f"V0.3A BLS actuals {i}/{len(records)}")

    populated = {
        "document_type": "NEWS_SHOCK_LAB_V03A_CPI_ACTUAL_PROVENANCE_MANIFEST",
        "version": "0.3A",
        "status": "BLS_FIRST_RELEASE_ACTUALS_COLLECTED_CONSENSUS_STILL_GATED",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "slot_manifest_fingerprint": slots["fingerprint"],
        "event_count": len(records),
        "retrieved_at_utc": retrieved_at,
        "source_policy": "BLS_ARCHIVED_RELEASE_PRIMARY",
        "records": records,
        "source_receipts": receipts,
        "guards": {
            "market_outcomes_accessed": False,
            "crypto_returns_computed": False,
            "profitability_computed": False,
            "holdout_2026_accessed": False,
            "mexc_2025_09_through_2025_12_accessed": False,
        },
    }
    unsigned = deepcopy(populated)
    populated["fingerprint"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()

    validation_input = {
        "records": records,
    }
    validation = validate_manifest_records(validation_input)
    if validation["record_count"] != EXPECTED_EVENT_COUNT:
        raise RuntimeError("V0.3A actual validation count drift")
    if validation["status_counts"].get("ACTUAL_PROVENANCE_INCOMPLETE", 0) != 0:
        raise RuntimeError("V0.3A actual provenance unexpectedly incomplete")
    if validation["complete_a_count"] != 0 or validation["complete_b_count"] != 0:
        raise RuntimeError("V0.3A actual-only manifest must not become consensus-complete")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(populated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return populated, validation


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: news_shock_lab_v03a_bls_actuals <actual_manifest.json> <validation.json>")
    populated, validation = collect_actuals(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps({
        "status": populated["status"],
        "event_count": populated["event_count"],
        "manifest_fingerprint": populated["fingerprint"],
        "validation_fingerprint": validation["fingerprint"],
        "validation_status_counts": validation["status_counts"],
        "guards": populated["guards"],
    }, indent=2, sort_keys=True))
