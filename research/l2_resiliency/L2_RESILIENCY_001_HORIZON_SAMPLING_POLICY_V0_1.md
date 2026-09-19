# L2-RESILIENCY-001 — Horizon Sampling / Source Timing Policy V0.1

Status: FROZEN PRE-OUTCOME / SOURCE-TIMING ONLY

## Frozen scientific horizons
- Replenishment observation targets: +1s, +5s, +15s from the sweep anchor.
- Midpoint-response observation targets: +5s, +15s, +60s from the sweep anchor.

## Canonical anchor and clock
- Sweep anchor = post-transition top-level envelope time.
- Horizon lookup uses only accepted normalized states in top-level envelope arrival order.
- STALE_LATE_PAYLOAD records are not eligible states.
- No interpolation is permitted.
- No lookup may cross a missing-hour segment boundary.

## Lookup rule
For a target horizon H, select the FIRST eligible normalized state whose envelope time is >= anchor + H.

## Maximum lateness
That first state is usable only if its envelope time is <= anchor + H + 1,100 ms.

1,100 ms is frozen from source-only cadence evidence before any replenishment or midpoint outcome is computed:
- all-transition p99 cadence = 1,009 ms;
- sweep-transition p99 cadence = 1,042 ms;
- the larger observed p99 is rounded upward to the next 100 ms => 1,100 ms.

This is a source-quality tolerance, not a scientific-performance parameter. It may not be widened after outcomes to rescue coverage or results.

## Missing horizon handling
If no eligible state exists inside [anchor+H, anchor+H+1,100ms], that event-horizon observation is MISSING_SOURCE_TIMING and remains missing.
No interpolation, backfill, nearest-before substitution, cross-segment lookup, or alternate venue/source is allowed.

## Outcome-blind coverage preflight
Before Discovery, an authorized source-timing preflight may count availability/missingness at +1s/+5s/+15s/+60s and measure lookup lateness distributions.
It may NOT read or aggregate forward depth, replenishment, midpoint direction/magnitude, returns, PnL, weak/strong labels, or performance.

## Discovery gate
Discovery remains separately gated after timing coverage is recorded.