# AAVE-LIQUIDATION-OVERHANG-001 — PRE-SOURCE AUTHORITY V0.1

Status: **FROZEN / SOURCE-CENSUS ONLY / OUTCOME-BLIND**  
Date: **2026-09-17**  
Repository: `joseluisvieira28-oss/Laboratorio`  
Branch: `aave-liquidation-overhang-v0.1`

## Governance

Research-only. Fail-closed. This authority permits only source/provenance census work.

Forbidden at this stage:
- future price/return inspection;
- liquidation-overhang calculation;
- health-factor threshold optimization;
- PnL, win rate, PF, drawdown or trading performance;
- 2025/2026 data access;
- live trading, exchange/wallet mutation, orders or execution webhooks;
- merge to `main`;
- post-outcome tuning or rescue.

Flags:
- `ECONOMIC_VALUES_DECODE_ALLOWED=false` for this census
- `PRICE_OUTCOMES_ALLOWED=false`
- `RETURNS_ALLOWED=false`
- `PNL_ALLOWED=false`
- `2025_ACCESS_ALLOWED=false`
- `2026_ACCESS_ALLOWED=false`

## Lab identity

- LAB_ID: `AAVE-LIQUIDATION-OVERHANG-001`
- Primary family: `CREDIT`
- Secondary family: `MICRO`
- Mechanism: latent borrower-level forced-sale inventory before realized liquidation.

## Economic hypothesis — not yet tested

Aave borrowers whose collateral/debt state is close to liquidation eligibility create a latent forced-flow inventory. If a sufficiently adverse but prospectively frozen collateral-price shock would push a material amount of borrower collateral below the liquidation boundary, subsequent Aave liquidation notional should increase and may later justify a separately authorized market-impact/execution study.

This source census does **not** choose the adverse-shock size, calculate health factor, calculate liquidation eligibility, or inspect any later outcome.

## Novelty firewall

This is not `AAVE-CREDIT-STRESS-001`, whose frozen predictor is the daily change in Aave V3 Ethereum USDC `variableBorrowRate` and whose outcome is next-day BTC return.

This is not `DEFI-LIQUIDATION-SHOCK-001`, which studies realized liquidation/forced-flow events. Here the intended predictor is borrower-level liquidation overhang observable **before** realized liquidation.

## Canonical source objects

Chain: Ethereum mainnet only.

Aave V3 Ethereum Core Pool:
- `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`

Pool Configurator:
- `0x64b761D848206f447Fe2dd461b0c635Ec39EbB27`

Primary historical transport for this census:
- SQD Portal dataset `ethereum-mainnet`
- endpoint `https://portal.sqd.dev/datasets/ethereum-mainnet/stream`

The transport is not the economic authority. Ethereum mainnet event identity and Aave official contract/event definitions are the authority.

## Frozen census block envelope

- from block: `16,490,000` (pre-activation safety lead-in around the 2023-01-27 Ethereum V3 activation)
- through block: `21,525,890`
- hard timestamp ceiling: `2024-12-31T23:59:59Z`

The census must fail closed if any returned block timestamp exceeds the hard ceiling.

## Source census objectives

Without decoding event `data` economic amounts, prove that the protected-safe archive can reproducibly enumerate:
- `Supply`
- `Withdraw`
- `Borrow`
- `Repay`
- `ReserveUsedAsCollateralEnabled`
- `ReserveUsedAsCollateralDisabled`
- `LiquidationCall`
- `ReserveDataUpdated`
- `UserEModeSet`
- Configurator `ReserveInitialized`

The census may use indexed address topics to enumerate stable participant identities and candidate borrower addresses. It may count events and unique identifiers. It must not decode amounts, prices, rates, balances, health factors, liquidation bonuses, debt values, collateral values or future market outcomes.

## Required integrity checks

1. every requested chunk is returned successfully;
2. every log contains block number, tx hash, log index, address and topic0;
3. `(transactionHash, logIndex)` is globally unique;
4. every Pool log address matches the frozen Pool;
5. every Configurator log address matches the frozen Configurator;
6. returned timestamps stay <= 2024-12-31T23:59:59Z;
7. at least one historical `Borrow`, `Repay`, `LiquidationCall`, `ReserveDataUpdated` and `ReserveInitialized` event is recovered;
8. participant identities can be deterministically extracted from indexed topics for the supported event families;
9. a deterministic structural SHA256 receipt is emitted;
10. no 2025/2026 traversal occurs.

## Permitted terminal states

- `SOURCE_CENSUS_PASS`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `PROVENANCE_FAILURE`
- `INSUFFICIENT_SOURCE_COVERAGE`

`NO_EDGE` is forbidden at this phase.

A pass authorizes only a separately frozen borrower-state reconstruction source gate. It does not authorize Discovery, returns, PnL or trading.