# LICP-001 — EXTERNAL PRIOR EVIDENCE V0.1

Date: 2026-09-26
Purpose: hypothesis motivation only — NOT Crypto Lab outcome evidence

## Official source mechanics

### Bybit
Official V5 all-liquidation stream:
- topic: allLiquidation.<symbol>
- covers USDT, USDC and inverse contracts
- push frequency: 500 ms
- documentation states that the stream pushes all liquidations that occur
- payload includes event timestamp, symbol, liquidated-position side, executed size and bankruptcy price

Source:
https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation

### Binance USD-M
Official all-market forceOrder stream:
- push frequency: 1,000 ms
- for each symbol, only the latest liquidation order inside the 1,000 ms interval is published
- therefore the stream is a throttled snapshot and cannot be treated as complete liquidation volume

Source:
https://developers.binance.info/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Mini-Tickers-Stream

## Recent independent research

### Hidden Liquidity, Displayed Depth, and Execution Risk During a Bitcoin Perpetual Futures Liquidation Cascade (2026)
Reported study design:
- Bybit BTCUSDT perpetual
- 39-hour window containing an approximately 9% decline
- 7.16 million raw sub-fills
- 14,704 reconstructed parent market orders
- 50-level order book
- hidden liquidity appeared more frequently and at larger estimated ratios during the cascade

Implication for LICP-001:
Displayed book depth becomes especially unreliable during liquidation stress. The lab must not assume that displayed depth alone represents executable liquidity.

Source:
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6891658

### Anatomy of a Crypto Cascade: Minute-Level Evidence from the October 2025 Crash (2026)
Reported observations for the 10 Oct 2025 event include:
- BTC down 12.6% in ten minutes on Binance
- futures led the crash
- futures basis moved by USD 1,367 within eight minutes
- volume reached 22× baseline before the price trough
- SOL futures/spot divergence reached 13.4 percentage points
- intra-minute spread reached 6.79%

Implication:
Cascade mechanics naturally operate at a magnitude that can dominate normal API fee hurdles, unlike the sub-bps microstructure families already closed by the Crypto Lab.

Source:
https://papers.ssrn.com/sol3/Delivery.cfm/6579278.pdf?abstractid=6579278&mirid=1&type=2

### Early-warning heterogeneity across seven crypto-perpetual liquidation cascades (2026)
Reported result:
No tested early-warning state variable was invariant across all seven cascades. The study distinguishes endogenous buildup from sudden exogenous-shock cascades.

Implication:
LICP-001 should not be framed as a universal pre-crash predictor. Its first hypothesis should concern observable cascade ignition and subsequent propagation.

Source:
https://arxiv.org/abs/2607.27070

## Public replication package — Forced or Frantic? (2026)

Public repository:
https://github.com/edwinyeeshunwan/forced-or-frantic

Reported sample:
- Hyperliquid
- BTC + ETH
- Aug–Dec 2025
- 162 liquidation-triggered events
- approximately 760k liquidation fills
- 530k+ price/open-interest observations

Reported headline result:
- forced-deleveraging events dislocated prices about 0.55 percentage points more than voluntary-churn events of comparable liquidation size
- the public repository reports the result as robust across a predeclared 16-specification grid

Its bundled result files report:
- median peak dislocation: deleverage 2.10% vs churn 1.26%
- magnitude-controlled effect at the higher-powered 95th-percentile event trigger: approximately +0.55 percentage points

Important caveats:
- single venue
- working paper / independent research
- its raw pipeline uses public Hyperliquid data and a requester-pays archive path with small AWS transfer cost
- these results are external prior evidence only; they are not counted as Crypto Lab Discovery/OOS evidence

## Research consequence

The prior evidence is strong enough to justify a separate liquidation-cascade family because the natural event magnitude is tens to hundreds of basis points.

It is NOT sufficient to claim a tradable edge.

Crypto Lab must independently establish:
1. source integrity;
2. causal timestamps;
3. forward event construction;
4. target-venue propagation after event observability;
5. executable economics;
6. OOS/forward survival without post-outcome tuning.
