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
    expected_events: int,
    expected_keys: int,
    expected_chain_head: str,
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
            int(event_count) == int(expected_events)
            and int(key_count) == int(expected_keys)
            and int(min_id) == 1
            and int(max_id) == int(expected_events)
            and str(chain_head) == str(expected_chain_head)
        )
        result.update(
            {
                "status": "EXACT_TARGET_MATCH" if exact else "REACHABLE_NOT_EQUIVALENT",
                "event_count": int(event_count),
                "key_count": int(key_count),
                "min_event_id": int(min_id),
                "max_event_id": int(max_id),
                "chain_head_matches": str(chain_head) == str(expected_chain_head),
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
    expected_events: int,
    expected_keys: int,
    expected_chain_head: str,
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
            expected_events=expected_events,
            expected_keys=expected_keys,
            expected_chain_head=expected_chain_head,
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
        "expected_identity": {
            "event_count": int(expected_events),
            "key_count": int(expected_keys),
            "chain_head_sha256": str(expected_chain_head),
        },
        "results": results,
        "database_mutation": False,
        "secret_value_exposed": False,
        "final_cutover_authorized": False,
    }


def _required_int_env(name: str) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        raise SupabasePoolerProbeError(f"{name} is required")
    value = int(raw)
    if value < 0:
        raise SupabasePoolerProbeError(f"{name} must be non-negative")
    return value


def _required_chain_head_env() -> str:
    raw = os.getenv("RADAR_SUPABASE_POOLER_EXPECTED_CHAIN_HEAD")
    if raw is None or not raw.strip():
        raise SupabasePoolerProbeError(
            "RADAR_SUPABASE_POOLER_EXPECTED_CHAIN_HEAD is required"
        )
    value = raw.strip().lower()
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise SupabasePoolerProbeError(
            "RADAR_SUPABASE_POOLER_EXPECTED_CHAIN_HEAD must be 64 hex chars"
        )
    return value


def probe_from_env() -> dict[str, Any]:
    password = os.getenv("RADAR_SUPABASE_POOLER_PASSWORD", "")
    expected_events = _required_int_env(
        "RADAR_SUPABASE_POOLER_EXPECTED_EVENTS"
    )
    expected_keys = _required_int_env(
        "RADAR_SUPABASE_POOLER_EXPECTED_KEYS"
    )
    expected_chain_head = _required_chain_head_env()
    indices = _indices_from_env(os.getenv("RADAR_SUPABASE_POOLER_INDICES"))
    timeout = int(os.getenv("RADAR_SUPABASE_POOLER_TIMEOUT_SECONDS", "4"))
    if timeout < 1 or timeout > 15:
        raise ValueError("RADAR_SUPABASE_POOLER_TIMEOUT_SECONDS must be 1..15")
    return discover_session_pooler(
        password=password,
        expected_events=expected_events,
        expected_keys=expected_keys,
        expected_chain_head=expected_chain_head,
        indices=indices,
        timeout=timeout,
    )
