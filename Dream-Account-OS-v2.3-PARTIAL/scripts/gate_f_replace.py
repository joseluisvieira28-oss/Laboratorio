from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

from compact_rescue_database import build_candidate, integrity, sha256, table_count, table_names

GATE_F_ENV = "DREAM_GATE_F_REPLACE"
MAINTENANCE_ENV = "DREAM_FORCE_MAINTENANCE"
EXPECTED_SOURCE_SHA_ENV = "DREAM_RECOVERY_EXPECTED_SOURCE_SHA256"
EXPECTED_CANDIDATE_SHA_ENV = "DREAM_RECOVERY_EXPECTED_CANDIDATE_SHA256"
DB_PATH_ENV = "DREAM_DB_PATH"
DEFAULT_SOURCE = Path("/var/data/dream_account.sqlite3")
DEFAULT_CANDIDATE = Path("/tmp/dream_account.gate-f.sqlite3")
DEFAULT_REPORT = Path("/tmp/dream_account.gate-f-report.json")
DEFAULT_INSTALL = Path("/var/data/.dream_account.sqlite3.gate-f-installing")
DEFAULT_MARKER = Path("/var/data/GATE_F_IN_PROGRESS.json")
DEFAULT_RECEIPT = Path("/var/data/GATE_F_RECOVERY_RECEIPT.json")
MAX_SNAPSHOTS = 500_000
COPY_CHUNK_BYTES = 8 * 1024 * 1024


def truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def emit(event: str, **fields) -> None:
    print(json.dumps({
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **fields,
    }, sort_keys=True, default=str), flush=True)


def valid_sha(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise ValueError("expected SHA-256 must be exactly 64 lowercase/uppercase hex characters")
    return normalized


def fsync_directory(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json_durable(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    data = (json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8")
    with temp.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
    fsync_directory(path.parent)


def sqlite_summary(path: Path) -> dict:
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        checks = integrity(connection)
        tables = table_names(connection)
        counts = {name: table_count(connection, name) for name in tables}
        if "normalized_snapshots" in tables:
            minimum, maximum, rows = connection.execute(
                "SELECT COALESCE(MIN(id),0), COALESCE(MAX(id),0), COUNT(*) FROM normalized_snapshots"
            ).fetchone()
        else:
            minimum, maximum, rows = (0, 0, 0)
        return {
            "integrity_check": checks,
            "table_counts": counts,
            "snapshot_rows": int(rows),
            "snapshot_min_id": int(minimum),
            "snapshot_max_id": int(maximum),
        }
    finally:
        connection.close()


def copy_durable(source: Path, destination: Path) -> None:
    with source.open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst, length=COPY_CHUNK_BYTES)
        dst.flush()
        os.fsync(dst.fileno())
    fsync_directory(destination.parent)


def perform_gate_f(
    source: Path,
    candidate: Path,
    report_path: Path,
    install_path: Path,
    marker_path: Path,
    receipt_path: Path,
    max_snapshots: int,
    expected_source_sha: str,
    expected_candidate_sha: str,
) -> dict:
    expected_source_sha = valid_sha(expected_source_sha)
    expected_candidate_sha = valid_sha(expected_candidate_sha)

    if not source.exists():
        raise RuntimeError("canonical source database is missing")

    current_hash = sha256(source)
    if current_hash == expected_candidate_sha:
        installed = sqlite_summary(source)
        if installed["integrity_check"] != ["ok"]:
            raise RuntimeError("already-installed candidate failed integrity_check")
        result = {
            "status": "PASS_ALREADY_INSTALLED",
            "source": str(source),
            "installed_sha256": current_hash,
            "installed_size_bytes": source.stat().st_size,
            "installed": installed,
            "production_replacement_performed": False,
            "idempotent": True,
        }
        write_json_durable(receipt_path, result)
        return result

    if current_hash != expected_source_sha:
        raise RuntimeError(f"source SHA-256 mismatch before Gate F: expected {expected_source_sha} got {current_hash}")

    for path in (candidate, report_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    if install_path.exists():
        raise RuntimeError(f"stale install path exists: {install_path}")

    report = build_candidate(
        source,
        candidate,
        max_snapshots,
        expected_source_sha256=expected_source_sha,
    )
    if report.get("status") != "PASS":
        raise RuntimeError(f"candidate construction failed: {report.get('status')}")
    write_json_durable(report_path, report)

    candidate_hash = sha256(candidate)
    if candidate_hash != expected_candidate_sha:
        raise RuntimeError(
            f"candidate SHA-256 mismatch: expected {expected_candidate_sha} got {candidate_hash}"
        )
    candidate_summary = sqlite_summary(candidate)
    if candidate_summary["integrity_check"] != ["ok"]:
        raise RuntimeError("candidate integrity_check failed")
    if candidate_summary["table_counts"] != report["candidate_table_counts"]:
        raise RuntimeError("candidate table counts differ from compaction report")
    if candidate_summary["snapshot_rows"] != report["candidate_snapshot_rows"]:
        raise RuntimeError("candidate snapshot count differs from compaction report")

    final_source_hash = sha256(source)
    if final_source_hash != expected_source_sha:
        raise RuntimeError("source changed between candidate validation and destructive boundary")

    marker = {
        "status": "IN_PROGRESS",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": str(source),
        "source_sha256": final_source_hash,
        "candidate": str(candidate),
        "candidate_sha256": candidate_hash,
        "candidate_size_bytes": candidate.stat().st_size,
        "production_replacement_authorized": True,
    }
    write_json_durable(marker_path, marker)

    destructive_started = True
    source.unlink()
    fsync_directory(source.parent)

    copy_durable(candidate, install_path)
    installed_temp_hash = sha256(install_path)
    if installed_temp_hash != expected_candidate_sha:
        raise RuntimeError("persistent install copy SHA-256 mismatch")
    installed_temp_summary = sqlite_summary(install_path)
    if installed_temp_summary["integrity_check"] != ["ok"]:
        raise RuntimeError("persistent install copy integrity_check failed")
    if installed_temp_summary["table_counts"] != report["candidate_table_counts"]:
        raise RuntimeError("persistent install copy table counts differ from candidate report")

    os.replace(install_path, source)
    fsync_directory(source.parent)

    installed_hash = sha256(source)
    installed_summary = sqlite_summary(source)
    if installed_hash != expected_candidate_sha:
        raise RuntimeError("final installed database SHA-256 mismatch")
    if installed_summary["integrity_check"] != ["ok"]:
        raise RuntimeError("final installed database integrity_check failed")
    if installed_summary["table_counts"] != report["candidate_table_counts"]:
        raise RuntimeError("final installed database table counts differ from candidate report")

    result = {
        "status": "PASS",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_original_sha256": expected_source_sha,
        "candidate_sha256": candidate_hash,
        "candidate_size_bytes": candidate.stat().st_size,
        "installed_path": str(source),
        "installed_sha256": installed_hash,
        "installed_size_bytes": source.stat().st_size,
        "installed": installed_summary,
        "candidate_report": report,
        "production_replacement_performed": destructive_started,
        "forced_maintenance_required": True,
    }
    write_json_durable(receipt_path, result)
    try:
        marker_path.unlink()
        fsync_directory(marker_path.parent)
    except FileNotFoundError:
        pass
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Perform the explicitly authorized Dream Account OS Gate F replacement.")
    parser.add_argument("--source", type=Path, default=Path(os.getenv(DB_PATH_ENV, str(DEFAULT_SOURCE))))
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--install", type=Path, default=DEFAULT_INSTALL)
    parser.add_argument("--marker", type=Path, default=DEFAULT_MARKER)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--max-snapshots", type=int, default=MAX_SNAPSHOTS)
    args = parser.parse_args()

    if not truthy(GATE_F_ENV):
        emit("gate_f_skipped", reason=f"{GATE_F_ENV} is not enabled")
        return 0
    if not truthy(MAINTENANCE_ENV):
        emit("gate_f_failed", error=f"{MAINTENANCE_ENV} must remain enabled", destructive_started=False)
        return 3

    expected_source = os.getenv(EXPECTED_SOURCE_SHA_ENV, "")
    expected_candidate = os.getenv(EXPECTED_CANDIDATE_SHA_ENV, "")
    if not expected_source or not expected_candidate:
        emit("gate_f_failed", error="expected source and candidate SHA-256 pins are required", destructive_started=False)
        return 4

    emit(
        "gate_f_start",
        source=str(args.source),
        max_snapshots=args.max_snapshots,
        expected_source_sha256=expected_source.lower(),
        expected_candidate_sha256=expected_candidate.lower(),
        forced_maintenance=True,
    )
    try:
        result = perform_gate_f(
            args.source,
            args.candidate,
            args.report,
            args.install,
            args.marker,
            args.receipt,
            args.max_snapshots,
            expected_source,
            expected_candidate,
        )
    except Exception as exc:
        emit(
            "gate_f_failed",
            error=f"{type(exc).__name__}: {exc}",
            source_exists=args.source.exists(),
            install_exists=args.install.exists(),
            marker_exists=args.marker.exists(),
            destructive_started=args.marker.exists(),
        )
        return 10

    emit("gate_f_replacement_result", result=result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
