from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .execution_journal import ExecutionJournal
from .execution_shadow_rehearsal import PhaseAObservation, aggregate_phase_a_observations

DEFAULT_MIN_SUCCESSFUL_CYCLES = 100
DEFAULT_MIN_CALENDAR_DAYS = 7


@dataclass(frozen=True)
class CampaignSummary:
    status: str
    attempted_cycles: int
    successful_cycles: int
    blocked_cycles: int
    calendar_days_observed: int
    first_observed_at_utc: str | None
    last_observed_at_utc: str | None
    aggregate_metrics: dict[str, object]
    blocking_reasons: tuple[str, ...]
    remaining_successful_cycles: int
    remaining_calendar_days: int
    fingerprint: str

    def sanitized_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "attempted_cycles": self.attempted_cycles,
            "successful_cycles": self.successful_cycles,
            "blocked_cycles": self.blocked_cycles,
            "calendar_days_observed": self.calendar_days_observed,
            "first_observed_at_utc": self.first_observed_at_utc,
            "last_observed_at_utc": self.last_observed_at_utc,
            "aggregate_metrics": self.aggregate_metrics,
            "blocking_reasons": list(self.blocking_reasons),
            "remaining_successful_cycles": self.remaining_successful_cycles,
            "remaining_calendar_days": self.remaining_calendar_days,
            "fingerprint": self.fingerprint,
        }


def _canonical_fingerprint(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normalize(record: PhaseAObservation | dict[str, object]) -> dict[str, object]:
    if isinstance(record, PhaseAObservation):
        return record.sanitized_dict()
    return dict(record)


def _parse_utc(value: str) -> datetime:
    observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if observed.tzinfo is None:
        raise ValueError("observed_at_utc must be timezone-aware")
    return observed.astimezone(timezone.utc)


def _blocking_reasons(rows: list[dict[str, object]]) -> tuple[str, ...]:
    reasons: set[str] = set()
    for row in rows:
        if row.get("status") == "BLOCKED":
            reasons.add("blocked_observation_present")
        if row.get("exchange_mutation_routes") != 0:
            reasons.add("exchange_mutation_route_present")
        if row.get("submitted_to_exchange") is not False:
            reasons.add("exchange_submission_claim_present")
        if row.get("live_trade_proposals_created") != 0:
            reasons.add("live_trade_proposal_present")
        if row.get("reconciliation_status") != "PASS_CLEAN":
            reasons.add("reconciliation_not_clean")
        if (row.get("reconciliation_daos_open_orders") or 0) != 0:
            reasons.add("unexpected_daos_open_order_activity")
        if (row.get("reconciliation_daos_recent_trades") or 0) != 0:
            reasons.add("unexpected_daos_recent_trade_activity")
    return tuple(sorted(reasons))


def summarize_campaign(
    records: Iterable[PhaseAObservation | dict[str, object]],
    *,
    min_successful_cycles: int = DEFAULT_MIN_SUCCESSFUL_CYCLES,
    min_calendar_days: int = DEFAULT_MIN_CALENDAR_DAYS,
) -> CampaignSummary:
    if min_successful_cycles <= 0 or min_calendar_days <= 0:
        raise ValueError("campaign evidence thresholds must be positive")

    rows = [_normalize(row) for row in records]
    rows.sort(key=lambda row: (str(row.get("observed_at_utc", "")), str(row.get("observation_id", ""))))

    timestamps = [_parse_utc(str(row["observed_at_utc"])) for row in rows]
    days = {stamp.date().isoformat() for stamp in timestamps}
    successful = sum(row.get("status") == "PASS" for row in rows)
    blocked = sum(row.get("status") == "BLOCKED" for row in rows)
    reasons = _blocking_reasons(rows)

    if reasons:
        status = "BLOCKED"
    elif successful >= min_successful_cycles and len(days) >= min_calendar_days:
        status = "PASS"
    else:
        status = "INSUFFICIENT_EVIDENCE"

    aggregate = aggregate_phase_a_observations(rows)
    payload_without_fingerprint: dict[str, object] = {
        "status": status,
        "attempted_cycles": len(rows),
        "successful_cycles": successful,
        "blocked_cycles": blocked,
        "calendar_days_observed": len(days),
        "first_observed_at_utc": timestamps[0].isoformat() if timestamps else None,
        "last_observed_at_utc": timestamps[-1].isoformat() if timestamps else None,
        "aggregate_metrics": aggregate,
        "blocking_reasons": list(reasons),
        "remaining_successful_cycles": max(0, min_successful_cycles - successful),
        "remaining_calendar_days": max(0, min_calendar_days - len(days)),
    }
    return CampaignSummary(
        status=status,
        attempted_cycles=len(rows),
        successful_cycles=successful,
        blocked_cycles=blocked,
        calendar_days_observed=len(days),
        first_observed_at_utc=payload_without_fingerprint["first_observed_at_utc"],
        last_observed_at_utc=payload_without_fingerprint["last_observed_at_utc"],
        aggregate_metrics=aggregate,
        blocking_reasons=reasons,
        remaining_successful_cycles=int(payload_without_fingerprint["remaining_successful_cycles"]),
        remaining_calendar_days=int(payload_without_fingerprint["remaining_calendar_days"]),
        fingerprint=_canonical_fingerprint(payload_without_fingerprint),
    )


def record_and_summarize_cycle(
    journal: ExecutionJournal,
    observation: PhaseAObservation,
    *,
    min_successful_cycles: int = DEFAULT_MIN_SUCCESSFUL_CYCLES,
    min_calendar_days: int = DEFAULT_MIN_CALENDAR_DAYS,
) -> CampaignSummary:
    payload = observation.sanitized_dict()
    journal.record_phase_a_observation(observation.observation_id, observation.fingerprint(), payload)
    return summarize_campaign(
        journal.phase_a_observations(),
        min_successful_cycles=min_successful_cycles,
        min_calendar_days=min_calendar_days,
    )


def summarize_journal(
    journal_path: str,
    *,
    min_successful_cycles: int = DEFAULT_MIN_SUCCESSFUL_CYCLES,
    min_calendar_days: int = DEFAULT_MIN_CALENDAR_DAYS,
) -> CampaignSummary:
    journal = ExecutionJournal(journal_path)
    try:
        integrity = journal.integrity_check()
        if integrity != ["ok"]:
            raise RuntimeError("campaign journal integrity check failed")
        return summarize_campaign(
            journal.phase_a_observations(),
            min_successful_cycles=min_successful_cycles,
            min_calendar_days=min_calendar_days,
        )
    finally:
        journal.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Gate K Phase A observation campaign evidence.")
    parser.add_argument("--journal", required=True, help="Path to persistent Phase A SQLite journal")
    parser.add_argument("--min-successful-cycles", type=int, default=DEFAULT_MIN_SUCCESSFUL_CYCLES)
    parser.add_argument("--min-calendar-days", type=int, default=DEFAULT_MIN_CALENDAR_DAYS)
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    summary = summarize_journal(
        args.journal,
        min_successful_cycles=args.min_successful_cycles,
        min_calendar_days=args.min_calendar_days,
    )
    encoded = json.dumps(summary.sanitized_dict(), sort_keys=True, indent=2)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 2 if summary.status == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
