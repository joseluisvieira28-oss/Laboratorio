# MRCR H02 — Target Capture Runtime Guard Contract V0.1
Status: PRE-TARGET / FAIL-CLOSED / NO TARGET AUTHORITY ISSUED
Date: 2026-09-25

## Purpose

Prevent any future prospective MRCR capture runtime from starting merely because
a collector exists or a calendar date arrives.

A capture process may become eligible only when all of the following already
exist and bind exactly:

1. complete official calendar manifest;
2. frozen target-locked protocol;
3. implementation manifest whose head equals the protocol implementation head;
4. ACTIVE TARGET_OBSERVATION_OPEN authority;
5. authority bindings equal the exact protocol/calendar/implementation hashes;
6. current time is not earlier than the authority's earliest target timestamp.

## Fail-closed boundaries

The guard rejects:

- missing or wrong authority type;
- incomplete or mutated calendar;
- implementation hash/head mismatch;
- protocol fingerprint or calendar binding mismatch;
- invalid timestamps;
- execution before earliest target time;
- a protocol that is not H02-frozen and target-locked.

## Outcome boundary

Passing this guard would authorize only the already-authorized prospective target
capture process. It does not reveal future returns and does not supersede the
blind outcome-reveal gate.

Current state: no TARGET_OBSERVATION_OPEN authority exists, so the real runtime
must remain closed.
