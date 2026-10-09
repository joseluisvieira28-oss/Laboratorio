# MRCR H02 — Trigger-A Finalizer Contract V0.2
Status: CANONICAL PRE-TARGET ORCHESTRATION / TARGET LOCKED
Date: 2026-09-27

## Purpose

Turn a READY official 2027 calendar status into the complete frozen pre-target
package in one deterministic orchestration path.

Pipeline:

1. official_2027_calendar_live_probe;
2. annual_plan_builder_v02;
3. annual plan SHA-256;
4. implementation manifest from IMPLEMENTATION_FREEZE_FILESET_V01;
5. final_binding_preflight_v02;
6. frozen target-locked protocol V0.2;
7. Trigger-A finalizer receipt.

## READY requirement

The finalizer advances only when the live status is
READY_FOR_V02_ANNUAL_PLAN and annual_plan_trigger_ready_v02=true.

Otherwise it writes only:

- the live source-status receipt;
- a BLOCKED finalizer receipt.

It must not create an annual plan, implementation manifest or protocol while the
official annual plan is incomplete.

## Provenance

The annual plan binds:

- official source URLs;
- retrieval timestamp;
- SHA-256 of the extracted official source text;
- 12 CPI dates;
- 12 Employment Situation dates;
- 8 FOMC meeting dates.

The implementation manifest binds the exact canonical fileset and Git commit
SHA used by the finalizer.

## Successful output package

A successful Trigger-A package contains:

- MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01.json
- MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json
- MRCR_IMPLEMENTATION_MANIFEST_TRIGGER_A_V02.json
- MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json
- MRCR_TRIGGER_A_FINALIZER_RECEIPT_V02.json

The package is valid only when the finalizer receipt says
PASS_TARGET_LOCKED_PROTOCOL_FROZEN and all embedded hashes validate.

## Hard stop

The finalizer MUST NOT:

- issue TARGET_OBSERVATION_OPEN;
- set protocol target_observation_authorized=true;
- activate an event;
- start market-data target capture;
- inspect outcomes;
- compute trading signals;
- submit orders;
- mutate an exchange;
- merge main.

Success means only:

READY_FOR_SEPARATE_TARGET_OPEN_AUTHORITY.

## GitHub watcher behavior

When the official calendar watcher sees Trigger A become ready it may run the
finalizer and upload the target-locked package as a workflow artifact.

It does not commit the package automatically and does not issue authority.

Scheduled execution remains inactive while the workflow is absent from the
repository default branch.

Promotion credit: NONE.
