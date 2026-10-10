# AMM-LVR-CROSSVENUE-001 — FORWARD ENGINE IMPLEMENTATION FREEZE V0.1

**Frozen:** 2026-09-23 before first internal forward economic sweep  
**Authority:** FORWARD_ECONOMIC_FREEZE_V0.1  
**MVE:** AMM-LVR-CROSSVENUE-001-FWD-MVE1  
**Mode:** read-only engineering pilot

## Snapshot boundary

Each sweep freezes one Ethereum block number before any economic quote. All Uniswap V3 Quoter calls in that sweep use exactly that block tag.

CEX hedge books are fetched only **after** the DEX quote for the candidate being evaluated. The local UTC and monotonic receive times are persisted.

## USD notional sizing

For each frozen input bucket 100 / 500 / 1000 / 5000 USD:
- USDT input uses the bucket directly.
- Every other input token is sized using the Binance Spot top ask observed before the DEX quote: input_qty = bucket / ask.
- Amounts are floored to native token units. No post-outcome resizing.

## DEX route

For each pair × direction × notional, quote exact-input against all standard fee tiers 100 / 500 / 3000 / 10000 that have a canonical Uniswap V3 pool.

Choose the tier with the **largest amountOut** for the identical amountIn. This is the prospectively frozen execution rule.

Uniswap Quoter amountOut is executable-route evidence only; no mid-price substitution is allowed.

## CEX hedge economics

Every DEX swap is evaluated as a USDT inventory cycle:

1. replenish the exact DEX input token by buying it on Binance Spot asks;
2. liquidate the exact DEX output token by selling it into Binance Spot bids;
3. if the token is USDT, that leg has no CEX trade;
4. WETH maps to ETHUSDT, WBTC to BTCUSDT, USDC to USDCUSDT; frozen alt symbols map directly to their USDT spot markets.

The Binance public depth endpoint is swept level-by-level up to 100 levels. A candidate is unavailable if depth cannot fill the required exact quantity.

Gross PnL = executable USDT proceeds from output token - executable USDT cost to replenish input token.

This deliberately avoids mid, last trade, candle or single-top-level fantasy fills.

## CEX fees

BASE: 10 bps on the USDT value of each actual CEX hedge leg.

STRESS: 20 bps on each actual CEX hedge leg.

No BNB discount, VIP tier or promotional fee is allowed.

## Gas implementation

Use eth_feeHistory over the most recent 20 blocks with reward percentiles [50, 90].

- p50 priority = median of the 20 p50 reward observations.
- p90 priority = median of the 20 p90 reward observations.
- base fee = final baseFeePerGas value returned for the next block estimate.

BASE gas cost:
300,000 × (base_fee + p50_priority)

STRESS gas cost:
500,000 × (base_fee + p90_priority)

ETH gas is converted to USDT using the first causally observed ETHUSDT ask book after the DEX quote.

## Known-cost PnL

BASE_KNOWN = gross PnL - BASE CEX fees - BASE gas cost.

STRESS_KNOWN = gross PnL - STRESS CEX fees - STRESS gas cost.

Direct builder/coinbase payment, failed inclusion probability and competitive latency are **not** set to zero. They remain UNBOUND.

Therefore the strongest possible result from this engine is:
KNOWN_COST_SURVIVOR / ACCESSIBILITY_UNPROVEN.

No row may be classified FULL_COST_SURVIVOR.

## Engineering sweep

The first sweep evaluates all:
- 6 frozen pairs
- 2 directions
- 4 notional buckets

= 48 candidate states, subject only to technical executability.

The first sweep is an engineering pilot. It cannot promote the lab regardless of profitability.

No parameter, pair, fee tier, notional, cost or direction may be changed because of the first result.
