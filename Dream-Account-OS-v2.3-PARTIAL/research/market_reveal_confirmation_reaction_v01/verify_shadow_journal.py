"""Offline verifier for a locally persisted MRCR shadow journal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from shadow_journal import connect_journal, sqlite_integrity_ok
from shadow_recovery import replay_coinbase_level2_session, verify_session_chain


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--session-id")
    return parser.parse_args()


def _latest_session(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT session_id, product_id, status
        FROM shadow_sessions
        ORDER BY started_wall_ns DESC
        LIMIT 1
        """
    ).fetchone()


def main() -> int:
    args = parse_args()
    conn = connect_journal(args.db)

    if args.session_id:
        row = conn.execute(
            """
            SELECT session_id, product_id, status
            FROM shadow_sessions
            WHERE session_id=?
            """,
            (args.session_id,),
        ).fetchone()
    else:
        row = _latest_session(conn)

    if row is None:
        print(json.dumps({
            "verifier": "MRCR_SHADOW_JOURNAL_VERIFY_V01",
            "status": "FAIL_CLOSED",
            "reason": "NO_SESSION",
        }, sort_keys=True))
        conn.close()
        return 2

    session_id = str(row["session_id"])
    product_id = str(row["product_id"])
    chain = verify_session_chain(conn, session_id=session_id)
    recovery = replay_coinbase_level2_session(
        conn,
        session_id=session_id,
        product_id=product_id,
    )
    sqlite_ok = sqlite_integrity_ok(conn)

    receipt = {
        "verifier": "MRCR_SHADOW_JOURNAL_VERIFY_V01",
        "session_id": session_id,
        "transport_fixture_product": product_id,
        "transport_fixture_is_scientific_target": False,
        "stored_session_status": str(row["status"]),
        "sqlite_integrity_pass": sqlite_ok,
        "chain_integrity_pass": chain.ok,
        "persisted_message_count": chain.message_count,
        "chain_head_sha256": chain.chain_head_sha256,
        "recovery_pass": recovery.ok,
        "recovery_failure_reason": recovery.failure_reason,
        "snapshot_count": recovery.snapshot_count,
        "update_message_count": recovery.update_message_count,
        "recovered_final_sequence": recovery.final_sequence,
        "signals_computed": False,
        "outcomes_computed": False,
        "orders_enabled": False,
        "status": (
            "PASS"
            if sqlite_ok and chain.ok and recovery.ok
            else "FAIL_CLOSED"
        ),
    }
    print(json.dumps(receipt, sort_keys=True))
    conn.close()
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
