from __future__ import annotations

"""Pre-outcome reference-file identity gate for TFG-PBR01-1D-001.

Uses a fresh anonymous Chromium session on the official MEXC market-data-download
page to observe the frontend's own file-list request, resolves the BTC/USDT spot
symbol id, requests the official monthly Min15 file list, downloads exactly one
reference CSV, and computes SHA-256 over raw bytes only.

It DOES NOT parse CSV rows, inspect prices, derive candles, form signals, compute
returns/PnL, access 2025/2026 market files, place orders, or mutate an exchange.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import sync_playwright

LAB_ID = "TFG-PBR01-1D-001"
PAGE = "https://www.mexc.com/market-data-download/BTC?type=kline&interval=monthly&pair=USDT"
REF_NAME = "BTC_USDT-Min15-2023-02-01.csv"
EXPECTED_SHA256 = "31eff305411e5e5589e53b22e47554c9b50208d372322b19422270bfe5766e25"
LIST_MARKER = "/file-svc/history/download?filePath="


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_symbol_id(file_path: str) -> str:
    # Expected frontend path shape: SPOT2/kline/<symbol_id>/monthly/Day1/
    parts = [p for p in file_path.strip("/").split("/") if p]
    if len(parts) < 5 or parts[0] != "SPOT2" or parts[1] != "kline":
        raise RuntimeError(f"UNEXPECTED_FRONTEND_FILE_PATH:{file_path}")
    symbol_id = parts[2]
    if not re.fullmatch(r"[A-Za-z0-9_:\-.]+", symbol_id):
        raise RuntimeError(f"UNSAFE_SYMBOL_ID:{symbol_id}")
    return symbol_id


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()

    receipt = {
        "lab_id": LAB_ID,
        "status": "REFERENCE_HASH_GATE_STARTED",
        "page": PAGE,
        "reference_file": REF_NAME,
        "expected_sha256": EXPECTED_SHA256,
        "frontend_observed_file_list_url": None,
        "frontend_observed_file_path": None,
        "resolved_symbol_id": None,
        "min15_list_url": None,
        "min15_list_http_status": None,
        "min15_metadata_count": None,
        "reference_metadata_found": False,
        "reference_file_size_metadata": None,
        "reference_last_modified_metadata": None,
        "reference_masked_url_host": None,
        "reference_download_http_status": None,
        "reference_download_byte_count": None,
        "reference_actual_sha256": None,
        "reference_hash_match": False,
        "csv_rows_parsed": False,
        "market_prices_inspected": False,
        "outcome_evaluation_performed": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
        "errors": [],
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                locale="en-US",
                timezone_id="UTC",
                accept_downloads=False,
                user_agent="Mozilla/5.0 TFG-PBR01-1D reference identity audit",
            )
            page = context.new_page()

            observed: dict[str, str] = {}

            def on_request(req):
                if LIST_MARKER in req.url and "file_list_url" not in observed:
                    observed["file_list_url"] = req.url

            page.on("request", on_request)
            page.goto(PAGE, wait_until="domcontentloaded", timeout=60000)
            # The symbol map and component initialize asynchronously.
            for _ in range(30):
                if "file_list_url" in observed:
                    break
                page.wait_for_timeout(1000)
            if "file_list_url" not in observed:
                raise RuntimeError("FRONTEND_FILE_LIST_REQUEST_NOT_OBSERVED")

            observed_url = observed["file_list_url"]
            receipt["frontend_observed_file_list_url"] = observed_url
            query = parse_qs(urlparse(observed_url).query)
            vals = query.get("filePath") or query.get("filepath")
            if not vals:
                raise RuntimeError("FRONTEND_FILEPATH_QUERY_MISSING")
            observed_path = unquote(vals[0])
            receipt["frontend_observed_file_path"] = observed_path
            symbol_id = extract_symbol_id(observed_path)
            receipt["resolved_symbol_id"] = symbol_id

            min15_path = f"SPOT2/kline/{symbol_id}/monthly/Min15/"
            # Preserve the exact origin used by the observed official request.
            parsed = urlparse(observed_url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            min15_url = origin + LIST_MARKER + min15_path
            receipt["min15_list_url"] = min15_url

            list_resp = context.request.get(min15_url, headers={"referer": PAGE}, timeout=60000)
            receipt["min15_list_http_status"] = list_resp.status
            if not list_resp.ok:
                raise RuntimeError(f"MIN15_LIST_HTTP_{list_resp.status}")
            payload = list_resp.json()
            # Frontend request helper receives an object whose .data is the array.
            if isinstance(payload, dict) and isinstance(payload.get("data"), list):
                rows = payload["data"]
            elif isinstance(payload, list):
                rows = payload
            else:
                raise RuntimeError("MIN15_LIST_RESPONSE_SHAPE_UNEXPECTED")
            receipt["min15_metadata_count"] = len(rows)

            ref = next((r for r in rows if isinstance(r, dict) and r.get("fileName") == REF_NAME), None)
            if ref is None:
                receipt["status"] = "SOURCE_ACCESS_BLOCKED_REFERENCE_FILE_ABSENT"
                browser.close()
                rc = 2
            else:
                receipt["reference_metadata_found"] = True
                receipt["reference_file_size_metadata"] = ref.get("fileSize")
                receipt["reference_last_modified_metadata"] = ref.get("lastModified")
                masked_url = ref.get("maskedUrl")
                if not isinstance(masked_url, str) or not masked_url.startswith(("https://", "http://")):
                    raise RuntimeError("REFERENCE_MASKED_URL_MISSING_OR_UNSAFE")
                receipt["reference_masked_url_host"] = urlparse(masked_url).hostname

                file_resp = context.request.get(masked_url, headers={"referer": PAGE}, timeout=120000)
                receipt["reference_download_http_status"] = file_resp.status
                if not file_resp.ok:
                    raise RuntimeError(f"REFERENCE_DOWNLOAD_HTTP_{file_resp.status}")
                raw = file_resp.body()
                receipt["reference_download_byte_count"] = len(raw)
                actual = sha256_bytes(raw)
                receipt["reference_actual_sha256"] = actual
                match = actual == EXPECTED_SHA256
                receipt["reference_hash_match"] = match
                if match:
                    receipt["status"] = "PASS_REFERENCE_FILE_BYTE_IDENTITY_GATE"
                    rc = 0
                else:
                    receipt["status"] = "SOURCE_VERSION_DRIFT_REFERENCE_HASH_MISMATCH"
                    rc = 3
                browser.close()
    except Exception as exc:
        receipt["status"] = "BLOCKED_PRE_OUTCOME_REFERENCE_HASH_GATE"
        receipt["errors"].append(f"{type(exc).__name__}:{exc}")
        rc = 2

    out = Path(args.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    safe = {
        k: receipt[k]
        for k in (
            "status", "frontend_observed_file_path", "resolved_symbol_id",
            "min15_list_http_status", "min15_metadata_count", "reference_metadata_found",
            "reference_download_http_status", "reference_download_byte_count",
            "reference_actual_sha256", "reference_hash_match", "csv_rows_parsed",
            "outcome_evaluation_performed", "validation_2025_access_performed",
            "holdout_2026_access_performed"
        )
    }
    print(json.dumps(safe, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
