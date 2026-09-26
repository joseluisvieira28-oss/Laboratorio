# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C HISTORICAL TOKEN IDENTITY ADDENDUM V0.2

Date: 2026-09-26
Status: FROZEN TECHNICAL CORRECTION / SOURCE-ONLY / OUTCOME-BLIND

## Trigger

V0.1 independent ABI reconciliation failed closed only because Save0c account positions 0 and 1
are historical user token accounts that are now closed and therefore return null from current-state
`getMultipleAccounts`.

All other V0.1 checks passed:
- exact successful transaction and slot;
- exact 12-account instruction identity;
- exact 9-byte instruction data;
- tag 0x0c;
- Clock / Token Program tail positions;
- Solend ownership for reserve / obligation / lending-market positions;
- SPL Token ownership for surviving token-account positions 3 and 5.

This addendum does not alter the candidate ABI.

## Historical token-account identity source

Use SQD finalized-stream at the exact frozen slot:

`110526981`

Request ONLY token-balance identity fields:
- `account`
- `preMint`
- `postMint`

Do NOT request:
- preAmount
- postAmount
- decimals
- prices
- balances
- token quantities

Target only the two closed accounts:

0. `GsXfKKyK2pDm4Tn8WdYBzfGUrSBDFh4ZGh7y2SV7sTtc`
1. `9c9JC96jg7nSovijiTpxWQAXvLMf6sbMuT9jR6RFRqb3`

## Exact PASS rule

For each of the two accounts, the exact historical slot must contain at least one token-balance
record whose `account` equals the target and has at least one non-empty mint identity
(`preMint` or `postMint`).

This demonstrates that each account was represented as an SPL-token balance account in the
historical transaction context without inspecting numerical balances.

V0.2 PASS requires:
1. V0.1 structural checks remain unchanged and passed except current-state existence of accounts 0/1;
2. both historical target accounts pass this token-balance identity check;
3. no token amount fields are requested or persisted.

PASS:
`SAVE0C_HISTORICAL_TOKEN_IDENTITY_2_OF_2_PASS`

Combined ABI promotion is authorized only if this receipt and the unchanged V0.1 structural evidence
are jointly satisfied.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
balances=false
token_amounts=false
token_decimals=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
