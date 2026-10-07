# BITGET-FUNDING-INTERVAL-PREMIUM-REPLICATION-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY BITGET MARKET OUTCOME

### 1. Purpose
Independent external-exchange replication of the BFIRS economic mechanism on Bitget using Bitget's own historical premium candles.

Known Binance evidence:
- 2023-2025 Discovery: SURVIVES_FUNDING_INTERVAL_DISCOVERY.
- 2026 Jan-Sep holdout: HOLDOUT_INSUFFICIENT_SAMPLE with ZERO market outcomes opened.
- prospective Binance confirmation remains outcome-sealed.

This Bitget family must not use Binance outcomes to tune Bitget event selection, horizons, controls, signs, thresholds or subsets.

### 2. Economic hypothesis
When Bitget shortens the funding interval of an already-live USDT perpetual contract at a pre-announced effective timestamp, the affected contract's absolute premium should compress toward zero after the public announcement more than unaffected controls.

This is a direct premium replication, not an outright price-direction hypothesis.

### 3. Frozen source calendar
- 2024-01-01 through 2025-12-31 inclusive.
- 2026 excluded.
- The 2024 start is frozen before any Bitget premium outcome and is chosen because the replication requires at least two calendar years if such events exist; source gate must prove official archive coverage across the entire frozen calendar.

### 4. Official/public authorities
Event source:
- official Bitget Support Center announcement pages and official support archive/search mechanisms only.
- Search-engine results may diagnose archive/parser coverage but may not define the eligible universe.

Reserved outcome source if source passes:
- Bitget public GET /api/v3/market/history-candles
- category=USDT-FUTURES
- interval=1m
- type=premium

No authenticated/private endpoint.

### 5. Eligible event
An asset-event qualifies only if ALL:
1. official Bitget article publication timestamp exists;
2. publication is within 2024-2025;
3. affected trading pair is an already-live USDT perpetual;
4. article explicitly states an adjustment to funding interval/frequency;
5. exact adjustment/effective timestamp is explicit;
6. OLD and NEW intervals are explicit in the official article;
7. NEW interval is strictly SHORTER than OLD interval;
8. article publication precedes adjustment/effective timestamp;
9. event is not an initial listing/launch;
10. event is not a delisting/automatic-settlement bundle;
11. event is not a lengthening/restoration;
12. event is not selected by later premium/funding/price outcomes.

No inference from funding-rate values is needed or allowed.

### 6. Independent shock cluster
One independent shock =
official Bitget article ID + publication timestamp + adjustment timestamp + old->new interval.

Multiple contracts sharing one official article and one exact transition remain one independent shock.

### 7. Source enumeration
The source gate must prove a defensible complete official Bitget Support enumeration for the frozen 2024-2025 calendar.

It must:
- enumerate official support announcement/search results through the whole frozen calendar;
- inspect every official article whose title/body refers to funding interval/frequency adjustment;
- retain article ID/URL, publication timestamp, affected pair(s), exact adjustment timestamp, explicit old/new interval and exclusion reason;
- prove the enumeration reaches before 2024-01-01.

If Bitget's official archive cannot be enumerated completely, the verdict is SOURCE_BLOCKED even if individual search-engine results exist.

### 8. Source sample gate
EXTERNAL_SOURCE_PASS requires ALL:
- >=12 independent eligible shock clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- >=2 calendar years represented;
- no single cluster >35% of eligible asset-events;
- official archive enumeration crosses before 2024-01-01;
- canonical Bitget provenance resolved for every eligible event.

If official enumeration is complete but minimums fail:
VERDICT = EXTERNAL_INSUFFICIENT_SAMPLE.

If official enumeration/provenance cannot be demonstrated:
VERDICT = EXTERNAL_SOURCE_BLOCKED.

### 9. Outcome capability gate
Before any premium values are opened, the source stage may verify only:
- public endpoint HTTP/schema capability;
- historical query support for type=premium;
- symbol/category/interval availability metadata;
- timestamps and row counts if required.

Forbidden at source stage:
- premium OHLC values;
- funding rate values;
- mark/index values;
- price returns;
- volume;
- basis magnitudes;
- PnL.

### 10. If source gate passes
Create a separate immutable PRE-OUTCOME REPLICATION FREEZE before opening any premium OHLC value.

The replication freeze should reproduce BFIRS V0.2 unless a purely mechanical Bitget timestamp/API adaptation is required:
- T0 = official publication timestamp;
- Tm = first full minute strictly after T0;
- baseline [Tm-65m,Tm-5m);
- post [Tm+5m,Tm+65m);
- controls BTCUSDT, ETHUSDT, BNBUSDT, excluding any treated control in the same cluster;
- require >=2 valid controls;
- B(s,W) = median(abs(premium close));
- C_raw = B_baseline - B_post;
- C_e = treated C_raw - median control C_raw;
- C_k = median C_e within shock cluster;
- primary unit = shock cluster;
- same 2 bps economic floor only after unit equivalence of Bitget premium close to Binance premium-index ratio is verified BEFORE outcomes;
- exact one-sided sign test alpha 0.05;
- 10,000 cluster bootstrap;
- both chronological halves positive;
- no rescue.

### 11. Verdict taxonomy
Source:
- EXTERNAL_SOURCE_PASS
- EXTERNAL_INSUFFICIENT_SAMPLE
- EXTERNAL_SOURCE_BLOCKED

Outcome:
- EXTERNAL_PREMIUM_REPLICATION_SURVIVES
- EXTERNAL_PREMIUM_REPLICATION_FAILS

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
- no Bitget premium OHLC value has been opened for this family;
- no Bitget funding-rate value has been opened;
- no Bitget mark/index value, return or PnL has been opened.
