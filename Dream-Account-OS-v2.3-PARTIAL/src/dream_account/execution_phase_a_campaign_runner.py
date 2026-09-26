from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .execution_phase_a_campaign import summarize_journal
from .execution_shadow_rehearsal import (
    OBSERVATION_JOURNAL_ENV,
    SHADOW_REHEARSAL_ENABLE_ENV,
    ShadowProposalBlocked,
    run_shadow_rehearsal,
)


def validate_persistent_journal_path(value: str) -> Path:
    if not value or not value.strip():
        raise ValueError("persistent journal path is required")
    if value.strip() == ":memory:":
        raise ValueError("in-memory SQLite is not permitted for Phase A campaign evidence")
    path = Path(value).expanduser().resolve()
    if path.exists() and path.is_dir():
        raise ValueError("journal path must be a file, not a directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_one_local_campaign_cycle(journal_path: str) -> dict[str, object]:
    path = validate_persistent_journal_path(journal_path)
    if os.getenv(SHADOW_REHEARSAL_ENABLE_ENV) != "1":
        raise ShadowProposalBlocked(
            f"set {SHADOW_REHEARSAL_ENABLE_ENV}=1 explicitly before running a Phase A local cycle"
        )

    previous = os.getenv(OBSERVATION_JOURNAL_ENV)
    os.environ[OBSERVATION_JOURNAL_ENV] = str(path)
    try:
        report = run_shadow_rehearsal()
        campaign = summarize_journal(str(path))
    finally:
        if previous is None:
            os.environ.pop(OBSERVATION_JOURNAL_ENV, None)
        else:
            os.environ[OBSERVATION_JOURNAL_ENV] = previous

    return {
        "runner_mode": "LOCAL_ONE_SHOT",
        "journal_path": str(path),
        "shadow_rehearsal": report.sanitized_dict(),
        "campaign": campaign.sanitized_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run exactly one Gate K Phase A real-market shadow observation into a persistent local SQLite journal."
    )
    parser.add_argument("--journal", required=True, help="Persistent local SQLite journal path")
    parser.add_argument("--output", help="Optional sanitized JSON receipt path")
    args = parser.parse_args()

    try:
        result = run_one_local_campaign_cycle(args.journal)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 2

    encoded = json.dumps(result, sort_keys=True, indent=2)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)

    rehearsal_status = str(result["shadow_rehearsal"]["status"])
    campaign_status = str(result["campaign"]["status"])
    if rehearsal_status.startswith("BLOCKED") or campaign_status == "BLOCKED":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
