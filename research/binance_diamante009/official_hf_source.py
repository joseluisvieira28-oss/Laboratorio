#!/usr/bin/env python3
"""BINANCE009 SOURCE-ONLY wrapper after independent HF redirect proof.
Original 007 U/u parser and 007E 90MB cap unchanged. No orders or alpha.
"""
from __future__ import annotations
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"binance_diamante007e"))
import probe_90mb as previous

SOURCE=previous.pinned.frozen
OFFICIAL_HOSTS=frozenset((
    "huggingface.co",
    "cas-bridge.xethub.hf.co",
    "cas-server.xethub.hf.co",
    "cas-server.xethub-eu.hf.co",
    "transfer.xethub.hf.co",
    "transfer.xethub-eu.hf.co",
    "us.aws.cdn.hf.co",
    "us.gcp.cdn.hf.co",
    "cdn-lfs-us-1.hf.co",
    "cdn-lfs-eu-1.hf.co"
))
RUN_DIR=Path("binance009-evidence")

def official_hf_redirect(url):
    try:
        parsed=urllib.parse.urlparse(url)
        return (parsed.scheme=="https" and
                parsed.hostname in OFFICIAL_HOSTS and
                parsed.username is None and parsed.password is None and
                parsed.port in (None,443) and
                not parsed.path.startswith("//"))
    except ValueError:
        return False

SOURCE.is_allowed_redirect=official_hf_redirect
SOURCE.OUT=RUN_DIR

def finalize_receipt(exit_code):
    path=RUN_DIR/"l2_source_manifest.json"
    if not path.exists():return
    existing=json.loads(path.read_text())
    original_status=existing.get("status")
    existing["study"]="BINANCE-DIAMANTE-009"
    existing["original_007_module_source_status"]=original_status
    existing["independent_redirect_verification"]={
        "verified_in_prior_run":"45177917291",
        "actual_first_redirect_host":"us.aws.cdn.hf.co",
        "host_documented_official":True,
        "only_pinned_https_official_hosts":sorted(OFFICIAL_HOSTS),
        "no_redirect_signed_query_persisted":True
    }
    existing["known_provider_capture_issue"]="Goooddy June-Aug 2026 documented silently overwritten flushes; NOT full-month/90d verified"
    existing["economic_returns_or_trades_tested"]=False
    existing["full_month_coverage_certified"]=False
    existing["live_trading_go"]=False
    if exit_code==0:
        existing["status"]="REAL_L2_BOUNDED_WINDOW_REPLAY_PASS_ONLY_WITH_AUG_SOURCE_CORRUPTION_RISK"
        existing["limitations"]=[
            "SINGLE SOLUSDT August 2026 limited source-window: NOT 90 days",
            "Known upstream Goooddy June-Aug collector overwrite bug; full source unreliability remains",
            "Only 200k price level rows OR 30 min maximum audited in bounded replay",
            "No live fills, actual commissions, PnL or BINANCE004 absorption edge",
            "Even 007 original sequence bridge alone does not certify clean full-month replay"
        ]
    else:
        existing["status"]="SOURCE_BLOCKED"
    path.write_text(json.dumps(existing,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    receipt=hashlib.sha256(path.read_bytes()).hexdigest()
    (RUN_DIR/"l2_source_manifest.sha256").write_text(receipt+"  l2_source_manifest.json\n")
    print(json.dumps({"study":"BINANCE-DIAMANTE-009",
        "source_gate":existing["status"],"prior_engine_status":original_status,
        "blocker":existing.get("blocker"),"original_bytes_SHA256_downloads":{
            k:v.get("original_sha256") for k,v in existing.get("download_receipts",{}).items()
        },"strict_book_replay":existing.get("strict_book_replay"),
        "known_corrupted_month":True,
        "independent_post_bug_OOS":False,
        "no_economic_inference":True,"no_real_orders":True},indent=2,sort_keys=True))

if __name__=="__main__":
    status=SOURCE.main()
    finalize_receipt(status)
    raise SystemExit(status)
