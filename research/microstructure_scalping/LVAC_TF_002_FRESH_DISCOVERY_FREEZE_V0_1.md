# LVAC-TF-002 — LIQUIDITY VACUUM + AGGRESSIVE TRADE FLOW
## FRESH-DISCOVERY ECONOMIC CEILING — PRE-RUN FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: DISCOVERY ONLY

## Scientific question
Can a sudden one-sided top-10 liquidity depletion, confirmed by strictly trailing aggressive trade flow in the same direction, isolate rare short-horizon moves large enough to clear current MEXC API execution fees?

This is economically distinct from:
- static L1/L5/L10 imbalance;
- microprice displacement alone;
- LVAC-001 depletion alone;
- AggTrades-only research.

## Deterministic fresh Discovery dates
Chosen before outcomes by calendar rule: first Wednesday of each quarter after the archive-start period used by prior MVE.

- 2023-04-05
- 2023-07-05
- 2023-10-04
- 2024-01-03

These dates are all inside the previously frozen 2023–2024 Discovery partition.
2025 OOS remains LOCKED.
2026 protected holdout remains LOCKED.

## Source slice per date
- Bybit BTCUSDT linear historical L2
- first 250,000 order-book messages
- public historical BTCUSDT trades overlapping the same L2 slice
- one-second anchors
- 5-second cooldown after a selected event

Historical 2023/2024 L2 uses archive ts as the event clock when cts is absent.
Historical public-trade timestamps are converted to integer milliseconds.
No same-timestamp trade is treated as pre-existing flow for an anchor.

## Causal features at anchor t

### Liquidity depletion
Top-10 displayed depth is compared with the previous one-second anchor:

ask_depletion = max(0, (prev_ask_depth - ask_depth_now) / prev_ask_depth)
bid_depletion = max(0, (prev_bid_depth - bid_depth_now) / prev_bid_depth)

Direction:
- LONG when ask_depletion > bid_depletion
- SHORT when bid_depletion > ask_depletion

depletion_strength = max(ask_depletion, bid_depletion)

### Aggressive trade flow
Only trades with timestamp strictly less than anchor t are eligible.

Windows:
- trailing 1,000 ms
- trailing 5,000 ms

Notional flow:
buy_notional = sum(size * price for taker Buy trades)
sell_notional = sum(size * price for taker Sell trades)

flow_imbalance = (buy_notional - sell_notional) / (buy_notional + sell_notional)

Direction agreement:
- LONG requires flow_imbalance > 0
- SHORT requires flow_imbalance < 0

No contemporaneous or future trade may confirm an anchor.

## Feature-only calibration
The first fresh date, 2023-04-05, is used only to derive numeric feature thresholds from causal feature distributions.

Frozen generic percentile families:
- depletion strength: p90 / p95 / p99
- absolute flow imbalance: p75 / p90 / p95

No return/PnL outcome may be used to choose a threshold.

The resulting numeric thresholds are then held constant for all four dates.

## Predeclared variants
For each flow window (1s and 5s), test these joint gates:

1. D90 + F75
2. D95 + F75
3. D95 + F90
4. D99 + F90
5. D99 + F95

All require flow direction agreement with depletion direction.

Total predeclared signal variants: 10.

## Horizons
- 5s
- 15s
- 30s
- 60s

## Economic ceilings

### MEXC taker/taker
Executable BBO entry and exit.
Fee hurdle: 16 bps round trip.
No slippage added in this ceiling test.

### MEXC perfect maker/maker upper bound
Assume immediate perfect maker fill at current best quote and perfect maker exit at future best quote.
Fee hurdle: 12 bps round trip.
No queue penalty, no adverse selection, no slippage.

This is deliberately unrealistically favorable.

## Family survival rule
A predeclared variant/horizon is a CEILING_SURVIVOR only when ALL hold:
- pooled n >= 40;
- pooled mean MEXC perfect-maker net > 0;
- at least 3 of 4 date-level mean MEXC perfect-maker nets > 0.

Otherwise the family remains failed at this economic-ceiling stage.

No threshold rescue and no OOS opening is allowed from this MVE.
