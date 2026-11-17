# LVAC-001 — LIQUIDITY VACUUM SCALPING — ECONOMIC CEILING FREEZE V0.1

Date: 2026-09-25
Phase: DISCOVERY MVE
Status: PRE-OUTCOME FREEZE

## Hypothesis
A sudden asymmetric depletion of top-of-book depth can precede a short-lived price displacement larger than that produced by static imbalance.

This is distinct from:
- static imbalance/microprice sign rules;
- pure aggressive-trade flow;
- prior scalping V1–V5.1;
- prior AggTrades V2.

## Source / partitions
MVE:
- Bybit BTCUSDT L2
- 2023-01-18
- first 250,000 messages

Scientific partitions remain:
- 2023–2024 Discovery
- 2025 OOS locked
- 2026 protected holdout locked

## Causal event construction
At 1-second anchors:
- compute top-10 bid displayed depth
- compute top-10 ask displayed depth
- compare with previous 1-second anchor
- ask_depletion = max(0, (prev_ask_depth - ask_depth_now)/prev_ask_depth)
- bid_depletion = max(0, (prev_bid_depth - bid_depth_now)/prev_bid_depth)

Direction:
- LONG when ask_depletion > bid_depletion
- SHORT when bid_depletion > ask_depletion

Strength:
max(ask_depletion, bid_depletion)

No future information is used to define the event.

## Generic sparse-event buckets
Use magnitude percentiles:
- 90%
- 95%
- 99%

Percentiles are computed from causal depletion strength only, not future returns.

Apply a 5-second cooldown after a selected event to reduce burst duplication.

Two predeclared variants:
A. depletion-only
B. depletion + contemporaneous L10 imbalance agrees with direction

No numeric outcome-based tuning is allowed inside this MVE.

## Horizons
1s, 5s, 15s, 30s.

## Economic ceiling
Report:
- directional mid move
- taker/taker executable gross and MEXC net (16 bps fees)
- optimistic perfect maker/maker gross and MEXC net (12 bps fees)

The maker/maker case assumes impossible perfect fills and zero slippage/adverse selection. It is an upper bound.

## MVE survival rule
A bucket is a CEILING_SURVIVOR only when:
- n >= 50
- mean optimistic MEXC maker/maker net > 0

Otherwise:
LVAC_001_MEXC_ECONOMIC_CEILING_FAIL_SAMPLE

No OOS is opened from this MVE.
