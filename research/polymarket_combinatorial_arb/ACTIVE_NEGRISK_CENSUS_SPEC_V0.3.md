# POLY-COMBINATORIAL-ARB-001 — ACTIVE NEG-RISK POPULATION CENSUS V0.3

Date: 2026-09-27
Status: FROZEN_PRE_RUN / SOURCE-METADATA-ONLY

## Why V0.3 exists
V0.2 returned zero eligible events under an engineering cap of <=20 markets. No economic outcome was opened. This census determines the actual active standard negative-risk population before any new completeness rule is frozen.

## Allowed data
Gamma active-event metadata only:
- event id / slug / title;
- active / closed / archived;
- negRisk / negRiskAugmented;
- market count;
- market active/closed/orderbook-enabled flags;
- outcome-label and token-id schema completeness.

## Forbidden
No CLOB books, prices, bids, asks, spreads, package sums, fees, PnL, fills, profitability, historical outcomes, ranking by apparent economic value, authenticated endpoints or orders.

## Pagination
Enumerate all current active/non-closed events using Gamma API with limit=500 and increasing offset until a page returns <500 rows or a hard safety limit of 20 pages is reached.

## Output
Produce only population counts and distributions:
- total active events;
- standard neg-risk events;
- augmented neg-risk events;
- standard neg-risk market-count distribution;
- schema-complete standard neg-risk events;
- orderbook-enabled standard neg-risk events.

The resulting population geometry may justify a new SOURCE ROUTE specification because no economic outcome has been observed.
