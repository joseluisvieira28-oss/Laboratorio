# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — DIRECT DEX LINK FREEZE V0.2

Date: 2026-09-28
Status: FROZEN / SOURCE-MECHANISM ONLY / MARKET OUTCOMES LOCKED

## Purpose

Strengthen V0.1.2 DEX route evidence by requiring a direct on-receipt linkage between the sold collateral route and a recognized DEX swap emitter.

The exact deterministic 64-transaction sample and the recognized DEX ABI signature list are unchanged.

## Frozen direct-link rule

For each BuyCollateral event:

1. infer the collateral recipient exactly as in V0.1.3;
2. identify all later ERC20 Transfer logs in the same transaction where:
   - token = the BuyCollateral collateral asset;
   - from = inferred recipient;
   - amount > 0;
3. identify all recognized DEX swap logs after BuyCollateral;
4. mark DIRECT_DEX_LINK=true if at least one qualifying collateral onward transfer has:
   - transfer.to == recognized swap log emitter address.

No swap amount, price, reserve, tick, quote, slippage, market return or PnL is used.

## Source route labels

- DIRECT_DEX_LINK_STRONG: >=60% of onward-transfer events satisfy DIRECT_DEX_LINK.
- DIRECT_DEX_LINK_PRESENT: >0% but <60%.
- DIRECT_DEX_LINK_NOT_DEMONSTRATED: 0%.

This is only a mechanism-route classification. It does not establish net selling direction at external venues, persistence after block confirmation, tradability, edge or PnL.

## Firewall

source_only=true
market_prices_opened=false
swap_prices_computed=false
returns_computed=false
pnl_computed=false
protected_2025_market_outcomes_opened=false
direction_selected_from_market_outcomes=false
holding_period_selected_from_market_outcomes=false
live_trading=false
orders=false
capital=false
main_merge=false
