# TOKEN-UNLOCK-EVENT-001 — HISTORICAL EMISSIONS SNAPSHOT SOURCE PROTOCOL V0.1

STATUS: FROZEN_PRE_OUTCOME / SOURCE-ONLY
DISCOVERY: CLOSED
LAB_ID: TOKEN-UNLOCK-EVENT-001
MVE_ID: TUE-CLIFF-ADV30-001

## Source authority

Historical public repository snapshot:
- repository: `0xnirmal/emissions-adapters`
- immutable commit: `539e7cf40a4cecc73953f3ae2b196b3fa66ae34a`
- commit timestamp: `2023-03-17T16:43:59Z`

The snapshot contains protocol-level emissions/vesting configuration files and manual event constructors. It is used as an archived provider snapshot, not as an outcome source.

## Frozen extraction semantics

Eligible source primitives for candidate event construction:
- `manualCliff(start, amount)` — one discrete release at `start`;
- `manualStep(start, stepDuration, steps, amount)` — a sequence of discrete scheduled releases according to the repository's own step semantics.

Excluded from candidate event construction:
- `manualLinear(...)` and other continuously accruing/linear schedules;
- mining/staking/inflationary emissions without discrete unlock events;
- dynamic on-chain reward adapters whose future event amount is not encoded prospectively;
- events before the 30-day PIT lead requirement;
- events after 2024-12-31;
- any price, market-cap, forward-return, PnL or other outcome field.

## Point-in-time rule

For this snapshot:
- `known_at_utc = 2023-03-17T16:43:59Z`;
- a candidate event must occur no earlier than `2023-04-17T16:43:59Z` to satisfy the frozen >=30-day known-ahead rule;
- only events through `2024-12-31T23:59:59Z` may be serialized.

A protocol file is candidate PIT evidence only when the relevant event timestamp and amount are fully determined by static values present in the immutable snapshot. Source URLs embedded in protocol files should be retained for provenance and later primary-source upgrade where possible.

## Aggregation

If multiple static allocations for the same protocol/token share the exact event timestamp, aggregate their token amounts into one token-event row while preserving component count and source labels.

## Gate treatment

Rows produced from this snapshot are `IMMUTABLE_PROVIDER_SNAPSHOT_CANDIDATE`, not automatically final PIT authority. They may upgrade to final PIT-qualified after source semantics, token identity, event amount and exact timestamp are verified and the embedded/primary source trail is auditable.

The existing hard gates remain unchanged:
- >=40 final PIT-qualified events;
- >=15 distinct tokens;
- >=2 calendar years within 2021-2024;
- 100% exact amount/timestamp public >=30 days before event;
- Binance pre-event base-volume route available;
- no outcome-based selection;
- no future-market/outcome data.

## Hard guards

No outcomes. No 2025/2026 market/outcome data. No live trading. No exchange mutation. No main merge. No Render deployment. No post-outcome tuning. No reduction of gate thresholds if the source is too small.
