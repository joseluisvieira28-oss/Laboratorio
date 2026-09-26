# CIRV Prospective Forward Operations V0.2

Status: ARMED — prospective observation only.

Scientific model remains frozen by FORWARD_PREFREEZE_V0.1.json. This operations layer changes no model parameter, asset, sampling interval, HAR lag, weekday dummy, rolling window, metric, or promotion threshold.

## Boundary
- Freeze date: 2026-09-20 UTC
- First eligible target: 2026-09-21 UTC
- Scheduled generation: 00:25 UTC after the previous UTC day is complete.
- Any target before 2026-09-21 is fail-closed.

## Evidence
Each successful target creates a GitHub Actions artifact named with target date and workflow run ID. Artifacts are retained for 90 days. Source digest is produced by the frozen watcher.

## Recovery rule
If a scheduled run fails or is missed, do not backfill after target-day outcome information is available and call it prospective. Record it as MISSED_FORWARD_TARGET. A manual workflow run is valid only while the target outcome remains unopened and the frozen temporal rule is satisfied.

## Safety
Research only. No trading, PnL authorization, exchange mutation, wallet access, parameter tuning, or merge to main.
