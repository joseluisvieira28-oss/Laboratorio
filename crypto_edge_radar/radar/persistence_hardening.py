from __future__ import annotations

import os
from typing import Any, Mapping

CANONICAL_RENDER_SERVICE_ID = "srv-dalqkpu1egvs73fhiehg"
CANONICAL_RENDER_SERVICE_NAME = "crypto-edge-radar-v05-canary"
CANONICAL_TARGET_MODE = "SUPABASE_POOLER"
CANONICAL_TARGET_PROVIDER = "SUPABASE"
CANONICAL_TARGET_PROJECT_REF = "jqzdvgjeuveiktftyrlz"
HISTORICAL_SOURCE_POSTGRES_ID = "dpg-dalqi4qd0e5s738a77kg-a"
HISTORICAL_SOURCE_ROLE = "NON_CANONICAL_ROLLBACK_ONLY"
CUTOVER_CLOSEOUT_RECEIPT = "RADAR_SUPABASE_CUTOVER_CLOSEOUT_2026-09-27.md"


def _env_bool(
    environ: Mapping[str, str],
    name: str,
    *,
    default: bool = False,
) -> tuple[bool, bool]:
    raw = environ.get(name)
    if raw is None:
        return default, True
    value = str(raw).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True, True
    if value in {"0", "false", "no", "off"}:
        return False, True
    return False, False


def persistence_watchdog_state(
    *,
    database_target_mode: str,
    evidence_backend: str,
    evidence_chain_ok: bool,
    evidence_identity: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Secret-safe post-cutover route and integrity watchdog.

    The canonical Render Radar is not allowed to silently fall back to the
    historical source database. Any other Render service whose name begins
    with crypto-edge-radar is also rejected as a writer if it runs this
    hardened code. Local and test contexts remain non-enforced unless
    explicitly opted in with RADAR_ENFORCE_CANONICAL_PERSISTENCE=true.
    """

    env = os.environ if environ is None else environ
    render = str(env.get("RENDER", "")).strip().lower() == "true"
    service_id = str(env.get("RENDER_SERVICE_ID", "")).strip() or None
    service_name = str(env.get("RENDER_SERVICE_NAME", "")).strip() or None

    target_flag, target_flag_valid = _env_bool(
        env,
        "RADAR_USE_SUPABASE_TARGET",
        default=False,
    )
    explicit_enforce, explicit_enforce_valid = _env_bool(
        env,
        "RADAR_ENFORCE_CANONICAL_PERSISTENCE",
        default=False,
    )

    canonical_render_service = bool(
        render and service_id == CANONICAL_RENDER_SERVICE_ID
    )
    radar_render_service = bool(
        render and service_name and service_name.startswith("crypto-edge-radar")
    )
    enforcement_required = bool(
        canonical_render_service
        or radar_render_service
        or explicit_enforce
        or database_target_mode == CANONICAL_TARGET_MODE
    )

    max_event_id = evidence_identity.get("max_event_id")
    sequence_last_value = evidence_identity.get("sequence_last_value")
    sequence_is_called = evidence_identity.get("sequence_is_called")
    event_count = evidence_identity.get("event_count")

    if isinstance(max_event_id, int) and max_event_id == 0:
        sequence_exact = sequence_last_value in {None, 0}
    else:
        sequence_exact = bool(
            isinstance(max_event_id, int)
            and isinstance(sequence_last_value, int)
            and sequence_last_value == max_event_id
            and sequence_is_called is True
        )

    checks = {
        "target_flag_syntax_valid": target_flag_valid,
        "enforcement_flag_syntax_valid": explicit_enforce_valid,
        "target_flag_enabled": target_flag,
        "database_target_mode_is_supabase_pooler": (
            database_target_mode == CANONICAL_TARGET_MODE
        ),
        "evidence_backend_is_postgres": evidence_backend == "postgres",
        "evidence_chain_verified": evidence_chain_ok is True,
        "evidence_identity_verified": evidence_identity.get("status") == "VERIFIED",
        "identity_backend_is_postgres": evidence_identity.get("backend") == "postgres",
        "sequence_exact_to_max_event_id": sequence_exact,
        "canonical_writer_service": (
            (not radar_render_service)
            or service_id == CANONICAL_RENDER_SERVICE_ID
        ),
    }

    if enforcement_required:
        passed = all(checks.values())
        classification = (
            "PASS_CANONICAL_SUPABASE_SINGLE_WRITER"
            if passed
            else "FAIL_CLOSED_PERSISTENCE_ROUTE"
        )
    else:
        passed = True
        classification = "NON_RENDER_LOCAL_CONTEXT_NOT_ENFORCED"

    pooler_host_configured = bool(
        str(env.get("RADAR_SUPABASE_POOLER_HOST", "")).strip()
    )
    credential_configured = bool(env.get("RADAR_SUPABASE_POOLER_PASSWORD"))
    target_url_configured = bool(
        target_flag
        and pooler_host_configured
        and credential_configured
        and database_target_mode == CANONICAL_TARGET_MODE
    )

    failures = [name for name, value in checks.items() if not value]
    return {
        "schema_version": "RADAR_PERSISTENCE_WATCHDOG_V0.1",
        "classification": classification,
        "pass": passed,
        "writes_allowed": passed,
        "enforcement_required": enforcement_required,
        "canonical_render_service": canonical_render_service,
        "canonical_render_service_id": CANONICAL_RENDER_SERVICE_ID,
        "canonical_render_service_name": CANONICAL_RENDER_SERVICE_NAME,
        "observed_render_service_id": service_id,
        "observed_render_service_name": service_name,
        "database_target_mode": database_target_mode,
        "canonical_target_mode": CANONICAL_TARGET_MODE,
        "canonical_target_provider": CANONICAL_TARGET_PROVIDER,
        "canonical_target_project_ref": CANONICAL_TARGET_PROJECT_REF,
        "historical_source_postgres_id": HISTORICAL_SOURCE_POSTGRES_ID,
        "historical_source_role": HISTORICAL_SOURCE_ROLE,
        "cutover_complete": bool(
            passed and database_target_mode == CANONICAL_TARGET_MODE
        ),
        "rollback_blind_url_flip_allowed": False,
        "rollback_requires_reconciliation": True,
        "configuration": {
            "target_flag_enabled": target_flag,
            "pooler_host_configured": pooler_host_configured,
            "credential_configured": credential_configured,
            "target_url_configured": target_url_configured,
            "historical_source_url_present": bool(
                str(env.get("RADAR_DATABASE_URL", "")).strip()
            ),
            "secret_value_exposed": False,
        },
        "integrity_proof": {
            "event_count": event_count,
            "key_count": evidence_identity.get("key_count"),
            "max_event_id": max_event_id,
            "chain_head_sha256": evidence_identity.get("chain_head_sha256"),
            "key_binding_sha256": evidence_identity.get("key_binding_sha256"),
            "sequence_last_value": sequence_last_value,
            "sequence_is_called": sequence_is_called,
            "chain_verified": evidence_identity.get("chain_verified"),
        },
        "checks": checks,
        "failures": failures,
        "database_mutation": False,
        "science_changed": False,
        "outcomes_changed": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
        "secret_value_exposed": False,
    }


def post_cutover_persistence_state(
    legacy_state: Mapping[str, Any],
    *,
    watchdog: Mapping[str, Any],
) -> dict[str, Any]:
    """Translate legacy migration telemetry into current post-cutover truth."""

    state = dict(legacy_state)
    if not watchdog.get("cutover_complete"):
        state["operational_authority"] = "LEGACY_MIGRATION_TELEMETRY"
        state["persistence_watchdog_classification"] = watchdog.get("classification")
        return state

    source_expiry_classification = state.get("classification")
    source_expiry_utc = state.get("expiry_utc")

    config = watchdog.get("configuration") or {}
    state.update(
        {
            "classification": "CUTOVER_COMPLETE_CANONICAL_SUPABASE",
            "operational_authority": "POST_CUTOVER_RUNTIME_TRUTH",
            "migration_required": False,
            "cutover_complete": True,
            "canonical_store": CANONICAL_TARGET_PROVIDER,
            "canonical_database_target_mode": CANONICAL_TARGET_MODE,
            "canonical_target_project_ref": CANONICAL_TARGET_PROJECT_REF,
            "historical_source_postgres_id": HISTORICAL_SOURCE_POSTGRES_ID,
            "historical_source_role": HISTORICAL_SOURCE_ROLE,
            "historical_source_expiry_classification": source_expiry_classification,
            "historical_source_expiry_utc": source_expiry_utc,
            "expiry_relevance": "HISTORICAL_SOURCE_ROLLBACK_ONLY",
            "target_url_configured": bool(config.get("target_url_configured")),
            "target_pooler_host_discovered": bool(
                config.get("pooler_host_configured")
            ),
            "target_connection_credential_configured": bool(
                config.get("credential_configured")
            ),
            "cutover_blocker": None,
            "final_quiesced_refresh_required": False,
            "final_cutover_authorized": True,
            "cutover_authority_consumed": True,
            "rollback_blind_url_flip_allowed": False,
            "rollback_requires_reconciliation": True,
            "cutover_closeout_receipt": CUTOVER_CLOSEOUT_RECEIPT,
            "persistence_watchdog_classification": watchdog.get("classification"),
            "database_mutation": False,
        }
    )
    return state


def historical_preflight_view(
    preflight: Mapping[str, Any],
    *,
    cutover_complete: bool,
) -> dict[str, Any]:
    result = dict(preflight)
    if cutover_complete:
        result["operational_relevance"] = "HISTORICAL_PRE_CUTOVER_RECEIPT_ONLY"
        result["superseded_by"] = "RADAR_PERSISTENCE_WATCHDOG_V0.1"
        result["cutover_complete"] = True
    else:
        result["operational_relevance"] = "ACTIVE_PRE_CUTOVER_GATE"
    return result
