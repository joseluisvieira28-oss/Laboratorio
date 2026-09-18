from __future__ import annotations

import argparse
import json
from pathlib import Path

from .execution_phase_a_campaign import summarize_journal
from .execution_phase_a_campaign_runner import validate_persistent_journal_path


def build_operational_summary(journal_path: str) -> dict[str, object]:
    path = validate_persistent_journal_path(journal_path)
    if not path.exists():
        raise FileNotFoundError(f"campaign journal does not exist: {path}")

    campaign = summarize_journal(str(path)).sanitized_dict()
    metrics = campaign.get("aggregate_metrics", {})

    safety_rate = metrics.get("SafetyIntegrityRate", {}) if isinstance(metrics, dict) else {}
    reconciliation_rate = metrics.get("ReconciliationCleanRate", {}) if isinstance(metrics, dict) else {}
    failure_rate = metrics.get("ObservationFailureRate", {}) if isinstance(metrics, dict) else {}

    return {
        "runner_mode": "LOCAL_READ_ONLY_SUMMARY",
        "journal_path": str(path),
        "campaign_status": campaign.get("status"),
        "successful_cycles": campaign.get("successful_cycles"),
        "required_successful_cycles": 100,
        "remaining_successful_cycles": campaign.get("remaining_successful_cycles"),
        "calendar_days_observed": campaign.get("calendar_days_observed"),
        "required_calendar_days": 7,
        "remaining_calendar_days": campaign.get("remaining_calendar_days"),
        "attempted_cycles": campaign.get("attempted_cycles"),
        "blocked_cycles": campaign.get("blocked_cycles"),
        "safety_integrity_rate": safety_rate.get("value") if isinstance(safety_rate, dict) else None,
        "reconciliation_clean_rate": reconciliation_rate.get("value") if isinstance(reconciliation_rate, dict) else None,
        "observation_failure_rate": failure_rate.get("value") if isinstance(failure_rate, dict) else None,
        "first_observed_at_utc": campaign.get("first_observed_at_utc"),
        "last_observed_at_utc": campaign.get("last_observed_at_utc"),
        "campaign_fingerprint": campaign.get("fingerprint"),
        "blocking_reasons": campaign.get("blocking_reasons", []),
    }


def render_text(summary: dict[str, object]) -> str:
    def rate(value: object) -> str:
        return "UNDEFINED" if value is None else f"{float(value):.3f}"

    lines = [
        "Gate K Phase A — Operational Summary",
        "====================================",
        f"Status: {summary['campaign_status']}",
        f"Successful cycles: {summary['successful_cycles']}/{summary['required_successful_cycles']}",
        f"Calendar days: {summary['calendar_days_observed']}/{summary['required_calendar_days']}",
        f"Remaining cycles: {summary['remaining_successful_cycles']}",
        f"Remaining days: {summary['remaining_calendar_days']}",
        f"Attempted cycles: {summary['attempted_cycles']}",
        f"Blocked cycles: {summary['blocked_cycles']}",
        f"Safety integrity rate: {rate(summary['safety_integrity_rate'])}",
        f"Reconciliation clean rate: {rate(summary['reconciliation_clean_rate'])}",
        f"Observation failure rate: {rate(summary['observation_failure_rate'])}",
        f"First observation UTC: {summary['first_observed_at_utc']}",
        f"Last observation UTC: {summary['last_observed_at_utc']}",
        f"Campaign fingerprint: {summary['campaign_fingerprint']}",
    ]
    reasons = summary.get("blocking_reasons") or []
    lines.append("Blocking reasons: NONE" if not reasons else "Blocking reasons: " + "; ".join(map(str, reasons)))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact read-only Gate K Phase A campaign summary.")
    parser.add_argument("--journal", required=True, help="Persistent Phase A SQLite journal path")
    parser.add_argument("--json", action="store_true", help="Print compact sanitized JSON instead of text")
    args = parser.parse_args()

    try:
        summary = build_operational_summary(args.journal)
    except Exception as exc:
        print(f"BLOCKED: {type(exc).__name__}: {exc}")
        return 2

    if args.json:
        print(json.dumps(summary, sort_keys=True, indent=2))
    else:
        print(render_text(summary))

    return 3 if summary.get("campaign_status") == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
