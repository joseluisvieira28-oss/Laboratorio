# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — SAME-TX DEX ROUTE CLASSIFICATION FREEZE V0.1

Date: 2026-09-28
Status: FROZEN / SOURCE-MECHANISM ONLY / MARKET OUTCOMES LOCKED

## Purpose

Resolve the strongest surviving source-level alternative explanation:
same-transaction onward collateral transfer may represent custody/router movement rather than an actual exchange interaction.

This diagnostic reuses the exact deterministic 64-transaction sample frozen before any route result:
ascending SHA256(lowercase BuyCollateral transaction hash), first 64 unique transactions from the 2023-2024 corpus.

No market price, return, execution price, slippage, PnL, future outcome, or protected 2025 market data may be read.

## Frozen evidence rule

For each sampled transaction:
1. reconstruct each BuyCollateral event and recipient exactly as in source V0.1.3;
2. inspect only log topics occurring after the BuyCollateral log;
3. mark RECOGNIZED_DEX_SWAP if a later log matches one of the prospectively enumerated exchange event ABI signatures below;
4. do not use swap amounts or prices;
5. unrecognized routes remain UNCLASSIFIED, never NON_SWAP.

Recognized ABI event signatures:
- Uniswap V2-style: Swap(address,uint256,uint256,uint256,uint256,address)
- Uniswap V3-style: Swap(address,address,int256,int256,uint160,uint128,int24)
- Balancer Vault: Swap(bytes32,address,address,uint256,uint256)
- Curve classic: TokenExchange(address,int128,uint256,int128,uint256)
- Curve underlying: TokenExchangeUnderlying(address,int128,uint256,int128,uint256)
- Curve uint-index: TokenExchange(address,uint256,uint256,uint256,uint256)
- Curve underlying uint-index: TokenExchangeUnderlying(address,uint256,uint256,uint256,uint256)

Topics are computed from these literal ABI strings at runtime using Ethereum Keccak-256.

## Outputs

- exact sample size;
- BuyCollateral events;
- recipient-inferred events;
- same-tx onward-transfer events;
- events with >=1 recognized DEX swap log after BuyCollateral;
- share of inferred events with recognized DEX swap evidence;
- share of onward-transfer events with recognized DEX swap evidence;
- counts by recognized signature;
- transaction-level examples by hash.

## Interpretation

There is no scientific PASS threshold for economic edge.

Route evidence states:
- DEX_ROUTE_EVIDENCE_STRONG if >=60% of onward-transfer events have a recognized DEX swap after BuyCollateral;
- DEX_ROUTE_EVIDENCE_PRESENT if >0% but <60%;
- DEX_ROUTE_EVIDENCE_NOT_DEMONSTRATED if 0%.

These labels apply only to the same-transaction route mechanism.
They do not establish direction, persistence, tradability, PnL or edge.

## Firewall

source_only=true
market_prices_opened=false
swap_prices_computed=false
swap_amounts_used_for_economics=false
returns_computed=false
pnl_computed=false
protected_2025_market_outcomes_opened=false
direction_selected=false
holding_period_selected=false
live_trading=false
orders=false
capital=false
main_merge=false
