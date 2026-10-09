"""Offline verifier for the MRCR H02 frozen-scope shadow journal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from h02_scope_journal import connect_scope_journal, latest_batch_id, sqlite_integrity_ok
from h02_scope_recovery import verify_scope_batch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--batch-id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = connect_scope_journal(args.db)
    batch_id = args.batch_id or latest_batch_id(conn)
    if batch_id is None:
        receipt = {
            "verifier": "MRCR_H02_FROZEN_SCOPE_OFFLINE_VERIFIER_V01",
            "status": "FAIL_CLOSED",
            "failure_reason": "NO_BATCH_FOUND",
        }
        print(json.dumps(receipt, sort_keys=True))
        conn.close()
        return 2

    sqlite_ok = sqlite_integrity_ok(conn)
    result = verify_scope_batch(conn, batch_id=batch_id)
    session_rows = conn.execute(
        """
        SELECT venue, native_symbol, stream_group, status
        FROM scope_sessions
        WHERE batch_id=?
        ORDER BY venue, native_symbol, stream_group
        """,
        (batch_id,),
    ).fetchall()
    conn.close()

    status = "PASS" if sqlite_ok and result.ok else "FAIL_CLOSED"
    receipt = {
        "verifier": "MRCR_H02_FROZEN_SCOPE_OFFLINE_VERIFIER_V01",
        "batch_id": batch_id,
        "sqlite_integrity_pass": sqlite_ok,
        "batch_recovery_pass": result.ok,
        "session_count": result.session_count,
        "passed_session_count": result.passed_session_count,
        "blockers": list(result.blockers),
        "sessions": [
            {
                "venue": str(row["venue"]),
                "native_symbol": str(row["native_symbol"]),
                "stream_group": str(row["stream_group"]),
                "terminal_status": str(row["status"]),
            }
            for row in session_rows
        ],
        "authentication_used": False,
        "account_endpoints_used": False,
        "signals_computed": False,
        "outcomes_computed": False,
        "orders_enabled": False,
        "scientific_use": "SOURCE_INFRASTRUCTURE_HARDENING_ONLY",
        "promotion_credit": "NONE",
        "status": status,
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
