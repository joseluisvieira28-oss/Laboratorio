#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from radar.options_v21_execution_economics import analyze_session


def main() -> int:
    ap = argparse.ArgumentParser(description="OPTIONS V2.1 execution-economics truth gate")
    ap.add_argument("--session", required=True, help="Directory containing immutable executor receipts")
    ap.add_argument("--out", help="Optional output JSON path")
    args = ap.parse_args()

    result = analyze_session(args.session)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    return 0 if result.get("economic_verdict_allowed") else 4


if __name__ == "__main__":
    raise SystemExit(main())
