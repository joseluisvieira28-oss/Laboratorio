# MEXC-FUNDING-INTERVAL-BASIS-REPLICATION-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY MEXC MARKET OUTCOME

### 1. Purpose
Independent external-exchange construct replication of the BFIRS mechanism on MEXC.

Known Binance evidence:
- BFIRS 2023-2025 Discovery survived all frozen primary gates.
- Binance 2026 Jan-Sep confirmatory source gate was insufficient and opened zero outcomes.
- Binance V0.4 prospective confirmation remains outcome-sealed.

Known external source attempts:
- Bybit: source transport blocked.
- OKX: source concentration gate failed.
- Gate: historical cadence/source coverage blocked.
- Bitget: abundant 2025 events but frozen two-year source gate failed.

No prior MEXC funding-interval family exists in the repository.

### 2. Economic hypothesis
A publicly announced shortening of funding settlement frequency for an already-live MEXC USDT-M perpetual contract may cause abnormal compression of the contract's fair-price vs index-price basis after the announcement relative to unaffected controls.

This is an external construct replication.
It is not an outright directional return hypothesis.

### 3. Frozen source calendar
- 2024-01-01 through 2025-12-31 inclusive.
- 2026 excluded.
- No MEXC fair/index/funding-rate/return/PnL outcomes have been opened for this family.

### 4. Official/public authorities
Event source:
- official MEXC Support / Announcements pages and official MEXC archive/search mechanisms only.

Mechanics-only API:
- public GET /api/v1/contract/funding_rate/history
- source stage may read/store/use ONLY:
  - symbol
  - settleTime
  - collectCycle
- source code MUST NOT read/store/print/use fundingRate.

Reserved outcome source if source passes:
- public MEXC fair-price 1-minute candles
- public MEXC index-price 1-minute candles

No authenticated/private endpoint.

### 5. Eligible event definition
An asset-event qualifies only if ALL:
1. official MEXC article publication timestamp is resolved;
2. publication timestamp lies in 2024-2025;
3. affected contract is an already-live USDT-M perpetual;
4. article explicitly announces/records a funding settlement frequency change;
5. exact effective UTC timestamp is explicit;
6. publication timestamp is STRICTLY EARLIER than effective timestamp;
7. announced/new collection cycle is explicit or mechanically unambiguous from the first post-effective funding-history collectCycle;
8. old collection cycle is recovered from public historical collectCycle records before effective time;
9. old and new cycles are each in {1h,2h,4h,8h,12h,24h};
10. new cycle is STRICTLY SHORTER than old cycle;
11. at least 3 pre-effective funding-history records exist and at least 2 of the last 3 have the old collectCycle;
12. at least 3 post-effective records exist and at least 2 of the first 3 have the new collectCycle;
13. no listing/launch confound;
14. no delisting/automatic-settlement confound;
15. no outcome-based selection.

Retrospective notices published at or after the effective timestamp are excluded.

### 6. Independent shock cluster
One independent shock =
official article ID + publication timestamp + effective timestamp + old->new collectCycle.

Multiple contracts in one article/effective transition remain one independent cluster.

### 7. Source enumeration
The source gate must prove a defensible complete official MEXC announcement universe for the frozen 2024-2025 calendar.

It must:
- enumerate official MEXC Support/Announcements archive/search results across the full window;
- cross before 2024-01-01;
- inspect every official article whose title/body refers to funding settlement frequency / funding rate interval adjustment;
- retain canonical URL/article ID, publication timestamp, effective timestamp, contract(s), pre/post collectCycle evidence, and exclusion reason.

Search-engine results may diagnose coverage but may not define the final universe.

### 8. Source sample gate
EXTERNAL_SOURCE_PASS requires ALL:
- >=12 independent eligible shock clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- >=2 calendar years represented;
- no single cluster >35% of eligible asset-events;
- official archive enumeration crosses before 2024-01-01;
- canonical MEXC provenance resolved for every eligible event;
- historical collectCycle coverage passes for every eligible event.

If official enumeration is complete but minimums fail:
VERDICT = EXTERNAL_INSUFFICIENT_SAMPLE.

If archive/provenance/historical collectCycle coverage cannot be demonstrated:
VERDICT = EXTERNAL_SOURCE_BLOCKED.

### 9. Outcome capability / safety
At source stage allowed:
- HTTP/schema capability;
- row counts;
- settlement timestamps;
- collectCycle;
- article metadata.

Forbidden at source stage:
- fundingRate values;
- fair-price candle values;
- index-price candle values;
- reconstructed basis;
- outright price returns;
- volume;
- PnL.

### 10. If source gate passes
Create a separate immutable PRE-OUTCOME REPLICATION FREEZE before requesting fair/index candle values.

That freeze must specify before outcomes:
- publication T0 and minute alignment;
- exact fair/index basis formula;
- baseline/post windows;
- BTC_USDT / ETH_USDT / BNB_USDT controls when untreated;
- missingness rules;
- cluster aggregation;
- economic-effect floor in ratio/bps units;
- sign test;
- bootstrap;
- chronological robustness;
- exact verdict.

No rescue after outcomes.

### 11. Verdict taxonomy
Source:
- EXTERNAL_SOURCE_PASS
- EXTERNAL_INSUFFICIENT_SAMPLE
- EXTERNAL_SOURCE_BLOCKED

Outcome:
- EXTERNAL_CONSTRUCT_REPLICATION_SURVIVES
- EXTERNAL_CONSTRUCT_REPLICATION_FAILS

### 12. Governance
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

### 13. Outcome-access declaration
At this freeze:
- no MEXC fundingRate value has been read/used;
- no MEXC fair/index candle value has been opened;
- no MEXC return/basis/PnL outcome has been opened.
