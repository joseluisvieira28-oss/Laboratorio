# SCL-LIQPULL-TOXICITY-FWD-001 — IMPLEMENTATION CLARIFICATION V0.1.1

Date: 2026-09-25
Status: FROZEN PRE-DATA / ADDITIVE TO PROTOCOL V0.1
Parent protocol freeze commit: edd69260fe4b86cc453223df38ff0a69bde980d3

This clarification resolves implementation details before any prospective market-data collection. It does not change the economic mechanism, hypothesis, horizons, sample gates, or pass/fail rules.

## Provider-time semantics
- Sampling and all scientific horizons use provider timestamps in milliseconds.
- For each integer UTC second, use the first valid l2Book snapshot whose provider timestamp is at or after that boundary.
- A markout horizon uses the first valid l2Book snapshot at or after fill_time + horizon.
- Maximum admitted markout-snapshot lateness is 1,100 ms. If exceeded, that candidate fill is incomplete and excluded.

## Hyperliquid public trade-side semantics
For the public WsTrade stream:
- B / BUY = aggressive buy;
- A / SELL = aggressive sell.
Unknown side labels fail closed.

Thus:
- passive BUY queue is consumed only by aggressive SELL trades at the exact joined bid price;
- passive SELL queue is consumed only by aggressive BUY trades at the exact joined ask price.

## Top-5 depth
Displayed top-5 depth is notional sum(px * sz) over the first five levels on the relevant side. Books with empty sides, non-positive/non-finite price or size, or crossed/locked top of book fail closed.

## Fill proxy details
- Entry touch queue is frozen at displayed touch size at the entry snapshot.
- Post-entry cancellation or displayed-size reduction does not improve hypothetical queue position.
- The fill threshold remains entry_touch_size + 0.001 BTC.
- Joined price invalidation occurs when the relevant best bid/ask changes away from the exact joined price before fill.
- Exact-price aggressive trades only count toward the conservative fill proof.
- No inferred or partial fill is allowed.

## Statistical implementation
Primary estimand remains the slope of +5s signed markout on liquidity-pull score.
- Global slope: ordinary least-squares slope with intercept.
- Cluster unit: UTC day.
- Bootstrap: resample UTC days with replacement.
- Replicates: 10,000.
- Random seed: 20260925.
- CI: percentile 95% interval.
- Quartile diagnostic: highest 25% pull-score proved fills minus lowest 25% pull-score proved fills, using +5s signed markout.

The existing required gates remain unchanged:
- >=14 UTC days;
- >=5,000 proved fills total;
- >=1,500 BUY and >=1,500 SELL;
- global +5s slope < 0;
- bootstrap CI upper bound < 0;
- BUY slope < 0;
- SELL slope < 0;
- top-minus-bottom quartile +5s mean markout < 0.

Classification remains:
- sample gate failure => INSUFFICIENT_FORWARD_SAMPLE;
- adequate sample but any scientific gate failure => DISCOVERY_FAIL_NO_PROMOTION;
- all gates pass => MECHANISM_FORWARD_PASS only.

## Firewalls
No fees, PnL, PF, Sharpe, leverage, sizing, live orders, account endpoints, exchange mutation, historical 2026 backfill, threshold optimization, or Tier claim are authorized.
