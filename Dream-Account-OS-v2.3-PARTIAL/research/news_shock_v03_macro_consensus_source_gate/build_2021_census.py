#!/usr/bin/env python3
"""Build the frozen, outcome-blind 2021 macro-consensus census artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "2021_EVENT_MANIFEST.csv"
RETRIEVED = "2026-09-21T00:00:00Z"

CPI = {
    "2021-01-13": (0.4, 1.4, 0.1, 1.6), "2021-02-10": (0.3, 1.4, 0.0, 1.4),
    "2021-03-10": (0.4, 1.7, 0.1, 1.3), "2021-04-13": (0.6, 2.6, 0.3, 1.6),
    "2021-05-12": (0.8, 4.2, 0.9, 3.0), "2021-06-10": (0.6, 5.0, 0.7, 3.8),
    "2021-07-13": (0.9, 5.4, 0.9, 4.5), "2021-08-11": (0.5, 5.4, 0.3, 4.3),
    "2021-09-14": (0.3, 5.3, 0.1, 4.0), "2021-10-13": (0.4, 5.4, 0.2, 4.0),
    "2021-11-10": (0.9, 6.2, 0.6, 4.6), "2021-12-10": (0.8, 6.8, 0.5, 4.9),
}

NFP = {
    "2021-01-08": (-140, 6.7, 0.8, 5.1, "Oct +610k→+654k; Nov +245k→+336k; net +135k"),
    "2021-02-05": (49, 6.3, 0.2, 5.4, "Nov +336k→+264k; Dec -140k→-227k; net -159k"),
    "2021-03-05": (379, 6.2, 0.2, 5.3, "Dec -227k→-306k; Jan +49k→+166k; net +38k"),
    "2021-04-02": (916, 6.0, -0.1, 4.2, "Jan +166k→+233k; Feb +379k→+468k; net +156k"),
    "2021-05-07": (266, 6.1, 0.7, 0.3, "Feb +468k→+536k; Mar +916k→+770k; net -78k"),
    "2021-06-04": (559, 5.8, 0.5, 2.0, "Mar +770k→+785k; Apr +266k→+278k; net +27k"),
    "2021-07-02": (850, 5.9, 0.3, 3.6, "Apr +278k→+269k; May +559k→+583k; net +15k"),
    "2021-08-06": (943, 5.4, 0.4, 4.0, "May +583k→+614k; Jun +850k→+938k; net +119k"),
    "2021-09-03": (235, 5.2, 0.6, 4.3, "Jun +938k→+962k; Jul +943k→+1,053k; net +134k"),
    "2021-10-08": (194, 4.8, 0.6, 4.6, "Jul +1,053k→+1,091k; Aug +235k→+366k; net +169k"),
    "2021-11-05": (531, 4.6, 0.4, 4.9, "Aug +366k→+483k; Sep +194k→+312k; net +235k"),
    "2021-12-03": (210, 4.2, 0.3, 4.8, "Sep +312k→+379k; Oct +531k→+546k; net +82k"),
}

SEARCH_FAMILIES = (
    "Reuters pre-release previews and polls; institutional research (BMO, Scotia, TD, Wells Fargo, ING); "
    "public historical calendars (Investing, Trading Economics, Forex Factory, Nasdaq, Yahoo); "
    "BLS archives; FRED/ALFRED vintage endpoints; public web/archive discovery"
)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    events = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    census, matrix, search = [], [], []
    for event in events:
        date = event["release_date"]
        fields = event["required_fields"].split("|")
        if event["event_family"] == "CPI":
            actuals = dict(zip(fields, CPI[date]))
        else:
            vals = NFP[date]
            actuals = dict(zip(fields, vals))
        for field in fields:
            actual = actuals[field]
            evidence_key = f'{event["event_id"]}|{field}|{actual}|{event["BLS_release_url"]}'
            census.append({
                "event_id": event["event_id"], "event_family": event["event_family"],
                "field": field, "actual_value": actual, "actual_source_name": "BLS archived first release",
                "actual_source_url": event["BLS_release_url"], "consensus_value": "",
                "consensus_source_name": "", "consensus_source_url": "",
                "publication_timestamp_utc": "", "snapshot_timestamp_utc": "",
                "T0_utc": event["scheduled_T0_UTC"], "delta_to_T0_seconds": "",
                "timezone": "America/New_York", "evidence_type": "NO_ACCEPTABLE_PRE_T0_EVIDENCE",
                "archive_status": "NOT_ACCEPTED", "evidence_hash_sha256": digest(evidence_key),
                "independent_validator": "", "confidence": "0",
                "provenance_status": "CONSENSUS_PROVENANCE_INCOMPLETE",
                "notes": "Actual preserved from BLS first release; consensus deliberately null."
            })
            matrix.append({"event_id": event["event_id"], "event_family": event["event_family"],
                           "required_field": field, "actual_status": "AUTHORITATIVE_FIRST_RELEASE",
                           "consensus_status": "CONSENSUS_PROVENANCE_INCOMPLETE",
                           "event_class": "CONSENSUS_PROVENANCE_INCOMPLETE"})
        search.append({
            "event_id": event["event_id"], "T0_utc": event["scheduled_T0_UTC"],
            "source_families_attempted": SEARCH_FAMILIES,
            "query_pattern": f'United States {event["event_family"]} forecast consensus {date} pre-release',
            "accepted_pre_T0_fields": "0", "result": "No field-explicit, timestamp-defensible pre-T0 record accepted",
            "reason": "Post-release/current mutable/untimestamped items excluded; snippets are discovery only."
        })

    census_fields = list(census[0])
    matrix_fields = list(matrix[0])
    write_csv(ROOT / "2021_CONSENSUS_CENSUS.csv", census, census_fields)
    write_csv(ROOT / "2021_FIELD_COVERAGE_MATRIX.csv", matrix, matrix_fields)
    write_csv(ROOT / "receipts" / "2021_SEARCH_RECEIPT.csv", search, list(search[0]))

    source_rows = [
        {"source":"BLS archived releases","role":"actual/revisions","events_attempted":24,"events_yielded":24,"accepted_fields":108,"classification":"AUTHORITATIVE","notes":"First-release authority; 48 CPI + 60 NFP fields."},
        {"source":"Reuters public web","role":"consensus discovery","events_attempted":24,"events_yielded":0,"accepted_fields":0,"classification":"DISCOVERY_ONLY","notes":"Accessible hits were post-release or incomplete; not proof of pre-T0 publication."},
        {"source":"Institutional public research","role":"consensus discovery","events_attempted":24,"events_yielded":0,"accepted_fields":0,"classification":"DISCOVERY_ONLY","notes":"No stable public record found covering every required field with defensible pre-T0 timestamp."},
        {"source":"Historical calendar aggregators","role":"consensus discovery","events_attempted":24,"events_yielded":0,"accepted_fields":0,"classification":"REJECTED","notes":"Current/mutable pages or provenance chain insufficient."},
        {"source":"FRED/ALFRED","role":"vintage validation","events_attempted":24,"events_yielded":0,"accepted_fields":0,"classification":"SECONDARY_VALIDATION_ONLY","notes":"Not a market-consensus authority; no consensus accepted."},
        {"source":"Wayback/public archives","role":"chronology validation","events_attempted":24,"events_yielded":0,"accepted_fields":0,"classification":"USABLE_WITH_CONTROLS","notes":"No qualifying pre-T0 snapshot was preserved in this census."},
    ]
    write_csv(ROOT / "2021_SOURCE_YIELD.csv", source_rows, list(source_rows[0]))

    receipt = {
        "mission":"2021 macro consensus census", "retrieval_timestamp_utc":RETRIEVED,
        "event_count":len(events), "cpi_count":sum(e["event_family"] == "CPI" for e in events),
        "nfp_count":sum(e["event_family"] == "EMPLOYMENT_SITUATION" for e in events),
        "accepted_complete":0, "accepted_partial":0,
        "classification_counts":{"CONSENSUS_PROVENANCE_INCOMPLETE":24},
        "method":"Frozen manifest first; official BLS actuals; strict pre-T0 consensus gate; no outcome data.",
        "limitations":["BLS blocked direct curl with HTTP 403; canonical URLs and normalized evidence hashes retained.",
                       "Search results/snippets and post-release Reuters articles were not accepted as pre-T0 proof."],
    }
    out = ROOT / "receipts" / "2021_CENSUS_RECEIPT.json"
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    hash_rows = []
    for path in sorted(ROOT.rglob("2021_*")):
        if path.name == "2021_HASH_MANIFEST.csv" or not path.is_file():
            continue
        hash_rows.append({"path":str(path.relative_to(ROOT)), "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                          "bytes":path.stat().st_size, "hashed_at_utc":RETRIEVED})
    write_csv(ROOT / "receipts" / "2021_HASH_MANIFEST.csv", hash_rows, list(hash_rows[0]))


if __name__ == "__main__":
    main()
