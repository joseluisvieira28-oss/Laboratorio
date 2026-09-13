from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from research import news_shock_lab_v03a_bls_actuals as base
from research import news_shock_lab_v03a_bls_actuals_amend01 as amend01

AMENDMENT_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V03A_BLS_ARCHIVE_FORMAT_NORMALIZATION_AMENDMENT_V0.3.json"
)
EXPECTED_AMENDMENT_FINGERPRINT = (
    "9b614a0c86d6f3d1fadaebfdb0a42f68ae511a942a26c27f63113d0675968047"
)
NUM_RE = re.compile(r"(?<![A-Za-z0-9])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?![A-Za-z0-9])")


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
        raise PermissionError("V0.3A BLS parser amendment03 fingerprint mismatch")
    if _canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.3A BLS parser amendment03 canonical hash mismatch")
    if raw["status"] != "FROZEN_PRE_OUTCOME_PARSER_NORMALIZATION":
        raise PermissionError("V0.3A BLS parser amendment03 status mismatch")
    if raw["trigger"]["crypto_market_outcomes_accessed"] is not False:
        raise PermissionError("V0.3A BLS amendment03 outcome guard drift")
    if raw["normalization"]["actual_values_changed"] is not False:
        raise PermissionError("V0.3A BLS amendment03 value-change guard drift")
    if raw["normalization"]["headline_and_core_actuals_source"] != "TABLE_A_ROWS":
        raise PermissionError("V0.3A BLS amendment03 Table A source guard drift")
    return raw


def _table_a_scope(text: str) -> str:
    start = re.search(r"Table A\.\s*Percent changes in CPI for All Urban Consumers", text, re.I)
    if start is None:
        raise ValueError("Table A start not found")
    tail = text[start.start():]
    endings = []
    for pattern in (
        r"\b1\s+Not seasonally adjusted\.",
        r"\bFootnotes\b",
        r"\bFood\s+The food index\b",
    ):
        m = re.search(pattern, tail, re.I)
        if m is not None:
            endings.append(m.start())
    if not endings:
        raise ValueError("Table A end boundary not found")
    return tail[: min(endings)]


def _row_body(table: str, label_pattern: str, next_label_pattern: str, label: str) -> str:
    m = re.search(
        rf"{label_pattern}\s*(.*?)(?={next_label_pattern})",
        table,
        re.I | re.S,
    )
    if m is None:
        raise ValueError(f"{label}: Table A row not found")
    return m.group(1)


def _last_two_values(body: str, label: str) -> tuple[float, float]:
    tokens = [float(m.group(0)) for m in NUM_RE.finditer(body)]
    # Table A carries seven monthly seasonally-adjusted changes plus one 12-month change.
    if len(tokens) != 8:
        raise ValueError(f"{label}: expected exactly 8 Table A numeric values, got {len(tokens)}")
    return tokens[-2], tokens[-1]


def parse_release(raw: bytes, expected_release_date: str) -> dict:
    load_amendment()
    text = base._normalize_text(raw)
    local_date = datetime.strptime(expected_release_date, "%Y-%m-%d")
    expected_long = local_date.strftime("%B %d, %Y").replace(" 0", " ")

    # Identity / timing proof remains the archived release itself.
    embargo = amend01._one_of(
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

    title = amend01._one_of(
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

    table = _table_a_scope(text)
    headline_body = _row_body(
        table,
        r"\bAll items(?:\.{2,}|\s)",
        r"\s+Food(?:\.{2,}|\s)",
        "headline",
    )
    core_body = _row_body(
        table,
        r"\bAll items less food and\s+energy(?:\.{2,}|\s)",
        r"\s+Commodities less food and\s+energy commodities",
        "core",
    )
    headline_mom, headline_yoy = _last_two_values(headline_body, "headline")
    core_mom, core_yoy = _last_two_values(core_body, "core")

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
        "actual_parse_source": "BLS_TABLE_A",
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
            "usage: news_shock_lab_v03a_bls_actuals_amend03 <actual_manifest.json> <validation.json>"
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
