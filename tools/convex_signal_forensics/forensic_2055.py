"""Offline, read-only forensic examination of two operator-observed 2026-10-15 CONVEX alerts.

No network, broker, Telegram, credentials, order methods, or data mutation.
Outputs only sanitized booleans, counts, SHA256, UTC timestamps and one Telegram message ID.
The pinned V5 engine is replayed against independent V07/V12 LOCAL candle caches:
not proof of external Binance archive parity or trading profitability.
"""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote

from engine.three_convex_v05.signals import (
    Bar, MS5, aggregate_complete, parent_signal_function, Halt,
)
from engine.three_convex_v07.feed import LOOKBACK as LOOKBACK_V07
from engine.three_convex_v12.public_feed import LOOKBACK as LOOKBACK_V12

CLOSE_MS = 1792097700000
EXPECTED_UTC = "2026-10-15T20:55:00+00:00"
assert LOOKBACK_V07 == LOOKBACK_V12 == 48 * 260 + 96
LOOKBACK = LOOKBACK_V07
EVENTS = {
    "V07_SOL_5M": {
        "lane": "SOL_CONVEX_NATIVE_5M",
        "symbol": "SOL_USDT",
        "sqlite": "v07_events.sqlite3",
        "table": "outbox",
        "row_id": "SIGNAL:SOL_CONVEX_NATIVE_5M:1792097700000",
    },
    "V12_BNB_5M": {
        "lane": "BNB_CONVEX_NATIVE_5M_EXPERIMENTAL",
        "symbol": "BNB_USDT",
        "sqlite": "V12_ONLY.sqlite3",
        "table": "notices",
        "row_id": "BNB_CONVEX_NATIVE_5M_EXPERIMENTAL:1792097700000",
    },
}
ROOTS = {"V07": "ThreeConvexV07", "V12": "ThreeConvexV12"}
SUFFIXES = {"V07": "_binance_5m.json", "V12": "_v12_5m.json"}

def utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()

def parse_cache(path: Path, symbol: str) -> tuple[dict[int, tuple], str]:
    raw = path.read_bytes()
    if len(raw) > 4_000_000:
        raise ValueError("PUBLIC_CACHE_EXCESSIVE_BYTES")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("symbol") != symbol or payload.get("source") != "BINANCE_USDM_5M_PUBLIC":
        raise ValueError("PUBLIC_CACHE_IDENTITY_INVALID")
    items = payload.get("bars")
    if not isinstance(items, list) or len(items) > LOOKBACK:
        raise ValueError("PUBLIC_CACHE_LENGTH_INVALID")
    out = {}
    prior = None
    for row in items:
        if not isinstance(row, list) or len(row) != 6 or type(row[0]) is not int:
            raise ValueError("PUBLIC_CACHE_ROW_SHAPE_INVALID")
        t = row[0]
        if prior is not None and t != prior + MS5:
            raise ValueError("PUBLIC_CACHE_GAP_OR_DUPLICATE")
        bar = Bar(*row).validate()
        out[t] = (t, bar.open, bar.high, bar.low, bar.close, bar.volume)
        prior = t
    return out, hashlib.sha256(raw).hexdigest()

def cache_paths(local: Path, version: str, symbol: str) -> list[Path]:
    root = local / "CryptoLab"
    active = root / ROOTS[version] / "data" / "market_cache" / (symbol + SUFFIXES[version])
    matches = []
    backups = root / "CONVEX10_BACKUPS" / version
    if backups.is_dir():
        for d in sorted(backups.iterdir()):
            if d.is_dir() and (d / "UPGRADE_RECEIPT.json").is_file():
                f = d / "data" / "market_cache" / (symbol + SUFFIXES[version])
                if f.is_file():
                    matches.append(f)
    if active.is_file():
        matches.append(active)
    return matches

def reconstruct(local: Path, version: str, symbol: str) -> dict:
    files = cache_paths(local, version, symbol)
    union = {}
    mismatches = 0
    evidence = []
    for path in files:
        source, original_digest = parse_cache(path, symbol)
        disagreements = [t for t, row in source.items() if t in union and union[t] != row]
        mismatches += len(disagreements)
        # Never silently accept a changed historical candle, or overwrite with a newer cache.
        for t, row in source.items():
            union.setdefault(t, row)
        evidence.append({"kind": "active" if ROOTS[version] in str(path) else "cutover_backup",
                         "sha256": original_digest, "bar_count": len(source)})
    last_open = CLOSE_MS - MS5
    first_open = last_open - (LOOKBACK - 1) * MS5
    window = [union.get(t) for t in range(first_open, last_open + MS5, MS5)]
    complete = all(row is not None for row in window) and len(window) == LOOKBACK
    digest = hashlib.sha256(json.dumps(window, separators=(",", ":"), allow_nan=False).encode()).hexdigest() if complete else None
    return {
        "source": version,
        "symbol": symbol,
        "cache_files": evidence,
        "overlap_conflicts": mismatches,
        "rows_available_in_target_window": sum(row is not None for row in window),
        "required_rows": LOOKBACK,
        "exact_window_reconstructed": complete,
        "window_sha256": digest,
        "_window": window if complete and not mismatches else None,
    }


def cross_observer_diff(a: list | None, b: list | None) -> dict:
    """Compare two full local windows; never disclose OHLC or outcome prices."""
    if a is None or b is None or len(a) != len(b):
        return {"comparable": False, "reason": "INCOMPLETE_OR_CONFLICTED_LOCAL_WINDOW"}
    fields = {key: 0 for key in ("open", "high", "low", "close", "volume")}
    first = last = None
    count = last20 = last200 = 0
    mismatch_times = []
    close_relative_bps_max = 0.0
    volume_relative_pct_max = 0.0
    for i, (left, right) in enumerate(zip(a, b)):
        if left[0] != right[0]:
            return {"comparable": False, "reason": "CANDLE_TIMESTAMPS_NOT_ALIGNED"}
        if left == right:
            continue
        count += 1
        if first is None:
            first = left[0]
        last = left[0]
        # A bounded set of timestamps is enough for the forensic follow-up.
        if len(mismatch_times) < 12:
            mismatch_times.append(utc(left[0]))
        if i >= len(a) - 20:
            last20 += 1
        if i >= len(a) - 200:
            last200 += 1
        for j, field in enumerate(fields, 1):
            if left[j] != right[j]:
                fields[field] += 1
        if left[4] != right[4]:
            denom = max(abs(left[4]), abs(right[4]), 1e-12)
            close_relative_bps_max = max(
                close_relative_bps_max, 10000 * abs(left[4] - right[4]) / denom)
        if left[5] != right[5]:
            denom = max(abs(left[5]), abs(right[5]), 1e-12)
            volume_relative_pct_max = max(
                volume_relative_pct_max, 100 * abs(left[5] - right[5]) / denom)
    return {
        "comparable": True,
        "total_rows_compared": len(a),
        "mismatched_candles": count,
        "mismatched_open_times_utc_first_12": mismatch_times,
        "mismatched_times_truncated": count > len(mismatch_times),
        "first_mismatch_open_utc": utc(first) if first is not None else None,
        "last_mismatch_open_utc": utc(last) if last is not None else None,
        "recent_last_20_candles_mismatched": last20,
        "recent_last_200_candles_mismatched": last200,
        "signal_candle_2050_exact_match": a[-1] == b[-1],
        "field_mismatch_counts": fields,
        "max_close_relative_difference_bps": round(close_relative_bps_max, 8),
        "max_volume_relative_difference_pct": round(volume_relative_pct_max, 8),
        "prices_disclosed": False,
    }


def v5_decision(window: list | None) -> tuple[bool | None, str | None, dict | None]:
    """Replay the unchanged pinned parent V5 and report only decision features."""
    if window is None:
        return None, None, None
    try:
        bars = [Bar(*row) for row in window]
        fn = parent_signal_function()
        values = aggregate_complete(bars, 1)
        decisions, details = fn(values)
        features = details[-1] if details and isinstance(details[-1], dict) else {}
        allow = ("score", "regime", "rsi_flag", "z_flag", "bb_flag", "vol_flag")
        safe_features = {
            k: features.get(k) if isinstance(features.get(k), (bool, int)) else None
            for k in allow
        }
        return bool(decisions[-1]), None, safe_features
    except (Halt, ValueError, TypeError, OSError, IndexError) as exc:
        return None, type(exc).__name__, None


def outbox_receipt(local: Path, version: str, event: dict) -> dict:
    dbpath = local / "CryptoLab" / ROOTS[version] / "data" / event["sqlite"]
    if not dbpath.is_file():
        return {"found": False, "reason": "SQLITE_FILE_MISSING"}
    # mode=ro: no SQL writes, no SQLite schema changes, no checkpoint.
    uri = "file:" + quote(str(dbpath.resolve()).replace("\\", "/"), safe="/:") + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=2)) as db:
            if version == "V07":
                row = db.execute(
                    "SELECT id, sent_at_ms, telegram_message_id, added_ms, message FROM outbox WHERE id=?",
                    (event["row_id"],),
                ).fetchone()
                if row is None:
                    return {"found": False, "reason": "EVENT_NOT_IN_OUTBOX"}
                rid, sent, message_id, added, msg = row
                return {
                    "found": True,
                    "db_marked_sent": type(sent) is int,
                    "added_at_utc": utc(added) if type(added) is int else None,
                    "sent_at_utc": utc(sent) if type(sent) is int else None,
                    "telegram_message_id": message_id if type(message_id) is int and message_id > 0 else None,
                    "message_binds_signal_and_symbol": event["row_id"][7:] in msg and event["symbol"] in msg,
                }
            row = db.execute(
                "SELECT id, sent_ms, close_ms, expired_ms, message FROM notices WHERE id=?",
                (event["row_id"],),
            ).fetchone()
            if row is None:
                return {"found": False, "reason": "EVENT_NOT_IN_OUTBOX"}
            rid, sent, close, expired, msg = row
            return {
                "found": True,
                "db_marked_sent": type(sent) is int,
                "db_marked_expired": type(expired) is int,
                "close_matches_image": close == CLOSE_MS,
                "sent_at_utc": utc(sent) if type(sent) is int else None,
                "telegram_message_id": None,
                "telegram_message_id_not_persisted_by_v12": True,
                "message_binds_signal_and_symbol": rid in msg and event["symbol"] in msg,
            }
    except (sqlite3.Error, OSError) as exc:
        return {"found": False, "reason": "READONLY_SQLITE_INACCESSIBLE", "error_type": type(exc).__name__}

def check_one(local: Path, name: str, event: dict, all_caches: dict) -> dict:
    actual = "V07" if name.startswith("V07") else "V12"
    other = "V12" if actual == "V07" else "V07"
    symbol = event["symbol"]
    data = all_caches[(actual, symbol)]
    independent = all_caches[(other, symbol)]
    parity = (data["window_sha256"] == independent["window_sha256"]
              if data["_window"] is not None and independent["_window"] is not None else None)
    comparison = cross_observer_diff(data["_window"], independent["_window"])
    flags, engine_error, primary_features = v5_decision(data["_window"])
    independent_flags, independent_error, other_features = v5_decision(independent["_window"])
    receipt = outbox_receipt(local, actual, event)
    return {
        "signal_id": event["row_id"][7:] if actual == "V07" else event["row_id"],
        "close_utc": EXPECTED_UTC,
        "source_window": {k: v for k, v in data.items() if k != "_window"},
        "independent_other_observer": {
            "version": other,
            "full_source_parity_at_exact_close": parity,
            "window_sha256": independent["window_sha256"],
            "internal_cache_conflicts": independent["overlap_conflicts"],
            "pinned_v5_replay_five_minute_signal": independent_flags,
            "pinned_v5_replay_error": independent_error,
            "pinned_v5_signal_features": other_features,
        },
        "cross_observer_diagnostic": comparison,
        "pinned_v5_replay_five_minute_signal": flags,
        "pinned_v5_replay_error": engine_error,
        "pinned_v5_signal_features": primary_features,
        "sqlite": receipt,
        "verdict": (
            "LOCAL_CAUSAL_REPLAY_PASS_NOT_EXTERNAL_MARKET_PARITY"
            if flags is True and parity is True and receipt.get("found") and receipt.get("db_marked_sent")
               and receipt.get("message_binds_signal_and_symbol")
            else "NOT_YET_PROVEN_CHECK_REPLAY_OR_RECEIPT"
        ),
    }

def assess(local: Path) -> dict:
    sources = {}
    for symbol in ("SOL_USDT", "BNB_USDT"):
        for version in ROOTS:
            try:
                sources[(version, symbol)] = reconstruct(local, version, symbol)
            except (OSError, ValueError, TypeError, Halt) as exc:
                sources[(version, symbol)] = {
                    "source": version, "symbol": symbol,
                    "cache_files": [], "overlap_conflicts": 0,
                    "rows_available_in_target_window": 0, "required_rows": LOOKBACK,
                    "exact_window_reconstructed": False, "window_sha256": None,
                    "_window": None, "reconstruction_error": type(exc).__name__
                }
    return {
        "protocol": "CONVEX_2055_TWO_SIGNALS_OFFLINE_READONLY_V03",
        "forensic_timestamp_utc": EXPECTED_UTC,
        "market_api_access": False,
        "telegram_api_access": False,
        "exchange_api_access": False,
        "writes_to_original_sqlite": False,
        "guarantees_external_market_parity": False,
        "event_results": {name: check_one(local, name, ev, sources) for name, ev in EVENTS.items()},
        "interpretation": "Replay on local cache and SQLite only. Source cache authenticity, image provenance and economic edge still require separate proof.",
    }

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--localappdata", type=Path, default=os.environ.get("LOCALAPPDATA"))
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        assert utc(CLOSE_MS) == EXPECTED_UTC
        assert all(e["row_id"].endswith(str(CLOSE_MS)) for e in EVENTS.values())
        assert LOOKBACK == 12576
        fn = parent_signal_function()
        assert callable(fn)
        print(json.dumps({"self_test": "PASS", "network": False, "trading": False}))
        return 0
    if not a.localappdata:
        p.error("LOCALAPPDATA is required")
    result = assess(Path(a.localappdata))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
