from __future__ import annotations

import argparse
import json

from .config import Settings
from .dashboard import render
from .database import Journal
from .engines import calculate_costs, confirmed_breakout_retest, position_size, score_candidate
from .fixtures import candles, liquid_book
from .mexc_client import MEXCClient
from .models import Candidate, utc_now
from .scanner import ScanResult, Scanner


def fixture_scan(settings: Settings, journal: Journal) -> ScanResult:
    now = utc_now()
    sol_candles = candles(105.5, 107.0)
    active, evidence = confirmed_breakout_retest(sol_candles, 107.0, 106.5, 107.0)
    book = liquid_book(107.15)
    costs = calculate_costs(107.15, 103.8, 114.0, 0.1, book.spread_pct, 0.01)
    candidate = Candidate("SOLUSDT", "SPOT", 107.15, 20_000_000, book.spread_pct, {"15m": 0.2, "1h": 2.1, "24h": 4.2}, 1.8, "RISK_ON_TREND", "BREAKOUT_RETEST", 107.15, 103.8, 114, 120)
    candidate.status = "LONG_CANDIDATE" if active else "NO_TRADE"
    score_candidate(candidate, settings, costs.net_rr, catalyst_confirmed=True)
    sizing = position_size(56, 2, candidate.entry, candidate.stop, 56)
    payload = {"fixture": True, "evidence": evidence, "costs": costs.__dict__, "sizing": sizing}
    result = ScanResult("OFFLINE_FIXTURE_ONLY", now, "FIXTURE", "RISK_ON_TREND", 1, 1, 1 if not candidate.rejection_reasons else 0, [candidate], [])
    scan_id = journal.record_scan(now, "FIXTURE", result.status, result.regime, payload)
    journal.record_candidate(scan_id, candidate.as_dict())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["live-scan", "fixture-scan"])
    args = parser.parse_args()
    settings = Settings()
    journal = Journal(settings.database_path)
    try:
        result = Scanner(MEXCClient(settings.request_timeout_seconds), settings, journal).live_scan() if args.mode == "live-scan" else fixture_scan(settings, journal)
        render(result, settings.dashboard_path)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
        raise SystemExit(0 if result.status in {"PASS", "OFFLINE_FIXTURE_ONLY"} else 2)
    finally:
        journal.close()


if __name__ == "__main__":
    main()
