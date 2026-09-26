# MRCR H02 — Final Binding Trigger Contract V0.2
Status: ACTIVE PRE-TARGET GOVERNANCE / SCIENCE UNCHANGED
Date: 2026-09-26

## Canonical path

V0.2 supersedes the V0.1 all-events-simultaneously-confirmed binding rule.

### Trigger A — complete official annual plan

Advance final protocol binding only when:

- 12 official 2027 US CPI dates are published by BLS;
- 12 official 2027 Employment Situation dates are published by BLS;
- 8 official 2027 FOMC meeting decision dates are published by the Federal Reserve;
- no inferred/media/aggregator dates are used;
- annual plan hash validates.

Federal Reserve dates may carry OFFICIAL_TENTATIVE in the annual plan when the
Federal Reserve itself labels them tentative.

Trigger A allows building/fingerprinting a target-locked protocol V0.2. It does
not activate any event and does not authorize outcomes.

### Separate TARGET_OBSERVATION_OPEN authority

After the target-locked protocol V0.2 is frozen, a separate explicit authority
must bind:

- protocol fingerprint;
- annual-plan hash (using the legacy calendar binding field name for authority
  compatibility);
- implementation-manifest hash;
- earliest target UTC.

The frozen protocol itself remains target_observation_authorized=false.

### Trigger B — event activation

Before each individual event capture, a V0.2 activation receipt must prove:

- event exists in the annual plan;
- exact official T0 is published by BLS/Federal Reserve;
- official confirmation occurred before T0;
- official domain/authority match;
- T0 date matches the annual-plan date;
- receipt hash validates;
- current time remains before T0.

If the official date changes, the old row fails closed and calendar rebinding is
required before capture.

## Why this preserves science

The frozen H02 still uses exactly:

T0 = official scheduled release timestamp from BLS/Federal Reserve authority.

V0.2 never derives T0 from historical convention. It merely separates the
annual date plan from the exact event timestamp that becomes officially
available before each event.

No classifier, threshold, horizon, asset, venue, inference, sample rule or
outcome policy changes.

## Current real status — 2026-09-26

- FOMC: eight 2027 meeting dates officially published, currently tentative.
- BLS CPI: complete 2027 schedule not yet published.
- BLS Employment Situation: complete 2027 schedule not yet published.

Therefore Trigger A remains BLOCKED_BY_BLS.

Target observation: LOCKED.
Outcomes: LOCKED.
Promotion credit: NONE.
