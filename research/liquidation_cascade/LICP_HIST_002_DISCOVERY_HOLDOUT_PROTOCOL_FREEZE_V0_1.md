# LICP-HIST-002 — CROSS-VENUE DISCOVERY / HOLDOUT PROTOCOL FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE

## Event source
Pinned external Hyperliquid event table:
- commit fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04
- only t0 and symbol are permitted

The event family is downside / long-liquidation triggered.

No external classification, OI outcome, liquidation magnitude, price outcome, recovery outcome or permanent/transitory outcome may be used.

## Partitions
- DISCOVERY: 2025-08-10 00:00 UTC through 2025-10-31 23:59 UTC
- LOCKED HOLDOUT: 2025-11-01 00:00 UTC through 2025-12-31 23:59 UTC

Discovery code MUST reject any event in the holdout.

## Target
Official Binance Vision USD-M Futures 1-minute klines:
- BTCUSDT for BTC events
- ETHUSDT for ETH events

## Causal observable time
External event t0 is the LEFT label of a completed 5-minute liquidation bin.

Therefore:
- earliest theoretical observable time = t0 + 5 minutes
- PRIMARY entry proxy = 1-minute candle open at t0 + 6 minutes
- OPTIMISTIC ceiling entry proxy = 1-minute candle open at t0 + 5 minutes

The +1 minute primary delay is frozen before outcomes and represents coarse signal-processing / cross-venue reaction latency.

## Direction
The source event is triggered by long-liquidation notional.
Frozen continuation direction = SELL / SHORT.

No reversal rescue is allowed if continuation fails.

## Horizons
Measured from each entry proxy:
- 5 minutes
- 15 minutes
- 30 minutes
- 60 minutes

Future price proxy = 1-minute candle open at entry_time + horizon.
No use of intrabar high/low to improve an entry or exit.

## Historical directional move
For SELL / SHORT continuation:

gross_directional_bps = (entry_open - future_open) / entry_open × 10,000

This is NOT executable PnL because 1-minute candles do not provide BBO/spread/fill information.

## MEXC-transfer economic ceiling
For triage only:

transfer_ceiling_net_bps = gross_directional_bps - 16 bps

The 16 bps hurdle is the frozen current MEXC API taker/taker round-trip fee assumption.
No spread/slippage is added, so this deliberately favors survival.

This metric must NEVER be called Binance PnL or MEXC backtest PnL.

## Discovery survival criterion
A PRIMARY-latency horizon survives Discovery only when ALL are true:
- pooled n >= 50;
- BTC n >= 15;
- ETH n >= 15;
- pooled mean gross_directional_bps > 16 bps;
- pooled median gross_directional_bps > 0;
- at least 2 distinct Discovery calendar months have positive mean gross_directional_bps.

No criterion uses the optimistic t0+5m ceiling.

## Candidate selection
If multiple horizons satisfy all survival rules:
- select the horizon with the highest PRIMARY pooled mean transfer_ceiling_net_bps;
- exact tie => select the shorter horizon.

Freeze the selected horizon before opening HOLDOUT.

If no horizon survives:
LICP_HIST_002_DISCOVERY_NO_EDGE.

## Holdout
HOLDOUT is single-pass and remains unopened until a Discovery survivor has been serialized and frozen.

No rescue tuning after holdout.

## Interpretation boundaries
A Discovery/Holdout survivor would demonstrate cross-venue continuation from Hyperliquid event timing into Binance futures at coarse minute resolution.

It would NOT prove:
- MEXC transferability;
- sub-second propagation;
- executable fills;
- live profitability;
- live-trading authority.

Those require the canonical LICP-001 MEXC forward path.
