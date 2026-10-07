# OKX-FUNDING-INTERVAL-BASIS-REPLICATION-001
## V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY OKX MARKET OUTCOME

### 1. Purpose
Independent external-exchange replication of the economic mechanism discovered by BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001 (BFIRS), using OKX public sources.

Known Binance evidence:
- V0.2 2023-2025 Discovery: SURVIVES_FUNDING_INTERVAL_DISCOVERY.
- V0.3 2026 Jan-Sep holdout: HOLDOUT_INSUFFICIENT_SAMPLE, with ZERO 2026 market outcomes opened.
- V0.4 prospective confirmation is accumulating new post-freeze shocks and remains outcome-sealed.

This OKX family is external supporting replication. It MUST NOT reuse Binance outcomes to select OKX events, horizons, assets, signs, controls or thresholds beyond literal mechanism replication.

### 2. Economic question
When OKX shortens the funding-fee settlement interval of an already-live USDT-margined perpetual contract at a pre-announced effective timestamp, does the contract-specific mark-vs-index basis compress after the public announcement relative to unaffected controls?

Mechanism:
shorter settlement cadence changes the timing and normalization of funding pressure, which may reduce persistent perp-vs-index dislocation.

This is NOT:
- an outright directional price-return hypothesis;
- an extreme-funding fade;
- a listing effect;
- a delisting effect;
- an automatic cap/floor transition inferred from outcomes.

### 3. Why the endpoint differs from Binance
The Binance discovery used 1-minute premiumIndexKlines directly.

For historical OKX replication, V0.1 freezes a construct based on official historical mark-price and index-price candles because those public endpoints retain recent years of history, while the premium-history endpoint does not provide the same multi-year depth.

If the source gate passes, the later pre-outcome freeze must define the exact mark/index basis formula before any values are opened.

This is therefore an EXTERNAL CONSTRUCT REPLICATION, not an exact metric replication.

### 4. Frozen source calendar
Official OKX announcement universe:
- 2023-01-01 through 2025-12-31 inclusive.
- 2026 excluded.

Official announcement authority:
- OKX Help Center -> Announcements -> Trading updates.
- Canonical/global OKX help pages preferred.
- Region mirrors may be used only to locate a canonical article; conflicting regional content is a provenance blocker for that event unless resolved by a canonical/global page.

### 5. Eligible event definition
An independent shock is one exact:
official article + effective timestamp + interval transition.

An asset-event qualifies only if ALL are true before market outcomes:
1. USDT-margined perpetual contract explicitly identified;
2. contract was already live before the change;
3. official article publication date/time precedes the effective adjustment time;
4. old funding interval and new funding interval are both explicit in official OKX content;
5. new interval is strictly SHORTER than old interval;
6. exact effective UTC date/time is explicit or mechanically fixed by a table that unambiguously pairs the contract with adjustment date/time;
7. not an initial listing/launch specification;
8. not a delisting/automatic-settlement bundle;
9. not an interval lengthening/reversion;
10. not an automatic rule transition with no pre-announced fixed event timestamp.

Multiple contracts sharing one article and exact effective timestamp/transition are one independent shock cluster.

### 6. Source enumeration
Frozen discovery route:
- enumerate the official OKX Trading updates archive pages in reverse chronological order;
- continue until the archive crosses before 2023-01-01;
- inspect every article whose title or official body refers to funding interval, funding fee settlement interval, or funding-rate interval adjustment;
- retain article URL, publication metadata, affected contracts, before/after intervals, effective UTC timestamp and exclusion reason.

Search-engine results may help diagnose parser coverage but may not define the eligible universe.

### 7. Source sample gate
EXTERNAL_SOURCE_PASS requires ALL:
- >=12 independent eligible shock clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- >=2 calendar years represented;
- no single shock cluster >35% of eligible asset-events;
- canonical provenance resolved for every eligible event.

If official archive enumeration is complete but minimums fail:
VERDICT = EXTERNAL_INSUFFICIENT_SAMPLE.

If official archive enumeration/provenance cannot be demonstrated:
VERDICT = EXTERNAL_SOURCE_BLOCKED.

### 8. Outcome source reserved for later
If and only if EXTERNAL_SOURCE_PASS:

Primary outcome source family:
- OKX public historical mark price candles: /api/v5/market/history-mark-price-candles
- OKX public historical index candles: /api/v5/market/history-index-candles
- 1-minute bar size where supported.

No market values may be opened during this source gate.

### 9. Required pre-outcome replication freeze
If EXTERNAL_SOURCE_PASS, create a separate immutable PRE-OUTCOME REPLICATION FREEZE before requesting mark/index candle values.

That freeze must specify exactly:
- T0 and full-minute alignment;
- baseline/post windows;
- basis formula from mark and index;
- absolute-basis compression statistic;
- unaffected-control construction;
- missingness rules;
- cluster aggregation;
- sample gates;
- economic floor;
- statistical test;
- bootstrap;
- chronological robustness;
- exact verdict.

No outcome-driven rule changes.

### 10. Replication philosophy
The later OKX analysis should preserve BFIRS conceptually:
- publication-time information event;
- direction-agnostic compression toward zero;
- contemporaneous controls;
- shock-cluster as evidence unit;
- no asset-level pseudo-replication;
- no rescue horizons/subsets.

Because OKX uses a reconstructed mark/index basis rather than Binance premiumIndexKlines, a successful OKX result is independent supporting replication, not by itself a literal replication of the Binance metric.

### 11. Verdict taxonomy
Source:
- EXTERNAL_SOURCE_PASS
- EXTERNAL_INSUFFICIENT_SAMPLE
- EXTERNAL_SOURCE_BLOCKED

Outcome replication:
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
At the time of this freeze:
- no OKX mark-price candle values have been opened for this family;
- no OKX index-price candle values have been opened for this family;
- no OKX funding-rate values have been opened for this family;
- no OKX returns/PnL have been opened for this family.
