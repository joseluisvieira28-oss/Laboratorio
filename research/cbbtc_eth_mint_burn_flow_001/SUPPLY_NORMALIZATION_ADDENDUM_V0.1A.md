# CBBTC-ETH-MINT-BURN-FLOW-001 — SUPPLY NORMALIZATION ADDENDUM V0.1A

Frozen: 2026-09-26
Parent: OUTCOME_BLIND_FLOW_CENSUS_FREEZE_V0.1
Freeze timing: before the full flow census is opened.

## Purpose

Raw cbBTC mint/burn amounts scale with circulating supply. Preserve both raw flow and a dimensionless supply-normalized signed-flow state without using any price outcome.

## Supply anchor

At the exact block immediately before the census start boundary:
- query cbBTC totalSupply() from a public archive source.

At the exact census end block:
- query cbBTC totalSupply() again.

Historical state transport:
https://rpc-eth.blockmachine.io

## Reconstructed supply

Let S_0 be totalSupply at block start_block - 1.

Process the exact zero-address ledger chronologically:
- mint adds amount;
- burn subtracts amount.

For each UTC day t retain:
- prior_supply_raw;
- end_supply_raw;
- daily_net_raw;
- net_flow_rate_exact = daily_net_raw / prior_supply_raw when prior_supply_raw > 0.

No floating-point decision is authorized.

## Supply reconciliation gate

PREDICTOR_FLOW_CENSUS_PASS additionally requires:

reconstructed end supply == archive totalSupply() at the exact census end block.

If not exactly equal:
PREDICTOR_FLOW_CENSUS_BLOCKED.

No unexplained supply adjustment or imputation is permitted.

## Boundary

This addendum opens no market price, future return, direction, PnL, 2026 data or live action.
