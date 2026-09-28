# DLS — SIGNED FLOW AMOUNT ROUTE CALIBRATION FREEZE V0.1

Date: 2026-09-28
Status: FROZEN SOURCE-ONLY MICRO-CALIBRATION

## Purpose

Before any population-scale signed-flow extraction, prove that the already-authorized SQD instruction -> transactionTokenBalances relation can materialize realized pre/post token amounts and owners for the exact three reference liquidations previously frozen in the token-balance relation authority.

References are unchanged:
- Save0c slot 110526981
- Save11 slot 278496102
- Kamino slot 230572965

## Fields authorized

tokenBalance:
- account
- preMint
- postMint
- preDecimals
- postDecimals
- preOwner
- postOwner
- preAmount
- postAmount

No prices, returns, USD notional or later transaction linkage.

## PASS

For all 3 references:
1. exact successful liquidation instruction/signature recovered;
2. transaction token balances materialize;
3. at least two frozen target token accounts expose parseable pre/post amount values;
4. at least one frozen target account has a non-zero realized delta;
5. mint/decimals are not contradictory to the prior unit authority.

PASS:
SIGNED_FLOW_AMOUNT_ROUTE_3_OF_3_PASS

Otherwise:
SIGNED_FLOW_AMOUNT_ROUTE_BLOCKED

PASS authorizes a separately frozen population extraction. It does not itself assign buy/sell direction.

## Firewall

prices=false
returns=false
usd_notional=false
2025_market_outcomes=false
2026_market_outcomes=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
