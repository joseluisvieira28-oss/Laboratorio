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
UA="CryptoLab-KXBTC15M-TermsProbe/0.2 research-only"
OUT=Path("artifacts/prediction_oracle_basis/kalshi_terms")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def fetch(url: str) -> tuple[int, bytes, str]:
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw=r.read()
        return int(r.status), raw, r.headers.get("content-type","")


def preserve(label: str, url: str | None, result: dict[str,Any]) -> None:
    if not url or not str(url).startswith("http"):
        result[f"{label}_fetch_state"]="NO_HTTP_URL"
        return
    status, raw, ctype=fetch(str(url))
    suffix=".pdf" if "pdf" in ctype.lower() or str(url).lower().endswith(".pdf") else ".bin"
    path=OUT/(label+suffix)
    path.write_bytes(raw)
    result.update({
        f"{label}_http_status":status,
        f"{label}_content_type":ctype,
        f"{label}_bytes":len(raw),
        f"{label}_sha256":hashlib.sha256(raw).hexdigest(),
        f"{label}_artifact_path":str(path),
    })
    print(f"{label.upper()}_HTTP_STATUS=", status)
    print(f"{label.upper()}_CONTENT_TYPE=", ctype)
    print(f"{label.upper()}_SHA256=", result[f"{label}_sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    status, raw, _=fetch(f"{BASE}/series/KXBTC15M")
    payload=json.loads(raw.decode("utf-8"))
    series=payload.get("series", payload)
    terms_url=series.get("contract_terms_url")
    contract_url=series.get("contract_url")
    settlement=series.get("settlement_sources")
    result: dict[str,Any]={
        "schema":"KXBTC15M_CONTRACT_PROVENANCE_V0.2",
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
    preserve("contract_terms", terms_url, result)
    preserve("product_certification", contract_url, result)

    out=OUT/"terms_provenance_receipt.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
