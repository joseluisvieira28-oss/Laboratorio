# COMPOUND-INVENTORY-PERSISTENCE-001 — SOURCE / MECHANISM FREEZE V0.1

Date: 2026-09-27
Status: NEW_ID / FROZEN_SOURCE_FIRST / MARKET OUTCOMES LOCKED
Parent source lineage: COMPOUND-INVENTORY-LIQUIDATION-001
Primary family: CREDIT
Secondary family: MICRO / FLOW

## Materially distinct mechanism

The parent source work established two facts without opening market prices:

1. Compound III USDC mainnet produced a large 2023–2024 liquidation/disposal population:
   - 894 AbsorbCollateral logs;
   - 999 BuyCollateral logs;
   - 505 absorbed borrowers lower bound;
   - 7 collateral assets.
2. Although the first same-asset disposal often begins immediately, a lower-bound event ledger identified 43 closed known-inventory episodes, of which 31 persisted more than 20 blocks and 27 persisted more than 100 blocks.

New frozen primitive:
**known positive protocol-owned seized-collateral inventory that remains after the liquidation transaction/block and must later be disposed.**

This is not generic liquidation-event direction and not borrower-health crowding.

## Source-state definition

For each collateral asset, reconstruct a conservative lower-bound inventory ledger using only:
- AbsorbCollateral collateralAbsorbed increments;
- BuyCollateral collateralAmount decrements;
- chronological block / transaction / log order.

At the 2023-01-01 left boundary, unknown prior inventory is never fabricated.
A BuyCollateral amount exceeding known lower-bound inventory may reduce the lower bound only to zero and is counted as boundary/unknown underflow.

Positive lower-bound inventory therefore means inventory is definitely known to exist from observed in-window absorptions.

## Candidate execution universe — source coverage only

Primary market source: Binance Data Vision Spot monthly 1m archives.

Frozen asset mapping:
- WETH collateral -> ETHUSDT
- LINK collateral -> LINKUSDT
- UNI collateral -> UNIUSDT
- COMP collateral -> COMPUSDT
- WBTC is excluded from the future cross-rate primary because BTCUSDT will be the benchmark leg.
- wstETH and cbBTC are source-excluded from V0.1 because no frozen direct Binance Spot mapping is asserted here.

Benchmark:
- BTCUSDT

No asset may be added after market outcomes.

## Source gate

Before any Discovery freeze, verify for each frozen symbol:
- monthly 1m archive route exists for every month 2023-01 through 2024-12;
- HTTP/source access is credential-free;
- ZIP payload is non-empty;
- no price rows, returns or PnL are emitted by the source gate.

Required source coverage:
5 symbols x 24 months = 120 / 120 archive objects available.

Failure => SOURCE_BLOCKED / SOURCE_PARTIAL.
Pass => source may proceed to a separate pre-outcome Discovery freeze.

## Future mechanism concept — NOT YET AUTHORIZED

If source coverage passes, a later frozen Discovery may test whether an asset underperforms BTC while known Compound seized-collateral inventory is positive.

The exact entry, exit, horizon, cross-rate return, inference and pass gates are intentionally not frozen by this source document.

## Firewall

market_price_values_emitted=false
returns_computed=false
pnl_computed=false
protected_2025_opened=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
paid_data=false
main_merge=false
