#!/usr/bin/env python3
import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBS_DIR = ROOT / "observations"
OUT_DIR = ROOT / "outcomes"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://fapi.binance.com"
PATH = "/fapi/v1/klines"
SYMBOL_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
HORIZONS = {"1h": 60, "4h": 240}

def parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"naive timestamp: {s}")
    return dt.astimezone(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def next_whole_minute_strict(dt: datetime) -> datetime:
    floored = dt.replace(second=0, microsecond=0)
    return floored + timedelta(minutes=1)

def fingerprint(row: dict) -> str:
    return json.dumps(row["tiers"], sort_keys=True, separators=(",", ":"))

def fetch_exact_kline(symbol: str, minute: datetime):
    target_ms = int(minute.timestamp() * 1000)
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": "1m",
        "startTime": target_ms,
        "endTime": target_ms + 59999,
        "limit": 1,
    })
    url = f"{BASE_URL}{PATH}?{params}"
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-CoInvest-Forward/0.1"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, list) or len(data) != 1:
                raise RuntimeError(f"unexpected kline payload: {data!r}")
            row = data[0]
            if not isinstance(row, list) or len(row) < 7:
                raise RuntimeError(f"malformed kline row: {row!r}")
            if int(row[0]) != target_ms:
                raise RuntimeError(f"kline open time mismatch: expected {target_ms}, got {row[0]}")
            return row, url
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch exact kline {symbol} {iso(minute)}: {last_err}")

def classify_rows(rows):
    prev = {}
    classified = []
    for payload, row in rows:
        symbol = row["symbol"]
        src = parse_iso(row["source_created_at_utc"])
        fp = fingerprint(row)
        if symbol not in prev:
            cls = "BASELINE_ONLY"
        else:
            prev_src, prev_fp = prev[symbol]
            if src < prev_src:
                raise RuntimeError(f"{row['observation_id']}: source timestamp regressed")
            if src == prev_src and fp == prev_fp:
                cls = "DUPLICATE_SOURCE_SNAPSHOT"
            elif src > prev_src and fp != prev_fp:
                cls = "EVENT_ELIGIBLE"
            elif src > prev_src and fp == prev_fp:
                cls = "SOURCE_TIMESTAMP_ONLY"
            else:
                raise RuntimeError(
                    f"{row['observation_id']}: SOURCE_INTEGRITY_CONFLICT payload changed without source timestamp advance"
                )
        prev[symbol] = (src, fp)
        classified.append((payload, row, cls))
    return classified

def load_rows():
    rows = []
    for path in sorted(OBS_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed = parse_iso(payload["observed_at_utc"])
        for row in payload["observations"]:
            rows.append((observed, path.name, payload, row))
    rows.sort(key=lambda x: (x[0], x[3]["symbol"], x[3]["observation_id"]))
    return [(payload, row) for _, _, payload, row in rows]

def main():
    now = datetime.now(timezone.utc)
    rows = classify_rows(load_rows())
    created = 0
    skipped_not_due = 0
    skipped_non_event = 0

    for payload, row, event_class in rows:
        symbol = row["symbol"]
        if symbol not in SYMBOL_MAP:
            raise RuntimeError(f"symbol outside frozen mapping: {symbol}")

        if event_class not in {"BASELINE_ONLY", "EVENT_ELIGIBLE"}:
            skipped_non_event += 1
            continue

        observed_at = parse_iso(payload["observed_at_utc"])
        entry_minute = next_whole_minute_strict(observed_at)

        for horizon, mins in HORIZONS.items():
            target_minute = entry_minute + timedelta(minutes=mins)
            eligible_after = target_minute + timedelta(minutes=1)
            if now < eligible_after:
                skipped_not_due += 1
                continue

            out_path = OUT_DIR / f"{row['observation_id']}__{horizon}.json"
            if out_path.exists():
                continue

            venue_symbol = SYMBOL_MAP[symbol]
            entry_row, entry_url = fetch_exact_kline(venue_symbol, entry_minute)
            exit_row, exit_url = fetch_exact_kline(venue_symbol, target_minute)

            entry_open = float(entry_row[1])
            exit_open = float(exit_row[1])
            if not (math.isfinite(entry_open) and math.isfinite(exit_open) and entry_open > 0 and exit_open > 0):
                raise RuntimeError(f"{row['observation_id']} {horizon}: invalid open price")

            simple_return_pct = 100.0 * (exit_open / entry_open - 1.0)
            result = {
                "experiment": "LIQUID_COINVEST_FORWARD_V0.1",
                "outcome_freeze": "LIQUID_COINVEST_OUTCOME_RESOLUTION_FREEZE_V0.1",
                "source_observation_id": row["observation_id"],
                "symbol": symbol,
                "event_class": event_class,
                "observed_at_utc": payload["observed_at_utc"],
                "entry_minute_utc": iso(entry_minute),
                "horizon": horizon,
                "target_minute_utc": iso(target_minute),
                "eligible_after_utc": iso(eligible_after),
                "resolved_at_utc": iso(now),
                "venue": "Binance USD-M perpetual",
                "binance_symbol": venue_symbol,
                "source_endpoint": f"{BASE_URL}{PATH}",
                "entry_request_url": entry_url,
                "exit_request_url": exit_url,
                "entry_raw_kline": entry_row,
                "exit_raw_kline": exit_row,
                "entry_open": entry_open,
                "exit_open": exit_open,
                "simple_return_pct": simple_return_pct,
                "absolute_return_pct": abs(simple_return_pct),
                "status": "RESOLVED"
            }

            with out_path.open("x", encoding="utf-8") as f:
                json.dump(result, f, indent=2, sort_keys=False)
                f.write("\n")

            created += 1
            print(f"RESOLVED {row['observation_id']} {horizon} {simple_return_pct:+.6f}%")

    print(
        f"DONE created={created} skipped_not_due={skipped_not_due} "
        f"skipped_non_event={skipped_non_event}"
    )

if __name__ == "__main__":
    main()
