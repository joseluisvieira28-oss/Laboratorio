# MRCR H02 — Calendar Binding V0.2 Governance Correction
Status: PRE-TARGET GOVERNANCE CORRECTION / SCIENCE UNCHANGED
Date: 2026-09-26
LAB_ID: MARKET-REVEAL-CONFIRMATION-REACTION-001
H02_ID: MRCR-H02-ACCEPTANCE-REJECTION-V01

## Why V0.1 is superseded

The frozen H02 science requires:

- calendar year 2027;
- complete official calendar required;
- T0 = official scheduled release timestamp from BLS/Federal Reserve authority.

The later V0.1 implementation added a stronger condition that every one of the
8 FOMC events had to be simultaneously CONFIRMED before the final calendar could
bind.

That condition is operationally impossible for prospective 2027 observation.
The Federal Reserve publishes all eight 2027 meeting dates but explicitly states
that each meeting date remains tentative until confirmed at the immediately
preceding meeting. Therefore an all-at-once confirmation requirement would delay
the final gate until nearly the end of 2027 and would make earlier prospective
events unobservable.

This is a governance/binding defect, not a scientific result and not a reason to
change H02.

## V0.2 two-stage binding

### Stage A — Annual Plan Gate

The annual plan may bind once the official authorities publish a complete 2027
schedule for the three frozen families:

- 12 US_CPI dates from BLS;
- 12 US_EMPLOYMENT_SITUATION dates from BLS;
- 8 FOMC meeting decision dates from the Federal Reserve.

The annual plan contains official dates and source provenance. It may record an
FOMC date as OFFICIAL_TENTATIVE when the Federal Reserve itself labels that date
tentative.

No inferred, historical-pattern, media or aggregator date is permitted.

Stage A does not itself authorize event capture.

### Stage B — Event Activation Gate

Each event must independently activate before collection around its T0.

Activation requires:

- exact event identity and family already exist in the bound annual plan;
- exact scheduled release timestamp is published by the correct official
  authority before T0;
- source URL and retrieval timestamp are preserved;
- event status is OFFICIAL_CONFIRMED_FOR_CAPTURE;
- activation timestamp precedes event T0;
- for FOMC, the official confirmed meeting date must match the annual-plan date;
- if the official date changes, the old event row fails closed and a calendar
  amendment/rebinding receipt is required before activation.

For BLS, the official release page normally supplies both date and release time.
For FOMC, the event activation receipt must source the actual official statement
release timestamp; V0.2 does not infer 2:00 p.m. merely from historical practice.

## Scientific invariants preserved

V0.2 does not change:

- event families;
- calendar year;
- T0 definition;
- assets;
- venues;
- classifier;
- decision clock;
- depth rule;
- future horizon;
- inference;
- sample/reveal rules;
- contamination rules;
- outcome access policy.

The annual plan is calendar provenance. The event activation receipt supplies
the exact T0 required by the frozen ruleset.

## Target-open boundary

A future TARGET_OBSERVATION_OPEN authority may bind:

- canonical H02 ruleset;
- annual plan manifest;
- implementation manifest;
- protocol fingerprint.

The runtime must additionally require a valid event activation receipt for the
specific event before starting its capture window.

TARGET_OBSERVATION_OPEN alone is insufficient to activate an event.

## Hard fail-closed cases

No event capture when:

- annual plan missing/incomplete;
- event missing from annual plan;
- exact T0 not officially published;
- event confirmation obtained after T0;
- official date differs from annual plan without rebinding;
- wrong official domain/authority;
- target-open authority absent;
- implementation/protocol fingerprints mismatch.

## Status of V0.1

The old all-events-simultaneously-confirmed gate remains preserved as historical
governance evidence but is superseded for future binding because it creates a
prospective-observation deadlock not required by the frozen scientific ruleset.

Promotion credit: NONE.
Target observation: LOCKED.
Outcomes: LOCKED.
