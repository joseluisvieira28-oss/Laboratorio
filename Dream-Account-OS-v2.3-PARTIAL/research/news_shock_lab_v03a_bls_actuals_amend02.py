from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from research import news_shock_lab_v03a_bls_actuals as base
from research import news_shock_lab_v03a_bls_actuals_amend01 as amend01

AMENDMENT_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V03A_BLS_ARCHIVE_FORMAT_NORMALIZATION_AMENDMENT_V0.2.json"
)
EXPECTED_AMENDMENT_FINGERPRINT = (
    "f928cec95c6b715a2c8f5c81d4f04d1b1346be3d1abc12003a7c2588c25ccea9"
)


def _canonical_hash(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def load_amendment() -> dict:
    raw = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    if supplied != EXPECTED_AMENDMENT_FINGERPRINT:
        raise PermissionError("V0.3A BLS parser amendment02 fingerprint mismatch")
    if _canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.3A BLS parser amendment02 canonical hash mismatch")
    if raw["status"] != "FROZEN_PRE_OUTCOME_PARSER_NORMALIZATION":
        raise PermissionError("V0.3A BLS parser amendment02 status mismatch")
    if raw["trigger"]["crypto_market_outcomes_accessed"] is not False:
        raise PermissionError("V0.3A BLS amendment02 outcome guard drift")
    if raw["normalization"]["actual_values_changed"] is not False:
        raise PermissionError("V0.3A BLS amendment02 value-change guard drift")
    if raw["normalization"]["parse_actuals_only_from_opening_summary_before_table_a"] is not True:
        raise PermissionError("V0.3A BLS amendment02 summary-boundary guard drift")
    return raw


def _opening_summary(text: str) -> str:
    marker = re.search(r"\bTable A\.", text, re.I)
    if marker is None:
        raise ValueError("opening summary boundary Table A not found")
    return text[: marker.start()]


def parse_release(raw: bytes, expected_release_date: str) -> dict:
    load_amendment()
    amend01.load_amendment()
    text = base._normalize_text(raw)
    summary = _opening_summary(text)
    local_date = datetime.strptime(expected_release_date, "%Y-%m-%d")
    expected_long = local_date.strftime("%B %d, %Y").replace(" 0", " ")

    embargo = amend01._one_of(
        [
            r"embargoed until\s+8:30 a\.m\.\s*\(ET\)\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"embargoed until\s+8:30 a\.m\.\s*\(ET\)\s+[A-Za-z]+,\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        ],
        summary,
        "embargo",
    )
    release_date_text = embargo.group(1)
    if release_date_text != expected_long:
        raise ValueError(
            f"embargo release-date mismatch: {release_date_text!r} != {expected_long!r}"
        )

    title = amend01._one_of(
        [
            r"CONSUMER PRICE INDEX\s+[^A-Z0-9]+\s*([A-Z]+)\s+(20\d{2})",
            r"CONSUMER PRICE INDEX\s*-\s*([A-Z]+)\s+(20\d{2})",
        ],
        summary,
        "reference month title",
    )
    month_name, year = title.group(1), title.group(2)
    if month_name not in base.MONTHS:
        raise ValueError(f"unknown reference month: {month_name}")
    reference_month = f"{year}-{base.MONTHS[month_name]}"

    hm = amend01._one_of(
        [
            r"Consumer Price Index for All Urban Consumers \(CPI-U\)\s+"
            r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+on a seasonally adjusted basis\s+in\s+[A-Za-z]+",
            r"Consumer Price Index for All Urban Consumers \(CPI-U\)\s+"
            r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+in\s+[A-Za-z]+\s+on a seasonally adjusted basis",
        ],
        summary,
        "headline_cpi_mom",
    )
    headline_mom = base._signed_change(hm.group(1), hm.group(2))

    hy = amend01._one_of(
        [
            r"Over the last 12 months,\s+the all items index\s+"
            r"(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent",
            r"The all items index\s+(increased|decreased|declined|fell|rose)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+for the 12 months ending\s+[A-Za-z]+",
        ],
        summary,
        "headline_cpi_yoy",
    )
    headline_yoy = base._signed_change(hy.group(1), hy.group(2))

    cm = base._one(
        r"The index for all items less food and energy\s+"
        r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+in\s+[A-Za-z]+",
        summary,
        "core_cpi_mom",
    )
    core_mom = base._signed_change(cm.group(1), cm.group(2))

    cy = amend01._one_of(
        [
            r"(?:The\s+)?all items less food and energy index\s+"
            r"(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+"
            r"over the (?:last|past) 12 months",
            r"(?:The\s+)?all items less food and energy index\s+"
            r"(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent,\s+"
            r"the largest 12-month (?:change|increase)",
        ],
        summary,
        "core_cpi_yoy",
    )
    core_yoy = base._signed_change(cy.group(1), cy.group(2))

    return {
        "reference_month": reference_month,
        "actuals": {
            "headline_cpi_mom": headline_mom,
            "headline_cpi_yoy": headline_yoy,
            "core_cpi_mom": core_mom,
            "core_cpi_yoy": core_yoy,
        },
        "embargo_proof": {
            "release_date_text": release_date_text,
            "release_time_et": "08:30:00",
        },
        "parser_amendment_fingerprint": EXPECTED_AMENDMENT_FINGERPRINT,
    }


def collect_actuals(output_path: Path, validation_path: Path):
    load_amendment()
    original = base.parse_release
    try:
        base.parse_release = parse_release
        return base.collect_actuals(output_path, validation_path)
    finally:
        base.parse_release = original


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: news_shock_lab_v03a_bls_actuals_amend02 <actual_manifest.json> <validation.json>"
        )
    populated, validation = collect_actuals(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps({
        "status": populated["status"],
        "event_count": populated["event_count"],
        "amendment_fingerprint": EXPECTED_AMENDMENT_FINGERPRINT,
        "manifest_fingerprint": populated["fingerprint"],
        "validation_fingerprint": validation["fingerprint"],
        "validation_status_counts": validation["status_counts"],
        "guards": populated["guards"],
    }, indent=2, sort_keys=True))
