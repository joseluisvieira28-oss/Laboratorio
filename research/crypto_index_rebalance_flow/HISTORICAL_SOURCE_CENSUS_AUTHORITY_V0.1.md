# CRYPTO-INDEX-REBALANCE-FLOW-001 — HISTORICAL SOURCE CENSUS AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_SOURCE_ONLY / NO MARKET OUTCOMES
Branch: crypto-index-rebalance-flow-v0.1
Parent prospective pilot: 2026-09-30 Bitwise rebalance

## Purpose
Determine whether the official Bitwise Crypto Asset Index rebalance-results archive provides a complete and sufficiently populated historical event corpus to justify a later, separately frozen Discovery.

This authority does NOT authorize a backtest.

## Frozen source period
2022-01 through 2025-12 inclusive.

Expected monthly rebalance-result dates: 48.

2026 historical market outcomes are excluded from this source census. The separately frozen Sep 30 2026 event remains prospective under its own authority.

## Primary official source
Bitwise Investments:
https://bitwiseinvestments.com/indexes/rebalance-results/bitwise-crypto-asset-indexes

Only first-party Bitwise result pages may satisfy the primary source gate.

## Data allowed
For each monthly result page:
- canonical URL;
- official Date;
- official Time;
- index-section names;
- textual Changes fields;
- result-page SHA256;
- source availability/HTTP metadata.

No external market prices.
No returns.
No volume.
No PnL.
No exchange APIs.
No trading data.

## Completeness gate
SOURCE_CORPUS_COMPLETE requires:
- all 48 expected month-year result pages recovered;
- unique official rebalance Date parsed for all 48;
- official Time parsed for all 48;
- zero duplicate month identities;
- zero source substitution.

If fewer than 48 are recovered:
SOURCE_CORPUS_INCOMPLETE.
This is not NO_EDGE.

## Event-density diagnostic
Report, without market outcomes:
- months with at least one non-"No changes" Changes field;
- total non-no-change section records;
- number of distinct raw change strings;
- month distribution by year.

This diagnostic does not itself authorize Discovery.

## Future Discovery firewall
Even if SOURCE_CORPUS_COMPLETE:
- do not fetch BTC/token prices;
- do not compute event returns;
- do not select assets based on historical performance;
- do not decide horizons from market outcomes.

A separate FINAL PRE-DISCOVERY AUTHORITY must freeze:
- event-unit deduplication;
- add/remove parsing;
- asset mapping;
- execution geometry;
- control benchmark;
- cost model if trading economics are tested;
- inference and sample gates;
before any market outcome is opened.
