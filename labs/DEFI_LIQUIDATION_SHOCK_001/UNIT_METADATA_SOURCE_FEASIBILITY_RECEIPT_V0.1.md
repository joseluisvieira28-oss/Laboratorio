# DEFI-LIQUIDATION-SHOCK-001 — UNIT METADATA SOURCE FEASIBILITY RECEIPT V0.1

Date: 2026-09-26
Status: SOURCE-ONLY / OUTCOME-BLIND / FEASIBILITY PASS

## Purpose

Determine, prospectively and without reading economic outcomes, whether each frozen protocol family exposes
source-authoritative identifiers and unit metadata sufficient for later amount normalization.

This receipt does NOT claim population-wide unit coverage and does not authorize USD notional.

## Kamino Lend

Historical source:
`Kamino-Finance/klend@57074f4599a36ab0b433a71599b206c73efe1fd7`

`ReserveLiquidity` contains:
- `mint_pubkey: Pubkey`
- `mint_decimals`

`ReserveCollateral` contains:
- `mint_pubkey: Pubkey`

Liquidation accounts directly identify:
- repay_reserve
- withdraw_reserve
- withdraw_reserve_collateral_mint

Classification:
`KAMINO_UNIT_METADATA_SOURCE_RECONSTRUCTABLE`

## marginfi v2

Historical source:
`0dotxyz/marginfi-v2@f6d3d5616e293c9468333571c3ceb90bb2410b00`

Historical `Bank` contains:
- `mint: Pubkey`
- `mint_decimals: u8`

Liquidation accounts directly identify:
- asset_bank
- liab_bank

Classification:
`MARGINFI_UNIT_METADATA_SOURCE_RECONSTRUCTABLE`

## Drift v2

Historical source:
`velocity-exchange/protocol-v2@e77518dec79b9ade13680d1d8da1a479aca759b1`

Historical `SpotMarket` contains:
- `mint: Pubkey`
- `decimals: u32`
- `market_index: u16`
- oracle identity

Historical `PerpMarket` contains:
- `market_index: u16`
- oracle identity
- protocol precision constants are referenced explicitly in historical source.

Frozen liquidation args directly identify the relevant spot/perp market indexes.

Perp markets need not be forced into an SPL-mint identity; their protocol-native market index and frozen
precision semantics are the authoritative asset/unit identity.

Classification:
`DRIFT_UNIT_METADATA_SOURCE_RECONSTRUCTABLE`

## Save / Solend

For classic lending ABI, historical SPL token-lending reserve source
`fd662e5f878d58ad06d3cb6365171ebaec41b39d` contains:

- reserve liquidity mint pubkey;
- reserve liquidity mint decimals;
- reserve collateral mint pubkey.

For Save11-era official Solend SDK source:
`solendprotocol/public@91d2936930b412ce752be71c6d166deba65489cc`

the reserve state layout explicitly contains:
- `liquidityMintPubkey`
- `liquidityMintDecimals`
- `collateralMintPubkey`

Save0c / Save11 liquidation accounts directly identify repay and withdraw reserve accounts.

Classification:
`SAVE_SOLEND_UNIT_METADATA_SOURCE_RECONSTRUCTABLE`

## Global feasibility verdict

All frozen protocol families expose a defensible source route from event-level reserve/bank/market identity
to protocol-native asset/unit metadata.

Classification:

`UNIT_METADATA_SOURCE_FEASIBILITY_PASS`

## Important limitation

This is a schema/source feasibility result only.

Before any normalized amount or notional is used:
- event-specific reserve/bank/market metadata must be reconstructed under a frozen source route;
- missing metadata must be explicit;
- no decimals may be guessed;
- requested/max instruction arguments must remain distinct from realized transfers;
- USD notional remains forbidden until FINAL PRE-DISCOVERY authority explicitly defines it.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
usd_notional=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
