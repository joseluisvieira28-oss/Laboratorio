# OKX-FUNDING-INTERVAL-REGIME-REPLICATION-001
## V0.1 EXTERNAL REPLICATION SOURCE / MECHANISM FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY OKX MARKET OUTCOME

### 1. Purpose
Independently replicate the economic mechanism that survived Binance BFIRS V0.2 on a different exchange.

Known Binance discovery is acknowledged and may justify the replication target, but MUST NOT be used to alter OKX event eligibility after OKX outcomes are opened.

### 2. Replication question
When OKX publicly announces a shorter funding settlement interval for an already-live USDT perpetual contract, does the contract's absolute perp/index premium compress toward zero after the announcement relative to contemporaneous unaffected controls?

### 3. Independence
Exchange: OKX, not Binance.
Announcement authority: official OKX Help / Announcements.
Market outcome authority, if later authorized by a second freeze: official OKX public market-data endpoints and/or defensible public OKX historical archives.

No Binance market outcome enters the OKX primary statistic.

### 4. Source calendar
Mechanically enumerate official OKX funding-interval adjustment announcements from:
- 2023-01-01 through 2025-12-31 inclusive.

2026 OKX outcomes remain CLOSED in V0.1.

### 5. Eligible shock
An asset-event qualifies only if ALL:
1. OKX USDT perpetual explicitly identified;
2. contract already live before the change;
3. official OKX publication precedes effective timestamp;
4. exact effective UTC date/time explicit;
5. old and new funding intervals explicit;
6. new interval is SHORTER than old interval;
7. fixed announced transition, not merely a generic automatic rule;
8. not an initial listing/launch term;
9. not a delisting/settlement bundle.

Cluster = official article + exact effective UTC timestamp + old->new interval.

### 6. Explicit exclusions
- interval lengthening/reversion;
- automatic dynamic changes without a separately announced fixed transition;
- launch specifications;
- non-USDT contracts;
- delistings;
- outcome-selected cases.

### 7. Source / replication feasibility gate
REPLICATION_SOURCE_PASS requires ALL:
- >=12 independent eligible clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- >=2 calendar years;
- no single cluster >35% of eligible asset-events;
- official/public historical market data capability is demonstrated for every eligible event for:
  a) a one-minute perp price or mark/premium series;
  b) a contemporaneous OKX index-price series sufficient to construct/observe perp-index premium;
- capability checking is metadata/schema/timestamp only; no price/premium/return values may be opened.

If the official announcement universe is complete but sample minimums fail:
REPLICATION_INSUFFICIENT_SAMPLE.

If provenance/enumeration or defensible historical outcome capability cannot be demonstrated:
REPLICATION_SOURCE_BLOCKED.

### 8. Outcome blindness
Allowed:
- announcement titles/URLs/publication timestamps;
- effective timestamps;
- instruments;
- old/new interval;
- endpoint/archive availability;
- schemas, row counts and timestamp coverage only.

Forbidden:
- prices;
- mark/index values;
- premium values;
- funding values;
- returns;
- volumes;
- volatility;
- OI/liquidations/PnL.

### 9. Analysis gate
Only after REPLICATION_SOURCE_PASS:
create a separate pre-outcome analysis freeze.

The intended replication target is the SAME Binance discovery endpoint:
abnormal compression of absolute perp/index premium after public announcement, using independent shock clusters as the primary unit.

Exact OKX data mapping, controls, windows, missingness, statistic, floor and tests must be frozen before any OKX market value is opened.

### 10. Governance
Research-only; fail-closed.
No main merge.
No trading/orders/wallets/account reads/private endpoints/exchange mutation/spending.
No post-outcome tuning.

### 11. Outcome-access declaration
No OKX market price, mark, index, premium, funding, return, volume, volatility, OI, liquidation or PnL outcome for this replication family has been opened at freeze time.
