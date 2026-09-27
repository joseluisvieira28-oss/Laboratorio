# MRCR H02 — Trigger-A Finalizer Runbook V0.2
Status: PRE-TARGET / TARGET LOCKED
Date: 2026-09-27

## Normal path

The official calendar watcher checks only BLS and Federal Reserve sources.

While annual_plan_trigger_ready_v02=false:

- do not build the final annual plan;
- do not freeze the final protocol;
- do not request TARGET_OBSERVATION_OPEN.

When annual_plan_trigger_ready_v02=true, the watcher runs
trigger_a_finalizer_v02.py automatically in the workflow and uploads a
target-locked artifact package.

## Manual equivalent

From a repository checkout at the exact commit to freeze:

```bash
BASE="Dream-Account-OS-v2.3-PARTIAL/research/market_reveal_confirmation_reaction_v01"
HEAD="$(git rev-parse HEAD)"
FREEZE_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

python "$BASE/trigger_a_finalizer_v02.py" \
  --implementation-head-sha "$HEAD" \
  --output-dir ./mrcr_trigger_a_v02 \
  --protocol-frozen-at-utc "$FREEZE_AT"
```

The CLI fails closed if the supplied implementation SHA differs from the actual
checked-out Git HEAD.

## Expected successful package

- MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01.json
- MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json
- MRCR_IMPLEMENTATION_MANIFEST_TRIGGER_A_V02.json
- MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json
- MRCR_TRIGGER_A_FINALIZER_RECEIPT_V02.json

Expected receipt status:

`PASS_TARGET_LOCKED_PROTOCOL_FROZEN`

Expected protocol status:

`FROZEN_PRETARGET_PROTOCOL__TARGET_LOCKED`

Required booleans remain false:

- target_observation_authorized
- outcomes_authorized
- orders_enabled
- live_trading_authorized

## Blocked result

When the official annual plan is incomplete:

`BLOCKED_OFFICIAL_ANNUAL_PLAN_NOT_READY`

Only the live-status receipt and blocked finalizer receipt may be produced.

## After successful Trigger A

STOP.

A separate explicit TARGET_OBSERVATION_OPEN authority is required. The
finalizer cannot issue it.

No outcome access or promotion credit is created by Trigger A.
