#!/usr/bin/env python3
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "outcomes"
SYMBOL_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
HORIZON_MINUTES = {"1h": 60, "4h": 240}
REL_TOL = 1e-12
ABS_TOL = 1e-10
EXPECTED_ENDPOINT = "https://fapi.binance.com/fapi/v1/klines"
EXPECTED_AMENDMENT = "LIQUID_COINVEST_OUTCOME_TRANSPORT_AMENDMENT_V0.1"
ALLOWED_ROUTES = {"FAPI_LIVE", "BINANCE_PUBLIC_DATA_DAILY_ARCHIVE"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"naive timestamp: {s}")
    return dt.astimezone(timezone.utc)


def fail(msg):
    raise SystemExit(f"FAIL: {msg}")


def validate_transport(path_name, label, t):
    if not isinstance(t, dict):
        fail(f"{path_name}: {label} transport missing")
    route = t.get("route")
    if route not in ALLOWED_ROUTES:
        fail(f"{path_name}: {label} unauthorized transport route {route!r}")
    if t.get("underlying_endpoint") != EXPECTED_ENDPOINT:
        fail(f"{path_name}: {label} underlying endpoint mismatch")

    request_url = t.get("request_url", "")
    if route == "FAPI_LIVE":
        if not request_url.startswith(EXPECTED_ENDPOINT + "?"):
            fail(f"{path_name}: {label} live request URL mismatch")
    else:
        if not request_url.startswith("https://data.binance.vision/data/futures/um/daily/klines/"):
            fail(f"{path_name}: {label} archive URL mismatch")
        if not request_url.endswith(".zip"):
            fail(f"{path_name}: {label} archive must be ZIP")
        checksum_url = t.get("checksum_url", "")
        if checksum_url != request_url + ".CHECKSUM":
            fail(f"{path_name}: {label} checksum URL mismatch")
        actual = str(t.get("zip_sha256", "")).lower()
        expected = str(t.get("checksum_expected_sha256", "")).lower()
        if not SHA256_RE.match(actual) or not SHA256_RE.match(expected):
            fail(f"{path_name}: {label} malformed archive SHA256")
        if actual != expected:
            fail(f"{path_name}: {label} archive SHA256 does not match official checksum")
        if not t.get("archive_member"):
            fail(f"{path_name}: {label} archive member missing")


files = sorted(OUT_DIR.glob("*.json")) if OUT_DIR.exists() else []
seen = set()

for path in files:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("experiment") != "LIQUID_COINVEST_FORWARD_V0.1":
        fail(f"{path.name}: wrong experiment")
    if d.get("outcome_freeze") != "LIQUID_COINVEST_OUTCOME_RESOLUTION_FREEZE_V0.1":
        fail(f"{path.name}: wrong outcome freeze")
    if d.get("transport_amendment") != EXPECTED_AMENDMENT:
        fail(f"{path.name}: missing/wrong transport amendment")
    if d.get("status") != "RESOLVED":
        fail(f"{path.name}: non-resolved status")

    key = (d["source_observation_id"], d["horizon"])
    if key in seen:
        fail(f"duplicate outcome key {key}")
    seen.add(key)

    symbol = d["symbol"]
    if d["binance_symbol"] != SYMBOL_MAP.get(symbol):
        fail(f"{path.name}: symbol mapping mismatch")
    if d.get("venue") != "Binance USD-M perpetual":
        fail(f"{path.name}: venue mismatch")
    if d.get("source_endpoint") != EXPECTED_ENDPOINT:
        fail(f"{path.name}: source endpoint mismatch")

    horizon = d["horizon"]
    if horizon not in HORIZON_MINUTES:
        fail(f"{path.name}: unknown horizon")

    observed = parse_iso(d["observed_at_utc"])
    entry = parse_iso(d["entry_minute_utc"])
    target = parse_iso(d["target_minute_utc"])
    eligible_after = parse_iso(d["eligible_after_utc"])
    resolved = parse_iso(d["resolved_at_utc"])

    if not (entry > observed):
        fail(f"{path.name}: entry minute not strictly after observation")
    if entry.second != 0 or entry.microsecond != 0:
        fail(f"{path.name}: entry not whole minute")
    if (target - entry).total_seconds() != HORIZON_MINUTES[horizon] * 60:
        fail(f"{path.name}: target horizon mismatch")
    if (eligible_after - target).total_seconds() != 60:
        fail(f"{path.name}: eligible-after must be target + 1 minute")
    if resolved < eligible_after:
        fail(f"{path.name}: outcome resolved before frozen eligibility")

    validate_transport(path.name, "entry", d.get("entry_transport"))
    validate_transport(path.name, "exit", d.get("exit_transport"))

    entry_raw = d["entry_raw_kline"]
    exit_raw = d["exit_raw_kline"]
    if int(entry_raw[0]) != int(entry.timestamp() * 1000):
        fail(f"{path.name}: entry raw kline timestamp mismatch")
    if int(exit_raw[0]) != int(target.timestamp() * 1000):
        fail(f"{path.name}: exit raw kline timestamp mismatch")

    entry_open = float(d["entry_open"])
    exit_open = float(d["exit_open"])
    if not math.isclose(entry_open, float(entry_raw[1]), rel_tol=REL_TOL, abs_tol=ABS_TOL):
        fail(f"{path.name}: entry open mismatch")
    if not math.isclose(exit_open, float(exit_raw[1]), rel_tol=REL_TOL, abs_tol=ABS_TOL):
        fail(f"{path.name}: exit open mismatch")

    ret = 100.0 * (exit_open / entry_open - 1.0)
    if not math.isclose(ret, float(d["simple_return_pct"]), rel_tol=REL_TOL, abs_tol=ABS_TOL):
        fail(f"{path.name}: return mismatch")
    if not math.isclose(abs(ret), float(d["absolute_return_pct"]), rel_tol=REL_TOL, abs_tol=ABS_TOL):
        fail(f"{path.name}: absolute return mismatch")

print(f"PASS: {len(files)} outcome receipts validated")
