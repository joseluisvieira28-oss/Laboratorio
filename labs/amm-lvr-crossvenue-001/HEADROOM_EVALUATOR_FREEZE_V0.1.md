# AMM-LVR-CROSSVENUE-001 — HEADROOM EVALUATOR FREEZE V0.1

**Frozen:** 2026-09-23 before any internal event-level economic outcome is computed  
**Authority:** FORWARD_ECONOMIC_PROTOCOL_V0.1 + AUTHORITY_RECONCILIATION_V0.2  
**Status:** INTERIM DIAGNOSTIC ONLY / ZERO VERDICT CREDIT

## Objective

Measure whether a prospectively observed DEX event leaves any executable economic room **before** the still-unbound competitive inclusion layers.

This evaluator does not claim FULL_COST PnL.

## Event state

Raw source is the protocol-compliant forward capture.

A unique diagnostic event-state is keyed by:
- Ethereum block number;
- exact Uniswap pool address.

If more than one captured swap touches the same pool in the same block, the state is evaluated once and the earliest captured transaction hash is retained as the reproducible anchor.

The DEX state is the canonical end-of-block state at the captured block number. This tests whether an independent participant observing the completed block has an actionable cross-venue convergence state for the next transaction opportunity.

It does not claim to reconstruct transaction-index intermediate state.

## Frozen universe

Only the six already-frozen pair families:
- WETH-USDC
- WETH-USDT
- WBTC-WETH
- LINK-WETH
- PEPE-WETH
- SHIB-WETH

Both directions are mechanically evaluated for each event-state.

No token, DEX, pool or direction can be added after outcomes.

## Frozen notionals

Exactly:
- 500 USDT
- 1,000 USDT
- 5,000 USDT

Input token quantity is sized from the T0 Binance Spot ask depth for the exact USDT budget. USDT input equals the exact bucket.

Insufficient top-20 depth => INFEASIBLE for that direction/bucket.

## DEX execution

Use only the exact event pool.

Uniswap V3:
- QuoterV2 exact-input call at the captured block number;
- exact event pool fee tier.

Uniswap V2:
- exact getReserves state at the captured block number;
- standard 0.30% constant-product exact-input formula.

No cross-pool best-route selection is allowed in this evaluator.

## Direction rule

At each event-state and notional:
1. compute both directions at T0;
2. choose the direction with the higher **gross executable convergence value at T0**;
3. freeze that direction for the same event-state/notional at +250 ms, +1000 ms and +3000 ms.

The later latency buckets may not reselect direction.

## CEX execution

For every latency bucket use the already-captured first Binance Spot depth snapshot at or after:
- T0
- T0 +250 ms
- T0 +1000 ms
- T0 +3000 ms

Replenish the DEX input token on asks and liquidate the DEX output token on bids, sweeping observed top-20 depth.

No mid, last trade, candle, interpolation or REST backfill.

## Costs deducted in HEADROOM

DEX fee is embedded in the exact DEX quote/formula.

Deduct:
- Binance Spot taker 10 bps on each actual CEX hedge leg;
- Ethereum base-fee burn using frozen 300,000 gas units;
- ETH conversion at the captured T0 ETHUSDT ask.

Do **not** set these to zero:
- priority fee;
- direct builder / fee-recipient transfer;
- unobserved private/bundle payment;
- failed-inclusion probability.

They remain UNBOUND.

Therefore:

PRE_INCLUSION_HEADROOM =
gross executable convergence
- CEX taker fees
- base-fee gas burn.

Positive headroom means only that this amount remains available to pay the missing competitive inclusion stack.

## Outputs

For each event-state/notional/latency:
- direction frozen at T0;
- gross USDT and bps;
- CEX fee;
- base-fee gas;
- pre-inclusion headroom USDT and bps;
- executable / infeasible status.

Summary may report counts and distribution of positive headroom but must state:
- FULL_COST_PNL = NOT COMPUTED;
- SCIENTIFIC_VERDICT = NOT OPEN;
- DISCOVERY_EVENT_CREDIT = 0.

No survival or promotion conclusion may be drawn before the controlling >=500 events AND >=14 days gate with all required cost layers bound.
