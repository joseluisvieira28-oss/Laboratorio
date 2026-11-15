# LIQUIDATION-PRESSURE-002-FORWARD — ECONOMIC MVE FREEZE V0.1

**Frozen:** 2026-09-23 before internal markout analysis  
**MVE ID:** LP2-BYBIT-REV5S-Q95-H30-V1  
**Mode:** read-only shadow

## Economic hypothesis

A sufficiently large mechanically forced liquidation burst temporarily pushes the local perpetual order book beyond its short-horizon equilibrium. After the burst closes, part of the forced impact reverses.

Primary tradable direction is **reversal only**:
- net long-liquidation burst => forced sell pressure => hypothetical post-burst LONG;
- net short-liquidation burst => forced buy pressure => hypothetical post-burst SHORT.

Continuation is diagnostic only and cannot be selected for promotion under this MVE.

## Frozen venue and symbols

Bybit USDT linear perpetuals only: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, BNBUSDT.

## Source-only calibration

Primary burst window: fixed non-overlapping **5 seconds**.

Calibration uses liquidation messages only. Price/order-book outcomes may not be used to choose the threshold.

Calibration closes after:
- at least 24 UTC hours from first calibration record; AND
- at least 500 raw liquidation records total.

For each symbol, compute the empirical distribution of 5-second absolute liquidation notional among windows with at least one liquidation.

Primary threshold = per-symbol **95th percentile** of that source-only distribution.

A symbol requires at least 30 non-empty calibration windows or is INELIGIBLE_INSUFFICIENT_SOURCE.

The q95 choice is frozen now. q90/q99 may be reported descriptively but cannot replace q95 after outcomes.

## Burst direction

Bybit S=Buy means a long position was liquidated, implying forced sell pressure.  
Bybit S=Sell means a short position was liquidated, implying forced buy pressure.

For a 5-second window:
- long_liq_notional = sum(v × p) where S=Buy
- short_liq_notional = sum(v × p) where S=Sell
- net_forced_buy_notional = short_liq_notional - long_liq_notional

Zero net direction => no trade event.

## Frozen hypothetical execution

Entry:
- first valid order-book state timestamped at or after the 5-second burst close;
- take liquidity in the reversal direction;
- consume visible order-book depth level-by-level.

Exit:
- 30 seconds after entry using first valid book at or after the horizon;
- take liquidity;
- consume visible depth level-by-level.

Frozen notionals:
- 100 USDT
- 500 USDT
- 1,000 USDT
- 5,000 USDT

No leverage assumption is required for return-in-bps evaluation. No bucket may be added because it looks better.

## Fees and frictions

BASE:
- Bybit non-VIP perpetual taker fee = 5.5 bps per executed side.
- Round-trip fee floor = 11 bps.
- observed spread and depth slippage at entry and exit.

STRESS:
- 10 bps taker cost per executed side.
- round-trip fee = 20 bps.
- observed spread and depth slippage.

Any event whose 30-second holding interval overlaps a scheduled funding timestamp is excluded prospectively to prevent an unmodeled funding transfer.

No maker rebates.

## Independence

Once a q95 burst event fires for a symbol:
- no new independent event for that symbol until 60 seconds after exit.
- overlapping bursts are attached to the active event for descriptive intensity only.

## Discovery sample gates

No economic verdict before:
- >=500 independent q95 events total;
- >=75 independent events in at least 3 symbols;
- >=14 distinct UTC calendar days after calibration freeze.

Below the gates: INSUFFICIENT_FORWARD_SAMPLE.

## Survival gates

All mandatory:
- BASE mean net bps > 0;
- STRESS mean net bps > 0;
- bootstrap lower 95% CI of BASE mean > 0;
- positive-event rate > 50%;
- at least 3 symbols have positive BASE mean;
- no single symbol contributes >50% of total positive PnL;
- no single UTC day contributes >25% of total positive PnL;
- at least two notional buckets remain positive under STRESS.

Failure after a valid sample => NO_EDGE for LP2-BYBIT-REV5S-Q95-H30-V1. No continuation, q90/q99, horizon, symbol or notional rescue under the same MVE.

## Governance

No live orders, no account API, no exchange mutation, no main merge, no promotion from source/calibration/engineering.
