# V0.1 DEVELOPMENT METRIC IMPLEMENTATION SPEC
Date: 2026-10-05
Status: FROZEN BEFORE 2025 SUB-MINUTE OUTCOME INSPECTION

Parent freeze:
5110f7ebda90809de56155b4605b9621bd8fb781

Identity/pre-history resolution:
9744ce8e12b99e644a0f9bee55b1d89689a9b0dd

This document clarifies implementation details without changing the economic hypothesis.

## Gate deal schema
Gate official SPOT deals archive:
timestamp, dealid, price, amount, side

timestamp is interpreted as UTC seconds with decimal fractional precision.
price and amount are parsed only after the source gate passes and the 2025 development activation receipt is created.

## Ordering
All trades for an event window are sorted ascending by:
1. timestamp
2. dealid where numeric ordering is available

If timestamps are equal, file order may be used only as a deterministic tie-breaker for metrics that require a single last trade.

## P0
P0 = price of the last trade strictly before T0 in [T0-10s, T0).

## Horizon returns
For h in {1s,5s,10s,30s,60s}:
- eligible post trades have T0 <= timestamp <= T0+h.
- if at least one eligible post trade exists, Ph = the last eligible trade price.
- Rh = Ph/P0 - 1.
- if no post trade exists by h, Rh = NULL.

No pre-T0 forward fill is allowed.

## Baseline activity blocks
Baseline window:
[T0-10 minutes, T0-1 minute)

It is partitioned into fixed, non-overlapping 5-second blocks aligned from the exact baseline start.
Blocks with zero trades are retained with:
- trade_count = 0
- quote_volume = 0

Baseline medians are medians across ALL blocks, including zero blocks.

Activity shock ratio is NULL if the corresponding baseline median is zero.

Quote volume per trade:
price * amount.

## Reaction-speed fractions
For each h in {1,5,10,30}s:
signed_fraction_h_of_R60 is reported only if:
- Rh and R60 are non-NULL;
- R60 != 0;
- Rh has the same sign as R60 or Rh == 0.

Then:
signed_fraction_h_of_R60 = Rh / R60.

No clipping is applied; overshoot may yield a value >1.

## Time to 50% / 80% of 60-second displacement
Only defined when R60 != 0.

For positive R60:
earliest post-T0 trade whose price >= P0*(1 + fraction*R60).

For negative R60:
earliest post-T0 trade whose price <= P0*(1 + fraction*R60).

Latency is trade timestamp - T0 in milliseconds.

## Frozen detection-latency grid
L milliseconds:
250, 500, 1000, 2000, 5000, 10000, 30000, 60000.

Entry:
first trade with timestamp >= T0+L and timestamp <= T0+60s.

Exit:
last trade with timestamp <= T0+60s and timestamp >= T0.

If entry or exit is absent, latency observation = NULL.

Gross capture:
exit_price / entry_price - 1.

Actual entry latency:
entry_timestamp - T0.

## Cost sensitivity
For round-trip cost C:
- 20 bps => C=0.0020
- 50 bps => C=0.0050
- 100 bps => C=0.0100

Adverse symmetric implementation:
half = C/2
net_C = [exit_price*(1-half)] / [entry_price*(1+half)] - 1

Costs are descriptive in V0.1 and do not claim actual venue fill cost.

## Cross-event summaries
For every latency bucket independently report:
- valid n
- median gross capture
- gross positive hit rate
- gross leave-one-out median-positive boolean
- gross positive-return concentration
- median net20
- median net50
- median net100
- net50 positive hit rate
- net50 leave-one-out median-positive boolean
- net50 positive-return concentration

Positive-return concentration:
max(max(0,r_i)) / sum(max(0,r_i))
when summed positive return >0; otherwise 1.

## Development label
The parent V0.1 development interpretation rule remains authoritative.

Additionally report, without changing that label:
COST_ROBUST_50BPS = true for a latency bucket only if ALL:
- latency >= 1 second
- n >= 8
- median net50 > 0
- net50 hit rate >=60%
- net50 leave-one-out median >0
- net50 positive concentration <=35%

A 2026 forward protocol SHOULD NOT be promoted as a serious execution candidate unless at least one >=1s bucket is COST_ROBUST_50BPS or a later pre-outcome freeze provides a defensible lower all-in cost model from independent evidence.

No 2026 outcomes may be opened here.
