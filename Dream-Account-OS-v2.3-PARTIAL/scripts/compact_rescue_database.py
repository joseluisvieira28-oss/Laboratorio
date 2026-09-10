from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

MAX_OPERATIONAL_SNAPSHOTS = 500_000
SNAPSHOT_TABLE = "normalized_snapshots"
BATCH_ROWS = 5_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integrity(connection: sqlite3.Connection) -> list[str]:
    return [row[0] for row in connection.execute("PRAGMA integrity_check").fetchall()]


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def table_names(connection: sqlite3.Connection) -> list[str]:
    return [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]


def table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0])


def table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in connection.execute(f"PRAGMA table_info({q(table)})").fetchall()]


def schema_objects(connection: sqlite3.Connection, object_type: str) -> list[tuple[str, str]]:
    return [(row[0], row[1]) for row in connection.execute(
        "SELECT name, sql FROM sqlite_master WHERE type=? AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY name",
        (object_type,),
    )]


def copy_query_rows(source: sqlite3.Connection, destination: sqlite3.Connection, table: str,
                    select_sql: str, params: tuple = ()) -> int:
    columns = table_columns(source, table)
    if not columns:
        return 0
    column_sql = ",".join(q(column) for column in columns)
    placeholders = ",".join("?" for _ in columns)
    insert_sql = f"INSERT INTO {q(table)} ({column_sql}) VALUES ({placeholders})"
    cursor = source.execute(select_sql, params)
    copied = 0
    while True:
        rows = cursor.fetchmany(BATCH_ROWS)
        if not rows:
            break
        destination.executemany(insert_sql, rows)
        copied += len(rows)
    return copied


def build_candidate(source_path: Path, destination_path: Path, max_snapshots: int) -> dict:
    if max_snapshots < 1:
        raise ValueError("max_snapshots must be >= 1")
    if not source_path.is_file():
        raise FileNotFoundError("source database does not exist")
    if destination_path.exists():
        raise FileExistsError("destination already exists; refusing to overwrite")
    if source_path.resolve() == destination_path.resolve():
        raise ValueError("source and destination must be different files")
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    wal_path = Path(str(source_path) + "-wal")
    shm_path = Path(str(source_path) + "-shm")
    nonempty_sidecars = {
        str(path): path.stat().st_size
        for path in (wal_path, shm_path)
        if path.exists() and path.stat().st_size > 0
    }
    if nonempty_sidecars:
        raise RuntimeError(f"non-empty SQLite WAL/SHM sidecar detected: {nonempty_sidecars}")

    source_hash_before = sha256(source_path)
    source = sqlite3.connect(f"file:{source_path.resolve().as_posix()}?mode=ro", uri=True)
    source.execute("PRAGMA query_only=ON")
    source_integrity = integrity(source)
    source_journal_mode = str(source.execute("PRAGMA journal_mode").fetchone()[0]).lower()
    if source_integrity != ["ok"]:
        source.close()
        raise RuntimeError(f"source integrity failed: {source_integrity}")
    if source_journal_mode == "wal":
        source.close()
        raise RuntimeError("source is in WAL mode; refuse compaction until a stable checkpointed source is frozen")

    source_tables = table_names(source)
    source_counts = {name: table_count(source, name) for name in source_tables}
    source_schemas = {name: sql for name, sql in schema_objects(source, "table")}
    source_indexes = schema_objects(source, "index")
    source_triggers = schema_objects(source, "trigger")
    source_views = schema_objects(source, "view")
    user_version = int(source.execute("PRAGMA user_version").fetchone()[0])
    application_id = int(source.execute("PRAGMA application_id").fetchone()[0])

    snapshot_source_count = source_counts.get(SNAPSHOT_TABLE, 0)
    keep = min(snapshot_source_count, max_snapshots)
    oldest_kept_id: int | None = None
    if snapshot_source_count > keep:
        anchor = source.execute(
            f"SELECT id FROM {q(SNAPSHOT_TABLE)} ORDER BY id DESC LIMIT 1 OFFSET ?",
            (keep - 1,),
        ).fetchone()
        if anchor is None:
            source.close()
            raise RuntimeError("snapshot retention anchor could not be resolved")
        oldest_kept_id = int(anchor[0])

    destination = sqlite3.connect(destination_path)
    try:
        for table in source_tables:
            sql = source_schemas.get(table)
            if not sql:
                raise RuntimeError(f"missing CREATE TABLE SQL for {table}")
            destination.execute(sql)
        destination.execute(f"PRAGMA user_version={user_version}")
        destination.execute(f"PRAGMA application_id={application_id}")
        destination.commit()

        copied_counts: dict[str, int] = {}
        for table in source_tables:
            columns = table_columns(source, table)
            column_sql = ",".join(q(column) for column in columns)
            if table == SNAPSHOT_TABLE and oldest_kept_id is not None:
                select_sql = f"SELECT {column_sql} FROM {q(table)} WHERE id >= ? ORDER BY id"
                params = (oldest_kept_id,)
            else:
                select_sql = f"SELECT {column_sql} FROM {q(table)}"
                params = ()
            with destination:
                copied_counts[table] = copy_query_rows(source, destination, table, select_sql, params)

        for _, sql in source_indexes:
            destination.execute(sql)
        for _, sql in source_triggers:
            destination.execute(sql)
        for _, sql in source_views:
            destination.execute(sql)
        destination.commit()

        destination_integrity = integrity(destination)
        destination_tables = table_names(destination)
        destination_counts = {name: table_count(destination, name) for name in destination_tables}
        destination_schema = {
            row[0]: row[1]
            for row in destination.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        }

        mismatches = {
            table: {"source": source_counts[table], "candidate": destination_counts.get(table)}
            for table in source_tables
            if table != SNAPSHOT_TABLE and source_counts[table] != destination_counts.get(table)
        }
        schema_mismatches = {
            table: {"source": source_schemas.get(table), "candidate": destination_schema.get(table)}
            for table in source_tables
            if source_schemas.get(table) != destination_schema.get(table)
        }
        snapshot_ids = destination.execute(
            f"SELECT COALESCE(MIN(id),0), COALESCE(MAX(id),0), COUNT(*) FROM {q(SNAPSHOT_TABLE)}"
        ).fetchone() if SNAPSHOT_TABLE in destination_tables else (0, 0, 0)
    finally:
        destination.close()
        source.close()

    source_hash_after = sha256(source_path)
    destination_hash = sha256(destination_path)
    status = (
        destination_integrity == ["ok"]
        and not mismatches
        and not schema_mismatches
        and int(snapshot_ids[2]) == keep
        and source_hash_before == source_hash_after
    )
    return {
        "status": "PASS" if status else "FAIL",
        "source": str(source_path),
        "source_size_bytes": source_path.stat().st_size,
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "source_unchanged": source_hash_before == source_hash_after,
        "source_integrity_check": source_integrity,
        "source_journal_mode": source_journal_mode,
        "source_nonempty_sidecars": nonempty_sidecars,
        "destination": str(destination_path),
        "destination_size_bytes": destination_path.stat().st_size,
        "destination_sha256": destination_hash,
        "destination_integrity_check": destination_integrity,
        "max_snapshots": max_snapshots,
        "source_snapshot_rows": snapshot_source_count,
        "candidate_snapshot_rows": int(snapshot_ids[2]),
        "candidate_snapshot_min_id": int(snapshot_ids[0]),
        "candidate_snapshot_max_id": int(snapshot_ids[1]),
        "oldest_kept_source_snapshot_id": oldest_kept_id,
        "non_snapshot_count_mismatches": mismatches,
        "schema_mismatches": schema_mismatches,
        "source_table_counts": source_counts,
        "candidate_table_counts": destination_counts,
        "copied_table_counts": copied_counts,
        "production_replacement_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a validated compact Dream Account OS SQLite candidate copy.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--max-snapshots", type=int, default=MAX_OPERATIONAL_SNAPSHOTS)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        report = build_candidate(args.source, args.destination, args.max_snapshots)
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        raise SystemExit(str(exc))
    output = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
