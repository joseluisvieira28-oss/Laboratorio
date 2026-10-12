"""Offline first-touch bar-path classifier. NOT a fill or trading simulator.

Input JSON: array of objects with entry_ts (Unix ms), end_ts, step_seconds,
entry_price, stop_price, target_price, bars (timestamp ts plus OHLC).
All bars must be complete and contiguous from entry_ts. Price-only and long-only.
"""
import argparse
import json
from pathlib import Path


def classify(case):
    try:
        entry_ts = int(case["entry_ts"])
        end_ts = int(case["end_ts"])
        seconds = int(case["step_seconds"])
        px = float(case["entry_price"])
        stop = float(case["stop_price"])
        target = float(case["target_price"])
        bars = case["bars"]
        if not (seconds > 0 and entry_ts < end_ts and 0 < stop < px < target):
            return "INVALID_INPUT"
        if not bars:
            return "MISSING_PATH"
        tick = seconds * 1000
        expected_ts = entry_ts
        for b in bars:
            ts = int(b["ts"])
            o, h, l, c = (float(b[k]) for k in ("open", "high", "low", "close"))
            if ts != expected_ts or ts + tick > end_ts:
                return "MISSING_OR_PARTIAL_PATH"
            if not (0 < l <= min(o, c) <= max(o, c) <= h):
                return "INVALID_OHLC"
            if o <= stop:
                return "STOP_GAP_FIRST_NO_FILL_GUARANTEE"
            if o >= target:
                return "TARGET_GAP_FIRST_NO_FILL_GUARANTEE"
            stop_hit, target_hit = l <= stop, h >= target
            if stop_hit and target_hit:
                return "AMBIGUOUS_SAME_BAR"
            if stop_hit:
                return "STOP_FIRST_NO_FILL_GUARANTEE"
            if target_hit:
                return "TARGET_FIRST_NO_FILL_GUARANTEE"
            expected_ts += tick
        if expected_ts < end_ts:
            return "MISSING_OR_PARTIAL_PATH"
        return "NEITHER_TOUCHED"
    except (ValueError, TypeError, KeyError, OverflowError):
        return "INVALID_INPUT"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON array of permitted research cases")
    args = parser.parse_args()
    cases = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("Expect a JSON array")
    for i, case in enumerate(cases):
        print(json.dumps({"index": i, "classification": classify(case)}, sort_keys=True))


if __name__ == "__main__":
    main()
