from __future__ import annotations

from typing import Any

from .evidence import POSTGRES_CHAIN_LOCK_ID
from .evidence_portability import (
    _read_target_snapshot,
    _sorted_keys,
    _target_sequence_state,
    verify_snapshot,
)

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


class SequenceFinalizationError(RuntimeError):
    pass


def _exact_target_rows(
    source_snapshot: dict[str, Any],
    target_snapshot: dict[str, Any],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    source_verified = verify_snapshot(source_snapshot)
    target_verified = verify_snapshot(target_snapshot)

    if target_snapshot["events"] != source_snapshot["events"]:
        reasons.append("TARGET_EVENTS_NOT_EXACT_SOURCE")
    if _sorted_keys(target_snapshot["event_keys"]) != _sorted_keys(
        source_snapshot["event_keys"]
    ):
        reasons.append("TARGET_KEYS_NOT_EXACT_SOURCE")
    if (
        target_verified["chain_head_sha256"]
        != source_verified["chain_head_sha256"]
    ):
        reasons.append("TARGET_CHAIN_HEAD_NOT_EXACT_SOURCE")
    if (
        target_verified["snapshot_sha256"]
        != source_verified["snapshot_sha256"]
    ):
        reasons.append("TARGET_SNAPSHOT_SHA_NOT_EXACT_SOURCE")

    ids = [int(x["id"]) for x in target_snapshot["events"]]
    if ids != list(range(1, len(ids) + 1)):
        reasons.append("TARGET_EVENT_IDS_NOT_CONTIGUOUS_FROM_ONE")

    return not reasons, reasons


def finalize_target_sequence(
    snapshot: dict[str, Any],
    *,
    target_url: str,
    apply: bool,
) -> dict[str, Any]:
    source_verified = verify_snapshot(snapshot)
    source_events = list(snapshot.get("events") or [])
    source_max_id = int(source_events[-1]["id"]) if source_events else 0

    if not target_url or not target_url.strip():
        return {
            "classification": "AUTH_REQUIRED_NOT_EXECUTED",
            "source_event_count": source_verified["event_count"],
            "source_key_count": source_verified["key_count"],
            "source_max_event_id": source_max_id,
            "target_mutation": False,
            "sequence_mutation": False,
            "cutover_authorized": False,
            "secret_value_exposed": False,
        }

    if not source_events:
        return {
            "classification": "EMPTY_SOURCE_SEQUENCE_FINALIZATION_NOT_REQUIRED",
            "source_event_count": 0,
            "source_key_count": source_verified["key_count"],
            "source_max_event_id": 0,
            "target_mutation": False,
            "sequence_mutation": False,
            "cutover_authorized": False,
            "secret_value_exposed": False,
        }

    if psycopg is None:
        raise SequenceFinalizationError(
            "psycopg is required for Postgres sequence finalization"
        )

    with psycopg.connect(target_url.strip(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            target = _read_target_snapshot(cur)
            exact, reasons = _exact_target_rows(snapshot, target)
            sequence_last, sequence_called = _target_sequence_state(cur)

    if not exact:
        return {
            "classification": "TARGET_SEQUENCE_FINALIZATION_FAIL_CLOSED_NO_MUTATION",
            "source_event_count": source_verified["event_count"],
            "source_key_count": source_verified["key_count"],
            "source_max_event_id": source_max_id,
            "reasons": reasons,
            "sequence_last_value": sequence_last,
            "sequence_is_called": sequence_called,
            "target_mutation": False,
            "sequence_mutation": False,
            "cutover_authorized": False,
            "secret_value_exposed": False,
        }

    sequence_exact = (
        int(sequence_last) == source_max_id and bool(sequence_called) is True
    )
    if sequence_exact:
        return {
            "classification": "TARGET_SEQUENCE_ALREADY_EXACT",
            "source_event_count": source_verified["event_count"],
            "source_key_count": source_verified["key_count"],
            "source_max_event_id": source_max_id,
            "sequence_last_value": sequence_last,
            "sequence_is_called": sequence_called,
            "target_rows_exact": True,
            "target_mutation": False,
            "sequence_mutation": False,
            "cutover_authorized": False,
            "secret_value_exposed": False,
        }

    if not apply:
        return {
            "classification": "DRY_RUN_TARGET_ROWS_EXACT__SEQUENCE_FINALIZATION_REQUIRED",
            "source_event_count": source_verified["event_count"],
            "source_key_count": source_verified["key_count"],
            "source_max_event_id": source_max_id,
            "sequence_last_value": sequence_last,
            "sequence_is_called": sequence_called,
            "target_rows_exact": True,
            "target_mutation": False,
            "sequence_mutation": False,
            "cutover_authorized": False,
            "secret_value_exposed": False,
        }

    with psycopg.connect(target_url.strip(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (POSTGRES_CHAIN_LOCK_ID,),
            )
            target_locked = _read_target_snapshot(cur)
            exact_locked, reasons_locked = _exact_target_rows(
                snapshot,
                target_locked,
            )
            if not exact_locked:
                raise SequenceFinalizationError(
                    "target changed before sequence finalization: "
                    + ",".join(reasons_locked)
                )

            current_last, current_called = _target_sequence_state(cur)
            if (
                int(current_last) == source_max_id
                and bool(current_called) is True
            ):
                final_last, final_called = current_last, current_called
                changed = False
            else:
                cur.execute(
                    "SELECT setval("
                    "pg_get_serial_sequence('radar_events','id'), %s, true"
                    ")",
                    (source_max_id,),
                )
                cur.fetchone()
                final_last, final_called = _target_sequence_state(cur)
                changed = True

            target_after = _read_target_snapshot(cur)
            exact_after, reasons_after = _exact_target_rows(
                snapshot,
                target_after,
            )
            if not exact_after:
                raise SequenceFinalizationError(
                    "target rows changed during sequence finalization: "
                    + ",".join(reasons_after)
                )
            if int(final_last) != source_max_id or bool(final_called) is not True:
                raise SequenceFinalizationError(
                    "target sequence not exact after finalization"
                )

    return {
        "classification": (
            "TARGET_SEQUENCE_FINALIZED_EXACT"
            if changed
            else "TARGET_SEQUENCE_ALREADY_EXACT"
        ),
        "source_event_count": source_verified["event_count"],
        "source_key_count": source_verified["key_count"],
        "source_max_event_id": source_max_id,
        "sequence_last_value": int(final_last),
        "sequence_is_called": bool(final_called),
        "target_rows_exact": True,
        "target_mutation": False,
        "sequence_mutation": bool(changed),
        "cutover_authorized": False,
        "secret_value_exposed": False,
    }
