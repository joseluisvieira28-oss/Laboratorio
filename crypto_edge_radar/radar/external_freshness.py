from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API = "https://api.github.com/repos/joseluisvieira28-oss/Laboratorio/actions/runs"
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
    url = API + "?" + urlencode({"branch": branch, "per_page": 30})
    request = Request(url, headers={"User-Agent": "crypto-edge-radar-external-freshness/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise ExternalFreshnessError(f"GitHub public runs unavailable:{type(exc).__name__}:{exc}") from exc
    runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
    if not isinstance(runs, list):
        raise ExternalFreshnessError("GitHub public runs payload missing workflow_runs")
    return runs


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
    return {
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


def all_external_freshness(*, now: datetime | None = None, timeout: int = 15) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for candidate, config in COLLECTORS.items():
        try:
            rows = fetch_runs(branch=config["branch"], timeout=timeout)
            out[candidate] = collector_freshness(candidate, now=now, runs=rows, timeout=timeout)
        except Exception as exc:
            out[candidate] = {
                "strategy_id": candidate,
                "collector_status": "FAIL_CLOSED",
                "freshness_classification": "FAIL_CLOSED",
                "source_status": "GITHUB_PUBLIC_ACTIONS_METADATA_UNAVAILABLE",
                "error": f"{type(exc).__name__}:{exc}",
                "forward_boundary": config["forward_boundary"],
                "authenticated_exchange_api_used": False,
                "orders_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            }
    return out
