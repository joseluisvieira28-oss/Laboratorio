from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

BUILD_ENV = "DREAM_BUILD_RECOVERY_CANDIDATE"
MAINTENANCE_ENV = "DREAM_FORCE_MAINTENANCE"
EXPECTED_SHA_ENV = "DREAM_RECOVERY_EXPECTED_SOURCE_SHA256"
DB_PATH_ENV = "DREAM_DB_PATH"
CANDIDATE_PATH = Path("/tmp/dream_account.compact.sqlite3")
REPORT_PATH = Path("/tmp/dream_account.compaction-report.json")
MAX_SNAPSHOTS = 500_000


def truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def emit(event: str, **fields) -> None:
    print(json.dumps({
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **fields,
    }, sort_keys=True, default=str), flush=True)


def main() -> int:
    if not truthy(BUILD_ENV):
        return 0
    if not truthy(MAINTENANCE_ENV):
        emit("recovery_candidate_failed", error=f"{MAINTENANCE_ENV} must be enabled")
        return 3

    expected_sha = os.getenv(EXPECTED_SHA_ENV, "").strip().lower()
    if not expected_sha:
        emit("recovery_candidate_failed", error=f"{EXPECTED_SHA_ENV} is required")
        return 4

    source = Path(os.getenv(DB_PATH_ENV, "/var/data/dream_account.sqlite3"))
    script = Path(__file__).with_name("compact_rescue_database.py")

    for path in (CANDIDATE_PATH, REPORT_PATH):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    command = [
        sys.executable,
        str(script),
        str(source),
        str(CANDIDATE_PATH),
        "--max-snapshots",
        str(MAX_SNAPSHOTS),
        "--report",
        str(REPORT_PATH),
        "--expected-source-sha256",
        expected_sha,
    ]
    emit(
        "recovery_candidate_start",
        source=str(source),
        destination=str(CANDIDATE_PATH),
        max_snapshots=MAX_SNAPSHOTS,
        expected_source_sha256=expected_sha,
        production_replacement_performed=False,
    )

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except subprocess.TimeoutExpired:
        emit("recovery_candidate_failed", error="compaction timed out after 1800 seconds")
        return 5

    report = None
    if REPORT_PATH.is_file():
        try:
            report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            emit("recovery_candidate_failed", error=f"invalid report: {type(exc).__name__}: {exc}")
            return 6

    if completed.returncode != 0 or not report or report.get("status") != "PASS":
        emit(
            "recovery_candidate_failed",
            returncode=completed.returncode,
            stderr=(completed.stderr or "")[-4000:],
            stdout=(completed.stdout or "")[-4000:],
            report=report,
            production_replacement_performed=False,
        )
        return 7

    emit(
        "recovery_candidate_result",
        returncode=completed.returncode,
        report=report,
        production_replacement_performed=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
