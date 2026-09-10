from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

MAX_OPERATIONAL_SNAPSHOTS = 500_000
SNAPSHOT_TABLE = "normalized_snapshots"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integrity(connection: sqlite3.Connection) -> list[str]:
    return [row[0] for row in connection.execute("PRAGMA integrity_check").fetchall()]


def table_names(connection: sqlite3.Connection) -> list[str]:
    return [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]


def table_count(connection: sqlite3.Connection, table: str) -> int:
    safe = table.replace('"', '""')
    return int(connection.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a validated compact Dream Account OS SQLite candidate copy.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--max-snapshots", type=int, default=MAX_OPERATIONAL_SNAPSHOTS)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if args.max_snapshots < 1:
        raise SystemExit("--max-snapshots must be >= 1")
    if not args.source.is_file():
        raise SystemExit("source database does not exist")
    if args.destination.exists():
        raise SystemExit("destination already exists; refusing to overwrite")
    args.destination.parent.mkdir(parents=True, exist_ok=True)

    source_hash = sha256(args.source)
    source = sqlite3.connect(f"file:{args.source.resolve().as_posix()}?mode=ro", uri=True)
    source.execute("PRAGMA query_only=ON")
    source_integrity = integrity(source)
    if source_integrity != ["ok"]:
        source.close()
        raise SystemExit(f"source integrity failed: {source_integrity}")

    source_tables = table_names(source)
    source_counts = {name: table_count(source, name) for name in source_tables}
    snapshot_source_count = source_counts.get(SNAPSHOT_TABLE, 0)
    keep = min(snapshot_source_count, args.max_snapshots)
    cutoff = 0
    if snapshot_source_count and keep:
        max_id = int(source.execute(f"SELECT MAX(id) FROM {SNAPSHOT_TABLE}").fetchone()[0])
        cutoff = max_id - keep

    # SQLite backup produces an independent candidate; the source remains read-only.
    destination = sqlite3.connect(args.destination)
    source.backup(destination)
    source.close()

    with destination:
        if snapshot_source_count > keep:
            destination.execute(f"DELETE FROM {SNAPSHOT_TABLE} WHERE id <= ?", (cutoff,))
    destination.execute("VACUUM")
    destination_integrity = integrity(destination)
    destination_counts = {name: table_count(destination, name) for name in source_tables}

    mismatches = {
        table: {"source": source_counts[table], "candidate": destination_counts[table]}
        for table in source_tables
        if table != SNAPSHOT_TABLE and source_counts[table] != destination_counts[table]
    }
    snapshot_ids = destination.execute(
        f"SELECT COALESCE(MIN(id),0), COALESCE(MAX(id),0), COUNT(*) FROM {SNAPSHOT_TABLE}"
    ).fetchone() if SNAPSHOT_TABLE in source_tables else (0, 0, 0)
    destination.close()

    destination_hash = sha256(args.destination)
    report = {
        "status": "PASS" if destination_integrity == ["ok"] and not mismatches and snapshot_ids[2] == keep else "FAIL",
        "source": str(args.source),
        "source_size_bytes": args.source.stat().st_size,
        "source_sha256": source_hash,
        "source_integrity_check": source_integrity,
        "destination": str(args.destination),
        "destination_size_bytes": args.destination.stat().st_size,
        "destination_sha256": destination_hash,
        "destination_integrity_check": destination_integrity,
        "max_snapshots": args.max_snapshots,
        "source_snapshot_rows": snapshot_source_count,
        "candidate_snapshot_rows": int(snapshot_ids[2]),
        "candidate_snapshot_min_id": int(snapshot_ids[0]),
        "candidate_snapshot_max_id": int(snapshot_ids[1]),
        "non_snapshot_count_mismatches": mismatches,
        "source_table_counts": source_counts,
        "candidate_table_counts": destination_counts,
        "production_replacement_performed": False,
    }
    output = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
