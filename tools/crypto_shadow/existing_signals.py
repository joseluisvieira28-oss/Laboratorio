"""Read-only, local-only inventory of recent CONVEX signal receipts from 10 lanes.

This CLI makes zero network calls, does not require credentials, does not mutate
SQLite, Windows tasks, or exchanges, and never reads Telegram message text.
Output is sanitized IDs/timestamps/receipt status only. Intended for independent
audit, NOT a trading execution tool.
"""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote

LANES = {
    "V07": {
        "SOL_CONVEX_NATIVE_5M": "SOL_USDT",
        "SOL_CONVEX_1H": "SOL_USDT",
        "BNB_CONVEX_4H": "BNB_USDT",
    },
    "V11": {
        "SOL_CONVEX_4H_EXPERIMENTAL": "SOL_USDT",
        "BNB_CONVEX_30M_EXPERIMENTAL": "BNB_USDT",
        "ETH_CONVEX_1H_EXPERIMENTAL": "ETH_USDT",
    },
    "V12": {
        "BNB_CONVEX_NATIVE_5M_EXPERIMENTAL": "BNB_USDT",
        "SOL_CONVEX_30M_EXPERIMENTAL": "SOL_USDT",
        "BNB_CONVEX_15M_EXPERIMENTAL": "BNB_USDT",
        "DOGE_CONVEX_4H_EXPERIMENTAL": "DOGE_USDT",
    }
}
DBS = {
    "V07": ("ThreeConvexV07", "v07_events.sqlite3"),
    "V11": ("ThreeConvexV11", "V11_OUTBOX.sqlite3"),
    "V12": ("ThreeConvexV12", "V12_ONLY.sqlite3"),
}

def as_utc(value):
    if type(value) is int and 1_500_000_000_000 <= value < 2_100_000_000_000:
        return datetime.fromtimestamp(value / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return None

def parse_id(raw, version):
    ident = raw.removeprefix("SIGNAL:") if version == "V07" else raw
    if not isinstance(ident, str) or ":" not in ident:
        return None
    lane, timestamp = ident.rsplit(":", 1)
    try:
        close = int(timestamp)
    except ValueError:
        return None
    if ident != f"{lane}:{close}" or lane not in LANES[version] or close % 300_000:
        return None
    return lane, close

def read_one(local: Path, version: str, limit: int) -> dict:
    folder, filename = DBS[version]
    path = local / "CryptoLab" / folder / "data" / filename
    if not path.is_file():
        return {"source": version, "status": "SQLITE_NOT_FOUND", "events": []}
    # Normal SQLite URI mode=ro preserves visibility of existing WAL commits.
    # No immutable flag, because it could silently hide uncheckpointed rows.
    uri = "file:" + quote(str(path.resolve()).replace("\\", "/"), safe="/:") + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=2)) as db:
            if version == "V07":
                sql = ("SELECT id, sent_at_ms, telegram_message_id, added_ms FROM outbox "
                       "WHERE id LIKE 'SIGNAL:%' ORDER BY added_ms DESC, id DESC LIMIT ?")
            elif version == "V11":
                sql = ("SELECT id, sent_ms, telegram_message_id, NULL FROM notices "
                       "ORDER BY ROWID DESC LIMIT ?")
            else:
                sql = ("SELECT id, sent_ms, NULL, expired_ms FROM notices "
                       "ORDER BY close_ms DESC, id DESC LIMIT ?")
            rows = db.execute(sql, (limit,)).fetchall()
    except (sqlite3.Error, OSError) as exc:
        return {"source": version, "status": "SQLITE_READ_BLOCKED",
                "error_type": type(exc).__name__, "events": []}
    output = []
    malformed = 0
    for raw_id, sent, ack, extra in rows:
        parsed = parse_id(raw_id, version)
        if not parsed:
            malformed += 1
            continue
        lane, close = parsed
        output.append({
            "version": version,
            "symbol": LANES[version][lane],
            "lane": lane,
            "signal_id": raw_id.removeprefix("SIGNAL:") if version == "V07" else raw_id,
            "signal_close_utc": as_utc(close),
            "outbox_marked_sent": type(sent) is int,
            "sent_at_utc": as_utc(sent),
            "api_message_id_persisted": type(ack) is int and ack > 0,
            "telegram_message_id": ack if type(ack) is int and ack > 0 else None,
            "expired_without_send": (type(extra) is int and type(sent) is not int) if version == "V12" else None,
        })
    output.sort(key=lambda x: x["signal_close_utc"] or "", reverse=True)
    return {
        "source": version,
        "status": "READONLY_QUERY_OK",
        "rows_examined": len(rows),
        "unrecognized_rows_ignored": malformed,
        "events": output,
    }

def assess(local: Path, limit: int) -> dict:
    monitors = {v: read_one(local, v, limit) for v in DBS}
    events = sorted((e for a in monitors.values() for e in a["events"]),
                    key=lambda e: (e["signal_close_utc"] or "", e["signal_id"]), reverse=True)
    by_close_symbol = {}
    for e in events:
        key = (e["symbol"], e["signal_close_utc"])
        by_close_symbol.setdefault(key, []).append(e["lane"])
    overlaps = [
        {"symbol": symbol, "close_utc": close, "lanes": sorted(lanes)}
        for (symbol, close), lanes in by_close_symbol.items() if len(set(lanes)) > 1
    ]
    return {
        "audit": "CONVEX_10_LANES_RECENT_SIGNAL_RECEIPTS_V01",
        "local_only": True,
        "sqlite_mode": "ro",
        "network_access": False,
        "exchange_orders": False,
        "telegram_messages_sent": False,
        "monitors": {k: {a: b for a, b in value.items() if a != "events"}
                     for k, value in monitors.items()},
        "events": events,
        "potential_same_symbol_same_close_overlaps": overlaps,
        "limitations": [
            "Outbox rows do not prove Binance source correctness or entry fill",
            "V12 does not persist Telegram API message_id",
            "Missing events may reflect non-detection or expired source; coverage evidence is separate",
            "No MEXC fill, verified hosted stop, take profit, or economic profitability claim",
        ]
    }

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--localappdata", type=Path, default=os.environ.get("LOCALAPPDATA"))
    p.add_argument("--limit", type=int, default=30, help="max rows per observer, 1-100")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        assert sum(len(x) for x in LANES.values()) == 10
        assert as_utc(1792097700000) == "2026-10-15T20:55:00Z"
        assert parse_id("SIGNAL:SOL_CONVEX_NATIVE_5M:1792097700000", "V07")
        assert parse_id("BNB_CONVEX_NATIVE_5M_EXPERIMENTAL:1792097700000", "V12")
        print('{"result":"RECENT_SIGNALS_OFFLINE_SELFTEST_PASS"}')
        return 0
    if a.localappdata is None:
        p.error("LOCALAPPDATA missing")
    if a.limit < 1 or a.limit > 100:
        p.error("--limit must be between 1 and 100")
    print(json.dumps(assess(a.localappdata, a.limit), indent=2, sort_keys=True, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
