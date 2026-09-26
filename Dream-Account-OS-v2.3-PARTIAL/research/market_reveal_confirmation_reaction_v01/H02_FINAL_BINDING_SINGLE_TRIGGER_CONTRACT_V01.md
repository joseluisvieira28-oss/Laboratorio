# MRCR H02 — Final Binding Single-Trigger Contract V0.1
Status: ACTIVE PRE-TARGET GOVERNANCE / REAL CALENDAR BLOCKED
Date: 2026-09-26

## Objective

Reduce the remaining pre-target transition to one deterministic external trigger.

No scientific field may be revisited when that trigger occurs.

## Frozen scientific authority

Canonical H02 ruleset:
`H02_SCIENTIFIC_RULESET_V01.json`

Canonical ruleset SHA-256:
`28b01887b73298bae5ffa695599c49af5c40355392ae64255abe06d9f0d6849e`

The classifier, decision clock, depth rule, assets, venues, horizon, inference,
sample/reveal rules and economics flag are already frozen.

## Single external trigger

The transition may advance only after one real official calendar manifest passes
`validate_h02_calendar_manifest`.

That means all of the following simultaneously:

- exactly 12 confirmed 2027 US CPI release events from BLS;
- exactly 12 confirmed 2027 US Employment Situation release events from BLS;
- exactly 8 confirmed 2027 FOMC statement events from the Federal Reserve;
- every event timestamp is in 2027;
- every event is CONFIRMED;
- all official source domains and authorities match;
- each family has a COMPLETE_OFFICIAL_CONFIRMED declaration;
- tentative events are forbidden;
- the manifest hash is self-consistent.

No inferred, historical-pattern, media, aggregator or tentative date may close
this gate.

## Deterministic transition after trigger

1. Build and hash the real official calendar manifest.
2. Build the real implementation manifest from the canonical freeze fileset.
3. Run `final_binding_preflight.py`.
4. Produce a target-locked final protocol with:
   - canonical ruleset hash;
   - exact calendar manifest hash;
   - exact implementation head;
   - exact H02 design-freeze authority receipt.
5. Verify protocol freeze binding.
6. Stop.

At this point target observation remains FALSE.

## Separate later authority

Only after the target-locked protocol is frozen may the operator issue a
separate `TARGET_OBSERVATION_OPEN` receipt.

That receipt must bind exactly:

- protocol fingerprint;
- official calendar manifest fingerprint;
- implementation manifest fingerprint;
- earliest target UTC strictly after authority/protocol/calendar freeze times.

The runtime guard must pass before any prospective target capture can start.

## Hard boundaries

This contract never authorizes:

- target observation by itself;
- outcome access;
- repeated outcome looks;
- threshold changes;
- event-family changes;
- asset/venue changes;
- trading or paper trading;
- exchange mutation;
- paid data;
- Render;
- main merge.

Current state:
REAL CALENDAR BLOCKED / FINAL BINDING REHEARSAL SYNTHETIC ONLY /
TARGET OBSERVATION LOCKED / OUTCOMES LOCKED / PROMOTION CREDIT NONE.
