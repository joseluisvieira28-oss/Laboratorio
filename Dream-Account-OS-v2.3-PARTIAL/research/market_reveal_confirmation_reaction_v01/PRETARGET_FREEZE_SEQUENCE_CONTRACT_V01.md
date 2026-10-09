# MRCR V0.1 — Pretarget Freeze Sequence Contract
Status: ACTIVE / H02 DESIGN FROZEN / TARGET LOCKED
Date: 2026-09-25

## Purpose

Make the chronology mechanically explicit so target observations can never
precede the scientific freeze.

## Required order

1. PRETARGET INFRASTRUCTURE
   - source, timestamp, availability, reconstruction and provenance tooling may
     be hardened without target outcomes;
   - historical contaminated outcomes remain unavailable for selection.

2. EXPLICIT H02 DESIGN/FREEZE AUTHORITY
   - a separate operator-issued MRCR_AUTHORITY_TRANSITION_V01 receipt must be
     ACTIVE with authority_type = H02_DESIGN_FREEZE;
   - it may authorize scientific design and freeze only;
   - target_observation must remain false;
   - it grants zero promotion credit.

3. SCIENTIFIC DESIGN FREEZE
   - COMPLETE: event families, venue/native symbols, anchor, decision clock,
     availability mode, depth definition, classifier, abstention rule, outcome
     horizon, benchmark, inference and economics flag are frozen in
     H02_SCIENTIFIC_RULESET_V01;
   - contaminated historical outcomes were not used to choose them.

4. OFFICIAL CALENDAR + FINAL PROTOCOL BINDING
   - PENDING: the complete prospective official calendar required by the frozen
     design must exist and be fingerprinted;
   - no inferred or unofficial future dates may satisfy this gate;
   - only then may protocol and implementation manifests be bound and frozen.

5. TARGET-OPEN AUTHORITY
   - only after a valid scientific freeze may a second ACTIVE authority receipt
     use authority_type = TARGET_OBSERVATION_OPEN;
   - it must bind the exact protocol fingerprint, calendar manifest hash and
     implementation manifest hash plus the earliest target timestamp.

6. PROSPECTIVE OBSERVATION
   - observation starts no earlier than the bound target timestamp;
   - any mutation to frozen science requires a new prospective identity/authority
     rather than silent rescue or hindsight tuning.

## Hard invariant

**FREEZE FIRST -> TARGET OPEN SECOND -> OUTCOMES LAST.**

Current MRCR state:

- step 2 COMPLETE: H02_DESIGN_FREEZE authority is ACTIVE;
- scientific ruleset is FROZEN under that authority;
- step 3 PENDING: complete official 2027 BLS calendar is not yet available;
- target observation remains locked;
- steps 5-6 are not authorized.
