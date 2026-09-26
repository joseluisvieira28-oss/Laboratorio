# DEFI-LIQUIDATION-SHOCK-001 — INSTRUCTION TOKEN BALANCE RELATION CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Test whether raw SQD finalized-stream accepts the instruction include relation
`transactionTokenBalances: true` and returns token-balance identity/unit metadata
for the same transaction as a matched liquidation instruction.

The public SQD Solana stream SDK documents instruction include relation
`transactionTokenBalances: true`. This calibration verifies the raw Portal transport
before it may be used in the lab.

## Frozen references

Use the same exact successful references already validated by
`LENDING_TOKEN_UNIT_METADATA_12_OF_12_ACCOUNT_PASS`:

- Save0c slot 110526981
- Save11 slot 278496102
- Kamino slot 230572965

## Query

For each exact slot request:
- instruction identity/account/data fields;
- transaction signature/error;
- tokenBalance identity/unit fields only:
  - account
  - preMint
  - postMint
  - preDecimals
  - postDecimals
- instruction filter:
  - exact program ID
  - `transaction: true`
  - `transactionTokenBalances: true`

Do NOT send a standalone catch-all `tokenBalances: [{}]` filter.

## Exact PASS

For each reference:
1. exact liquidation instruction/signature/prefix is recovered;
2. tokenBalances are present in the returned same block payload;
3. for every frozen target token account used in the prior 12/12 calibration,
   a mint+decimals pair equal to the prior authority is present;
4. no amount fields are requested.

PASS:
`INSTRUCTION_TOKEN_BALANCE_RELATION_3_OF_3_REFERENCE_PASS`

Any HTTP schema rejection, absent relation rows, or metadata mismatch:
`INSTRUCTION_TOKEN_BALANCE_RELATION_CALIBRATION_FAIL_CLOSED`

## Consequence

PASS authorizes this relation only as a source-only transport optimization.
It does not alter event identity/population and does not authorize token amount values,
prices, USD notional, returns or PnL.

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
token_balance_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
