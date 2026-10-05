#!/usr/bin/env python3
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBS_DIR = ROOT / "observations"
ALLOWED = {"BTC", "ETH", "SOL"}
TOL_SECONDS = 1.5
REL_TOL = 1e-9
ABS_TOL = 1e-4

def parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"naive timestamp: {s}")
    return dt.astimezone(timezone.utc)

def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=REL_TOL, abs_tol=ABS_TOL)

def fail(msg):
    raise SystemExit(f"FAIL: {msg}")

files = sorted(OBS_DIR.glob("*.json"))
if not files:
    fail("no observation receipts")

seen_ids = set()
previous = {}
cadence_deltas = {s: [] for s in sorted(ALLOWED)}
rows = 0

for path in files:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("experiment") != "LIQUID_COINVEST_FORWARD_V0.1":
        fail(f"{path.name}: wrong experiment")
    if payload.get("phase") != "SOURCE_CADENCE_CALIBRATION":
        fail(f"{path.name}: unexpected phase")
    if payload.get("outcome_opened") is not False:
        fail(f"{path.name}: outcome must remain unopened during cadence calibration")

    observed_at = parse_iso(payload["observed_at_utc"])

    obs_rows = payload.get("observations") or []
    symbols = [x.get("symbol") for x in obs_rows]
    if set(symbols) != ALLOWED or len(symbols) != 3:
        fail(f"{path.name}: expected exactly BTC/ETH/SOL")

    for row in obs_rows:
        rows += 1
        oid = row["observation_id"]
        if oid in seen_ids:
            fail(f"duplicate observation_id {oid}")
        seen_ids.add(oid)

        symbol = row["symbol"]
        if symbol not in ALLOWED:
            fail(f"{path.name}: symbol {symbol} outside frozen universe")

        source_at = parse_iso(row["source_created_at_utc"])
        if source_at > observed_at:
            fail(f"{oid}: source timestamp is after observation timestamp")

        calculated_age = (observed_at - source_at).total_seconds()
        if abs(calculated_age - float(row["source_age_seconds"])) > TOL_SECONDS:
            fail(f"{oid}: source_age_seconds mismatch")

        tiers = row.get("tiers") or []
        if len(tiers) != 10:
            fail(f"{oid}: expected 10 size tiers")

        total_pos = sum(float(t["total_position_value"]) for t in tiers)
        total_long = sum(float(t["total_position_value_long"]) for t in tiers)
        total_liq = sum(float(t["value_close_to_liquidation"]) for t in tiers)
        whales = [t for t in tiers if t.get("min") is not None and float(t["min"]) >= 250000]
        whale_total = sum(float(t["total_position_value"]) for t in whales)
        whale_long = sum(float(t["total_position_value_long"]) for t in whales)
        whale_liq = sum(float(t["value_close_to_liquidation"]) for t in whales)
        whale_share = whale_long / whale_total if whale_total else 0.0

        checks = {
            "total_positioning_usd": total_pos,
            "liq_near_total_usd": total_liq,
            "whale_total_position_value_usd": whale_total,
            "whale_long_position_value_usd": whale_long,
            "whale_liq_near_usd": whale_liq,
            "whale_long_share": whale_share,
        }
        for key, expected in checks.items():
            if not close(row[key], expected):
                fail(f"{oid}: derived field {key} inconsistent")

        sm = row.get("smart_money_long_pct")
        lc = row.get("losing_crowd_long_pct")
        div = row.get("cohort_divergence_pp")
        if sm is not None and lc is not None:
            if not close(div, float(sm) - float(lc)):
                fail(f"{oid}: cohort divergence inconsistent")

        prev = previous.get(symbol)
        tag = row.get("cadence_tag") or row.get("freshness_tag")
        if prev is not None:
            prev_source, prev_fingerprint = prev
            fingerprint = json.dumps(tiers, sort_keys=True, separators=(",", ":"))
            if source_at == prev_source and fingerprint == prev_fingerprint:
                if tag not in {"DUPLICATE_SOURCE_SNAPSHOT", "FRESHNESS_UNKNOWN"}:
                    fail(f"{oid}: unchanged source must be tagged duplicate/unknown")
            elif source_at > prev_source:
                cadence_deltas[symbol].append((source_at - prev_source).total_seconds())
                if tag not in {"ADVANCED_SOURCE_SNAPSHOT", "FRESHNESS_UNKNOWN"}:
                    fail(f"{oid}: advanced source must be tagged advanced/unknown")
            elif source_at < prev_source:
                fail(f"{oid}: source timestamp regressed")
        fingerprint = json.dumps(tiers, sort_keys=True, separators=(",", ":"))
        previous[symbol] = (source_at, fingerprint)

print(f"PASS: {len(files)} receipt files, {rows} observations, {len(seen_ids)} unique IDs")
for symbol in sorted(ALLOWED):
    ds = cadence_deltas[symbol]
    if ds:
        mins = ", ".join(f"{d/60:.3f}m" for d in ds)
        print(f"{symbol} observed source-advance intervals: {mins}")
    else:
        print(f"{symbol} observed source-advance intervals: none yet")
print("No outcomes were opened by this validator.")
