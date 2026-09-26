# DEFI-LIQUIDATION-SHOCK-001 — KAMINO UNIT METADATA RECOVERY PRECEDENCE ADDENDUM V0.3

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Why V0.3

Two source-layer facts were established before any market outcome access:

1. Kamino Release 1.6.0 changes account layout from 16 fixed accounts to 20 fixed accounts + remaining_accounts.
2. Population token-balance metadata can omit one user-side account even when the corresponding reserve-side account has exact mint+decimals; official successful token-transfer semantics prove both transfer accounts share the mint.

Therefore the current Kamino unit decoder authority is the combination of:
- KAMINO_HISTORICAL_ACCOUNT_LAYOUT_ADDENDUM_V0.2.md
- KAMINO_UNIT_METADATA_TRANSFER_IDENTITY_ADDENDUM_V0.2.md

## Frozen partition precedence

### Original V0.1 retained
- kamino-202311
- kamino-202312
- kamino-202401
- kamino-202402

These already passed before either newly observed source condition affected the population.

### V0.3 current authority
Re-query with the current source-backed decoder for:
- kamino-202403
- kamino-202404
- kamino-202405
- kamino-202406
- kamino-202407
- kamino-202408
- kamino-202409
- kamino-202410
- kamino-202411
- kamino-202412

V0.3 is selected for these months regardless of whether an older V0.1/V0.2 receipt happened to pass or fail.

### Save11
All Save11 partitions retain original V0.1 authority.

## Required V0.3 behavior

- canonical event population unchanged;
- missing=0;
- extra=0;
- duplicates=0;
- unsupported historical layout=0;
- token metadata conflicts=0;
- every event resolves debt underlying, collateral token and collateral underlying;
- direct pair resolutions and source-transfer fallback resolutions reported separately.

## Terminal

Aggregate:
`KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS`

Exact totals:
- Kamino 60,699
- Save11 13,300

## Firewall

prices=false
returns=false
pnl=false
economic_outcomes=false
token_amounts=false
protected_2025_2026_market_outcomes=false
post_outcome_tuning=false
live_trading=false
merge_main=false
