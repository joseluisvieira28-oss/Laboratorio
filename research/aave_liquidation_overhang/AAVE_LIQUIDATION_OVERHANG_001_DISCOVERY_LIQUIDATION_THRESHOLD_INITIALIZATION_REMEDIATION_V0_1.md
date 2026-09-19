# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY LIQUIDATION-THRESHOLD INITIALIZATION REMEDIATION V0.1

Status: **FROZEN AFTER RECONSTRUCTION FAILURE / BEFORE PREDICTOR OR OUTCOME**
Date: **2026-09-19**

## Triggering failure

Discovery run `35397902787` passed:
- preflight;
- 2023 calendar;
- global/eMode/oracle source.

Reserve reconstruction then failed in shards 0, 1, 4, 5 and 6 with the same class:

`DISCOVERY_RECONSTRUCTION_FAILURE — missing liquidation threshold`

Examples:
- USDT `0xdac17f958d2ee523a2206206994597c13d831ec7`;
- LUSD `0x5f98805a4e8be255a32880fdec7f6728c6568ba0`;
- GHO `0x40d16fc0246ad3160ccc09b8d0d3a2cd28ae6c2f`.

The predictor job and all 2023 liquidation-outcome jobs were skipped. No Discovery outcome was opened.

## Protocol-semantic finding

The official Aave V3 core implementation of `ConfiguratorLogic.executeInitReserve` creates:

`DataTypes.ReserveConfigurationMap memory currentConfig = DataTypes.ReserveConfigurationMap(0);`

and during reserve initialization sets only:
- decimals;
- active = true;
- paused = false;
- frozen = false.

It does **not** set LTV, liquidation threshold or liquidation bonus.

Therefore, after reserve initialization and before any later
`configureReserveAsCollateral(...)` call, the canonical liquidation threshold is exactly **0**.

`PoolConfigurator.configureReserveAsCollateral` later sets the liquidation threshold explicitly and emits
`CollateralConfigurationChanged(asset, ltv, liquidationThreshold, liquidationBonus)`.

## Authorized remediation

Only the reserve-replay initialization semantics change:

Before:
`cfg_lt={reserve: None}`

After:
`cfg_lt={reserve: 0}`

The existing event replay remains authoritative:
- every later `CollateralConfigurationChanged` overwrites the threshold;
- reserves remain excluded before their exact `init_block`;
- no threshold is imputed from outcomes;
- no reserve is dropped;
- no new data period is opened.

## Frozen science unchanged

Unchanged:
- 2023 Discovery period;
- daily 00:00 UTC snapshot clock;
- exact 37-reserve universe;
- point-in-time Aave oracle;
- eMode rules;
- 10% primary collateral shock;
- primary overhang definition;
- next-24h liquidation debt-notional outcome;
- Spearman statistic;
- stationary bootstrap and seed;
- all eligibility/pass gates;
- 2024 sealed until a canonical 2023 Discovery receipt;
- 2025/2026 locked;
- no market-return/PnL study;
- no live trading, wallets, orders, exchange mutation or main merge.

This is a reconstruction/protocol-semantics correction only and cannot be used to tune the scientific result.
