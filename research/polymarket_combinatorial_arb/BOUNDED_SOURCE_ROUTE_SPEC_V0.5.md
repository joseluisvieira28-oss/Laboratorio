# POLY-COMBINATORIAL-ARB-001 — BOUNDED SOURCE ROUTE V0.5

Date: 2026-09-27
Status: FROZEN_PRE_RUN / SOURCE-ONLY

## Why this route is legitimate
The V0.3 metadata-only first-page census identified three standard active non-augmented negative-risk events before any CLOB book, fee, package-price or economic output was opened:
- event 32228 — 5 component markets
- event 48292 — 7 component markets
- event 51456 — 13 component markets

These exact event IDs are frozen only as engineering fixtures for source feasibility. They are NOT Discovery/OOS evidence and may never be used for promotion.

V0.4 attempted a complete active-event census but hit a Gamma pagination HTTP 422 transport boundary. That is a source-transport limitation, not scientific evidence.

## Source-only objective
For the three frozen fixture events, prove that the public Polymarket route can recover:
- exact event/market identity and negRisk metadata;
- exactly one YES token per component market;
- executable CLOB bid/ask book with timestamp for every YES leg;
- fee schema for every YES leg;
- first-party CTF/neg-risk semantics.

No package sum, price inequality, arbitrage spread, PnL, profitability or opportunity ranking may be computed.

## PASS rule
SOURCE_ROUTE_PASS iff:
1. official market-data + CTF docs are snapshotted and required neg-risk semantics are found;
2. all three frozen event IDs resolve as active, standard negRisk, non-augmented;
3. at least 2 of the 3 events are SOURCE_PACKAGE_COMPLETE;
4. every leg inside a complete event has >=1 bid, >=1 ask, timestamp and fee schema;
5. zero auth, orders, future-nearest joins, silent imputations and economic outputs.

A failure is SOURCE_ROUTE_INCOMPLETE, never NO_EDGE.

## After PASS
Still no economics. Next step is a separate prospective collector freeze using future observations only. Historical/published Polymarket arbitrage periods remain contaminated and cannot validate the lab.
