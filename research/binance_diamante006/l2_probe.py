#!/usr/bin/env python3
"""Independent historical BINANCE SPOT L2 FREE SAMPLE discovery/metadata ONLY.

Never claims to have reconstructed order books: HEAD/metadata is not a replay,
and first-of-month samples cannot establish 90-day continuous coverage.
No payment, auth, API key, full paid request, deep download or market trades.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

OUT=Path("binance006-evidence")
TARGETS=(
    ("TARDIS_FREE_MONTH_FIRST_DAY",
      "https://datasets.tardis.dev/v1/binance/incremental_book_L2/2026/10/01/BTCUSDT.csv.gz"),
    ("HUGGINGFACE_OPEN_DATASET_METADATA",
      "https://huggingface.co/api/datasets/MaximumLeverage/crypto-lob-stream"),
)
def examine(label,url):
    rec={"candidate":label,"url":url,"metadata_status":"UNVERIFIED",
         "full_l2_book_verified":False,"continuous_90d_coverage_verified":False,
         "licensed_for_research_verified":False,"cost_or_account_approval":False}
    if not url.startswith("https://"):
        rec["metadata_status"]="BAD_SOURCE_URL"
        return rec
    try:
        req=urllib.request.Request(url,method="HEAD",
            headers={"User-Agent":"Crypto-Lab-Binance006-NoCost-L2Metadata/1.0"})
        with urllib.request.urlopen(req,timeout=15) as res:
            rec["http_head_status"]=res.status
            rec["content_length"]=res.headers.get("Content-Length")
            rec["content_type"]=res.headers.get("Content-Type")
            rec["accept_ranges"]=res.headers.get("Accept-Ranges")
        rec["metadata_status"]="PUBLIC_HEAD_OK_SAMPLE_ONLY" if rec["http_head_status"]==200 else "SOURCE_NOT_AVAILABLE"
    except Exception as exc:
        rec["metadata_status"]="SOURCE_BLOCKED_OR_UNVERIFIED"
        rec["error_type"]=type(exc).__name__
        rec["error"]=str(exc)[:150]
    return rec

def main():
    OUT.mkdir(exist_ok=True)
    report={"study":"BINANCE006_L2_HISTORICAL_SOURCE_AVAILABILITY",
            "checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "public_metadata_only":True,"no_paid_data":True,"no_orders":True,
            "no_history_backtest_claim":True,
            "interpretation":"Even an HTTP200 sample does NOT validate full L2 U/u sequence, snapshot bridge, aligned trades or 90 days",
            "candidates":[examine(a,b) for a,b in TARGETS]}
    p=OUT/"l2_free_source_gate.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (OUT/"l2_free_source_gate.sha256").write_text(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+p.name+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
