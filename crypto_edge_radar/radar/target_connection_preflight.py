from __future__ import annotations

import os
from typing import Any

from .evidence_portability import canonical_snapshot_sha, verify_snapshot

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

AUTHORITY_ID = "RADAR-SUPABASE-TARGET-PREFLIGHT-V0.1"
EXPECTED_EVENT_COUNT = 1032
EXPECTED_KEY_COUNT = 954
EXPECTED_MIN_EVENT_ID = 1
EXPECTED_MAX_EVENT_ID = 1032
EXPECTED_CHAIN_HEAD = "f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd"
EXPECTED_SNAPSHOT_SHA = "6c74bdcf1013b1ab49fdcefd2e046db6471ea2816c6b425f4a6378dda22de9cb"


class TargetPreflightError(RuntimeError):
    pass


def _safe_base() -> dict[str, Any]:
    return {
        "authority_id": AUTHORITY_ID,
        "target_provider": "SUPABASE",
        "target_project_ref": "jqzdvgjeuveiktftyrlz",
        "target_project_name": "crypto-edge-radar-evidence-v05",
        "target_region": "eu-central-1",
        "database_mutation": False,
        "source_mutation": False,
        "science_changed": False,
        "outcomes_changed": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
        "automatic_cutover": False,
        "secret_value_exposed": False,
    }


def _read_target_snapshot(target_url: str) -> tuple[dict[str, Any], int | None, dict[str, Any]]:
    if psycopg is None:
        raise TargetPreflightError("psycopg unavailable")

    with psycopg.connect(target_url.strip(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                "SELECT current_database(), current_user, current_setting('server_version_num')"
            )
            identity_row = cur.fetchone()
            identity = {
                "database_name": str(identity_row[0]),
                "database_role": str(identity_row[1]),
                "server_version_num": str(identity_row[2]),
            }

            cur.execute(
                "SELECT id,event_ts,event_type,payload_json,payload_sha256,"
                "prev_chain_sha256,chain_sha256 "
                "FROM radar_events ORDER BY id ASC"
            )
            events = [
                {
                    "id": int(r[0]),
                    "event_ts": r[1],
                    "event_type": r[2],
                    "payload_json": r[3],
                    "payload_sha256": r[4],
                    "prev_chain_sha256": r[5],
                    "chain_sha256": r[6],
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                "SELECT event_type,event_key,event_id "
                "FROM radar_event_keys ORDER BY event_type,event_key"
            )
            keys = [
                {
                    "event_type": r[0],
                    "event_key": r[1],
                    "event_id": int(r[2]),
                }
                for r in cur.fetchall()
            ]

            sequence_last = None
            cur.execute(
                "SELECT pg_get_serial_sequence('radar_events','id')"
            )
            seq_row = cur.fetchone()
            seq_name = seq_row[0] if seq_row else None
            if seq_name:
                cur.execute(f"SELECT last_value FROM {seq_name}")
                value = cur.fetchone()
                if value is not None:
                    sequence_last = int(value[0])

    snapshot = {
        "events": events,
        "event_keys": keys,
        "event_count": len(events),
        "key_count": len(keys),
        "chain_head_sha256": events[-1]["chain_sha256"] if events else "0" * 64,
    }
    snapshot["snapshot_sha256"] = canonical_snapshot_sha(snapshot)
    return snapshot, sequence_last, identity


def evaluate_target_snapshot(
    snapshot: dict[str, Any],
    *,
    sequence_last: int | None,
    identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verified = verify_snapshot(snapshot)
    event_ids = [int(row["id"]) for row in snapshot["events"]]
    min_id = min(event_ids) if event_ids else None
    max_id = max(event_ids) if event_ids else None

    checks = {
        "event_count_exact": verified["event_count"] == EXPECTED_EVENT_COUNT,
        "key_count_exact": verified["key_count"] == EXPECTED_KEY_COUNT,
        "min_event_id_exact": min_id == EXPECTED_MIN_EVENT_ID,
        "max_event_id_exact": max_id == EXPECTED_MAX_EVENT_ID,
        "chain_head_exact": verified["chain_head_sha256"] == EXPECTED_CHAIN_HEAD,
        "canonical_snapshot_exact": verified["snapshot_sha256"] == EXPECTED_SNAPSHOT_SHA,
        "sequence_last_exact": sequence_last == EXPECTED_MAX_EVENT_ID,
    }
    exact = all(checks.values())
    return {
        **_safe_base(),
        "classification": (
            "TARGET_PREFLIGHT_PASS_AT_BACKUP_BOUNDARY"
            if exact
            else "TARGET_PREFLIGHT_MISMATCH_FAIL_CLOSED"
        ),
        "connected": True,
        "identity": identity or {},
        "event_count": verified["event_count"],
        "key_count": verified["key_count"],
        "min_event_id": min_id,
        "max_event_id": max_id,
        "chain_head_sha256": verified["chain_head_sha256"],
        "canonical_snapshot_sha256": verified["snapshot_sha256"],
        "sequence_last_value": sequence_last,
        "checks": checks,
        "final_quiesced_refresh_required": True,
        "database_url_switch_authorized": False,
    }


def target_connection_preflight(target_url: str | None = None) -> dict[str, Any]:
    if target_url is None:
        target_url = os.getenv("RADAR_MIGRATION_TARGET_URL", "")
    if not target_url or not target_url.strip():
        return {
            **_safe_base(),
            "classification": "AUTH_REQUIRED_NOT_EXECUTED",
            "connected": False,
            "target_url_configured": False,
            "final_quiesced_refresh_required": True,
            "database_url_switch_authorized": False,
        }
    try:
        snapshot, sequence_last, identity = _read_target_snapshot(target_url)
        out = evaluate_target_snapshot(
            snapshot,
            sequence_last=sequence_last,
            identity=identity,
        )
        out["target_url_configured"] = True
        return out
    except Exception as exc:
        return {
            **_safe_base(),
            "classification": "TARGET_PREFLIGHT_FAIL_CLOSED",
            "connected": False,
            "target_url_configured": True,
            "error": f"{type(exc).__name__}:{exc}",
            "final_quiesced_refresh_required": True,
            "database_url_switch_authorized": False,
        }
