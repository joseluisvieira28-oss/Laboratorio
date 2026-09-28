# DLS — SIGNED FLOW TOKEN-BALANCE RELATION BINDING ADDENDUM V0.1

Date: 2026-09-28
Status: FROZEN SOURCE-TRANSPORT BINDING / NO MARKET OUTCOMES

## Observed transport shape

The exact three-reference amount diagnostic returned HTTP 200, exact successful liquidation instruction/signature matches, and transactionTokenBalances containing realized preAmount/postAmount.

The Portal response omitted tokenBalance.transactionIndex (null) in these relation-included rows.

This is a transport serialization limitation. It does not erase the query relation that requested transactionTokenBalances from an exact matching instruction.

## Frozen binding rule

For an exact reference query:
1. require exact slot;
2. require exact program + d1/d8 discriminator;
3. require isCommitted=true;
4. require exact frozen transaction signature;
5. require exactly one matching successful reference instruction in the response.

For each returned tokenBalance:
- if transactionIndex is present, require equality with the matched instruction transactionIndex;
- if transactionIndex is null/omitted, a row may be bound only when its account is one of the prior frozen target token accounts for that exact reference.

No non-target row with missing transactionIndex may be used for the calibration PASS.

## Scope

Transport/source identity only.
Does not assign market direction.

prices=false
returns=false
2025_market_outcomes=false
2026_market_outcomes=false
live_trading=false
orders=false
merge_main=false
