# CED1D-0031 — PRESERVED PROGRESS DURING SOURCE WAIT V0.6 — 2026-09-27

Status: FROZEN TELEMETRY/STATE-CARRY HARDENING — NO SCIENCE CHANGE

Authority ID: `CED1D-0031-PRESERVE-PROGRESS-WHILE-WAITING-V0.6`

Observed issue:
- CED1D has persisted prospective receipts/events for earlier mature through-days.
- when a newer mature through-day returns `WAITING_SOURCE_ARCHIVE`, the runtime state omitted `metrics`;
- Diamond Board maps missing metrics to zero, incorrectly displaying `0/60` despite persisted evidence.

Frozen remediation:
1. read only already-persisted `CED1D_RENDER_SHADOW_V03_RECEIPT` events;
2. choose the chronologically latest persisted receipt strictly before or equal to the current mature through-day;
3. when the current collector is `WAITING_SOURCE_ARCHIVE`, expose the prior persisted receipt's metrics as **preserved progress only**;
4. expose the exact through-signal-day from which those metrics came;
5. label metrics as stale/preserved while waiting;
6. do not create, delete, rewrite, backfill, resolve or reinterpret any scientific event;
7. once the current through-day completes, replace preserved metrics with the newly persisted canonical metrics as usual.

This change affects visibility only. It cannot advance a gate.

Firewalls:
- scientific rules changed = false
- event insertion from this telemetry carry = false
- retrospective backfill = false
- orders = false
- exchange mutation = false
- live capital = false
- main merge = false
