# News Shock Lab V0.3 — Public Source Recovery Closeout V0.3

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`

## Final verdict of this recovery cycle

**PARTIAL_SOURCE / FIELD_COMPLETE / VERSION_AUDIT_BLOCKED**

The exact two frozen reopening events are now field-complete from static institutional documents:

- **US_CPI_2021-01-13:** 4/4 required consensus fields recovered from Danske Bank *Weekly Focus*, dated 2021-01-08.
- **US_NFP_2021-01-08:** 4/4 required consensus fields recovered from The Baker Group *Lunch with Lester*, dated 2020-12-31.

The NFP document contains a strong internal anti-hindsight witness: the future 2021-01-08 rows show forecast values while their `Actual` cells are blank/`--`.

## What was additionally attempted

An independent-version-proof search was performed for:

- pre-T0 or contemporaneous archive captures;
- independent mirrors of the same static documents;
- externally visible immutable version identifiers;
- publisher revision-history evidence.

No qualifying independent mirror or archive capture was established in the current access path.

## Scientific conclusion

The old 2026-09-21 factual situation has materially changed:

- then: **0/4 CPI + 0/4 NFP accepted consensus fields**;
- now: **4/4 CPI + 4/4 NFP candidate fields with clear pre-release chronology**.

The remaining blocker is no longer missing consensus data. It is **independent version immutability / auditable revision history**, explicitly required by the inherited reopening condition.

Therefore:

- do not label this `SOURCE_PASS`;
- do not label this `NO_EDGE`;
- do not build a new census yet;
- do not calculate surprises;
- do not open market outcomes;
- do not weaken the inherited gate.

## Reopen trigger

Immediately resume this branch if any one of the following becomes available for both frozen documents:

1. pre-T0 archive capture;
2. publisher-side immutable version/revision metadata;
3. independent contemporaneous mirror with matching content and date;
4. cryptographically timestamped or otherwise auditable historical copy.

Only after both frozen events satisfy that version-proof requirement may a new consecutive census be prospectively frozen.

## Current state

**NEWS SHOCK LAB V0.3 remains UNTESTED, but the source blocker has been narrowed from “consensus unavailable” to “version immutability not independently proven.”**
