# MRCR H02 — Live Event Activation Probe Contract V0.2
Status: CANONICAL PRE-CAPTURE EVIDENCE GATE / NO CAPTURE ACTION
Date: 2026-09-27

## Purpose

For exactly one event already present in the frozen V0.2 annual plan, prove its
exact official T0 immediately before prospective target capture is allowed to be
armed.

The probe itself never starts target capture.

## BLS evidence chain

US_CPI and US_EMPLOYMENT_SITUATION require:

1. the correct official BLS release schedule page;
2. the official BLS dissemination policy proving the PFEI 8:30 a.m. Eastern
   release-time rule;
3. annual-plan date equality;
4. retrieval before T0;
5. SHA-256 of each extracted official text.

T0 is converted from America/New_York to UTC using timezone-aware conversion.

## FOMC evidence chain

FOMC_STATEMENT requires:

1. the official Federal Reserve 2027 annual schedule announcement containing
   the meeting dates and the rule that the policy statement is released at
   2:00 p.m. Eastern on the second day;
2. the immediately preceding regular FOMC meeting minutes confirming the next
   meeting date;
3. annual-plan meeting/date equality;
4. retrieval before T0;
5. SHA-256 of each extracted official text.

The preceding meeting is resolved from the official FOMC calendar. For the
first 2027 meeting this can resolve to the final regular meeting of 2026.

A missing minutes page or missing confirmation remains EVIDENCE_NOT_READY /
FAIL_CLOSED. Historical convention is never substituted.

## Activation receipt

A valid MRCR_H02_EVENT_ACTIVATION_RECEIPT_V02 binds:

- event identity;
- family;
- exact UTC T0;
- official authority/domain;
- confirmation timestamp;
- evidence roles;
- supporting official-source URLs;
- retrieval timestamps;
- extracted-text SHA-256 values;
- activation receipt SHA-256.

The receipt cannot self-authorize target observation or outcomes.

## Statuses

Without TARGET_OBSERVATION_OPEN:

ACTIVATION_RECEIPT_READY_TARGET_OBSERVATION_STILL_LOCKED

With protocol + implementation manifest + valid TARGET_OBSERVATION_OPEN:

- READY_FOR_EVENT_CAPTURE, only if event_capture_runtime_guard_v02 passes;
- BLOCKED_BY_RUNTIME_GUARD otherwise.

EVIDENCE_NOT_READY means the required official evidence is not yet published.

## Hard boundary

READY_FOR_EVENT_CAPTURE is a readiness verdict only. This probe has no code
path to start collectors, compute outcomes, trade, submit orders or mutate an
exchange.

Promotion credit: NONE.
