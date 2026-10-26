#!/usr/bin/env python3
"""Read-only frozen-source custody gate. Never computes PnL on incomplete data."""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ASSETS = {"BTCUSDT", "AVAXUSDT", "SOLUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "LINKUSDT"}
EXPECTED_PAIRS = 319

def evaluate(source_audit: dict) -> dict:
    if not isinstance(source_audit, dict) or not isinstance(source_audit.get("manifest"), list):
        raise ValueError("INVALID_AUDIT_RECEIPT")
    entries = source_audit["manifest"]
    if len(entries) != EXPECTED_PAIRS or source_audit.get("archive_pairs") != EXPECTED_PAIRS:
        raise ValueError("EXPECTED_319_ARCHIVES")
    if source_audit.get("holdout_access") is not False:
        raise ValueError("HOLDOUT_CUSTODY_NOT_ATTESTED")
    if any(e.get("asset") not in ASSETS or e.get("month") < "2021-12" or e.get("month") > "2023-12" for e in entries):
        raise ValueError("UNEXPECTED_ASSET_OR_DATE")
    if any(not re.fullmatch(r"[0-9a-f]{64}", str(e.get("zip_sha256", ""))) for e in entries):
        raise ValueError("BAD_ARCHIVE_HASH")
    if any(e.get("checksum_matches") is not True for e in entries):
        raise ValueError("UNVERIFIED_ZIP_CHECKSUM")
    passed = sum(e.get("status") == "PASS" for e in entries)
    if passed != source_audit.get("passed") or EXPECTED_PAIRS-passed != source_audit.get("failed"):
        raise ValueError("COUNT_INCONSISTENCY")
    failures = [e for e in entries if e.get("status") != "PASS"]
    counts = Counter(e["asset"] for e in failures)
    result = {
        "label": "CRYPTO_LAB_FUSION_MULTI_ASSET_SOURCE_GATE_V032",
        "archive_pairs": EXPECTED_PAIRS,
        "hash_matches": sum(e.get("checksum_matches") is True for e in entries),
        "complete_archives": passed,
        "incomplete_archives": len(failures),
        "failures_by_asset": dict(sorted(counts.items())),
        "failed_files": [{"asset": e["asset"], "month": e["month"],
                          "timeframe": e.get("timeframe"), "error": e.get("error", "UNKNOWN")}
                         for e in failures],
        "historical_pnl": "NOT_REPORTED",
        "independent_edge": "NOT_DEMONSTRATED",
        "live_trading": "NO_GO",
        "protected_years_opened": False,
    }
    result["status"] = ("SOURCE_INCOMPLETE_FAIL_CLOSED" if failures
                        else "SOURCE_COMPLETE_ONLY_NOT_ECONOMIC_CERTIFICATION")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_audit", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    output = evaluate(json.loads(args.source_audit.read_text(encoding="utf-8")))
    body = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    print(body)

if __name__ == "__main__":
    main()
