# PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001 — DISCOVERY FREEZE V0.1

Date: 2026-09-27
Status: FROZEN_PRE_OUTCOME / DISCOVERY 2022–2024 ONLY
Primary family: RV
Secondary family: CARRY

## 1. Scientific question

Does the fixed yield embedded in a Pendle PT **30 calendar days before expiry** exceed the subsequently observed variable-yield path of the same market's underlying exposure, after excluding markets with explicit points metadata?

This is not a PT-to-par convergence test and does not claim tradable PnL.

## 2. Pre-outcome source authority

Canonical source-completeness receipt:
PENDLE_SOURCE_COMPLETENESS_RECEIPT_V0.1

Frozen source facts established without emitting yield outcomes:
- 802 markets enumerated;
- 107 Ethereum markets expired before 2025;
- 73 have non-empty points metadata and are excluded;
- 34 are POINTS_FREE_SOURCE_CANDIDATE;
- all 34 have PT/YT identity metadata and reward-token metadata;
- 10/10 deterministic historical probes passed;
- v3 historical schema exposes impliedApy, underlyingApy, underlyingInterestApy and APY breakdown fields.

2025+ remains protected and unopened.

## 3. Frozen population

Include every market satisfying all:
1. chainId == 1;
2. expiry < 2025-01-01T00:00:00Z;
3. points metadata empty/absent under the frozen source-completeness rule;
4. immutable market address, expiry, accountingAsset, PT identity and YT identity present;
5. historical v3 endpoint returns the required T-30 / future-path observations.

No exclusion may use the sign or magnitude of implied APY, future underlying APY, protocol performance, market return or profitability.

Reward-token metadata is not an exclusion because Pendle's historical underlyingApy / APY breakdown is the canonical variable-yield source. Non-tokenized points are excluded because no defensible historical valuation is frozen.

## 4. Frozen observation time

For each market:
T0 = expiry timestamp minus exactly 30 calendar days.

Use the latest historical daily observation timestamp <= T0 with absolute staleness <= 36 hours.

If none exists, the market is SOURCE_INCOMPLETE and is excluded with count/reason preserved.

No alternate T-7/T-14/T-60/T-90 horizon may rescue the result.

## 5. Frozen fixed-yield leg

At T0 read impliedApy.

Convert it to a 30-day fixed-yield equivalent:

FIXED_30D = (1 + impliedApy_T0)^(30/365) - 1

Require impliedApy_T0 > -1 and finite.

## 6. Frozen future-variable leg

Use daily underlyingApy observations strictly after T0 and <= expiry.

For each chronological interval between consecutive eligible daily observations, cap interval length at 36 hours; any larger gap makes the market SOURCE_INCOMPLETE.

Convert each annualized APY into a time-proportional compound factor using the actual interval in seconds:

factor_i = (1 + underlyingApy_i)^(dt_i / (365*86400))

VARIABLE_30D = product(factor_i) - 1

Require each underlyingApy_i > -1 and finite.

The final covered interval must reach expiry with <=36h terminal gap.

No interpolation across larger gaps.

## 7. Primary economic quantity

PREMIUM_30D = FIXED_30D - VARIABLE_30D

Frozen expected sign: positive.

Interpretation: a positive premium means the fixed PT yield observed 30 days before expiry exceeded the subsequently observed variable-yield path under the canonical Pendle source convention.

This is a structural yield-premium diagnostic, not executable PnL.

## 8. Independence and inference

Hourly/daily source rows are never independent observations.

Primary independence unit: protocol.

For each protocol, average PREMIUM_30D across all eligible markets from that protocol.

Primary statistic:
- equal-weight mean protocol premium.

Primary uncertainty:
- deterministic bootstrap over protocols, 10,000 resamples, seed 20260927.

Primary pass requires ALL:
1. >= 12 eligible protocols;
2. >= 24 eligible markets;
3. mean protocol premium > 0;
4. bootstrap 95% lower bound > 0;
5. >= 60% of eligible protocols have positive mean premium;
6. leave-one-protocol-out mean premium remains > 0 for every protocol.

If any fail: DISCOVERY_FAIL_NO_PROMOTION.

If all pass: DISCOVERY_MECHANISM_SUPPORTED.

No Tier promotion is possible from this Discovery alone.

## 9. Mandatory diagnostics — zero rescue credit

Report but do not use to rescue:
- market-level mean / median premium;
- positive-market fraction;
- premium by expiry;
- premium by accounting asset;
- protocol contribution/concentration;
- fixed and variable 30d components;
- T0 staleness distribution;
- source exclusions and reasons.

No subgroup, protocol, accounting asset, maturity, sign inversion or alternate horizon may become the new primary after outcomes.

## 10. Protected validation

All markets with expiry >= 2025-01-01 remain unopened by this Discovery.

A pass may authorize only a separately frozen independent validation protocol on a future untouched population.

A fail closes this exact T-30 points-free implementation. No threshold/horizon/subgroup rescue.

## 11. Execution boundary

This test does not establish executable alpha.

No quote/slippage/gas/fee PnL is computed.
Any later tradable translation requires separate source/execution authority using point-in-time executable PT liquidity.

## 12. Firewall

2025_plus_opened=false
market_return_pnl=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
paid_data=false
main_merge=false
post_outcome_tuning=false
