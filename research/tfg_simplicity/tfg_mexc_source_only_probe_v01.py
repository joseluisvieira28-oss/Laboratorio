#!/usr/bin/env python3
"""TFG Donchian regime V1 source-only feasibility probe.

No keys, orders, trading account reads, price/return reports, or outcome evaluation.
Uses the exact public MEXC Spot REST feed and frozen universe from the Radar implementation.
This is operational diagnosis; it does NOT reconstruct missed prospective evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "crypto_edge_radar"))

from radar.strategies.tfg_donchian_regime_forward import (
    Candle, DAY_MS, FIFTEEN_MIN_MS, FORWARD_FREEZE_MS, FROZEN_UNIVERSE,
    MEXCSpotKlineFeed, _parse_kline, utc_iso_from_ms,
)

ANCHOR_MS = ((FORWARD_FREEZE_MS // DAY_MS) + 1) * DAY_MS


def self_test() -> None:
    row = [ANCHOR_MS, "100", "101", "99", "100.5", "2", ANCHOR_MS + FIFTEEN_MIN_MS, "201"]
    c = _parse_kline(row, "15m")
    assert isinstance(c, Candle)
    assert c.close_time == ANCHOR_MS + FIFTEEN_MIN_MS - 1
    try:
        _parse_kline(row[:6] + [ANCHOR_MS + FIFTEEN_MIN_MS - 1], "15m")
    except Exception:
        pass
    else:
        raise AssertionError("Native timestamp mismatch not rejected")
    assert FROZEN_UNIVERSE == ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
    print("SOURCE_ONLY_SYNTHETIC_TEST_PASS")


def live_probe(*, output: Path) -> int:
    # Test three operational necessities, independent of any profitability:
    # present-day 15m, first legitimate post-freeze 15m, and remote 1d warm-up.
    now_ms = int(time.time() * 1000)
    current_15m_end = (now_ms // FIFTEEN_MIN_MS) * FIFTEEN_MIN_MS
    current_day_end = (now_ms // DAY_MS) * DAY_MS
    frozen_start = ANCHOR_MS
    checks = (
        ("recent_15m", "15m", current_15m_end - 4 * FIFTEEN_MIN_MS,
         current_15m_end, 4),
        ("first_forward_15m_source_exists", "15m", frozen_start,
         frozen_start + 4 * FIFTEEN_MIN_MS, 4),
        ("daily_regime_warmup_source_exists", "1d",
         frozen_start - 220 * DAY_MS, frozen_start - 218 * DAY_MS, 2),
        ("recent_daily", "1d", current_day_end - 3 * DAY_MS,
         current_day_end, 3),
    )
    feed = MEXCSpotKlineFeed(timeout=8, max_attempts=2, retry_backoff_seconds=0.5)
    evidence = {
        "experiment": "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
        "classification": "SOURCE_ONLY",
        "source_identity": "MEXC_SPOT_PUBLIC_GET_/api/v3/klines",
        "frozen_universe": list(FROZEN_UNIVERSE),
        "probe_at_utc": utc_iso_from_ms(now_ms),
        "first_post_freeze_utc_boundary": utc_iso_from_ms(ANCHOR_MS),
        "checks": [],
        "permissions": {
            "public_unauthenticated_read_only": True,
            "account_reads": False, "orders": False, "live_trading": False,
            "historical_outcomes_evaluated": False,
            "reconstructed_forward_evidence": False,
        },
    }
    for symbol in FROZEN_UNIVERSE:
        for label, interval, start, end, expected in checks:
            entry = {"symbol": symbol, "check": label, "interval": interval,
                     "start_utc": utc_iso_from_ms(start),
                     "end_exclusive_utc": utc_iso_from_ms(end),
                     "expected_bars": expected}
            try:
                bars = feed.klines(symbol, interval, start_ms=start,
                                  end_ms=end, now_ms=now_ms)
                step = FIFTEEN_MIN_MS if interval == "15m" else DAY_MS
                found = [c.open_time for c in bars]
                want = [start + i * step for i in range(expected)]
                entry["bars_returned"] = len(bars)
                entry["strict_coverage_pass"] = found == want
                entry["native_timestamp_validated"] = True
                if bars:
                    entry["first_bar_utc"] = utc_iso_from_ms(bars[0].open_time)
                    entry["last_bar_utc"] = utc_iso_from_ms(bars[-1].open_time)
            except Exception as exc:
                entry["strict_coverage_pass"] = False
                entry["error_type"] = type(exc).__name__
                entry["error_message"] = str(exc)[:320]
            evidence["checks"].append(entry)
            print("SOURCE_CHECK", symbol, label,
                  "PASS" if entry["strict_coverage_pass"] else "FAIL",
                  entry.get("error_type", ""), flush=True)
    passed = sum(x["strict_coverage_pass"] for x in evidence["checks"])
    evidence["checks_passed"] = passed
    evidence["checks_total"] = len(evidence["checks"])
    evidence["status"] = "SOURCE_SAMPLE_PASS" if passed == len(evidence["checks"]) else "SOURCE_SAMPLE_BLOCKED"
    evidence["scientific_verdict"] = "NOT_TESTED"
    evidence["forward_verdict"] = "NOT_TESTED"
    evidence["note"] = (
        "A source health PASS does NOT establish continuous historical completeness, "
        "persisted forward signals, executable returns, or current runtime health. "
        "Do not backdate evidence or credit missed observations."
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SOURCE_PROBE_RESULT", evidence["status"], str(output), flush=True)
    return 0 if passed == len(evidence["checks"]) else 2


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("--live", action="store_true")
    cli.add_argument("--output", type=Path,
                     default=Path("research/tfg_simplicity/receipt_source_only.json"))
    args = cli.parse_args()
    if args.self_test:
        self_test()
    if args.live:
        raise SystemExit(live_probe(output=args.output))
    if not (args.self_test or args.live):
        cli.error("specify --self-test and/or --live")
