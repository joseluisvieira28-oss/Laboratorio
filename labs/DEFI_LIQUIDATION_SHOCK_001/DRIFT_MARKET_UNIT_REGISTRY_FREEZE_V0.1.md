# DEFI-LIQUIDATION-SHOCK-001 — DRIFT MARKET UNIT REGISTRY FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Build a source-defensible historical registry for every Drift spot/perp market index that can appear in the frozen liquidation population.

No prices, oracle values, trade data, returns, PnL or economic outcomes are used.

## Source authority

Repository history:
`velocity-exchange/protocol-v2`

Frozen interval:
`2022-11-04T00:00:00Z <= commit_date < 2025-01-01T00:00:00Z`

Files:
- `sdk/src/constants/spotMarkets.ts`
- `sdk/src/constants/perpMarkets.ts`
- `sdk/src/constants/numericConstants.ts`
- `programs/drift/src/state/spot_market.rs`
- `programs/drift/src/state/perp_market.rs`

Lower-bound structural commit:
`e77518dec79b9ade13680d1d8da1a479aca759b1`

## Spot registry

For every historical `MainnetSpotMarkets` snapshot in the interval, extract:
- marketIndex
- mint
- precisionExp / decimals source token
- symbol only as descriptive metadata
- launchTs when present
- source commit/date

Frozen unit mapping:
`spot_market_index -> mint + decimals`

Allowed precision-exp symbols must resolve only through pinned numeric constants or literal source:
- QUOTE_PRECISION_EXP = 6
- LAMPORTS_EXP = 9
- FIVE = 5
- SIX = 6
- EIGHT = 8
- NINE = 9
- or an explicit literal numeric exponent.

If an observed spot market index has conflicting mint or decimals across historical snapshots:
`DRIFT_SPOT_MARKET_UNIT_REGISTRY_CONFLICT_FAIL_CLOSED`

Symbol/oracle changes do not by themselves alter unit identity and may be retained as aliases/history.

## Perp registry

For every historical `MainnetPerpMarkets` snapshot extract:
- marketIndex
- symbol/baseAssetSymbol as descriptive aliases
- launchTs
- source commit/date

Frozen protocol-native unit semantics from pinned source:
- BASE / AMM reserve precision = 1e9
- BASE precision exponent = 9
- QUOTE precision = 1e6
- QUOTE precision exponent = 6

Perp market indices do not require an SPL mint identity.

A market index may change descriptive symbol/oracle labels, but:
- it must not be reused for a different launch identity;
- contradictory launchTs for the same index fail closed unless a source-only lineage explanation is frozen prospectively.

## Historical completeness rule

Use authenticated GitHub history for each file path across the full frozen interval.

For every commit touching a market-constant file:
1. retrieve exact file snapshot at that commit;
2. parse the full `MainnetSpotMarkets` or `MainnetPerpMarkets` array;
3. update the union registry;
4. record first_seen / last_seen commits and aliases;
5. detect unit-identity conflicts.

Do not select commits based on market outcomes.

## Population coverage rule

This registry alone is not terminal population PASS.

After `DRIFT_FIELD_ENRICHMENT_POPULATION_PASS`, collect the unique:
- spot market indexes appearing in frozen liquidations;
- perp market indexes appearing in frozen liquidations.

Every observed index must resolve in the historical registry.

PASS:
`DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS`

Any unresolved observed market index:
`DRIFT_MARKET_UNIT_REGISTRY_PENDING_SOURCE_COMPLETION`

Any contradictory unit identity:
`DRIFT_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED`

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
requested_max_amount_values=false
limit_price_values=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
