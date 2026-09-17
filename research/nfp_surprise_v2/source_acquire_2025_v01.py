#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

LAB_ID = "NFP-SURPRISE-V2-REPLICATION-01"
VERSION = "2025-SOURCE-V0.1"
AUTHORITY_COMMIT = "0bbd3ae2c6e406b1f86aaf1dde19f78c7bf3dc7d"
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SYMBOLS = ("BTCUSDT", "ETHUSDT")
RELEASE_DATES = (
    "2025-01-10", "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02",
    "2025-06-06", "2025-07-03", "2025-08-01", "2025-09-05", "2025-11-20",
    "2025-12-16",
)
DIRECTIONAL_DATES = (
    "2025-01-10", "2025-02-07", "2025-03-07", "2025-06-06", "2025-07-03",
    "2025-08-01", "2025-09-05", "2025-11-20", "2025-12-16",
)
USER_AGENT = f"{LAB_ID}/{VERSION} source-only"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def to_ms(raw: int) -> tuple[int, str]:
    if 1_000_000_000_000 <= raw < 10_000_000_000_000:
        return raw, "milliseconds"
    if 1_000_000_000_000_000 <= raw < 10_000_000_000_000_000:
        return raw // 1000, "microseconds"
    raise RuntimeError(f"FAIL_CLOSED: unexpected Binance timestamp magnitude {raw}")


def expected_bar_ms(date_s: str, hhmm: str) -> int:
    day = dt.date.fromisoformat(date_s)
    hh, mm = map(int, hhmm.split(":"))
    local = dt.datetime(day.year, day.month, day.day, hh, mm, tzinfo=NY)
    utc = local.astimezone(UTC)
    if utc.year >= 2026:
        raise RuntimeError("FAIL_CLOSED: protected 2026 timestamp")
    return int(utc.timestamp() * 1000)


def fetch_one(symbol: str, date_s: str, out: Path) -> dict:
    name = f"{symbol}-1m-{date_s}.zip"
    url = f"https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{name}"
    p = out / "raw" / symbol / name
    p.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        p.write_bytes(r.read())
    if not p.exists() or p.stat().st_size == 0:
        raise RuntimeError(f"FAIL_CLOSED: empty archive {name}")

    with zipfile.ZipFile(p) as zf:
        members = [n for n in zf.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"FAIL_CLOSED: unexpected zip members {name}")
        timestamps: list[int] = []
        units: set[str] = set()
        with zf.open(members[0]) as fh:
            for row in csv.reader(io.TextIOWrapper(fh, encoding="utf-8", newline="")):
                if not row:
                    continue
                ms, unit = to_ms(int(row[0]))
                units.add(unit)
                ts = dt.datetime.fromtimestamp(ms / 1000, tz=UTC)
                if ts.year >= 2026:
                    raise RuntimeError(f"FAIL_CLOSED: protected 2026 row in {name}")
                if ts.date() != dt.date.fromisoformat(date_s):
                    raise RuntimeError(f"FAIL_CLOSED: archive date drift {name}: {ts.isoformat()}")
                timestamps.append(ms)
    if len(units) != 1:
        raise RuntimeError(f"FAIL_CLOSED: mixed timestamp units {name}")
    if len(timestamps) not in (1439, 1440, 1441):
        raise RuntimeError(f"FAIL_CLOSED: unexpected 1m row count {name}: {len(timestamps)}")
    if len(set(timestamps)) != len(timestamps):
        raise RuntimeError(f"FAIL_CLOSED: duplicate timestamps {name}")

    entry = expected_bar_ms(date_s, "08:31")
    exit_ = expected_bar_ms(date_s, "08:45")
    if entry not in timestamps or exit_ not in timestamps:
        raise RuntimeError(f"FAIL_CLOSED: required bars absent {symbol} {date_s}")

    return {
        "symbol": symbol,
        "date": date_s,
        "file": str(p.relative_to(out)),
        "url": url,
        "sha256": sha256_file(p),
        "bytes": p.stat().st_size,
        "rows": len(timestamps),
        "timestamp_unit": next(iter(units)),
        "entry_0831_ny_ms": entry,
        "exit_0845_ny_ms": exit_,
        "prices_opened": False,
        "returns_computed": False,
        "pnl_computed": False,
    }


def run(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for date_s in RELEASE_DATES:
        if dt.date.fromisoformat(date_s).year != 2025:
            raise RuntimeError("FAIL_CLOSED: non-2025 release in frozen corpus")
        for symbol in SYMBOLS:
            records.append(fetch_one(symbol, date_s, out))

    checks = {
        "all_22_archives_present": len(records) == len(RELEASE_DATES) * len(SYMBOLS),
        "all_required_bars_present": all(r["entry_0831_ny_ms"] and r["exit_0845_ny_ms"] for r in records),
        "all_hashes_present": all(bool(r["sha256"]) for r in records),
        "macro_directional_count_is_9": len(DIRECTIONAL_DATES) == 9,
        "year_2026_accessed": False,
        "prices_opened": False,
        "returns_computed": False,
        "pnl_computed": False,
    }
    positive = all(v is True for k, v in checks.items() if k not in {"year_2026_accessed", "prices_opened", "returns_computed", "pnl_computed"})
    firewall = all(checks[k] is False for k in ("year_2026_accessed", "prices_opened", "returns_computed", "pnl_computed"))
    status = "SOURCE_AUDIT_PASS" if positive and firewall else "SOURCE_AUDIT_BLOCKED"
    manifest = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "authority_commit": AUTHORITY_COMMIT,
        "stage": "2025_BINANCE_SOURCE_ONLY",
        "status": status,
        "release_dates": list(RELEASE_DATES),
        "directional_dates": list(DIRECTIONAL_DATES),
        "symbols": list(SYMBOLS),
        "records": records,
        "checks": checks,
        "outcomes_computed": False,
        "year_2026_accessed": False,
        "live_trading": False,
        "exchange_mutation": False,
    }
    (out / "source_manifest_2025.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(status)
    print("ARCHIVES=", len(records))
    print("SOURCE_ONLY=true / PRICES_OPENED=false / RETURNS=false / PNL=false / 2026_LOCKED=true")
    return 0 if status == "SOURCE_AUDIT_PASS" else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    raise SystemExit(run(Path(args.output).resolve()))
