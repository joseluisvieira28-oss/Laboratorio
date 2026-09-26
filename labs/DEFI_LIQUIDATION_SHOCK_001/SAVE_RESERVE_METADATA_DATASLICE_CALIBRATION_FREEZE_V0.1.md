# DEFI-LIQUIDATION-SHOCK-001 — SAVE RESERVE METADATA DATASLICE CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Calibrate a minimal on-chain metadata resolver for exact Save/Solend reserve addresses without
retrieving reserve economic state.

## Layout authority

Pinned official source:
`solendprotocol/public@91d2936930b412ce752be71c6d166deba65489cc`
file:
`solend-sdk/src/state/reserve.ts`

The 619-byte Reserve layout places:
- liquidity mint pubkey at byte offset 42, length 32;
- liquidity mint decimals at byte offset 74, length 1;
- collateral mint pubkey at byte offset 227, length 32.

These offsets follow directly from:
- version: 1 byte
- LastUpdate: 9 bytes
- lendingMarket: 32 bytes
- liquidityMintPubkey: 32 bytes
- liquidityMintDecimals: 1 byte
and the frozen sequence through liquidityMarketPrice before collateralMintPubkey.

The same official source exposes RESERVE_SIZE = ReserveLayout.span and on-chain reserve parsing.

## RPC authority

Use official public Solana mainnet RPC:
`https://api.mainnet-beta.solana.com`

For exact reserve addresses only, issue two metadata-slice reads:

1. `getMultipleAccounts`
   - encoding: base64
   - dataSlice: offset=42, length=33
   - parse 32-byte liquidity mint + 1-byte decimals

2. `getMultipleAccounts`
   - encoding: base64
   - dataSlice: offset=227, length=32
   - parse collateral mint

Do not request or persist full reserve account data.
Do not persist lamports/rent metadata from the RPC response.

## Calibration references

Compare three pinned 2021 production reserves against
`SAVE0C_2021_PRODUCTION_RESERVE_REGISTRY_V0.1.json`:

- SOL reserve 8PbodeaosQP19SjYFx855UMqWxH2HynZLdBXmsrbac36
- USDC reserve BgxfHJDzm44T7XG68MYKx7YisTjZu73tVovyZSjJMpmw
- RAY reserve 9n2exoMQwMTzfw6NFoFFujxYPndWVLtKREJePssrKb36

Require:
- owner == frozen Solend program;
- both metadata slices present;
- liquidity mint exact match;
- decimals exact match;
- collateral mint exact match.

PASS:
`SAVE_RESERVE_METADATA_DATASLICE_3_OF_3_PASS`

Any mismatch:
`SAVE_RESERVE_METADATA_DATASLICE_CALIBRATION_FAIL_CLOSED`

## Consequence

PASS authorizes this minimal resolver only for exact reserve addresses that remain unresolved by
historical pinned config snapshots.

It does not authorize prices, balances, token amounts, USD notional, returns or PnL.

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
full_reserve_state=false
reserve_available_amount=false
reserve_borrowed_amount=false
token_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
