# MEXC EVENT FUTURES — DIRECTIONAL TRANSPORT AMENDMENT 01

Date: 2026-10-02
Status: FROZEN BEFORE ANY DIRECTIONAL OUTCOME WAS COMPUTED
Parent: MEXC_EVENT_FUTURES_DIRECTIONAL_PREOUTCOME_FREEZE_V0.1

## Why this amendment exists

The first retrospective runner attempted the frozen 1-minute MEXC index source and failed closed before computing any directional outcome:

EMPTY_SERIES:BTC_USDT:PREHOLDOUT

A source-only transport diagnostic was then executed. That diagnostic explicitly reported no prices and computed no outcomes.

It established that:

- Min1 returned zero rows for the July probe window.
- Min5 returned complete July probe rows.
- Min15, Min30, Min60, Hour4 and Day1 also returned historical July rows.
- Min5 also returned the September source probe rows.
- The same diagnostic was applied to all five frozen canonical symbols.

This is a source-availability correction, not outcome-driven tuning.

## Retrospective V0.1A base resolution

The retrospective experiment changes from Min1 to:

- MEXC public index-price Min5 klines.

Event settlement horizons remain unchanged:

- 10m
- 30m
- 60m
- 1440m

All are exact multiples of the 5-minute base grid.

## Historical chart/lookback matrix

Retrospective frozen lookbacks become:

- 5m
- 15m
- 60m
- 240m
- 1440m

The 1-minute chart/lookback is NOT silently replaced.

Instead:

- 1m is classified FORWARD_ONLY_V0.1 until a defensible 1-minute corpus is collected prospectively.
- No retrospective conclusion about the 1m signal is allowed from V0.1A.

## Multiple testing correction

The retrospective Development family is now:

5 assets × 4 settlement horizons × 5 lookbacks × 2 signal families = 200 cells.

Benjamini-Hochberg remains frozen at FDR q=0.05 across the complete 200-cell Development family.

All other progression rules, partitions, signal definitions, no-cross-partition target rule, payout sensitivity, governance and holdout firewall from the parent freeze remain unchanged.

## Scientific interpretation

V0.1A is a five-minute-grid directional proxy.

It is not exact Event Futures execution.
It is not historical Event Futures PnL.
It does not authorize live trading.

The transport correction was frozen before any directional price outcome from the retrospective experiment was computed.
