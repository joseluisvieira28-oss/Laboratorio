# SCL-LIQPULL-TOXICITY-FWD-001 — PROSPECTIVE PROTOCOL V0.1

Date: 2026-09-25
Status: FROZEN BEFORE PROSPECTIVE MARKET-DATA COLLECTION / RESEARCH ONLY

## Identity
- LAB_ID: SCL-LIQPULL-TOXICITY-FWD-001
- Primary edge family: MICRO
- Mathematical engine: passive-fill adverse selection / liquidity-withdrawal intensity
- Venue/source: Hyperliquid BTC perpetual, public mainnet WebSocket only
- Mode: prospective forward research; no historical 2026 backfill

## Anti-duplication / contamination map
This is not a rerun of legacy Scalping V1–V5.1, not simple aggTrade/taker imbalance, not generic queue imbalance, not H180 lead-lag, and not L2-RESILIENCY-001 replenishment-after-sweep.

The distinct mechanism is fill-conditioned adverse selection: liquidity providers may cancel/withdraw displayed same-side depth immediately before toxic marketable flow arrives. A passive order that remains at the touch may then be filled precisely when short-horizon markout is adverse.

Parent evidence may motivate the family but grants zero promotion credit. L2-RESILIENCY-001 remains separate and immutable.

## Source contract
Public subscriptions only:
- {"type":"l2Book","coin":"BTC"}
- {"type":"trades","coin":"BTC"}

Endpoint: wss://api.hyperliquid.xyz/ws

Raw collector requirements:
- persist provider payload plus local monotonic receive timestamp;
- no authenticated/user stream;
- no orders, cancels, wallet calls or exchange mutation;
- no derived returns, markouts, PnL, Sharpe, PF, signal win rate or parameter search inside the collector;
- log reconnect boundaries explicitly;
- hash every completed raw shard and write a machine-readable manifest.

## Prospective boundary
Only messages received after the canonical protocol-freeze commit may enter this MVE. No earlier 2026 message, archive, cache or backfill can be counted as forward evidence.

## Frozen first MVE
### Sampling
BTC only. Construct one eligible observation from the first valid l2Book snapshot at or after each integer UTC second. Both passive sides are evaluated symmetrically; no directional side selection.

### Pre-entry liquidity-pull measure
Use the immediately preceding 1,000 ms window.
For each side, compute top-5 displayed notional depth change and same-side consuming aggressive-trade notional.

For a hypothetical passive BUY at bid, same-side consumption is aggressive SELL notional.
For a hypothetical passive SELL at ask, same-side consumption is aggressive BUY notional.

Cancellation-residual notional:
`max(0, depth_top5_prev - depth_top5_now - aggressive_consuming_notional_1s)`

Liquidity-pull score:
`cancellation_residual_notional / max(depth_top5_prev, epsilon)`

No alternate lookback, depth count, residual definition or sign flip may be selected after outcomes.

### Hypothetical passive order / conservative fill proxy
- order size: 0.001 BTC;
- join the back of the displayed touch queue at the sampled best bid (BUY) and best ask (SELL);
- fill window: 2,000 ms;
- a fill is recognized only when cumulative opposing aggressive trade size at the exact joined price is at least `displayed_touch_size_at_entry + 0.001 BTC` before the quote is invalidated;
- cancellations after entry do not advance queue position in the fill proxy;
- if the exact fill condition is not proven, classify as NO_FILL, never infer a fill.

This intentionally conservative proxy may undercount fills. It must not be loosened after outcomes.

### Markout targets
For proved hypothetical fills, evaluate signed midpoint markout at +1s, +5s and +15s from the first timestamp at which the conservative fill condition is satisfied.

Direction convention:
- BUY: +1
- SELL: -1

Signed markout bps:
`direction * (mid_future / fill_price - 1) * 10_000`

Primary horizon: +5s. +1s and +15s are mandatory secondary horizons, not winner-selection alternatives.

## Primary hypothesis and falsification
Expected sign: larger pre-entry liquidity-pull score predicts worse subsequent passive-fill markout.

Primary estimand: UTC-day-clustered slope of 5s signed markout on liquidity-pull score.
Required sign: slope < 0.

Primary pass requires all:
1. >= 14 distinct UTC days;
2. >= 5,000 proved hypothetical fills globally;
3. >= 1,500 proved fills per side;
4. clustered/bootstrap 95% CI upper bound for the 5s slope < 0;
5. BUY slope < 0 and SELL slope < 0 separately;
6. top-quartile minus bottom-quartile 5s mean markout < 0.

If sample gates fail: INSUFFICIENT_FORWARD_SAMPLE.
If sample passes but any scientific gate fails: DISCOVERY_FAIL_NO_PROMOTION.
If all pass: MECHANISM_FORWARD_PASS only — not a tradable strategy and not Tier 2.

## Economics firewall
No claim that the mechanism is monetizable is allowed in this MVE. If mechanism passes, a new child identity must prospectively freeze:
- exact avoidance/entry threshold;
- queue/fill assumptions;
- maker fee from account/venue authority;
- spread capture;
- exit order type;
- latency/slippage;
- concurrency/notional;
- shadow sample and stop conditions.

No threshold may be optimized on this MVE's markout outcomes.

## Current fee context (informational, not an outcome gate)
Current Hyperliquid published base perp fees are 1.5 bps maker and 4.5 bps taker per fill. Account-specific discounts/rebates cannot be assumed. Any later economic child must freeze the applicable fee envelope before its outcomes.

## Governance
- research-only;
- no live trading;
- no authenticated endpoints;
- no orders/cancels;
- no wallet mutation;
- no leverage/position sizing;
- no main merge;
- no Render deployment under this authority;
- no post-outcome tuning;
- no inheritance of promotion status from L2-RESILIENCY-001;
- exact negative results stay negative.

## Source references
- Hyperliquid WebSocket: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket
- Hyperliquid subscriptions: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions
- Hyperliquid fees: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
