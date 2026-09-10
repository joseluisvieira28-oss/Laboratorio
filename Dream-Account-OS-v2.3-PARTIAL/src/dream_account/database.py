from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS market_scans(id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, mode TEXT NOT NULL, status TEXT NOT NULL, regime TEXT, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS candidates(id INTEGER PRIMARY KEY, scan_id INTEGER NOT NULL, symbol TEXT NOT NULL, score REAL NOT NULL, tier TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, FOREIGN KEY(scan_id) REFERENCES market_scans(id));
CREATE TABLE IF NOT EXISTS signals(id TEXT PRIMARY KEY, observed_at TEXT NOT NULL, symbol TEXT NOT NULL, setup TEXT NOT NULL, tier TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS signal_transitions(id INTEGER PRIMARY KEY, signal_id TEXT NOT NULL, from_state TEXT NOT NULL, to_state TEXT NOT NULL, observed_at TEXT NOT NULL, reason TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS paper_trades(id TEXT PRIMARY KEY, signal_id TEXT NOT NULL, state TEXT NOT NULL, entry REAL NOT NULL, stop REAL NOT NULL, tp1 REAL NOT NULL, tp2 REAL NOT NULL, mfe REAL DEFAULT 0, mae REAL DEFAULT 0, realized_r REAL, opened_at TEXT NOT NULL, closed_at TEXT, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS live_approved_trades(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS account_state(id INTEGER PRIMARY KEY CHECK(id=1), balance REAL NOT NULL, peak REAL NOT NULL, drawdown REAL NOT NULL, risk_mode TEXT NOT NULL, consecutive_losses INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS system_events(id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, level TEXT NOT NULL, event_type TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS normalized_snapshots(id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, source TEXT NOT NULL, symbol TEXT NOT NULL, market_type TEXT NOT NULL, data_quality TEXT NOT NULL, payload TEXT NOT NULL);
"""


class Journal:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.executescript(SCHEMA)
        existing = {row[1] for row in self.connection.execute("PRAGMA table_info(paper_trades)")}
        migrations = {"realized_r": "REAL", "opened_at": "TEXT", "closed_at": "TEXT"}
        for column, kind in migrations.items():
            if column not in existing:
                self.connection.execute(f"ALTER TABLE paper_trades ADD COLUMN {column} {kind}")
        self.connection.execute("INSERT OR IGNORE INTO account_state VALUES(1,56,56,0,'NORMAL',0)")
        self.connection.commit()

    def record_scan(self, observed_at: str, mode: str, status: str, regime: str | None, payload: dict[str, Any]) -> int:
        cur = self.connection.execute("INSERT INTO market_scans(observed_at,mode,status,regime,payload) VALUES(?,?,?,?,?)", (observed_at, mode, status, regime, json.dumps(payload, sort_keys=True)))
        self.connection.commit()
        return int(cur.lastrowid)

    def record_candidate(self, scan_id: int, candidate: dict[str, Any]) -> None:
        self.connection.execute("INSERT INTO candidates(scan_id,symbol,score,tier,status,payload) VALUES(?,?,?,?,?,?)", (scan_id, candidate["symbol"], candidate["score"], candidate["tier"], candidate["status"], json.dumps(candidate, sort_keys=True)))
        self.connection.commit()

    def event(self, observed_at: str, level: str, event_type: str, detail: str) -> None:
        self.connection.execute("INSERT INTO system_events(observed_at,level,event_type,detail) VALUES(?,?,?,?)", (observed_at, level, event_type, detail))
        self.connection.commit()

    @staticmethod
    def _snapshot_row(snapshot: Any) -> tuple[Any, ...]:
        payload = snapshot.as_dict()
        return (
            snapshot.timestamp_utc,
            snapshot.source,
            snapshot.symbol,
            snapshot.market_type,
            snapshot.data_quality.value,
            json.dumps(payload, sort_keys=True, default=str),
        )

    def record_snapshot(self, snapshot: Any) -> None:
        """Compatibility path for one snapshot; production runtime uses record_snapshots."""
        self.connection.execute(
            "INSERT INTO normalized_snapshots(observed_at,source,symbol,market_type,data_quality,payload) VALUES(?,?,?,?,?,?)",
            self._snapshot_row(snapshot),
        )
        self.connection.commit()

    def record_snapshots(self, snapshots: Iterable[Any]) -> int:
        """Persist one market scan as a single SQLite transaction.

        This changes persistence efficiency only. It does not alter the normalized
        snapshot contract or any strategy/scoring input.
        """
        rows = [self._snapshot_row(snapshot) for snapshot in snapshots]
        if not rows:
            return 0
        with self.connection:
            self.connection.executemany(
                "INSERT INTO normalized_snapshots(observed_at,source,symbol,market_type,data_quality,payload) VALUES(?,?,?,?,?,?)",
                rows,
            )
        return len(rows)

    def snapshot_storage_stats(self) -> dict[str, int]:
        row = self.connection.execute(
            "SELECT COUNT(*), COALESCE(MIN(id),0), COALESCE(MAX(id),0) FROM normalized_snapshots"
        ).fetchone()
        page_size = int(self.connection.execute("PRAGMA page_size").fetchone()[0])
        page_count = int(self.connection.execute("PRAGMA page_count").fetchone()[0])
        freelist_count = int(self.connection.execute("PRAGMA freelist_count").fetchone()[0])
        return {
            "rows": int(row[0]),
            "min_id": int(row[1]),
            "max_id": int(row[2]),
            "page_size": page_size,
            "page_count": page_count,
            "freelist_count": freelist_count,
            "database_bytes": page_size * page_count,
            "reusable_bytes": page_size * freelist_count,
        }

    def prune_normalized_snapshots(self, max_rows: int) -> dict[str, int]:
        """Bound operational raw snapshots while keeping the newest row IDs.

        SQLite freed pages are intentionally left on the freelist for reuse. This
        routine never VACUUMs the live database.
        """
        if max_rows < 1:
            raise ValueError("max_rows must be >= 1")
        before = self.snapshot_storage_stats()
        if before["rows"] <= max_rows:
            return {**before, "deleted_rows": 0, "max_rows": max_rows}
        cutoff_id = before["max_id"] - max_rows
        with self.connection:
            cursor = self.connection.execute(
                "DELETE FROM normalized_snapshots WHERE id <= ?", (cutoff_id,)
            )
        after = self.snapshot_storage_stats()
        return {
            **after,
            "deleted_rows": int(cursor.rowcount if cursor.rowcount >= 0 else before["rows"] - after["rows"]),
            "max_rows": max_rows,
        }

    def counts(self) -> dict[str, int]:
        tables = ["market_scans", "candidates", "signals", "paper_trades"]
        return {table: self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}

    def record_signal(self, signal_id: str, observed_at: str, symbol: str, setup: str, tier: str, payload: dict[str, Any]) -> None:
        self.connection.execute("INSERT INTO signals(id,observed_at,symbol,setup,tier,payload) VALUES(?,?,?,?,?,?)", (signal_id, observed_at, symbol, setup, tier, json.dumps(payload, sort_keys=True)))
        self.connection.commit()

    def record_transition(self, signal_id: str, transition: dict[str, Any]) -> None:
        self.connection.execute("INSERT INTO signal_transitions(signal_id,from_state,to_state,observed_at,reason) VALUES(?,?,?,?,?)", (signal_id, transition["from"], transition["to"], transition["timestamp"], transition["reason"]))
        self.connection.commit()

    def save_paper_trade(self, trade_id: str, trade: Any, state: str) -> None:
        payload = json.dumps(trade.__dict__, sort_keys=True)
        self.connection.execute(
            "INSERT INTO paper_trades(id,signal_id,state,entry,stop,tp1,tp2,mfe,mae,realized_r,opened_at,closed_at,payload) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state,mfe=excluded.mfe,mae=excluded.mae,realized_r=excluded.realized_r,closed_at=excluded.closed_at,payload=excluded.payload",
            (trade_id, trade.signal_id, state, trade.entry_price, trade.stop, trade.tp1, trade.tp2, trade.mfe, trade.mae, trade.realized_r, trade.entry_timestamp, trade.exit_timestamp, payload),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
