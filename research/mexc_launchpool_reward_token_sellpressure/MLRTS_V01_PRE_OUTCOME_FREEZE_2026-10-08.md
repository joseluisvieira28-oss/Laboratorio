# MEXC-LAUNCHPOOL-REWARD-TOKEN-SELLPRESSURE-001 — V0.1 PRE-OUTCOME FREEZE
Date: 2026-10-08
Status: FROZEN BEFORE ANY REWARD-TOKEN MARKET OUTCOME

## Economic distinction
This is NOT a rescue or sign inversion of MEXC-LAUNCHPOOL-MX-DEMAND-001.

The dead parent analogue tested:
Launchpool activation -> LONG MX relative to BTC for 24h.

This new family tests a different asset and mechanism:
Launchpool distributes a newly listed project token to participants -> newly circulating reward inventory can create initial sell pressure in the PROJECT TOKEN after its MEXC spot listing.

## Frozen hypothesis
For an official MEXC Launchpool event that is also an initial MEXC spot listing of the reward token:

Expected sign:
PROJECT TOKEN underperforms BTC over the first 24 hours after exact MEXC spot-listing T0.

## Source calendar
2025-01-01 through 2026-09-30 UTC.

2026-10-01 onward is excluded from historical Discovery and reserved for later prospective work.

## Eligible event
ALL must hold:
1. official MEXC Launchpool announcement;
2. reward token symbol unambiguous;
3. announcement states initial listing/new listing on MEXC, not merely an already-traded token campaign;
4. exact MEXC spot trading start T0 is recoverable from official MEXC material;
5. token/USDT spot market identity is recoverable from official/public MEXC symbol metadata;
6. no duplicate campaign for the same initial listing;
7. token has exact public 15m market candles at entry and +24h.

Launchpool activation time is NOT the T0 unless it equals the official spot-listing time.

## Source gate
Before any reward-token or BTC outcome is opened:
- >=10 eligible initial-listing Launchpool events;
- >=10 unique reward-token symbols;
- >=2 calendar years;
- exact listing T0 for every event;
- public reproducible MEXC source route.

Otherwise classify SOURCE_INSUFFICIENT_SAMPLE or SOURCE_BLOCKED.

## Frozen market construction
Market data:
official/public MEXC spot history only.

For event i:
- asset = PROJECT/USDT
- control = BTC/USDT
- entry = first exact 15m candle open at or after official spot-listing T0
- exit = exact entry +24h 15m candle open
- primary response:
  R_rel_24h = ln(PROJECT_exit / PROJECT_entry) - ln(BTC_exit / BTC_entry)

Expected sign: NEGATIVE.

Diagnostics frozen before outcomes:
- project raw 24h log return
- BTC raw 24h log return
- relative 1h
- relative 6h
Diagnostics cannot replace the 24h primary.

## Frozen Discovery adjudication
Report:
- N
- negative observations
- mean and median R_rel_24h
- negative fraction
- exact one-sided sign-test p for negative direction
- 10,000-sample bootstrap 90% CI for mean, seed 20261008
- leave-one-out maximum mean
- calendar-year mean/median diagnostics
- largest absolute observation share of total absolute response

SELLPRESSURE_DISCOVERY_SURVIVES requires ALL:
1. N >=10
2. median R_rel_24h <0
3. negative fraction >0.50
4. exact one-sided sign p <0.10
5. bootstrap 90% UPPER bound for mean <0
6. leave-one-out MAXIMUM mean <0
7. largest absolute observation share <=0.40

Otherwise: NO_EDGE_DISCOVERY.

## No-rescue
After any reward-token outcome is opened:
- no sign inversion;
- no 1h/6h promotion;
- no alternate horizon;
- no alternate T0;
- no reward-size filtering;
- no project-category filtering;
- no deleting extreme winners/losers;
- no switching BTC control;
- no post-outcome selection of only shortable/perpetual-listed tokens.

## Role
Research-only Discovery.
Even a SURVIVES result is not automatic live/micro-live authorization.

## Governance
No authenticated API.
No account read.
No order.
No exchange mutation.
No wallet.
No spending.
No main merge.
