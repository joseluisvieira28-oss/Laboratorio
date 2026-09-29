from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Callable

from .execution_phase_a_campaign_runner import run_one_local_campaign_cycle, validate_persistent_journal_path

MIN_INTERVAL_SECONDS = 120
MAX_INTERVAL_SECONDS = 21600
MAX_CYCLES_PER_BATCH = 20


def validate_campaign_plan(cycles: int, interval_seconds: int) -> tuple[int, int]:
    if isinstance(cycles, bool) or not isinstance(cycles, int):
        raise ValueError("cycles must be an integer")
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int):
        raise ValueError("interval_seconds must be an integer")
    if cycles < 1 or cycles > MAX_CYCLES_PER_BATCH:
        raise ValueError(f"cycles must be between 1 and {MAX_CYCLES_PER_BATCH}")
    if interval_seconds < MIN_INTERVAL_SECONDS or interval_seconds > MAX_INTERVAL_SECONDS:
        raise ValueError(
            f"interval_seconds must be between {MIN_INTERVAL_SECONDS} and {MAX_INTERVAL_SECONDS}"
        )
    return cycles, interval_seconds


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run_campaign_batch(
    journal_path: str,
    *,
    cycles: int,
    interval_seconds: int,
    latest_cycle_output: str | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    journal = validate_persistent_journal_path(journal_path)
    cycles, interval_seconds = validate_campaign_plan(cycles, interval_seconds)
    latest_path = Path(latest_cycle_output).expanduser().resolve() if latest_cycle_output else None

    completed = 0
    last_result: dict[str, object] | None = None

    for index in range(cycles):
        result = run_one_local_campaign_cycle(str(journal))
        completed += 1
        last_result = result

        if latest_path is not None:
            _write_json(latest_path, result)

        rehearsal_status = str(result["shadow_rehearsal"]["status"])
        campaign_status = str(result["campaign"]["status"])
        if rehearsal_status.startswith("BLOCKED") or campaign_status == "BLOCKED":
            break

        if index + 1 < cycles:
            sleep_fn(interval_seconds)

    campaign = last_result["campaign"] if last_result else None
    return {
        "runner_mode": "LOCAL_CONTROLLED_BATCH",
        "requested_cycles": cycles,
        "completed_cycles_this_batch": completed,
        "interval_seconds": interval_seconds,
        "journal_path": str(journal),
        "last_campaign_summary": campaign,
        "stopped_early": completed < cycles,
        "safety_note": "This batch runner only reuses the existing one-shot SHADOW / READ-ONLY Phase A runner. It contains no exchange mutation route and performs no trading.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a bounded Gate K Phase A local observation batch using the existing one-shot SHADOW / READ-ONLY runner."
    )
    parser.add_argument("--journal", required=True, help="Persistent local SQLite journal path")
    parser.add_argument("--cycles", required=True, type=int, help=f"Cycles in this batch (1-{MAX_CYCLES_PER_BATCH})")
    parser.add_argument(
        "--interval-seconds",
        required=True,
        type=int,
        help=f"Delay between cycles ({MIN_INTERVAL_SECONDS}-{MAX_INTERVAL_SECONDS} seconds)",
    )
    parser.add_argument("--latest-cycle-output", help="Optional sanitized JSON receipt for the latest completed cycle")
    parser.add_argument("--output", help="Optional sanitized JSON receipt for the batch summary")
    args = parser.parse_args()

    try:
        result = run_campaign_batch(
            args.journal,
            cycles=args.cycles,
            interval_seconds=args.interval_seconds,
            latest_cycle_output=args.latest_cycle_output,
        )
    except KeyboardInterrupt:
        print(json.dumps({"status": "INTERRUPTED", "reason": "operator interrupt"}, sort_keys=True))
        return 130
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 2

    encoded = json.dumps(result, sort_keys=True, indent=2)
    if args.output:
        _write_json(Path(args.output).expanduser().resolve(), result)
    print(encoded)

    summary = result.get("last_campaign_summary")
    if isinstance(summary, dict) and str(summary.get("status")) == "BLOCKED":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
