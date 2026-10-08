"""Read-only forensic receipt audit, not a strategy, execution engine, or promotion gate.

The input is a JSON array of rows from the SELECT-only SQL in the V1 closeout.
Required per row:
  event_key, symbol, entry_ms, exit_ms (nullable), receipt_ts_utc
This module never connects to an exchange, storage, or a trading account.
"""
from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict
from typing import Any


def _receipt_millis(ts: str) -> int:
    if not isinstance(ts, str) or not ts:
        raise ValueError("missing source receipt timestamp")
    value = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("receipt timestamp must be timezone aware")
    return int(value.astimezone(timezone.utc).timestamp() * 1000)


def audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fail closed on overlap or receipt after historical simulated entry.

    Overlap is judged using prior-entry signals on the same symbol and the prior
    entry's *recorded exit*. A missing recorded exit remains OPEN. This audit
    does NOT delete, reconstruct, credit, retune, or relabel past science.
    """
    seen_keys: set[str] = set()
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key, symbol, entry = row.get("event_key"), row.get("symbol"), row.get("entry_ms")
        if not isinstance(key, str) or not key or not isinstance(symbol, str) or not symbol:
            raise ValueError("missing event key/symbol")
        if key in seen_keys:
            raise ValueError("duplicate event key")
        seen_keys.add(key)
        if not isinstance(entry, int) or entry <= 0:
            raise ValueError("missing/invalid entry_ms")
        exit_ms = row.get("exit_ms")
        if exit_ms is not None and (not isinstance(exit_ms, int) or exit_ms < entry):
            raise ValueError("invalid exit timestamp")
        receipt_ms = _receipt_millis(row.get("receipt_ts_utc"))
        by_symbol[symbol].append({**row, "receipt_ms": receipt_ms})

    violations: list[dict[str, Any]] = []
    lagged: list[dict[str, Any]] = []
    clean_resolved = 0
    clean_unresolved = 0
    for symbol, entries in sorted(by_symbol.items()):
        entries.sort(key=lambda x: x["entry_ms"])
        prior: list[dict[str, Any]] = []
        for row in entries:
            competing = [
                p["event_key"] for p in prior
                if p["exit_ms"] is None or p["exit_ms"] > row["entry_ms"]
            ]
            overlapping = bool(competing)
            if overlapping:
                violations.append({
                    "event_key": row["event_key"],
                    "symbol": symbol,
                    "prior_open_keys": competing,
                })
            if row["receipt_ms"] > row["entry_ms"]:
                lagged.append({
                    "event_key": row["event_key"],
                    "receipt_delay_ms": row["receipt_ms"] - row["entry_ms"],
                })
            if not overlapping:
                if row["exit_ms"] is None:
                    clean_unresolved += 1
                else:
                    clean_resolved += 1
            prior.append(row)

    raw_resolved = sum(row.get("exit_ms") is not None for row in rows)
    invalid = bool(violations or lagged)
    return {
        "classification": "EXECUTION_INTEGRITY_FAIL" if invalid else "REQUIRES_SEPARATE_ECONOMIC_ADJUDICATION",
        "read_only": True,
        "total_signal_receipts": len(rows),
        "raw_resolved": raw_resolved,
        "raw_unresolved": len(rows) - raw_resolved,
        "overlap_violation_count": len(violations),
        "overlap_violations": violations,
        "retroactive_entry_receipt_count": len(lagged),
        "retroactive_entry_receipts": lagged,
        "nonoverlap_resolved_descriptive_only": clean_resolved,
        "nonoverlap_unresolved_descriptive_only": clean_unresolved,
        "live_trading_authorized": False,
        "economic_promotion_authorized": False,
    }


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Audit an exported TFG forward receipt JOIN (JSON array).")
    parser.add_argument("read_only_json_export", type=Path)
    args = parser.parse_args()
    source = json.loads(args.read_only_json_export.read_text(encoding="utf-8"))
    if not isinstance(source, list):
        raise SystemExit("Expected JSON array")
    print(json.dumps(audit_rows(source), indent=2, sort_keys=True))
