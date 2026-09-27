#!/usr/bin/env python3
"""Fetch first-party Kalshi KXBTC15M contract-term provenance.

Research-only. No prices, returns, PnL, or trade decisions are computed.
"""

from __future__ import annotations
import datetime as dt
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

BASE="https://external-api.kalshi.com/trade-api/v2"
UA="CryptoLab-KXBTC15M-TermsProbe/0.1 research-only"
OUT=Path("artifacts/prediction_oracle_basis/kalshi_terms")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def fetch(url: str) -> tuple[int, bytes, str]:
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw=r.read()
        return int(r.status), raw, r.headers.get("content-type","")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    status, raw, ctype=fetch(f"{BASE}/series/KXBTC15M")
    payload=json.loads(raw.decode("utf-8"))
    series=payload.get("series", payload)
    terms_url=series.get("contract_terms_url")
    contract_url=series.get("contract_url")
    settlement=series.get("settlement_sources")
    result: dict[str,Any]={
        "schema":"KXBTC15M_CONTRACT_TERMS_PROVENANCE_V0.1",
        "generated_at_utc":now(),
        "series_http_status":status,
        "series_raw_sha256":hashlib.sha256(raw).hexdigest(),
        "series_ticker":series.get("ticker"),
        "frequency":series.get("frequency"),
        "title":series.get("title"),
        "contract_terms_url":terms_url,
        "contract_url":contract_url,
        "settlement_sources":settlement,
        "prices_read":False,
        "returns_computed":False,
        "pnl_computed":False,
    }
    print("SERIES_TICKER=", series.get("ticker"))
    print("CONTRACT_TERMS_URL=", terms_url)
    print("CONTRACT_URL=", contract_url)
    print("SETTLEMENT_SOURCES=", json.dumps(settlement, sort_keys=True))
    if terms_url and str(terms_url).startswith("http"):
        tstatus,traw,tctype=fetch(str(terms_url))
        suffix=".pdf" if "pdf" in tctype.lower() or str(terms_url).lower().endswith(".pdf") else ".bin"
        term_path=OUT/("contract_terms"+suffix)
        term_path.write_bytes(traw)
        result.update({
            "terms_http_status":tstatus,
            "terms_content_type":tctype,
            "terms_bytes":len(traw),
            "terms_sha256":hashlib.sha256(traw).hexdigest(),
            "terms_artifact_path":str(term_path),
        })
        print("TERMS_HTTP_STATUS=", tstatus)
        print("TERMS_CONTENT_TYPE=", tctype)
        print("TERMS_SHA256=", result["terms_sha256"])
    else:
        result["terms_fetch_state"]="NO_HTTP_CONTRACT_TERMS_URL"

    out=OUT/"terms_provenance_receipt.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
