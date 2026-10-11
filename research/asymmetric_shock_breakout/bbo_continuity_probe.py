#!/usr/bin/env python3
"""Time-bounded PUBLIC BBO continuity probe. No trading or outcome calculations."""
import argparse
import datetime as dt
import json
import time
from pathlib import Path
from public_bbo_probe import SYMBOLS, probe


def adjudicate(rows, elapsed_s, expected, min_coverage=0.90):
    detail = {}
    for symbol in SYMBOLS:
        samples = [r for r in rows if r["symbol"] == symbol]
        good = [r for r in samples if r.get("status") == "VALID_BBO"]
        versions = [r["version"] for r in good]
        monotonic = all(b >= a for a, b in zip(versions, versions[1:]))
        covered = len(good) / max(1, expected)
        max_gap_s = None
        if len(good) > 1:
            max_gap_s = max((b["observation_timestamp_ms"]-a["observation_timestamp_ms"])/1000
                            for a,b in zip(good, good[1:]))
        detail[symbol] = {"observations": len(samples), "valid": len(good),
                          "valid_over_expected": covered,
                          "version_nondecreasing": monotonic, "largest_observation_gap_s": max_gap_s}
    passes = (elapsed_s >= 60 and expected >= 13 and all(
        x["valid_over_expected"] >= min_coverage and x["version_nondecreasing"]
        and x["largest_observation_gap_s"] is not None and x["largest_observation_gap_s"] <= 12
        for x in detail.values()))
    return {"status": "SOURCE_CONTINUITY_PASS_BOUNDED" if passes else "SOURCE_CONTINUITY_BLOCKED",
            "symbols": detail, "evaluation_duration_s": elapsed_s,
            "expected_snapshots_per_symbol": expected, "minimum_coverage": min_coverage,
            "limits": ["A 75s public source test cannot establish availability at future shock times, historical data, fill quality, or any trading edge."]}


def run(duration_s, interval_s):
    if not 60 <= duration_s <= 120 or not 4 <= interval_s <= 10:
        raise ValueError("BOUNDED_RANGE_REQUIRED")
    records = []
    start = time.monotonic()
    deadline = start + duration_s
    tick = 0
    while time.monotonic() <= deadline + 0.01:
        for symbol in SYMBOLS:
            try:
                d = probe(symbol)
                records.append({"status":"VALID_BBO", **d})
            except Exception as exc:
                records.append({"symbol":symbol, "status":"INVALID_BBO",
                                "error_type":type(exc).__name__, "reason":str(exc)[:120],
                                "observation_timestamp_ms":int(time.time()*1000)})
        tick += 1
        next_tick = start + tick * interval_s
        if next_tick > deadline:
            break
        time.sleep(max(0, next_tick - time.monotonic()))
    elapsed = time.monotonic()-start
    result = adjudicate(records, elapsed, tick)
    return {"schema":"asym_shock_bbo_continuity.v1",
            "trading_authority":"NONE", "live_trading":False,
            "collected_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "duration_requested_s":duration_s, "poll_interval_s":interval_s,
            "receipt":result, "records":records}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--duration-s",type=int,default=75)
    p.add_argument("--interval-s",type=int,default=5)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    out=run(a.duration_s,a.interval_s)
    dst=Path(a.out)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":out["schema"],"trading_authority":"NONE","receipt":out["receipt"]},sort_keys=True,indent=2))


if __name__=="__main__":
    main()
