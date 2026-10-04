# MEXC-BITGET-GOLD-LEADLAG-001 — V1.1 CLOSEOUT

Date: 2026-10-04
Run: 37196061877
Artifact SHA256: `ae2664a3a124fe122103d003c5bb67c8dea2062f7b4c315b93c4e85089fc4cba`
Rule SHA256: `0990f347babf18710fdf3db6a88ef86d26d59d87ec59319c7f003a24018a4d32`

## Coverage
- exact MEXC/Bitget timestamp alignment: 1.000
- Discovery overlap rows: 21,577
- OOS overlap rows available but unopened: 15,823
- first overlap: 2026-09-05T00:00:00Z
- last overlap: 2026-09-30T23:59:00Z

## Frozen family
64 cells:
- Bitget XAU 1m shock: 5 / 10 / 20 / 40 bps
- MEXC underreaction gap: 3 / 5 / 10 / 20 bps
- horizons: 1 / 2 / 5 / 15 minutes
- direction: FOLLOW_BITGET
- entry proxy: MEXC next-minute open

## Result
- pre-Holm eligible cells: 0
- Holm-selected cells: 0
- OOS opened: NO
- OOS survivors: 0

Verdict:
`NO_GOLD_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V11_GATE`

## Descriptive strongest observations — NOT candidates

The lowest p-value cell was:
- shock >= 5 bps
- lag gap >= 5 bps
- horizon 5m
- N = 20
- wins = 15
- win rate = 75%
- mean gross = +2.9635 bps
- one-sided exact binomial p = 0.02069
- chronological thirds = +1.8804 / +2.8071 / +4.0483 bps

It failed the frozen Discovery minimum N=30 and therefore was not eligible for Holm.

A few high-threshold cells showed very large gross returns (up to +50.85 bps) but each had only N=1. These are anecdotes, not evidence, and may not be promoted or used for parameter rescue.

No tested cell established an economically robust effect above the 12/14/16 bps standard-API fee-only hurdles with adequate sample size.

## Scientific interpretation

There is some descriptive evidence that rare XAU cross-venue shocks can be followed by large MEXC moves, but the frozen September sample is too sparse to establish a robust signal.

Do not lower N or retune thresholds/horizons around the observed N=20 or N=1 cells.

V1.1 is CLOSED.

No live trading, account reads, private endpoints, wallets, orders or exchange mutation.
