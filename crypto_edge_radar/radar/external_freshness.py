from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import time
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree


API = "https://api.github.com/repos/joseluisvieira28-oss/Laboratorio/actions/runs"
DH03_SAFE_PROGRESS_URL = (
    "https://raw.githubusercontent.com/joseluisvieira28-oss/Laboratorio/"
    "htf-dh03-12h-standalone-forward-v0.1/crypto_edge_radar/DH03_SAFE_PROGRESS.json"
)
DH03_SAFE_PROGRESS_SCHEMA = "DH03_SAFE_PROGRESS_V0.1"
DH03_SAFE_PROGRESS_COUNTS = (
    "signals",
    "price_exits",
    "final_resolutions",
    "funding_pending",
    "unresolved_price_paths",
    "overlap_skipped",
)
_API_COOLDOWN_UNTIL_EPOCH = 0.0
COLLECTORS = {
    "HTF-DH03-12H-STANDALONE-FORWARD-V1": {
        "branch": "htf-dh03-12h-standalone-forward-v0.1",
        "workflow": ".github/workflows/htf-dh03-12h-forward-shadow.yml",
        "forward_boundary": "2026-09-18T00:00:00Z",
    },
    "CED1D-0031": {
        "branch": "ced-1d-v3-byte-recovery-2026-09-17",
        "workflow": ".github/workflows/ced1d-0031-prospective-shadow-collector.yml",
        "forward_boundary": "2026-09-19T00:00:00Z",
        "superseded_by": "RENDER_SHADOW_V0.3",
        "superseded_at_utc": "2026-09-22T07:25:00Z",
        "new_forward_boundary": "2026-09-22T00:00:00Z",
    },
}


class ExternalFreshnessError(RuntimeError):
    pass


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _classification(*, conclusion: str | None, delay_seconds: float) -> str:
    if conclusion not in {"success", None}:
        return "FAIL_CLOSED"
    if delay_seconds <= 30 * 3600:
        return "FRESH"
    if delay_seconds <= 48 * 3600:
        return "DELAYED"
    return "STALE"


def fetch_runs(*, branch: str, timeout: int = 15) -> list[dict[str, Any]]:
    global _API_COOLDOWN_UNTIL_EPOCH
    if time.time() < _API_COOLDOWN_UNTIL_EPOCH:
        raise ExternalFreshnessError("GitHub public runs API in rate-limit cooldown")
    url = API + "?" + urlencode({"branch": branch, "per_page": 30})
    request = Request(url, headers={"User-Agent": "crypto-edge-radar-external-freshness/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in {403, 429}:
            reset = exc.headers.get("X-RateLimit-Reset") if exc.headers else None
            try:
                reset_epoch = float(reset) if reset else time.time() + 3600.0
            except (TypeError, ValueError):
                reset_epoch = time.time() + 3600.0
            _API_COOLDOWN_UNTIL_EPOCH = max(time.time() + 300.0, reset_epoch + 5.0)
        raise ExternalFreshnessError(f"GitHub public runs unavailable:{type(exc).__name__}:{exc}") from exc
    except Exception as exc:
        raise ExternalFreshnessError(f"GitHub public runs unavailable:{type(exc).__name__}:{exc}") from exc
    runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
    if not isinstance(runs, list):
        raise ExternalFreshnessError("GitHub public runs payload missing workflow_runs")
    return runs


def _safe_nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ExternalFreshnessError(f"DH03 safe progress invalid boolean count:{name}")
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise ExternalFreshnessError(f"DH03 safe progress invalid count:{name}") from exc
    if out < 0:
        raise ExternalFreshnessError(f"DH03 safe progress negative count:{name}")
    return out


def validate_dh03_safe_progress(
    payload: dict[str, Any],
    *,
    expected_run_id: int,
) -> dict[str, Any]:
    if payload.get("schema_version") != DH03_SAFE_PROGRESS_SCHEMA:
        raise ExternalFreshnessError("DH03 safe progress schema mismatch")
    if payload.get("strategy_id") != "HTF-DH03-12H-STANDALONE-FORWARD-V1":
        raise ExternalFreshnessError("DH03 safe progress strategy mismatch")

    run_id = _safe_nonnegative_int(
        payload.get("source_workflow_run_id"),
        "source_workflow_run_id",
    )
    if run_id != int(expected_run_id):
        raise ExternalFreshnessError(
            f"DH03 safe progress run mismatch:{run_id}:{int(expected_run_id)}"
        )

    for key in (
        "outcomes_included",
        "prices_included",
        "returns_included",
        "r_multiples_included",
        "profit_factor_included",
        "trade_rows_included",
        "symbol_breakdown_included",
        "science_changed",
        "authenticated_exchange_api_used",
        "orders_created",
        "exchange_mutation_performed",
        "live_capital_enabled",
    ):
        if payload.get(key) is not False:
            raise ExternalFreshnessError(
                f"DH03 safe progress firewall field not false:{key}"
            )

    counts = payload.get("counts")
    if not isinstance(counts, dict):
        raise ExternalFreshnessError("DH03 safe progress counts missing")
    if set(counts) != set(DH03_SAFE_PROGRESS_COUNTS):
        raise ExternalFreshnessError("DH03 safe progress count keys mismatch")
    normalized_counts = {
        key: _safe_nonnegative_int(counts.get(key), key)
        for key in DH03_SAFE_PROGRESS_COUNTS
    }

    allowed_top = {
        "schema_version",
        "strategy_id",
        "source_workflow_run_id",
        "checked_at_utc",
        "latest_archive_day",
        "collector_status",
        "used_as_forward_evidence",
        "counts",
        "outcomes_included",
        "prices_included",
        "returns_included",
        "r_multiples_included",
        "profit_factor_included",
        "trade_rows_included",
        "symbol_breakdown_included",
        "science_changed",
        "authenticated_exchange_api_used",
        "orders_created",
        "exchange_mutation_performed",
        "live_capital_enabled",
    }
    extras = sorted(set(payload) - allowed_top)
    if extras:
        raise ExternalFreshnessError(
            f"DH03 safe progress unexpected fields:{extras}"
        )

    out = dict(payload)
    out["source_workflow_run_id"] = run_id
    out["counts"] = normalized_counts
    return out


def fetch_dh03_safe_progress(
    *,
    expected_run_id: int,
    timeout: int = 15,
) -> dict[str, Any]:
    request = Request(
        DH03_SAFE_PROGRESS_URL,
        headers={"User-Agent": "crypto-edge-radar-dh03-safe-progress/1"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise ExternalFreshnessError(
            f"DH03 safe progress unavailable:{type(exc).__name__}:{exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ExternalFreshnessError("DH03 safe progress payload not object")
    return validate_dh03_safe_progress(
        payload,
        expected_run_id=expected_run_id,
    )


def fetch_public_fallback(*, branch: str, workflow: str, timeout: int = 15) -> dict[str, Any]:
    """Use public, non-API GitHub surfaces when the unauthenticated API is rate-limited.

    A workflow badge proves the latest branch workflow status and the dedicated
    branch Atom feed supplies a conservative activity timestamp.  This is
    telemetry only: no candidate outcomes or artifacts are read.
    """
    workflow_name = workflow.rsplit("/", 1)[-1]
    badge_url = (
        f"https://github.com/joseluisvieira28-oss/Laboratorio/actions/workflows/"
        f"{workflow_name}/badge.svg?branch={branch}"
    )
    feed_url = f"https://github.com/joseluisvieira28-oss/Laboratorio/commits/{branch}.atom"
    request_headers = {"User-Agent": "crypto-edge-radar-external-freshness/1"}
    try:
        with urlopen(Request(badge_url, headers=request_headers), timeout=timeout) as response:
            badge = response.read().decode("utf-8", errors="replace").lower()
        with urlopen(Request(feed_url, headers=request_headers), timeout=timeout) as response:
            feed = response.read()
        root = ElementTree.fromstring(feed)
        updated = root.findtext("{http://www.w3.org/2005/Atom}updated")
    except Exception as exc:
        raise ExternalFreshnessError(f"GitHub public fallback unavailable:{type(exc).__name__}:{exc}") from exc
    if not updated:
        raise ExternalFreshnessError("GitHub public fallback feed missing updated timestamp")
    success = "passing" in badge
    return {
        "created_at": updated,
        "updated_at": updated,
        "conclusion": "success" if success else "failure",
        "source_status": "GITHUB_PUBLIC_BADGE_AND_BRANCH_ATOM_FALLBACK",
    }


def fallback_freshness(candidate: str, *, now: datetime | None = None, row: dict[str, Any]) -> dict[str, Any]:
    config = COLLECTORS[candidate]
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    attempted = _dt(str(row["created_at"]))
    next_due = attempted + timedelta(hours=24)
    delay = max(0.0, (now - next_due).total_seconds())
    conclusion = row.get("conclusion")
    freshness = _classification(conclusion=conclusion, delay_seconds=delay)
    return {
        "strategy_id": candidate,
        "collector_status": "OK" if conclusion == "success" else "FAIL_CLOSED",
        "last_attempt_utc": _iso(attempted),
        "last_source_success_utc": _iso(attempted) if conclusion == "success" else None,
        "last_artifact_utc": None,
        "last_persisted_event_utc": None,
        "next_due_utc": _iso(next_due),
        "delay_seconds": delay,
        "freshness_classification": freshness,
        "last_workflow_run_id": None,
        "last_workflow_conclusion": conclusion,
        "forward_boundary": config["forward_boundary"],
        "eligible_event_count": None,
        "resolved_forward_count": None,
        "count_visibility": "NOT_AVAILABLE_FROM_PUBLIC_FALLBACK__NO_OUTCOMES_IMPORTED",
        "source_status": row["source_status"],
        "timestamp_semantics": "DEDICATED_BRANCH_ACTIVITY_PROXY_NOT_ARTIFACT_TIME",
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }


def collector_freshness(
    candidate: str,
    *,
    now: datetime | None = None,
    runs: list[dict[str, Any]] | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    config = COLLECTORS[candidate]
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    rows = runs if runs is not None else fetch_runs(branch=config["branch"], timeout=timeout)
    matching = [r for r in rows if r.get("path") == config["workflow"]]
    if not matching:
        raise ExternalFreshnessError(f"no workflow run found:{candidate}")
    latest = max(matching, key=lambda r: str(r.get("created_at") or ""))
    attempted = _dt(str(latest["created_at"]))
    artifact_time = _dt(str(latest.get("updated_at") or latest["created_at"]))
    next_due = attempted + timedelta(hours=24)
    delay = max(0.0, (now - next_due).total_seconds())
    conclusion = latest.get("conclusion")
    freshness = _classification(conclusion=conclusion, delay_seconds=delay)
    state = {
        "strategy_id": candidate,
        "collector_status": "OK" if conclusion == "success" else "FAIL_CLOSED",
        "last_attempt_utc": _iso(attempted),
        "last_source_success_utc": _iso(artifact_time) if conclusion == "success" else None,
        "last_artifact_utc": _iso(artifact_time) if conclusion == "success" else None,
        "last_persisted_event_utc": None,
        "next_due_utc": _iso(next_due),
        "delay_seconds": delay,
        "freshness_classification": freshness,
        "last_workflow_run_id": latest.get("id"),
        "last_workflow_conclusion": conclusion,
        "forward_boundary": config["forward_boundary"],
        "eligible_event_count": None,
        "resolved_forward_count": None,
        "count_visibility": "NOT_AVAILABLE_FROM_RUN_METADATA__NO_OUTCOMES_IMPORTED",
        "source_status": "GITHUB_PUBLIC_ACTIONS_METADATA",
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }
    if (
        candidate == "HTF-DH03-12H-STANDALONE-FORWARD-V1"
        and conclusion == "success"
        and latest.get("id") is not None
    ):
        try:
            safe = fetch_dh03_safe_progress(
                expected_run_id=int(latest["id"]),
                timeout=timeout,
            )
            counts = safe["counts"]
            state.update({
                "eligible_event_count": counts["signals"],
                "resolved_forward_count": counts["final_resolutions"],
                "price_exit_count": counts["price_exits"],
                "funding_pending_count": counts["funding_pending"],
                "unresolved_price_path_count": counts["unresolved_price_paths"],
                "overlap_skipped_count": counts["overlap_skipped"],
                "count_visibility": "SAFE_AGGREGATE_PROGRESS_BOUND_TO_WORKFLOW_RUN__NO_OUTCOMES_IMPORTED",
                "safe_progress_schema": safe["schema_version"],
                "safe_progress_checked_at_utc": safe.get("checked_at_utc"),
                "safe_progress_latest_archive_day": safe.get("latest_archive_day"),
                "safe_progress_outcomes_imported": False,
            })
        except Exception as exc:
            state["count_visibility"] = (
                "SAFE_PROGRESS_UNAVAILABLE_FAIL_CLOSED__NO_OUTCOMES_IMPORTED"
            )
            state["safe_progress_error"] = f"{type(exc).__name__}:{exc}"
    return state


def all_external_freshness(*, now: datetime | None = None, timeout: int = 15) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for candidate, config in COLLECTORS.items():
        if config.get("superseded_by"):
            out[candidate] = {
                "strategy_id": candidate,
                "collector_status": "SUPERSEDED",
                "freshness_classification": "SUPERSEDED",
                "source_status": "HISTORICAL_GITHUB_ROUTE_SUPERSEDED",
                "forward_boundary": config["forward_boundary"],
                "superseded_by": config["superseded_by"],
                "superseded_at_utc": config["superseded_at_utc"],
                "new_forward_boundary": config["new_forward_boundary"],
                "authenticated_exchange_api_used": False,
                "orders_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            }
            continue
        try:
            rows = fetch_runs(branch=config["branch"], timeout=timeout)
            out[candidate] = collector_freshness(candidate, now=now, runs=rows, timeout=timeout)
        except Exception as primary_exc:
            try:
                row = fetch_public_fallback(
                    branch=config["branch"], workflow=config["workflow"], timeout=timeout
                )
                out[candidate] = fallback_freshness(candidate, now=now, row=row)
                out[candidate]["primary_source_error"] = f"{type(primary_exc).__name__}:{primary_exc}"
            except Exception as fallback_exc:
                out[candidate] = {
                    "strategy_id": candidate,
                    "collector_status": "FAIL_CLOSED",
                    "freshness_classification": "FAIL_CLOSED",
                    "source_status": "GITHUB_PUBLIC_METADATA_AND_FALLBACK_UNAVAILABLE",
                    "error": f"primary={type(primary_exc).__name__}:{primary_exc};fallback={type(fallback_exc).__name__}:{fallback_exc}",
                    "forward_boundary": config["forward_boundary"],
                    "authenticated_exchange_api_used": False,
                    "orders_created": False,
                    "exchange_mutation_performed": False,
                    "live_capital_enabled": False,
                }
    return out
