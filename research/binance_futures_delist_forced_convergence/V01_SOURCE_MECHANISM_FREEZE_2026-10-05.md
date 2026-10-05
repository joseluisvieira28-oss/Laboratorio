# BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001 — V0.1 SOURCE/MECHANISM FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE MARKET OUTCOME INSPECTION

## Mechanism
Binance Futures delisting notices can impose a future time at which all remaining positions are closed and automatically settled.

This creates a hard mechanical boundary:
- residual open interest must reach zero at settlement;
- new risk can be restricted before settlement;
- the delisting contract's price/mark must terminate at a settlement mechanism tied to its index.

The economic hypothesis to be evaluated later is NOT "delistings make price go down."
The candidate mechanism is FORCED POSITION EXTINCTION + BASIS/SPREAD CONVERGENCE.

## Stage V0.1 scope
SOURCE AND MECHANISM FEASIBILITY ONLY.

Permitted before a later pre-outcome analysis freeze:
- enumerate official Binance Futures delisting announcements;
- parse publication timestamp, contract symbols, exact automatic-settlement timestamp and rule changes;
- verify public historical archive coverage;
- verify that mark/index/perpetual and OI/metrics data are available at sufficient resolution;
- identify possible public external hedge/reference venues;
- count eligible events.

Forbidden in V0.1:
- opening price paths around delisting;
- calculating returns, basis or spread outcomes;
- selecting horizons from observed outcomes;
- calculating PnL;
- opening 2026 market outcomes.

## Development / holdout boundary
- Development market outcomes, if source gate passes and a NEW analysis freeze is committed: 2024-2025.
- 2026 market outcomes remain CLOSED for later confirmation.
- Event metadata for 2026 may be inspected only for source/census feasibility; prices/returns/spreads/OI paths are not to be opened.

## Mechanical event inclusion
One observation per USDⓈ-M perpetual contract if ALL are true:
1. official Binance public notice;
2. exact automatic-settlement timestamp is stated;
3. contract is not already terminated before the notice;
4. public archive can identify the contract around the settlement date;
5. timestamp provenance is defensible.

Rebrand/migration events are retained at source census stage and tagged; no outcome-based exclusion.
Multiple contracts in one notice are separate observations sharing publication time.

## Required source fields
- official article identifier
- publication timestamp
- symbol
- settlement timestamp
- reduce-only/new-position restriction timestamp when stated
- reason/tag if explicitly stated
- perpetual trades/klines archive coverage
- mark-price archive coverage
- index-price archive coverage
- futures metrics/OI archive coverage if available

## Source-gate PASS
PASS only if:
- a reproducible official-announcement route can enumerate the 2024-2025 event universe;
- >=12 eligible contract observations are source-identifiable before outcomes;
- >=80% have required perpetual + mark + index archive coverage around settlement;
- an OI/metrics source is proven for mechanism validation OR the family is explicitly narrowed before outcomes to price/index convergence only;
- no market outcome has been opened during source work.

Otherwise:
- SOURCE_BLOCKED if public sources cannot support the frozen mechanism;
- INSUFFICIENT_SAMPLE if reproducible source census has <12 eligible events.

## Next authority if PASS
Commit a separate PRE-OUTCOME ANALYSIS FREEZE before reading market values.
That freeze must define:
- primary pre-settlement horizon;
- basis/spread formula;
- reference/hedge venue;
- OI decay test;
- controls;
- fees/slippage/financing;
- discovery gates;
- concentration/leave-one-out rules;
- exact holdout boundary.

No horizon or gate may be selected after seeing price outcomes.

## Governance
Research-only.
Public/unauthenticated data only.
No main merge.
No trading/orders.
No wallets/accounts.
No exchange mutation.
No post-outcome tuning.
