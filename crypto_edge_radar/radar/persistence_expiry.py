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
        "target_provider": "SUPABASE",
        "target_project_ref": "jqzdvgjeuveiktftyrlz",
        "target_project_name": "crypto-edge-radar-evidence-v05",
        "target_region": "eu-central-1",
        "target_plan": "free",
        "target_provisioned": True,
        "target_equivalence_receipt": "RADAR_SUPABASE_TARGET_EQUIVALENCE_2026-09-27.md",
        "target_equivalence_verified_at_backup_boundary": True,
        "target_event_count_at_backup_boundary": 1032,
        "target_key_count_at_backup_boundary": 954,
        "target_event_rowset_sha256": "f1fdde4843b8c33f42a2a90896ef4d86df411d02c00e25d551576b53f7a8efa2",
        "target_key_rowset_sha256": "978f6eea3070fbadd73ccb4688028a9f3dcf07ab5876ccdc47cfa53c2debf02d",
        "target_runtime_role": "radar_runtime",
        "target_runtime_role_prepared": True,
        "target_runtime_role_least_privilege": True,
        "target_connection_mode": "SUPAVISOR_SHARED_SESSION_5432_IPV4",
        "target_schema_preprovisioned_required": True,
        "pooler_discovery_authority": "RADAR_SUPABASE_RUNTIME_ROLE_POOLER_DISCOVERY_V0.1_2026-09-27.md",
        "target_url_configured": False,
        "target_pooler_host_discovered": False,
        "target_connection_credential_configured": False,
        "cutover_blocker": "TARGET_CONNECTION_CREDENTIAL_NOT_CONFIGURED",
        "final_quiesced_refresh_required": True,
        "final_cutover_authorized": False,
        "database_mutation": False,
    }
