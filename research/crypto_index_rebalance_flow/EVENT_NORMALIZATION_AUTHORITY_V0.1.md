# CRYPTO-INDEX-REBALANCE-FLOW-001 — EVENT NORMALIZATION AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_SOURCE_ONLY / MARKET_OUTCOME_BLIND
Input authority: HISTORICAL_SOURCE_CENSUS_AUTHORITY_V0.1
Input run: 36329364861
Input artifact: 10935615452
Input artifact ZIP SHA256: b3c5911e854e3d915a3a8293c1c7f4c4dccca37e8e4af0d7d52f6516cdc765b0

## Purpose
Convert the already-frozen official Bitwise 2022-2025 change strings into deterministic source event legs before any market outcome is opened.

## Event unit
Unique:
(rebalance official date, ticker, direction)

Direction:
- ENTER / ENTERED / ENTERS / RE-ENTERED => ADD
- EXIT / EXITED / EXITS / REMOVED => REMOVE
- "A entered/re-entered, replacing B" => A ADD + B REMOVE

Repeated identical legs across overlapping Bitwise index sections collapse to one event leg.

## Legacy name-only ticker mapping
Only the following source strings lack parenthetical ticker notation and need an explicit mapping:
- Polkadot -> DOT
- Cosmos -> ATOM
- Algorand -> ALGO
- Bitcoin Cash -> BCH

These identities are first-party-verifiable from Bitwise's official January 2022 asset table. No market data is involved.

All other normalized tickers must come from the parenthetical ticker in the official Changes text.

## Ambiguous-source rule
Exact string:
"Curve DAO (CRV); Liquity (LQTY) exited"

The official November 2023 Changes field omits a direction verb for CRV. Even though the same page's holdings may allow an inference, V0.1 does NOT infer it.

Treatment:
SOURCE_TEXT_AMBIGUOUS_EXCLUDED.

No CRV ADD leg and no LQTY REMOVE leg from that exact Changes field enter the normalized primary corpus.

This is a source-quality exclusion frozen before outcomes.

## Contradiction guard
If the same (date,ticker) normalizes to both ADD and REMOVE, FAIL_CLOSED_SOURCE_CONTRADICTION.

## Period roles
- 2022-01-01 through 2024-12-31 = candidate Discovery source corpus.
- 2025-01-01 through 2025-12-31 = HOLDOUT_SOURCE_ONLY. Event identities may be normalized, but NO 2025 market data may be fetched or computed.
- 2026 = separate prospective authority; not part of this historical normalization.

## Required outputs
- normalized event-leg JSON;
- unique event count;
- distinct rebalance-date count;
- ADD/REMOVE counts;
- counts by year;
- duplicates collapsed;
- ambiguous source strings;
- source-record lineage.

## Forbidden
- price APIs;
- klines;
- volume;
- returns;
- PnL;
- selecting/removing events based on market behavior;
- ticker aliases based on exchange availability;
- manual correction after seeing outcomes.

## Advancement condition
The later Discovery design may be frozen only if the 2022-2024 normalized source corpus contains:
- >= 30 unique event legs;
- >= 12 distinct rebalance dates;
- >= 2 calendar years;
- both ADD and REMOVE directions.

These are source sample gates, not performance gates.
