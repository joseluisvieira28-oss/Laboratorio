# BINANCE-LISTING-INFORMATION-CASCADE-001 — PRE-OUTCOME FREEZE V0.1
Date: 2026-10-05
Status: FROZEN BEFORE OUTCOME INSPECTION
Branch: binance-listing-information-cascade-v0.1-prereg-2026-10-05

## Research question
When Binance publicly announces a new spot listing for a token that is already continuously tradable on another liquid centralized venue, does the public announcement create a reproducible, executable information shock on that pre-existing venue?

## Economic mechanism
A Binance spot-listing decision expands expected future distribution, liquidity and access. The test is NOT the post-listing Binance opening auction. The treatment timestamp is the first official Binance public announcement timestamp T0. Outcomes are measured only on venues where the asset was already trading before T0.

## Source gate
Authority for event time: official Binance announcement page, using its displayed publication timestamp.
Market outcomes: public, unauthenticated exchange REST market-data endpoints only.
No account endpoints, keys, wallets, orders or trading.

## Frozen inclusion rules
1. Binance spot listing announcement must expose an exact publication timestamp.
2. Asset must have existed and traded on the selected comparison venue for >=24h before T0.
3. A valid 1-minute bar must exist immediately before T0.
4. Exclude stablecoins, wrapped fiat-like assets, simultaneous token genesis/TGE where no pre-existing venue history exists, and announcements whose exact first-public timestamp cannot be defended.
5. Multiple assets in one announcement are separate observations sharing T0.
6. Development census begins with calendar-year 2024 announcements. 2025+ is CLOSED holdout and MUST NOT be opened in V0.1 discovery.

## Frozen primary venue hierarchy
For each asset, select the first venue with valid pre-T0 public 1m history in this fixed order:
1. Bybit spot
2. OKX spot
3. Gate spot
No venue shopping after outcomes.

## Frozen outcomes
Entry reference P0 = close of the final complete 1m bar strictly before T0.
Returns: close(T0+1m)/P0-1, close(T0+5m)/P0-1, close(T0+15m)/P0-1, close(T0+60m)/P0-1.
Path metrics: MFE and MAE over first 5m, 15m, 60m using minute highs/lows.
Volume shock = first 5m quote/base volume divided by median non-overlapping 5m volume over T-24h to T-1h.

## Frozen hypothesis and direction
H1: public Binance listing announcements create a positive information shock on pre-existing venues.
Primary endpoint: median +15m return > 0.
Secondary: hit-rate(+15m)>60%, median +5m >0, and median 5m volume shock >=2x.

## Frozen survival gate
SURVIVES_DISCOVERY only if ALL hold:
- n >= 12 valid 2024 observations;
- median R15 > +0.75%;
- R15 positive hit-rate >= 65%;
- median R5 > +0.50%;
- median 5m volume shock >= 2.0x;
- leave-one-out sign stability: median R15 remains >0 after dropping any one observation;
- no single observation contributes >35% of summed positive R15.
Otherwise NO_EDGE_DISCOVERY. If n<12 because defensible sources/venue history are insufficient: SOURCE_BLOCKED, not NO_EDGE.

## Execution sanity
Discovery is gross-information-effect only. No claim of tradable net edge. If it survives, a separate freeze is required before spread/slippage/latency/cost modelling and before opening 2025+ holdout.

## Anti-hindsight
No threshold, venue hierarchy, inclusion rule, endpoint, direction or gate may be changed after any 2024 outcome is inspected. Any remediation after outcomes must be technical/source-only and preserve this freeze.

## Governance
Research-only. No main merge. No live trading. No exchange mutation. No private endpoints. No post-outcome tuning.
