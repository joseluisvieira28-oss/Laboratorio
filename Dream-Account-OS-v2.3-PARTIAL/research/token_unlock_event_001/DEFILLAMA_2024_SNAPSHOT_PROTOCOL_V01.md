# TOKEN-UNLOCK-EVENT-001 — 2024 HISTORICAL EMISSIONS SNAPSHOT PROTOCOL V0.1

STATUS: FROZEN_PRE_OUTCOME / SOURCE-ONLY
DISCOVERY: CLOSED
LAB_ID: TOKEN-UNLOCK-EVENT-001
MVE_ID: TUE-CLIFF-ADV30-001

## Source authority

Historical public GitHub fork preserving the emissions-adapters history:
- repository: `danaugrs/emissions-adapters`
- immutable commit: `ad6bcfa961d6f0bd9cd5d589656b8f78daf7be7a`
- commit timestamp: `2024-03-25T22:11:28Z`
- commit message: `Fix Ondo unlock schedule`
- repository metadata identifies `0xnirmal/emissions-adapters` as parent/source; preserved commit history explicitly includes merges from `https://github.com/DefiLlama/emissions-adapters`.

This snapshot is treated as an archived provider snapshot. It is not an outcome source.

## Frozen extraction semantics

Eligible static primitives:
- `manualCliff(start, amount)`;
- `manualStep(start, stepDuration, steps, amount)` using the repository's own converter semantics: event i occurs at `start + (i+1)*stepDuration`, each with change `amount`.

Excluded:
- `manualLinear` and all continuously accruing schedules;
- dynamic reward/mining/inflation adapters without prospectively fixed discrete token amounts;
- provider-authored assumptions or estimates explicitly disclosed in notes/source code unless independently upgraded to primary schedule authority;
- events before 30 days after the snapshot;
- events after 2024-12-31;
- all market/outcome data.

## PIT window

`known_at_utc = 2024-03-25T22:11:28Z`.

Candidate events must satisfy:
- event timestamp >= `2024-04-24T22:11:28Z`;
- event timestamp <= `2024-12-31T23:59:59Z`.

Mixed-horizon source files may be parsed only under quarantine: rows after 2024-12-31 must never be serialized into the scientific manifest. No 2025/2026 price, return, PnL, volume, market cap or other outcome data may be requested or opened.

## Deduplication across historical snapshots

If the 2023 and 2024 provider snapshots encode the same token-event timestamp and amount, keep one event row and retain both provenance receipts. The earliest qualifying `known_at_utc` governs the PIT lead time. If amounts conflict, the event is `SOURCE_CONFLICT` and cannot become final PIT-qualified until reconciled from primary evidence.

## Final qualification

Provider-snapshot candidates are not automatically final. A row may upgrade to `PIT_QUALIFIED` only if:
1. token identity is unambiguous;
2. exact event timestamp and amount follow deterministically from static snapshot values;
3. >=30-day known-ahead rule passes;
4. no provider note admits that the relevant schedule is an estimate/assumption;
5. source trail is auditable, with primary/official evidence preferred and required for conflicts or suspicious metadata;
6. event is a discrete unlock/vesting release compatible with the frozen MVE.

All existing hard gates and governance remain unchanged. Thresholds may not be reduced to fit the source.
