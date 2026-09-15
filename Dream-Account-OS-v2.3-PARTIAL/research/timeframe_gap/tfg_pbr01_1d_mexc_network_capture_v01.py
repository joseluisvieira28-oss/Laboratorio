from __future__ import annotations

"""Outcome-blind network-metadata capture for MEXC historical download page.

Fresh anonymous Chromium session. Records only request URL/method/resource type,
small request payloads for likely historical-data endpoints, response status and
content-type. It never reads response bodies, downloads market CSVs, parses prices,
forms candles, computes returns/PnL, accesses protected 2025/2026 market data, or
mutates an exchange.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

LAB_ID = "TFG-PBR01-1D-001"
PAGE = "https://www.mexc.com/market-data-download/BTC"
TERMS = (
    "market-data", "market_data", "download", "history", "historical", "kline",
    "candle", "archive", "file", "spot", "mday", "min15",
)


def likely(url: str) -> bool:
    low = url.lower()
    return any(t in low for t in TERMS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()

    requests_seen: list[dict] = []
    responses_seen: list[dict] = []
    errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="en-US",
            timezone_id="UTC",
            user_agent="Mozilla/5.0 TFG-PBR01-1D anonymous source-route audit",
        )
        page = context.new_page()

        def on_request(req):
            if req.resource_type not in {"xhr", "fetch", "document"} and not likely(req.url):
                return
            row = {
                "url": req.url,
                "method": req.method,
                "resource_type": req.resource_type,
                "host": urlparse(req.url).hostname,
            }
            if likely(req.url):
                data = req.post_data
                if data:
                    row["post_data_prefix"] = data[:4000]
            requests_seen.append(row)

        def on_response(resp):
            req = resp.request
            if req.resource_type not in {"xhr", "fetch", "document"} and not likely(resp.url):
                return
            headers = resp.headers
            responses_seen.append({
                "url": resp.url,
                "status": resp.status,
                "resource_type": req.resource_type,
                "content_type": headers.get("content-type"),
                "content_length": headers.get("content-length"),
                "host": urlparse(resp.url).hostname,
            })

        page.on("request", on_request)
        page.on("response", on_response)
        try:
            page.goto(PAGE, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(15000)
        except Exception as exc:
            errors.append(f"NAVIGATION:{type(exc).__name__}:{exc}")
        finally:
            browser.close()

    # Stable de-duplication.
    def dedup(rows: list[dict]) -> list[dict]:
        out = []
        seen = set()
        for row in rows:
            key = json.dumps(row, sort_keys=True, ensure_ascii=True)
            if key not in seen:
                seen.add(key)
                out.append(row)
        return out

    requests_seen = dedup(requests_seen)
    responses_seen = dedup(responses_seen)
    likely_requests = [r for r in requests_seen if likely(r["url"])]
    likely_responses = [r for r in responses_seen if likely(r["url"])]

    payload = {
        "lab_id": LAB_ID,
        "status": "PASS_ANONYMOUS_NETWORK_METADATA_CAPTURE" if likely_requests else "NO_LIKELY_HISTORICAL_ROUTE_OBSERVED",
        "page": PAGE,
        "likely_requests": likely_requests,
        "likely_responses": likely_responses,
        "all_xhr_fetch_document_requests": [r for r in requests_seen if r["resource_type"] in {"xhr", "fetch", "document"}],
        "errors": errors,
        "response_bodies_read": False,
        "market_file_downloaded": False,
        "market_rows_parsed": False,
        "outcome_evaluation_performed": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
    }
    out = Path(args.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"status": payload["status"], "likely_request_count": len(likely_requests), "xhr_fetch_document_count": len(payload["all_xhr_fetch_document_requests"]), "errors": errors}, indent=2))
    for row in likely_requests:
        print("REQUEST", json.dumps(row, sort_keys=True))
    for row in likely_responses:
        print("RESPONSE", json.dumps(row, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
