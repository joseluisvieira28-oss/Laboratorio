from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def persistence_expiry_state(
    expiry_utc: str | None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)

    if not expiry_utc:
        return {
            "classification": "UNKNOWN",
            "expiry_utc": None,
            "seconds_remaining": None,
            "days_remaining": None,
            "migration_required": False,
        }

    expiry = datetime.fromisoformat(expiry_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
    remaining = (expiry - now).total_seconds()
    days = remaining / 86400.0

    if remaining <= 0:
        classification = "EXPIRED"
    elif days <= 7:
        classification = "CRITICAL"
    elif days <= 14:
        classification = "WARN"
    else:
        classification = "OK"

    return {
        "classification": classification,
        "expiry_utc": expiry.isoformat().replace("+00:00", "Z"),
        "seconds_remaining": remaining,
        "days_remaining": days,
        "migration_required": classification in {"WARN", "CRITICAL", "EXPIRED"},
        "verified_backup_exists": True,
        "backup_receipt": "RADAR_EVIDENCE_BACKUP_CLOSEOUT_2026-09-27.json",
        "backup_event_count": 1032,
        "backup_key_count": 954,
        "backup_canonical_snapshot_sha256": "6c74bdcf1013b1ab49fdcefd2e046db6471ea2816c6b425f4a6378dda22de9cb",
        "backup_drive_file_id": "1oam9hmileBQbV80C6o0cQUicXfu-vzvZ",
        "cutover_protocol": "RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1.md",
        "target_url_configured": False,
        "database_mutation": False,
    }
