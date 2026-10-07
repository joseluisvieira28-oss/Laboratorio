# BYBIT-FUNDING-INTERVAL-REGIME-REPLICATION-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY BYBIT PREMIUM OUTCOME

### 1. Purpose
Independent external replication of the Binance BFIRS discovery on Bybit.

Known Binance result:
- SURVIVES_FUNDING_INTERVAL_DISCOVERY on 2023-2025.
- 2026 Binance confirmatory source gate is HOLDOUT_INSUFFICIENT_SAMPLE and remains unopened.

This Bybit family MUST NOT reuse Binance outcomes to choose event subsets, horizons, controls, signs or thresholds beyond literal replication of the already-frozen BFIRS mechanism.

### 2. Economic hypothesis
When Bybit shortens the funding settlement interval of an already-live USDT linear perpetual contract, the affected contract's absolute premium index should compress toward zero after the public announcement more than contemporaneous unaffected controls.

This is an external-exchange replication of the same premium-normalization mechanism.
It is not a new optimized hypothesis.

### 3. Frozen calendar
- 2023-01-01 through 2025-12-31 inclusive.
- 2026 excluded from this external replication.
- No Bybit premium-index outcome from this family has been opened at freeze time.

### 4. Public/free authorities
Official Bybit public sources only:
1. Announcement API: GET /v5/announcements/index
2. Official announcement pages returned by that API
3. Funding history API: GET /v5/market/funding/history
4. Premium Index Price Kline API: GET /v5/market/premium-index-price-kline

No authenticated/private endpoint.

### 5. Source-only funding timestamp rule
Bybit funding-history responses contain both:
- fundingRateTimestamp
- fundingRate

During SOURCE GATE:
- code MAY access and persist fundingRateTimestamp;
- code MUST NOT read, compare, print, store or use fundingRate values;
- fundingRate values are scientifically forbidden at source stage.

Settlement timestamps are treated as contract-mechanics metadata, not market outcomes.

### 6. Candidate announcement definition
An announcement candidate must:
- be published in the frozen 2023-2025 calendar;
- contain a title or official page text referring to a change/adjustment of funding interval/funding rate interval;
- identify at least one USDT perpetual/linear contract;
- not be an initial listing/launch announcement;
- not be a delisting/automatic-settlement announcement.

### 7. Eligible interval-shortening event
For each named contract candidate:

A source event is eligible only if:
1. official Bybit publication timestamp exists;
2. contract symbol ends in USDT;
3. funding-history timestamp data exists on both sides of publication;
4. pre-announcement settlement cadence is mechanically recoverable from at least 3 consecutive pre-publication settlement gaps;
5. post-announcement cadence is mechanically recoverable from at least 3 consecutive post-publication settlement gaps;
6. the modal pre cadence is stable: at least 2 of the last 3 pre gaps equal the inferred old interval;
7. the modal post cadence is stable: at least 2 of the first 3 post gaps equal the inferred new interval;
8. new interval is strictly SHORTER than old interval;
9. old and new intervals are each one of {1h, 2h, 4h, 8h, 12h, 24h};
10. transition occurs no earlier than publication time;
11. no initial listing or delisting confound.

The event information time T0 for later outcome analysis is the OFFICIAL PUBLICATION TIME, not the mechanically detected settlement transition.

### 8. Independent shock cluster
One independent shock cluster =
official announcement URL + publication timestamp.

Multiple contracts named by one announcement are one independent shock.

### 9. Source sample gate
EXTERNAL_SOURCE_PASS requires ALL:
- >=12 independent eligible announcement clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- >=2 calendar years represented;
- no single announcement cluster >35% of eligible asset-events.

If complete official enumeration is demonstrated but thresholds fail:
VERDICT = EXTERNAL_INSUFFICIENT_SAMPLE.

If the announcement archive cannot be completely enumerated back through 2023 or provenance is not defensible:
VERDICT = EXTERNAL_SOURCE_BLOCKED.

### 10. Premium endpoint capability
The Bybit public Premium Index Price Kline endpoint is the frozen outcome source if the source gate passes.

No premium OHLC values may be opened during this source gate.

Event-specific premium-data availability will be handled later under a frozen missingness rule before any verdict; it may not be used now to choose events.

### 11. If source gate passes
Create a separate PRE-OUTCOME REPLICATION FREEZE before any Bybit premium-index value is opened.

The replication freeze MUST copy the Binance BFIRS V0.2 rules unless a Bybit API-format adaptation is purely mechanical:
- publication T0;
- first full minute after publication;
- same baseline/post windows;
- BTCUSDT/ETHUSDT/BNBUSDT controls;
- same absolute-premium compression endpoint;
- same shock-cluster aggregation;
- same 2 bps economic floor;
- same exact one-sided sign test alpha 0.05;
- same 10,000 cluster bootstrap concept;
- same chronological-half robustness;
- no rescue.

### 12. Verdict taxonomy
Source:
- EXTERNAL_SOURCE_PASS
- EXTERNAL_INSUFFICIENT_SAMPLE
- EXTERNAL_SOURCE_BLOCKED

Outcome replication:
- EXTERNAL_REPLICATION_CONFIRMED
- EXTERNAL_REPLICATION_FAILS

### 13. Governance
- research-only;
- fail-closed;
- no main merge;
- no live trading;
- no orders;
- no wallets;
- no account reads;
- no authenticated/private endpoints;
- no exchange mutation;
- no spending;
- no post-outcome tuning.

### 14. Outcome-access declaration
At this freeze:
- no Bybit premium-index values opened;
- no Bybit funding-rate values opened/used;
- no Bybit price returns/PnL opened for this family.
