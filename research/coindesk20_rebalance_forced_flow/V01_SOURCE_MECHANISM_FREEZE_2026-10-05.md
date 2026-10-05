# COINDESK20-REBALANCE-FORCED-FLOW-001 — V0.1 SOURCE/MECHANISM FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE MARKET OUTCOME INSPECTION

## Mechanism
CoinDesk 20 is an investable, quarterly rebalanced index with linked funds, ETPs, trackers, derivatives and other products.

A published reconstitution that changes constituents creates a mechanically specified portfolio change for capital/products that track or replicate the index.

The hypothesis is NOT "index additions always pump."
The mechanism to test later is ANNOUNCED TARGET-PORTFOLIO CHANGE -> TRACKING/REHEDGING FLOW BEFORE EFFECTIVE REBALANCE.

## Why CoinDesk 20 is selected before outcomes
Official CoinDesk Indices sources provide:
- a historical index-announcement archive;
- dated quarterly reconstitution results/announcements;
- implementation details in official PDFs;
- an explicit linked-product ecosystem.

This source choice is made without inspecting asset price outcomes.

## V0.1 scope
SOURCE AND MECHANISM FEASIBILITY ONLY.

Allowed:
- enumerate official CD20 quarterly reconstitution notices/results for 2024-2025;
- record publication date/timestamp if available;
- record additions, deletions, implementation/reference dates and rules;
- prove that notices precede implementation;
- count asset-level additions/deletions;
- document linked-product evidence;
- verify public market-data coverage generically without opening event-window prices.

Forbidden:
- returns around announcements/effective dates;
- PnL;
- selecting horizons based on price reactions;
- selecting only successful additions/deletions;
- opening 2026 price outcomes.

## Development / holdout boundary
- Development outcomes, only after a separate PRE-OUTCOME ANALYSIS FREEZE: 2024-2025.
- 2026 market outcomes remain CLOSED for confirmation.
- 2026 source metadata may be inspected only for source feasibility.

## Event definition
One asset-level observation per constituent ADDITION or DELETION announced in an official CoinDesk 20 quarterly reconstitution publication.

Shared publication/effective timestamps are preserved.

No observation is excluded because later price movement is weak/adverse.

## Source fields required
- official publication title
- official publication URL/PDF
- publication date and exact timestamp if available
- quarter
- asset/ticker
- action: ADD or DELETE
- implementation date/time or official implementation rule
- initial/final weight determination date when stated
- evidence that publication precedes implementation

## Source gate
PASS only if ALL:
- official archive supports the complete 2024-2025 quarterly CD20 reconstitution sequence;
- >=6 quarterly reconstitutions are source-identifiable across 2024-2025;
- >=12 total asset-level ADD/DELETE observations are source-identifiable;
- >=90% of asset-level changes have a defensible publication-before-implementation interval;
- linked-product evidence is documented from official CoinDesk sources;
- no event-window market prices/returns have been opened.

If quarterly archive incomplete -> SOURCE_BLOCKED.
If archive complete but <12 changes -> INSUFFICIENT_SAMPLE.

## Exact-time ambiguity rule
If an official publication provides only a calendar date and no defensible intraday timestamp, later analysis MUST NOT pretend an exact announcement time.

Any later executable study must use a conservative post-publication boundary frozen before outcomes, such as the next UTC day, unless exact timestamp provenance is separately proven.

## Next authority after PASS
A separate PRE-OUTCOME ANALYSIS FREEZE must define BEFORE opening price outcomes:
- primary trade direction for ADD/DELETE;
- entry boundary relative to publication;
- exit relative to implementation;
- market venue and asset identity;
- benchmark/BTC-relative control;
- costs/slippage/borrow assumptions;
- primary endpoint;
- minimum n;
- hit-rate/median/LOO/concentration gates;
- cluster handling for multiple changes in one quarter.

## Governance
Research-only.
Public data only.
No main merge.
No live trading.
No orders.
No wallets/accounts.
No private/authenticated endpoints.
No post-outcome tuning.
