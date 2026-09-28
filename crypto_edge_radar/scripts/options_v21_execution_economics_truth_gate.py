#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from radar.options_v21_execution_economics import analyze_receipt_root, analyze_session


def main() -> int:
    ap = argparse.ArgumentParser(description="OPTIONS V2.1 execution-economics truth gate")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--session", help="One directory containing immutable executor receipts")
    group.add_argument("--receipt-root", help="Root directory containing all executor sessions")
    ap.add_argument("--out", help="Optional output JSON path")
    args = ap.parse_args()

    if args.session:
        result = analyze_session(args.session)
        ok = bool(result.get("per_trade_economic_decomposition_allowed"))
    else:
        result = analyze_receipt_root(args.receipt_root)
        ok = result.get("complete_trade_count", 0) > 0

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
