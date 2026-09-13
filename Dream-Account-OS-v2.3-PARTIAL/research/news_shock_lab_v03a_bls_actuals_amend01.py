from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from research import news_shock_lab_v03a_bls_actuals as base

AMENDMENT_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V03A_BLS_ARCHIVE_FORMAT_NORMALIZATION_AMENDMENT_V0.1.json"
)
EXPECTED_AMENDMENT_FINGERPRINT = (
    "cec34f875c4f8e4c3f72f1cf6e69ed8419aa98fbbc73ea1b53b2148025622ea8"
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
        raise PermissionError("V0.3A BLS parser amendment fingerprint mismatch")
    if _canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.3A BLS parser amendment canonical hash mismatch")
    if raw["status"] != "FROZEN_PRE_OUTCOME_PARSER_NORMALIZATION":
        raise PermissionError("V0.3A BLS parser amendment status mismatch")
    if raw["trigger"]["crypto_market_outcomes_accessed"] is not False:
        raise PermissionError("V0.3A BLS amendment outcome guard drift")
    if raw["normalization"]["actual_values_changed"] is not False:
        raise PermissionError("V0.3A BLS amendment value-change guard drift")
    if raw["authority"]["authorizes_parser_normalization_only"] is not True:
        raise PermissionError("V0.3A BLS amendment authority mismatch")
    return raw


def _one_of(patterns: list[str], text: str, label: str) -> re.Match[str]:
    unique: dict[tuple[int, int, tuple[str, ...]], re.Match[str]] = {}
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            key = (match.start(), match.end(), match.groups())
            unique[key] = match
    if len(unique) != 1:
        raise ValueError(f"{label}: expected exactly one unique match, got {len(unique)}")
    return next(iter(unique.values()))


def parse_release(raw: bytes, expected_release_date: str) -> dict:
    load_amendment()
    text = base._normalize_text(raw)
    local_date = datetime.strptime(expected_release_date, "%Y-%m-%d")
    expected_long = local_date.strftime("%B %d, %Y").replace(" 0", " ")

    # BLS legacy archives may omit the weekday; newer archives may include it.
    embargo = _one_of(
        [
            r"embargoed until\s+8:30 a\.m\.\s*\(ET\)\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"embargoed until\s+8:30 a\.m\.\s*\(ET\)\s+[A-Za-z]+,\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        ],
        text,
        "embargo",
    )
    release_date_text = embargo.group(1)
    if release_date_text != expected_long:
        raise ValueError(
            f"embargo release-date mismatch: {release_date_text!r} != {expected_long!r}"
        )

    # The historical HTML may render the separator as a dash, en dash, em dash,
    # legacy byte, or Unicode replacement character. Require a non-alphanumeric
    # separator, never infer the month/year from elsewhere on the page.
    title = _one_of(
        [
            r"CONSUMER PRICE INDEX\s+[^A-Z0-9]+\s*([A-Z]+)\s+(20\d{2})",
            r"CONSUMER PRICE INDEX\s*-\s*([A-Z]+)\s+(20\d{2})",
        ],
        text,
        "reference month title",
    )
    month_name, year = title.group(1), title.group(2)
    if month_name not in base.MONTHS:
        raise ValueError(f"unknown reference month: {month_name}")
    reference_month = f"{year}-{base.MONTHS[month_name]}"

    # BLS wording has used both word orders across archive generations.
    hm = _one_of(
        [
            r"Consumer Price Index for All Urban Consumers \(CPI-U\)\s+"
            r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+on a seasonally adjusted basis\s+in\s+[A-Za-z]+",
            r"Consumer Price Index for All Urban Consumers \(CPI-U\)\s+"
            r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+in\s+[A-Za-z]+\s+on a seasonally adjusted basis",
        ],
        text,
        "headline_cpi_mom",
    )
    headline_mom = base._signed_change(hm.group(1), hm.group(2))

    hy = base._one(
        r"Over the last 12 months,\s+the all items index\s+"
        r"(increased|decreased|declined|fell|rose)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+percent",
        text,
        "headline_cpi_yoy",
    )
    headline_yoy = base._signed_change(hy.group(1), hy.group(2))

    cm = base._one(
        r"The index for all items less food and energy\s+"
        r"(increased|decreased|declined|fell|rose|was unchanged|unchanged)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+percent\s+in\s+[A-Za-z]+",
        text,
        "core_cpi_mom",
    )
    core_mom = base._signed_change(cm.group(1), cm.group(2))

    core_patterns = [
        r"all items less food and energy index\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the last 12 months",
        r"index for all items less food and energy\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the last 12 months",
        r"all items less food and energy index\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the past 12 months",
        r"index for all items less food and energy\s+(increased|decreased|declined|fell|rose)\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+over the past 12 months",
    ]
    core_matches: dict[tuple[int, int, str, str], re.Match[str]] = {}
    for pattern in core_patterns:
        for match in re.finditer(pattern, text, re.I):
            core_matches[(match.start(), match.end(), match.group(1), match.group(2))] = match
    if len(core_matches) != 1:
        raise ValueError(
            f"core_cpi_yoy: expected exactly one unique match, got {len(core_matches)}"
        )
    cy = next(iter(core_matches.values()))
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
            "usage: news_shock_lab_v03a_bls_actuals_amend01 <actual_manifest.json> <validation.json>"
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
