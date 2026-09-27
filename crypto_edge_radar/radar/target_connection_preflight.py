from __future__ import annotations

import os
from typing import Any

from .evidence_portability import canonical_snapshot_sha, verify_snapshot

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

AUTHORITY_ID = "RADAR-SUPABASE-TARGET-PREFLIGHT-V0.2"
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
    verified_full = verify_snapshot(snapshot)
    events = list(snapshot.get("events") or [])
    keys = list(snapshot.get("event_keys") or [])
    event_ids = [int(row["id"]) for row in events]
    min_id = min(event_ids) if event_ids else None
    max_id = max(event_ids) if event_ids else None

    contiguous = event_ids == list(range(1, len(event_ids) + 1))
    boundary_events = [
        row for row in events if int(row["id"]) <= EXPECTED_MAX_EVENT_ID
    ]
    boundary_keys = [
        row for row in keys if int(row["event_id"]) <= EXPECTED_MAX_EVENT_ID
    ]
    boundary_snapshot = {
        "events": boundary_events,
        "event_keys": boundary_keys,
        "event_count": len(boundary_events),
        "key_count": len(boundary_keys),
        "chain_head_sha256": (
            boundary_events[-1]["chain_sha256"]
            if boundary_events
            else "0" * 64
        ),
    }
    boundary_snapshot["snapshot_sha256"] = canonical_snapshot_sha(
        boundary_snapshot
    )

    try:
        verified_boundary = verify_snapshot(boundary_snapshot)
        boundary_verify_ok = True
        boundary_verify_error = None
    except Exception as exc:
        verified_boundary = {
            "event_count": len(boundary_events),
            "key_count": len(boundary_keys),
            "chain_head_sha256": boundary_snapshot["chain_head_sha256"],
            "snapshot_sha256": boundary_snapshot["snapshot_sha256"],
        }
        boundary_verify_ok = False
        boundary_verify_error = f"{type(exc).__name__}:{exc}"

    checks = {
        "current_event_count_at_least_backup_boundary": (
            verified_full["event_count"] >= EXPECTED_EVENT_COUNT
        ),
        "current_key_count_at_least_backup_boundary": (
            verified_full["key_count"] >= EXPECTED_KEY_COUNT
        ),
        "current_min_event_id_is_one": min_id == EXPECTED_MIN_EVENT_ID,
        "current_event_ids_contiguous_from_one": contiguous,
        "current_sequence_exact_to_max_id": (
            max_id is not None and sequence_last == max_id
        ),
        "backup_boundary_verify_ok": boundary_verify_ok,
        "backup_boundary_event_count_exact": (
            verified_boundary["event_count"] == EXPECTED_EVENT_COUNT
        ),
        "backup_boundary_key_count_exact": (
            verified_boundary["key_count"] == EXPECTED_KEY_COUNT
        ),
        "backup_boundary_max_event_id_exact": (
            bool(boundary_events)
            and int(boundary_events[-1]["id"]) == EXPECTED_MAX_EVENT_ID
        ),
        "backup_boundary_chain_head_exact": (
            verified_boundary["chain_head_sha256"] == EXPECTED_CHAIN_HEAD
        ),
        "backup_boundary_snapshot_exact": (
            verified_boundary["snapshot_sha256"] == EXPECTED_SNAPSHOT_SHA
        ),
    }
    exact = all(checks.values())
    out = {
        **_safe_base(),
        "classification": (
            "TARGET_PREFLIGHT_PASS_BACKUP_PREFIX_CURRENT_CHAIN_OK"
            if exact
            else "TARGET_PREFLIGHT_MISMATCH_FAIL_CLOSED"
        ),
        "connected": True,
        "identity": identity or {},
        "current_event_count": verified_full["event_count"],
        "current_key_count": verified_full["key_count"],
        "current_min_event_id": min_id,
        "current_max_event_id": max_id,
        "current_chain_head_sha256": verified_full["chain_head_sha256"],
        "current_canonical_snapshot_sha256": verified_full["snapshot_sha256"],
        "sequence_last_value": sequence_last,
        "backup_boundary_event_count": verified_boundary["event_count"],
        "backup_boundary_key_count": verified_boundary["key_count"],
        "backup_boundary_chain_head_sha256": verified_boundary["chain_head_sha256"],
        "backup_boundary_snapshot_sha256": verified_boundary["snapshot_sha256"],
        "backup_boundary_verify_error": boundary_verify_error,
        "checks": checks,
        "suffix_event_count": max(
            0, verified_full["event_count"] - EXPECTED_EVENT_COUNT
        ),
        "suffix_key_count": max(
            0, verified_full["key_count"] - EXPECTED_KEY_COUNT
        ),
        "final_quiesced_refresh_required": True,
        "database_url_switch_authorized": False,
    }
    return out


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
