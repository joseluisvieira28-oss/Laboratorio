# POLY-COMBINATORIAL-ARB-001 — SOURCE ROUTE SPEC V0.2

Date: 2026-09-27
Status: FROZEN_PRE_RUN / SOURCE-ONLY

## Purpose
Repair V0.1 source selection without opening economics.

V0.1 was deliberately not adjudicated as SOURCE_DATA_PASS because it mixed generic multi-market events with the intended negative-risk population and therefore produced many irrelevant 404 books.

## V0.2 frozen population
- Polymarket event must have negRisk=true.
- active=true and closed=false from Gamma source.
- augmented negative-risk events are excluded when the metadata declares negRiskAugmented=true.
- event must contain 2 to 20 binary markets.
- each market must expose exactly one YES token through outcomes + clobTokenIds.
- markets explicitly closed/inactive/orderbook-disabled are excluded and make the event ineligible for the primary completeness count.

## First-party provenance
The run must snapshot and SHA256:
- Polymarket official agent-skills ctf-operations.md;
- Polymarket official agent-skills market-data.md.

The run must verify the official documentation states that negative-risk events have one winning outcome and identifies public Gamma/CLOB routes.

## Event completeness
For an event to be SOURCE_PACKAGE_COMPLETE:
- every YES token has a public CLOB book;
- every YES book has >=1 bid and >=1 ask;
- every YES book exposes a timestamp;
- every YES token has a fee schema;
- zero leg uses midpoint, last-trade substitution, future-nearest join or silent imputation.

No package price sum, arbitrage spread, PnL or profitability is computed.

## Route-pass threshold
SOURCE_ROUTE_PASS requires:
- first-party provenance PASS;
- >=3 eligible standard neg-risk events observed;
- >=2 SOURCE_PACKAGE_COMPLETE events in the probe population;
- zero authenticated endpoints;
- zero economic outputs.

This is a source-route verdict only. It does not authorize Discovery. A separate prospective collector/gate must be frozen before any package economics are opened.
