from __future__ import annotations

import os
from typing import Any, Callable

try:
    import psycopg  # type: ignore
except Exception:  # pragma: no cover
    psycopg = None

PROJECT_REF = "jqzdvgjeuveiktftyrlz"
PROJECT_REGION = "eu-central-1"
RUNTIME_ROLE = "radar_runtime"
SESSION_PORT = 5432
EXPECTED_EVENTS = 1032
EXPECTED_KEYS = 954
EXPECTED_CHAIN_HEAD = "f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd"
DEFAULT_INDICES = tuple(range(0, 10))


class SupabasePoolerProbeError(RuntimeError):
    pass


def _indices_from_env(raw: str | None) -> tuple[int, ...]:
    if raw is None or not raw.strip():
        return DEFAULT_INDICES
    out: list[int] = []
    for token in raw.split(","):
        value = int(token.strip())
        if value < 0 or value > 99:
            raise ValueError("pooler index must be between 0 and 99")
        if value not in out:
            out.append(value)
    if not out:
        raise ValueError("at least one pooler index is required")
    return tuple(out)


def _sanitized_error(exc: BaseException) -> str:
    text = str(exc).replace("\n", " ").strip()
    if len(text) > 240:
        text = text[:240] + "..."
    return f"{type(exc).__name__}:{text}"


def probe_one(
    *,
    host: str,
    password: str,
    connect_fn: Callable[..., Any] | None = None,
    timeout: int = 4,
) -> dict[str, Any]:
    if not password:
        raise SupabasePoolerProbeError("password is required")
    if connect_fn is None:
        if psycopg is None:
            raise SupabasePoolerProbeError("psycopg unavailable")
        connect_fn = psycopg.connect

    username = f"{RUNTIME_ROLE}.{PROJECT_REF}"
    result: dict[str, Any] = {
        "host": host,
        "port": SESSION_PORT,
        "mode": "SUPAVISOR_SESSION",
        "ssl_required": True,
        "database_mutation": False,
        "secret_value_exposed": False,
    }
    try:
        with connect_fn(
            host=host,
            port=SESSION_PORT,
            dbname="postgres",
            user=username,
            password=password,
            sslmode="require",
            connect_timeout=timeout,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(
                    "SELECT count(*), min(id), max(id), "
                    "(SELECT chain_sha256 FROM radar_events ORDER BY id DESC LIMIT 1) "
                    "FROM radar_events"
                )
                event_count, min_id, max_id, chain_head = cur.fetchone()
                cur.execute("SELECT count(*) FROM radar_event_keys")
                key_count = cur.fetchone()[0]

        exact = (
            int(event_count) == EXPECTED_EVENTS
            and int(key_count) == EXPECTED_KEYS
            and int(min_id) == 1
            and int(max_id) == EXPECTED_EVENTS
            and str(chain_head) == EXPECTED_CHAIN_HEAD
        )
        result.update(
            {
                "status": "EXACT_TARGET_MATCH" if exact else "REACHABLE_NOT_EQUIVALENT",
                "event_count": int(event_count),
                "key_count": int(key_count),
                "min_event_id": int(min_id),
                "max_event_id": int(max_id),
                "chain_head_matches": str(chain_head) == EXPECTED_CHAIN_HEAD,
                "accepted": exact,
            }
        )
        return result
    except Exception as exc:
        result.update(
            {
                "status": "CONNECT_FAIL",
                "accepted": False,
                "error": _sanitized_error(exc),
            }
        )
        return result


def discover_session_pooler(
    *,
    password: str,
    indices: tuple[int, ...] = DEFAULT_INDICES,
    connect_fn: Callable[..., Any] | None = None,
    timeout: int = 4,
) -> dict[str, Any]:
    results = []
    accepted = []
    for index in indices:
        host = f"aws-{index}-{PROJECT_REGION}.pooler.supabase.com"
        item = probe_one(
            host=host,
            password=password,
            connect_fn=connect_fn,
            timeout=timeout,
        )
        results.append(item)
        if item.get("accepted") is True:
            accepted.append(host)

    if len(accepted) == 1:
        classification = "EXACT_SESSION_POOLER_DISCOVERED"
        selected_host = accepted[0]
    elif len(accepted) == 0:
        classification = "NO_EXACT_SESSION_POOLER_DISCOVERED"
        selected_host = None
    else:
        classification = "AMBIGUOUS_MULTIPLE_EXACT_SESSION_POOLERS"
        selected_host = None

    return {
        "classification": classification,
        "project_ref": PROJECT_REF,
        "runtime_role": RUNTIME_ROLE,
        "region": PROJECT_REGION,
        "session_port": SESSION_PORT,
        "selected_host": selected_host,
        "tested_indices": list(indices),
        "results": results,
        "database_mutation": False,
        "secret_value_exposed": False,
        "final_cutover_authorized": False,
    }


def probe_from_env() -> dict[str, Any]:
    password = os.getenv("RADAR_SUPABASE_POOLER_PASSWORD", "")
    indices = _indices_from_env(os.getenv("RADAR_SUPABASE_POOLER_INDICES"))
    timeout = int(os.getenv("RADAR_SUPABASE_POOLER_TIMEOUT_SECONDS", "4"))
    if timeout < 1 or timeout > 15:
        raise ValueError("RADAR_SUPABASE_POOLER_TIMEOUT_SECONDS must be 1..15")
    return discover_session_pooler(
        password=password,
        indices=indices,
        timeout=timeout,
    )
