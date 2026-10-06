# BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001 — V0.2 PRE-OUTCOME DISCOVERY FREEZE
Date: 2026-10-06
Status: FROZEN BEFORE ANY 2024-2025 MARKET VALUE IS OPENED

## Authority
Source gate closeout: V01_SOURCE_GATE_CLOSEOUT_2026-10-06.md
Exact development universe: V02_FROZEN_DEVELOPMENT_UNIVERSE_2026-10-06.json
Universe size before source-validity checks: 33 exact contract-settlement observations.
2026 market outcomes: CLOSED.

## Economic mechanism
The hypothesis is NOT "delisting makes the token fall."

The hypothesis is:
A known mandatory settlement deadline forces residual perpetual positions toward extinction. Before the deadline, position-closing pressure and the inability to add new risk near settlement may cause the perpetual mark/index basis to converge toward zero more strongly than during a matched non-event control window.

This stage tests mechanism discovery only. The Binance index is not assumed tradeable, so no live-tradability claim can be made from V0.2.

## Primary event window
For each frozen observation with settlement T:
- entry observation: exact 1m close at T-60 minutes;
- exit observation: exact 1m close at T-1 minute.

This one-hour window is chosen before outcomes because Binance delisting notices commonly forbid opening new positions starting 30 minutes before settlement. T-60m is therefore a conservative pre-restriction measurement point while T-1m captures the final complete minute before automatic settlement.

## Matched control window
Same contract, same UTC minute-of-day, exactly one day earlier:
- control entry: T-25 hours;
- control exit: T-24 hours - 1 minute.

No alternate control may be selected after outcomes.

## Basis definition
At any timestamp t:
premium_bps(t) = 10,000 * (mark_close(t) / index_close(t) - 1)

Event signed convergence:
- if entry premium > 0: conv_bps = entry_premium - exit_premium
- if entry premium < 0: conv_bps = exit_premium - entry_premium
- if entry premium = 0: conv_bps = 0

Positive conv_bps means the premium moved toward zero in the direction implied by its entry sign.

Control convergence uses the same formula on the matched control window.
Excess convergence = event_conv_bps - control_conv_bps.

## Open-interest mechanism check
Use official Binance USD-M metrics snapshots only.

Event OI decay:
100 * (1 - OI_near_Tminus5m / OI_near_Tminus60m)

Control OI decay:
same construction one day earlier.

Metrics timestamps must be within 5 minutes at or before the requested clock. Otherwise that OI leg is missing; never interpolate or impute.
Excess OI decay = event OI decay - control OI decay.

## Mandatory source validity per observation
A row is valid only if all of the following exist exactly:
- event mark close at T-60m and T-1m;
- event index close at T-60m and T-1m;
- control mark/index closes at matched clocks;
- event and control OI snapshots for the frozen OI clocks.

Missing rows are SOURCE_INVALID, never zero-filled.
If final valid n < 12, verdict is SOURCE_BLOCKED.

## Primary discovery gate — ALL must pass
1. valid n >= 12;
2. median event signed convergence > +15 bps;
3. event convergence hit-rate (>0) >= 65%;
4. median excess convergence > +10 bps;
5. leave-one-out median event convergence > 0 for every single-observation drop;
6. no single observation contributes >35% of summed positive event convergence;
7. median event OI decay >= 20%;
8. median excess OI decay >= +10 percentage points.

If all pass: SURVIVES_MECHANISM_DISCOVERY.
If source valid n < 12: SOURCE_BLOCKED.
Otherwise: NO_EDGE_DISCOVERY.

No secondary statistic can rescue a failed primary gate.

## Secondary descriptive outputs — non-gating
Report:
- entry and exit absolute premium;
- event/control convergence distributions;
- event/control OI decay distributions;
- by-year 2024 vs 2025 summaries;
- article-cluster concentration;
- T-6h to T-1m and T-24h to T-1m basis convergence, descriptive only;
- raw per-observation table.

## Anti-hindsight
Forbidden after outcomes:
- changing T-60m/T-1m;
- changing the matched control;
- changing the +15/+10 bps gates;
- changing OI gates;
- removing losers/outliers because of result;
- selecting only direct delist vs rebrand events based on returns;
- splitting by event type to rescue;
- adding alternative basis formulas to rescue;
- opening 2026;
- post-outcome tuning.

## Next stage
If V0.2 survives, stop. A separate pre-outcome EXECUTION freeze is mandatory before any claim of tradability. That later stage must bind a genuinely tradeable hedge/reference venue and explicit fees, spread, slippage, borrow/funding and capacity.

## Governance
Research-only.
Public unauthenticated sources only.
No main merge.
No live trading/orders.
No exchange mutation.
No accounts/wallets/private endpoints.
