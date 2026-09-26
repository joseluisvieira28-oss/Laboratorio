# AMM-LVR-CROSSVENUE-001 — FORWARD ENGINE IMPLEMENTATION FREEZE V0.2

**Frozen:** 2026-09-23 before reading or accepting V0.1 economic sweep outcomes  
**Authority:** FORWARD_ECONOMIC_FREEZE_V0.1  
**MVE:** AMM-LVR-CROSSVENUE-001-FWD-MVE1  
**Status:** CANONICAL IMPLEMENTATION FOR SCIENTIFIC FORWARD EVIDENCE

V0.2 supersedes V0.1 for scientific forward evidence. V0.1 is retained as engineering-only because pre-result code review found two authority mismatches: one Ethereum block was reused across a sequential 48-state sweep, and CEX depth was fetched by REST rather than the frozen WebSocket market stream. V0.1 outcome signs are irrelevant and may not enter promotion evidence.

## 1. Per-state causal boundary

Every pair × direction × notional state is an independent causal observation attempt.

For each state:
1. require fresh pre-quote Binance WebSocket partial-depth snapshots;
2. freeze the latest Ethereum block number immediately before the DEX quote;
3. quote every canonical Uniswap V3 fee tier at exactly that block;
4. record quote completion monotonic time;
5. wait for the first fresh WebSocket partial-depth snapshot received after quote completion for every CEX hedge symbol required by that state;
6. evaluate the frozen hedge against those post-quote books only.

A later candidate state must use a new latest Ethereum block boundary. No block may be intentionally carried forward to make the DEX stale relative to CEX.

## 2. CEX source

Canonical source: wss://data-stream.binance.vision

Streams:
- ethusdt@depth20@100ms
- btcusdt@depth20@100ms
- linkusdt@depth20@100ms
- pepeusdt@depth20@100ms
- shibusdt@depth20@100ms
- usdcusdt@depth20@100ms

Partial-depth top 20 is accepted for the exact frozen notionals only. If 20 levels cannot fill an exact hedge quantity, that state is CEX_DEPTH_INSUFFICIENT; REST backfill is forbidden for scientific evidence.

Local UTC receive time, monotonic receive time and exchange update id are persisted. No authenticated endpoint is used.

## 3. Input sizing

For USDT input, amountIn = exact frozen notional.

For all other input tokens:
- use the freshest pre-quote WebSocket ask snapshot;
- mechanically solve the maximum base quantity purchasable for the exact USDT notional using observed asks;
- floor to native token units.

No mid, last trade or post-quote resizing.

## 4. DEX quote

Use Ethereum Uniswap V3 QuoterV2 at the per-state frozen block.

Quote exact input across all frozen standard fee tiers with canonical pools. Select maximum amountOut for the identical amountIn.

The Quoter output already incorporates pool fee and price impact for that path.

## 5. CEX hedge cycle

After DEX quote completion, use only first-post-quote WebSocket books.

- replenish exact DEX input token on CEX asks, unless input is USDT;
- liquidate exact DEX output token on CEX bids, unless output is USDT;
- WETH→ETHUSDT, WBTC→BTCUSDT, USDC→USDCUSDT, LINK/PEPE/SHIB→matching USDT spot;
- sweep levels until exact quantity is filled;
- insufficient top-20 depth => state unavailable.

Gross USDT PnL = executable output-token liquidation proceeds − executable input-token replenish cost.

## 6. Frozen costs

Unchanged from FORWARD_ECONOMIC_FREEZE_V0.1:
- BASE CEX taker = 10 bps per actual hedge leg;
- STRESS CEX taker = 20 bps per actual hedge leg;
- BASE gas = 300,000 × (base fee + p50 recent priority);
- STRESS gas = 500,000 × (base fee + p90 recent priority);
- gas ETH replenishment valued at the causal post-quote ETHUSDT ask.

Builder/direct fee-recipient transfer and failed-inclusion probability remain UNBOUND in this engine. Therefore no row can exceed KNOWN_COST_SURVIVOR / ACCESSIBILITY_UNPROVEN.

## 7. Scientific use

The first V0.2 sweep is still an engineering pilot:
- it can validate causal implementation;
- it can identify raw known-cost positive states;
- it counts zero independent Discovery events unless the frozen event-state machine later observes a <=0 → >0 transition and reset condition.

No result from one sweep can promote the lab.

V0.1 REST/fixed-block outputs are explicitly excluded from all statistical tests, promotion gates and economic verdicts.