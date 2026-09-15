from __future__ import annotations

"""Outcome-blind reconnaissance of the official MEXC historical market-data page.

This script only discovers page/script/network metadata needed to recover the exact
historical bulk CSV route. It does not parse market-price rows, form 1D candles,
evaluate PBR01, calculate returns/PnL, access 2025/2026, or mutate an exchange.
"""

import argparse
import json
import re
from urllib.parse import urljoin, urlparse

import requests

LAB_ID = "TFG-PBR01-1D-001"
PAGE = "https://www.mexc.com/market-data-download/BTC"
REF_NAME = "BTC_USDT-Min15-2023-02-01.csv"
REF_SHA = "31eff305411e5e5589e53b22e47554c9b50208d372322b19422270bfe5766e25"
KEYWORDS = ("market-data", "download", "Min15", "csv", "kline", "history", "historical")


def interesting(text: str) -> list[str]:
    found: list[str] = []
    # URLs and URL-like API paths only; no market payload extraction.
    candidates = re.findall(r"https?://[^\"'<>\\\s]+|/[A-Za-z0-9_./?=&%:-]{8,}", text)
    for value in candidates:
        low = value.lower()
        if any(k.lower() in low for k in KEYWORDS):
            found.append(value[:1000])
    return sorted(set(found))[:500]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", required=True)
    args = p.parse_args()
    headers = {"User-Agent": "Mozilla/5.0 TFG-PBR01-1D source-route audit"}
    result = {
        "lab_id": LAB_ID,
        "status": "SOURCE_ROUTE_RECON_STARTED",
        "page": PAGE,
        "reference_file": REF_NAME,
        "reference_sha256": REF_SHA,
        "page_http_status": None,
        "script_count": 0,
        "scripts_examined": 0,
        "candidate_route_strings": [],
        "outcome_evaluation_performed": False,
        "market_rows_parsed": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
    }
    try:
        r = requests.get(PAGE, headers=headers, timeout=30)
        result["page_http_status"] = r.status_code
        r.raise_for_status()
        html = r.text
        routes = interesting(html)
        scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, flags=re.I)
        script_urls = []
        for src in scripts:
            u = urljoin(PAGE, src)
            if urlparse(u).hostname and ("mexc" in urlparse(u).hostname or "static" in urlparse(u).hostname):
                script_urls.append(u)
        script_urls = list(dict.fromkeys(script_urls))[:80]
        result["script_count"] = len(script_urls)
        for u in script_urls:
            try:
                s = requests.get(u, headers=headers, timeout=20)
                if s.ok and len(s.text) <= 15_000_000:
                    routes.extend(interesting(s.text))
                    result["scripts_examined"] += 1
            except requests.RequestException:
                continue
        result["candidate_route_strings"] = sorted(set(routes))[:1000]
        # PASS here means only that reconnaissance completed. No source corpus is accepted yet.
        result["status"] = "PASS_SOURCE_ROUTE_RECON_METADATA_ONLY"
        rc = 0
    except Exception as exc:
        result["status"] = "SOURCE_ROUTE_RECON_BLOCKED"
        result["reason"] = f"{type(exc).__name__}:{exc}"
        rc = 2
    from pathlib import Path
    out = Path(args.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "page_http_status", "script_count", "scripts_examined")}, indent=2))
    for route in result.get("candidate_route_strings", [])[:100]:
        print(route)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
