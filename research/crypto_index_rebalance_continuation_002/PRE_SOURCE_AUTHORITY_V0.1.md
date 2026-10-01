# CRYPTO-INDEX-REBALANCE-CONTINUATION-002 — PRE-SOURCE AUTHORITY V0.1

Date: 2026-10-01
Status: FROZEN_PRE_SOURCE / OUTCOME_BLIND / RESEARCH ONLY
Branch: crypto-index-rebalance-continuation-v0.1

## Parent evidence and reason for a new identity
Parent CRYPTO-INDEX-REBALANCE-FLOW-001 closed DISCOVERY_FAIL_NO_PROMOTION under its frozen
"pre-pressure then post-implementation normalization" hypothesis.

Its 2022-2024 diagnostic nevertheless observed signed relative performance in the ADD/REMOVE
direction during the interval labelled parent post-window:
- mean +65.0718029844 bps
- median +57.1975350100 bps
- ADD mean +95.3035795373 bps
- REMOVE mean +86.7742844122 bps

Those values cannot rescue the parent.

A source-time inconsistency was subsequently identified before this child opens 2025/2026 prices:
the historical parent used the Rebalance Results page Date at 16:00 ET as T0, while the official
Bitwise methodology states standard crypto indexes are reconstituted at 16:00 ET on the last
NYSE Business Day of the month. The 2026-09 Results page is dated 2026-09-29, while the official
rebalance notification states the changes take place at the 2026-09-30 rebalance.

Therefore the apparent parent "post" effect may actually overlap the final pre-implementation
inventory-pressure interval. This is a materially new causal hypothesis and receives a new lab ID.

## Source-only question
For Bitwise Crypto Asset Index Rebalance Results pages from 2025-01 through 2026-09:
1. enumerate every official page and exact change string;
2. capture official page Date / "As of" time;
3. capture machine-readable publication timestamp if the official page exposes one;
4. deterministically normalize unique (month, ticker, ADD/REMOVE) legs;
5. derive the scheduled implementation boundary independently from the official methodology:
   16:00 America/New_York on the last NYSE Business Day of the month;
6. prove that the source information boundary precedes implementation.

No market data may be opened in this stage.

## Frozen source universe
Official Bitwise Crypto Asset Indexes Rebalance Results only.
Months:
- 2025-01 through 2025-12
- 2026-01 through 2026-09

Exactly 21 expected monthly pages.
No Crypto Equity Index or Quantitative Strategy pages may enter this lab.

## Normalization
Unique scientific event leg:
(implementation month, ticker, direction)

ADD verbs: enter, enters, entered, re-enter, re-enters, re-entered.
REMOVE verbs: exit, exits, exited, remove, removes, removed.

Identical legs repeated across overlapping index sections collapse to one.
Same month+ticker with conflicting directions => FAIL_CLOSED_SOURCE_CONTRADICTION.

Ticker is taken only from official parenthetical ticker notation.
No exchange-derived aliasing in the source census.

## Time semantics
The Results page Date / As-of time is source metadata, not automatically the implementation time.

Implementation boundary is frozen from the Bitwise methodology:
16:00 America/New_York on the last NYSE Business Day of each month.

The source gate must preserve separately:
- result_page_date
- result_asof_time
- machine datePublished if present
- implementation timestamp

If exact machine publication timestamp is unavailable, that fact is preserved. It may restrict later
economic entry timing; it must not be guessed from prices.

## Source advancement gate
SOURCE_CENSUS_PASS requires:
- 21/21 official pages recovered;
- zero duplicate month identities;
- every page has official Date and Time;
- every non-"No changes" string deterministically parsed or explicitly quarantined;
- zero direction contradictions;
- both 2025 and 2026 represented;
- >= 12 unique normalized event legs;
- >= 4 distinct change months;
- both ADD and REMOVE represented.

This gate is sample/source feasibility only.

## Protected outcomes
Market-price state at freeze:
- 2025 market outcomes: UNOPENED BY THIS CHILD
- 2026 Jan-Aug market outcomes: UNOPENED BY THIS CHILD
- 2026 Sep post-implementation boundary: PROSPECTIVE / NOT YET COMPLETE at this freeze

Forbidden:
- spot/futures prices
- returns
- PnL
- fee-adjusted results
- winner/loser filtering
- publication-time inference from market behavior
- main merge
- live trading / orders / exchange mutation

A SOURCE_CENSUS_PASS authorizes only a separate route-feasibility gate, still outcome-blind.
