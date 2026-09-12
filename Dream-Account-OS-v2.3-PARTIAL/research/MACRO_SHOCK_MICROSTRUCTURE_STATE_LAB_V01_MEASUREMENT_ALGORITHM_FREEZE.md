# Macro Shock Microstructure State Lab V0.1 — Measurement Algorithm Freeze

Status: **FROZEN PRE-OBSERVATION ALGORITHM SPEC / OFFLINE-SYNTHETIC ONLY**

This document disambiguates deterministic implementation details for the already-frozen non-directional prospective measurement contract. It does not alter scientific scope, authorize target observation, create H02, or define trading logic.

## Time boundaries

All event-relative windows use half-open intervals in nanoseconds:

- `PRE_BASELINE`: `[-30m, 0m)`
- `PRIMARY_EVENT_STATE`: `[0m, +30m)`
- `RECOVERY_STATE`: `[+30m, +60m)`

A timestamp exactly at release belongs to `PRIMARY_EVENT_STATE`.
A timestamp exactly at +30m belongs to `RECOVERY_STATE`.
A timestamp exactly at +60m is outside the frozen measurement windows.

## Canonical grid

- 1-second UTC timestamps.
- Grid points are exact integer multiples of 1,000,000,000 ns.
- For a requested interval `[start_ns, end_ns)`, the first grid point is the first exact second `>= start_ns`; the final grid point is the last exact second `< end_ns`.
- Each point uses strictly backward as-of selection only.
- `max_skew_ns = 2,000,000,000`.
- No interpolation.
- No forward observation may be used.
- Missing points remain missing.

## BBO summaries

For a non-empty set of valid sampled BBOs:

- median uses the conventional middle value for odd `n` and arithmetic mean of the two middle values for even `n`;
- p90 uses the **nearest-rank** rule: rank `ceil(0.90 * n)`, 1-indexed, on ascending values;
- top-of-book imbalance is `(bid_qty - ask_qty) / (bid_qty + ask_qty)` when denominator > 0;
- the contract summary uses `abs(imbalance)` and its median;
- spread_bps is the already-frozen mechanical `(ask-bid)/mid*10000`.

No winsorization, trimming, clipping or outlier deletion is permitted.

## Realized-volatility descriptor

For valid consecutive 1-second sampled mids within one frozen window:

- `r_t = ln(mid_t / mid_{t-1})`;
- no return is formed across a missing grid point;
- squared returns are summed;
- descriptor = `sqrt(sum(r_t^2))`;
- no annualization or directional sign enters the descriptor.

Fewer than two consecutive valid mid observations produces a missing volatility descriptor.

## Trade-intensity summaries

For source-valid trades inside one frozen window:

- trade_count = integer number of trades;
- base_quantity = sum of source base quantities;
- quote_notional = sum of `price * quantity` unless source provides a directly equivalent quote-notional field already normalized under a separately frozen parser;
- interval duration for rate normalization is the full frozen window duration, not observed-active duration;
- trades_per_minute = trade_count / frozen_window_minutes;
- notional_per_minute = quote_notional / frozen_window_minutes.

No filtering by trade size is permitted in V0.1.

## Flow magnitude

Only source records with unambiguous aggressive-side semantics may enter.

- buy_notional = sum quote notional of BUY-aggressor trades;
- sell_notional = sum quote notional of SELL-aggressor trades;
- total_notional = buy_notional + sell_notional;
- absolute_normalized_signed_flow = `abs(buy_notional - sell_notional) / total_notional` when total_notional > 0;
- otherwise missing.

The sign of flow is not a scientific output under this contract.

## Matched-control aggregation

For one event × venue × symbol case:

- control eligibility is determined before metric values are inspected;
- each valid control produces its own metric summary under identical rules;
- at least 3 valid controls are required;
- the control reference for each scalar metric is the **median across valid control summaries**;
- event/control ratio is `event_metric / control_reference` only when both are finite and control reference > 0;
- event-control difference is `event_metric - control_reference` when both are finite;
- neither ratio nor difference receives a directional price interpretation.

## Missingness and fail-closed behavior

- no metric value may be imputed;
- unavailable source fields stay unavailable;
- invalid/crossed books fail validation rather than being repaired;
- conflicting provenance/order records fail validation;
- unsynchronized book state emits no BBO-derived metric;
- a failed venue/symbol/event case is never silently substituted by another venue or symbol.

## Scientific boundary

These details are frozen before any target observation. They may not be changed later because measured state changes look weak, noisy or inconvenient.

`TARGET_OBSERVATION_AUTHORIZED = false`

`H02_STATUS = NOT_AUTHORIZED`

Final boundary: **OFFLINE/SYNTHETIC IMPLEMENTATION ONLY. STOP BEFORE TARGET OBSERVATION OR DIRECTIONAL H02.**
