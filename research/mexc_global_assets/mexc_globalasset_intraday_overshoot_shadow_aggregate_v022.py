#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

NOTIONAL_KEYS = ["10", "25", "50", "100"]
PRIMARY_FEE_BPS = 16.0
COOLDOWN_SEC = 600
MIN_EVENTS = 30
MIN_DATES = 5


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def median(xs):
    return statistics.median(xs) if xs else None


def halves(xs):
    if len(xs) < 2:
        return [None, None]
    k = len(xs) // 2
    return [mean(xs[:k]), mean(xs[k:])]


def signed_exec_bps(asset, key):
    if not asset.get("entry_timing_valid") or not asset.get("exit_timing_valid"):
        raise ValueError("TIMING_INVALID")
    ef = (asset.get("entry_fills") or {}).get(key) or {}
    xf = (asset.get("exit_fills") or {}).get(key) or {}
    if not ef.get("fillable") or not xf.get("fillable"):
        raise ValueError("UNFILLABLE")
    entry_quote = float(ef["quote_notional"])
    exit_quote = float(xf["quote_notional"])
    if entry_quote <= 0:
        raise ValueError("BAD_ENTRY_NOTIONAL")
    side = int(asset["side"])
    pnl_quote = (exit_quote - entry_quote) if side > 0 else (entry_quote - exit_quote)
    return 10000.0 * pnl_quote / entry_quote


def load_receipts(root):
    files = sorted(root.glob("**/shadow_*.json"))
    return files, [json.loads(p.read_text()) for p in files]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="artifacts/mexc_global_assets/intraday_overshoot_shadow_v022")
    ap.add_argument("--out", default="artifacts/mexc_global_assets/intraday_overshoot_shadow_v022/aggregate_v022.json")
    a = ap.parse_args()
    files, receipts = load_receipts(Path(a.root))

    if not receipts:
        report = {
            "overall_verdict": "EXECUTION_SHADOW_UNDERPOWERED",
            "reason": "NO_RECEIPTS",
            "receipt_files": 0,
            "admitted_event_baskets": 0,
            "distinct_session_dates": 0,
        }
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    source_errors = []
    raw_by_ts = defaultdict(dict)
    duplicate_conflicts = []

    for rec in receipts:
        if rec.get("shadow_version") != "0.2.2":
            source_errors.append({"date": rec.get("date"), "error": "WRONG_SHADOW_VERSION"})
        for e in rec.get("errors") or []:
            source_errors.append({"date": rec.get("date"), **e})
        if rec.get("pending_events"):
            source_errors.append({"date": rec.get("date"), "error": "PENDING_EVENTS_AT_RECEIPT"})
        for ev in rec.get("events") or []:
            ts = int(ev["timestamp"])
            for asset in ev.get("assets") or []:
                target = asset.get("target")
                if target in raw_by_ts[ts]:
                    old = raw_by_ts[ts][target]
                    old_hashes = json.dumps(old.get("source_evidence"), sort_keys=True)
                    new_hashes = json.dumps(asset.get("source_evidence"), sort_keys=True)
                    if old_hashes != new_hashes:
                        duplicate_conflicts.append({"timestamp": ts, "target": target})
                else:
                    raw_by_ts[ts][target] = asset

    merged = []
    for ts in sorted(raw_by_ts):
        assets = [raw_by_ts[ts][k] for k in sorted(raw_by_ts[ts])]
        merged.append({"timestamp": ts, "assets": assets})

    admitted = []
    last = None
    for ev in merged:
        if last is not None and ev["timestamp"] - last < COOLDOWN_SEC:
            continue
        admitted.append(ev)
        last = ev["timestamp"]

    dates = sorted({__import__("datetime").datetime.fromtimestamp(ev["timestamp"], __import__("datetime").timezone.utc).date().isoformat() for ev in admitted})
    by_bucket = {}

    for key in NOTIONAL_KEYS:
        event_rows = []
        bucket_failures = []
        for ev in admitted:
            asset_bps = []
            for asset in ev["assets"]:
                try:
                    asset_bps.append(signed_exec_bps(asset, key))
                except Exception as exc:
                    bucket_failures.append({
                        "timestamp": ev["timestamp"],
                        "target": asset.get("target"),
                        "error": str(exc),
                    })
            if len(asset_bps) != len(ev["assets"]):
                continue
            event_rows.append({
                "timestamp": ev["timestamp"],
                "gross_exec_bps": mean(asset_bps),
                "net_16bps": mean(asset_bps) - PRIMARY_FEE_BPS,
            })

        daily = defaultdict(list)
        for row in event_rows:
            d = __import__("datetime").datetime.fromtimestamp(row["timestamp"], __import__("datetime").timezone.utc).date().isoformat()
            daily[d].append(row["net_16bps"])
        daily_vals = [mean(daily[d]) for d in sorted(daily)]

        enough = len(admitted) >= MIN_EVENTS and len(dates) >= MIN_DATES
        source_blocked = bool(source_errors or duplicate_conflicts or bucket_failures)
        stats = {
            "admitted_event_baskets": len(admitted),
            "distinct_session_dates": len(dates),
            "complete_exec_event_baskets": len(event_rows),
            "source_or_book_failures": len(bucket_failures),
            "mean_daily_net_16bps": mean(daily_vals),
            "median_daily_net_16bps": median(daily_vals),
            "half_means_daily_net_16bps": halves(daily_vals),
        }

        if source_blocked:
            verdict = "EXECUTION_SOURCE_BLOCKED"
        elif not enough:
            verdict = "EXECUTION_SHADOW_UNDERPOWERED"
        elif (
            stats["mean_daily_net_16bps"] is not None
            and stats["mean_daily_net_16bps"] > 0
            and stats["median_daily_net_16bps"] > 0
            and all(x is not None and x > 0 for x in stats["half_means_daily_net_16bps"])
        ):
            verdict = "EXECUTION_FEASIBILITY_PASS__MICROLIVE_STILL_NOT_AUTHORIZED"
        else:
            verdict = "EXECUTION_FEASIBILITY_FAIL"

        by_bucket[key] = {
            "verdict": verdict,
            "metrics": stats,
            "bucket_failures": bucket_failures,
            "daily_net_16bps": [{"date": d, "net_bps": mean(daily[d])} for d in sorted(daily)],
        }

    verdicts = {x["verdict"] for x in by_bucket.values()}
    if "EXECUTION_SOURCE_BLOCKED" in verdicts:
        overall = "EXECUTION_SOURCE_BLOCKED"
    elif "EXECUTION_SHADOW_UNDERPOWERED" in verdicts:
        overall = "EXECUTION_SHADOW_UNDERPOWERED"
    elif verdicts == {"EXECUTION_FEASIBILITY_PASS__MICROLIVE_STILL_NOT_AUTHORIZED"}:
        overall = "EXECUTION_FEASIBILITY_PASS__MICROLIVE_STILL_NOT_AUTHORIZED"
    else:
        overall = "EXECUTION_FEASIBILITY_MIXED_BY_NOTIONAL"

    report = {
        "family_id": "MEXC-GLOBALASSET-INTRADAY-OVERSHOOT-SNAPBACK-V1.0",
        "shadow_version": "0.2.2",
        "receipt_files": len(files),
        "overall_verdict": overall,
        "admitted_event_baskets": len(admitted),
        "distinct_session_dates": len(dates),
        "source_errors": source_errors,
        "duplicate_conflicts": duplicate_conflicts,
        "by_notional_usdt": by_bucket,
        "orders": False,
        "account_reads": False,
        "private_endpoints_used": False,
        "exchange_mutation": False,
        "live_trading": False,
        "post_outcome_tuning": False,
    }

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
