# MRCR H02 — Event Activation Runbook V0.2
Status: PRE-CAPTURE EVIDENCE GATE
Date: 2026-09-27

## Purpose

Validate one annual-plan event immediately before it can be armed for
prospective target capture.

This runbook never starts the capture itself.

## Receipt-only mode

Use this before TARGET_OBSERVATION_OPEN exists, or simply to pre-validate
official T0 evidence:

```bash
BASE="Dream-Account-OS-v2.3-PARTIAL/research/market_reveal_confirmation_reaction_v01"

python "$BASE/live_event_activation_probe_v02.py" \
  --annual-plan ./MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json \
  --event-id "<exact event_id>" \
  --output ./mrcr_event_activation_status_v02.json
```

Expected successful pre-authority status:

`ACTIVATION_RECEIPT_READY_TARGET_OBSERVATION_STILL_LOCKED`

For FOMC, if the preceding meeting minutes are not yet published:

`EVIDENCE_NOT_READY`

## Full runtime-guard mode

Only after a separately authorized TARGET_OBSERVATION_OPEN receipt exists:

```bash
python "$BASE/live_event_activation_probe_v02.py" \
  --annual-plan ./MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json \
  --event-id "<exact event_id>" \
  --protocol ./MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json \
  --implementation-manifest ./MRCR_IMPLEMENTATION_MANIFEST_TRIGGER_A_V02.json \
  --target-open-authority ./TARGET_OBSERVATION_OPEN_RECEIPT.json \
  --ruleset "$BASE/H02_SCIENTIFIC_RULESET_V01.json" \
  --output ./mrcr_event_activation_status_v02.json
```

Possible statuses:

- READY_FOR_EVENT_CAPTURE
- BLOCKED_BY_RUNTIME_GUARD
- EVIDENCE_NOT_READY
- FAIL_CLOSED

READY_FOR_EVENT_CAPTURE is only a readiness verdict. This command does not
start collectors or inspect outcomes.

## BLS

The probe reads only:

- official family schedule page;
- official BLS dissemination policy.

It binds the extracted official text hashes and converts 8:30 a.m. Eastern to
UTC using America/New_York timezone rules.

## FOMC

The probe reads only:

- official FOMC calendar;
- official 2027 meeting-schedule announcement;
- preceding regular-meeting minutes.

The preceding minutes must explicitly confirm the target meeting date. The
annual announcement supplies the 2:00 p.m. Eastern statement-time rule.

If any required source is missing, changed incompatibly, or fails validation,
the event remains unarmed.

## GitHub manual workflow

`.github/workflows/mrcr-h02-event-activation-probe-v02.yml`

The workflow uploads the evidence/status JSON only. It has no market-data
capture or order action.

Promotion credit: NONE.
