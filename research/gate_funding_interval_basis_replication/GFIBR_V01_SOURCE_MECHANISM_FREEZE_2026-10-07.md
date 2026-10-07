# GATE-FUNDING-INTERVAL-BASIS-REPLICATION-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY GATE MARKET OUTCOME

### 1. Purpose
Independent external-exchange replication of the BFIRS economic mechanism on Gate.

Known Binance evidence:
- 2023-2025 Discovery: SURVIVES_FUNDING_INTERVAL_DISCOVERY.
- 2026 Jan-Sep holdout: HOLDOUT_INSUFFICIENT_SAMPLE with ZERO market outcomes opened.
- prospective Binance confirmation remains outcome-sealed.

This Gate family may not use Binance outcomes to tune Gate event selection, windows, controls, signs, thresholds or subsets.

### 2. Economic hypothesis
A pre-announced shortening of the funding settlement interval for an already-live Gate USDT perpetual contract creates abnormal compression of perp-vs-index basis after the public announcement relative to unaffected controls.

This is an external construct replication.
It is not an outright price-direction hypothesis.

### 3. Frozen source calendar
- 2023-01-01 through 2025-12-31 inclusive.
- 2026 excluded.
- No Gate mark/index/funding-rate values have been opened for this family.

### 4. Official/public authorities
Source:
- Gate official Announcements pages, including the official Fees announcement archive/category.
- Canonical Gate announcement article pages.

Mechanics-only API:
- GET /api/v4/futures/usdt/funding_rate
- during source gate, code may read ONLY settlement timestamps (t)
- code MUST NOT read/store/print/use funding-rate values (r)

Reserved outcome source if source passes:
- GET /api/v4/futures/usdt/candlesticks
- mark price via contract=mark_<CONTRACT>
- index price via contract=index_<CONTRACT>

No authentication/private endpoints.

### 5. Eligible event
A Gate asset-event qualifies only if ALL:
1. official Gate article publication timestamp exists;
2. article is published within 2023-2025;
3. named USDT perpetual contract was already live before the change;
4. article explicitly announces a funding-interval/funding-rate-interval change;
5. exact effective UTC date/time is explicit;
6. new interval is shorter than old interval;
7. not a listing/launch;
8. not a delisting/automatic-settlement bundle;
9. not a lengthening/restoration;
10. pre/post settlement cadence can be recovered mechanically from public funding-history timestamps without reading r values.

When the article states only the NEW interval, infer OLD interval from the last 3 pre-effective settlement gaps.
Require at least 2 of 3 pre gaps to agree on a canonical cadence in {1h,2h,4h,8h,12h,24h}.
For post cadence, require at least 2 of first 3 post-effective settlement gaps to agree and equal the announced new interval.
If old or post cadence is unresolved, exclude that asset-event.

### 6. Information timestamp
T0 for later analysis = official article publication timestamp.
Effective timestamp is source/mechanics metadata only and is not the primary information timestamp.

### 7. Independent shock cluster
One independent shock =
official article ID + publication timestamp + effective timestamp + old->new interval.

Multiple contracts sharing the same announcement/effective transition remain one independent shock.

### 8. Source enumeration
Complete official archive enumeration is required.
The source gate must:
- enumerate the official Gate announcement archive/category backwards;
- cross before 2023-01-01;
- inspect every article whose title/body refers to funding interval/funding rate interval adjustment;
- retain publication timestamp, article ID/URL, affected contracts, announced new interval, effective UTC, inferred old interval, exclusion reason.

Search-engine results may diagnose coverage but may not define the eligible universe.

### 9. Source sample gate
EXTERNAL_SOURCE_PASS requires ALL:
- >=12 independent eligible shock clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- >=2 calendar years represented;
- no single cluster >35% of eligible asset-events;
- official archive enumeration crossed before 2023;
- canonical provenance resolved for every eligible event.

If archive enumeration is complete but thresholds fail:
EXTERNAL_INSUFFICIENT_SAMPLE.

If archive/provenance/transport cannot be defended:
EXTERNAL_SOURCE_BLOCKED.

### 10. If source gate passes
Create a separate PRE-OUTCOME REPLICATION FREEZE before opening any mark/index candles.

The later freeze must specify:
- publication T0 and full-minute alignment;
- same BFIRS baseline/post windows unless a purely mechanical API timestamp adaptation is required;
- exact mark/index basis formula;
- BTC_USDT / ETH_USDT / BNB_USDT controls where available and untreated;
- absolute basis compression;
- shock-cluster aggregation;
- frozen missingness;
- 2 bps economic floor unless basis scaling requires a pre-outcome deterministic unit conversion;
- same one-sided sign test alpha 0.05;
- 10,000 cluster bootstrap;
- chronological-half robustness;
- no rescue.

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
- no Gate mark/index values opened;
- no Gate funding-rate r values read/used;
- no Gate returns/PnL opened.
