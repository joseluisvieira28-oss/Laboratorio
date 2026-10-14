#!/usr/bin/env python3
"""Read-only triage of operator-supplied Pine source. NEVER a science/edge PASS.

Usage: python research/tradingview_diamond_hunter_v01/pine_source_preflight.py file.pine
Prints JSON only; does not connect to TradingView or trade, store source, or run backtests.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

MAX_BYTES = 1024 * 1024
CHECKS = {
    "lookahead_on": r"\blookahead\s*=\s*barmerge\.lookahead_on\b|\bbarmerge\.lookahead_on\b",
    "higher_or_external_series": r"\b(?:request\.)?security\s*\(",
    "security_lower_tf": r"\brequest\.security_lower_tf\s*\(",
    "calc_on_every_tick": r"\bcalc_on_every_tick\s*=\s*true\b",
    "calc_on_order_fills": r"\bcalc_on_order_fills\s*=\s*true\b",
    "process_orders_on_close": r"\bprocess_orders_on_close\s*=\s*true\b",
    "nonstandard_chart": r"\bticker\.(?:heikinashi|renko|kagi|linebreak|pointfigure)\s*\(",
    "future_plot_offset": r"\boffset\s*=\s*[1-9][0-9]*\b",
    "barstate_confirmation": r"\bbarstate\.isconfirmed\b",
    "strategy_order": r"\bstrategy\.(?:entry|order|exit|close|close_all)\s*\(",
    "limit_orders": r"\b(?:limit|stop)\s*=",
}
def audit(raw: bytes) -> dict:
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("empty source or >1 MiB")
    source = raw.decode("utf-8-sig", errors="strict")
    if not re.search(r"//@version\s*=\s*[2-6]", source):
        raise ValueError("Pine version annotation missing or unsupported")
    is_strategy = bool(re.search(r"(?m)^\s*strategy\s*\(", source))
    is_indicator = bool(re.search(r"(?m)^\s*indicator\s*\(", source))
    if is_strategy == is_indicator:
        raise ValueError("source must have exactly one explicit strategy/indicator declaration")
    flags = {name: bool(re.search(pattern, source, re.IGNORECASE)) for name, pattern in CHECKS.items()}
    return {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw),
        "kind": "strategy" if is_strategy else "indicator",
        "flags_for_human_review": flags,
        "source_gate": "RECEIVED_NOT_AUDITED",
        "economic_outcome": "UNTESTED",
        "live_authority": "NONE",
        "note": "Regex flags are clues, not proof of repainting/no-repainting. Manual causal review and provenance/funding/venue gates mandatory.",
    }

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=pathlib.Path)
    a = ap.parse_args(argv)
    try:
        result = audit(a.path.read_bytes())
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"source_gate": "SOURCE_BLOCKED", "error": str(exc), "live_authority": "NONE"}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
