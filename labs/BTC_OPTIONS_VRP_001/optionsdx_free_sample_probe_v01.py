#!/usr/bin/env python3
"""Source-only probe of the public optionsDX BTC Deribit sample.

No strategy outcomes are computed. Output contains only transport, schema,
coverage and completeness metadata.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone

URL = "https://www.optionsdx.com/wp-content/uploads/2022/01/btc_sample.csv"
REQUIRED = {
    "QUOTE_UNIXTIME",
    "INSTRUMENT_NAME",
    "UNDERLYING_PRICE",
    "EXPIRY_UNIX",
    "DTE",
    "RIGHT",
    "STRIKE",
    "BID_SIZE",
    "BID_PRICE",
    "ASK_PRICE",
    "ASK_SIZE",
}


def norm(s: str) -> str:
    return "_".join(s.strip().upper().replace("-", "_").split())


def nonempty(v) -> bool:
    return v is not None and str(v).strip() not in {"", "nan", "NaN", "None", "null"}


def probe() -> dict:
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "CryptoLab-SourceOnly-optionsDX-Probe/0.1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            status = getattr(r, "status", 200)
            content_type = r.headers.get("Content-Type")
            raw = r.read()
    except Exception as exc:
        return {
            "classification":"OPTIONSDX_FREE_SAMPLE_ACQUISITION_FAILURE",
            "url":URL,
            "error_type":type(exc).__name__,
            "error":str(exc)[:500],
            "outcomes_opened":False,
        }

    sha256 = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        original_headers = reader.fieldnames or []
        header_map = {norm(h): h for h in original_headers}
        missing = sorted(REQUIRED - set(header_map))
        rows = 0
        unique_instruments = set()
        distinct_quote_dates = set()
        min_ts = None
        max_ts = None
        complete_bbo = 0
        complete_bbo_25_35 = 0

        for row in reader:
            rows += 1
            def get(k):
                return row.get(header_map[k]) if k in header_map else None

            if "INSTRUMENT_NAME" in header_map and nonempty(get("INSTRUMENT_NAME")):
                unique_instruments.add(str(get("INSTRUMENT_NAME")).strip())

            if "QUOTE_UNIXTIME" in header_map and nonempty(get("QUOTE_UNIXTIME")):
                try:
                    ts = float(get("QUOTE_UNIXTIME"))
                    # Accept seconds or milliseconds without changing the source value.
                    ts_sec = ts / 1000.0 if ts > 10_000_000_000 else ts
                    min_ts = ts_sec if min_ts is None else min(min_ts, ts_sec)
                    max_ts = ts_sec if max_ts is None else max(max_ts, ts_sec)
                    distinct_quote_dates.add(datetime.fromtimestamp(ts_sec, timezone.utc).date().isoformat())
                except Exception:
                    pass

            bbo_fields = ("BID_PRICE","BID_SIZE","ASK_PRICE","ASK_SIZE")
            bbo_ok = all(k in header_map and nonempty(get(k)) for k in bbo_fields)
            if bbo_ok:
                complete_bbo += 1
                if "DTE" in header_map and nonempty(get("DTE")):
                    try:
                        dte = float(get("DTE"))
                        if 25.0 <= dte <= 35.0:
                            complete_bbo_25_35 += 1
                    except Exception:
                        pass

        schema_ok = not missing
        passed = (
            status == 200
            and schema_ok
            and complete_bbo > 0
            and complete_bbo_25_35 > 0
        )
        classification = (
            "OPTIONSDX_FREE_SAMPLE_SCHEMA_PASS"
            if passed else
            "OPTIONSDX_FREE_SAMPLE_SCHEMA_INSUFFICIENT"
        )
        return {
            "classification":classification,
            "http_status":status,
            "content_type":content_type,
            "sha256":sha256,
            "bytes":len(raw),
            "row_count":rows,
            "column_count":len(original_headers),
            "normalized_columns":sorted(header_map),
            "missing_required_fields":missing,
            "unique_instrument_count":len(unique_instruments),
            "distinct_quote_date_count":len(distinct_quote_dates),
            "first_quote_date_utc":min(distinct_quote_dates) if distinct_quote_dates else None,
            "last_quote_date_utc":max(distinct_quote_dates) if distinct_quote_dates else None,
            "complete_bbo_rows":complete_bbo,
            "complete_bbo_rows_25_35_dte":complete_bbo_25_35,
            "outcomes_opened":False,
            "prices_emitted_in_receipt":False,
        }
    except Exception as exc:
        return {
            "classification":"OPTIONSDX_FREE_SAMPLE_SCHEMA_INSUFFICIENT",
            "http_status":status,
            "content_type":content_type,
            "sha256":sha256,
            "bytes":len(raw),
            "parse_error_type":type(exc).__name__,
            "parse_error":str(exc)[:500],
            "outcomes_opened":False,
        }


def main() -> int:
    result = probe()
    out = "optionsdx_free_sample_probe_receipt_v01.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["classification"] == "OPTIONSDX_FREE_SAMPLE_SCHEMA_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
