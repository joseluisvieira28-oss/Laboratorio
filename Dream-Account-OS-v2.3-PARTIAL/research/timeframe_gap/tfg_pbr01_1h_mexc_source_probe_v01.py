from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request

LAB_ID = "TFG-PBR01-1H-001"
BASE_URL = "https://api.mexc.com/api/v3/klines"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
CUTOFF_2025_MS = 1735689600000
PROBES = (
    ("START_2022", 1640995200000, 1640996099999),
    ("END_2024", 1735688700000, 1735689599999),
)


def fetch_probe(symbol: str, label: str, start_ms: int, end_ms: int) -> dict:
    query = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": "15m",
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": 10,
    })
    request = urllib.request.Request(
        f"{BASE_URL}?{query}",
        method="GET",
        headers={"User-Agent": "Crypto-Lab-Source-Probe/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read()
        status_code = response.status
    payload = json.loads(raw.decode("utf-8"))
    rows = payload if isinstance(payload, list) else []
    open_times = [int(row[0]) for row in rows if isinstance(row, list) and row]
    return {
        "symbol": symbol,
        "probe": label,
        "http_status": status_code,
        "target_open_time_ms": start_ms,
        "response_row_count": len(rows),
        "exact_target_open_found": start_ms in open_times,
        "minimum_open_time_ms": min(open_times) if open_times else None,
        "maximum_open_time_ms": max(open_times) if open_times else None,
        "returned_2025_or_later": any(ts >= CUTOFF_2025_MS for ts in open_times),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> int:
    results = []
    errors = []
    for symbol in SYMBOLS:
        for label, start_ms, end_ms in PROBES:
            try:
                results.append(fetch_probe(symbol, label, start_ms, end_ms))
            except Exception as exc:
                errors.append({"symbol": symbol, "probe": label, "error": f"{type(exc).__name__}:{exc}"})

    passed = (
        not errors
        and len(results) == len(SYMBOLS) * len(PROBES)
        and all(row["exact_target_open_found"] for row in results)
        and not any(row["returned_2025_or_later"] for row in results)
    )
    report = {
        "status": "PASS_SOURCE_ROUTE_PROBE" if passed else "SOURCE_ROUTE_PROBE_FAILED",
        "lab_id": LAB_ID,
        "source": "MEXC_PUBLIC_SPOT_KLINES_GET_ONLY",
        "results": results,
        "errors": errors,
        "outcome_evaluation_performed": False,
        "return_or_pnl_computation_performed": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
