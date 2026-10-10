# LICP-HIST-XALT-003 — SELECTED CANDIDATE + HOLDOUT FREEZE V0.1

Date: 2026-09-26
Status: CANDIDATE FROZEN / HOLDOUT NOT YET OPENED

## Discovery provenance
Workflow run: 36232546660

Discovery partition:
- 2025-08-10 through 2025-10-31 UTC

BTC ignition events:
- n = 45

Predeclared survivors:
- ETH / 60m
  - n = 45
  - mean gross = +22.8106074904 bps
  - median gross = +25.2165047976 bps
  - transfer-ceiling net after 16 bps hurdle = +6.8106074904 bps
  - positive months = 3

- SOL / 60m
  - n = 45
  - mean gross = +25.8210438500 bps
  - median gross = +20.0679221982 bps
  - transfer-ceiling net after 16 bps hurdle = +9.8210438500 bps
  - positive months = 2

## Mechanical selected candidate
Per the frozen candidate-selection rule, choose the surviving candidate with the highest PRIMARY mean transfer-ceiling net.

FROZEN CANDIDATE:
- event source: BTC ignition events only
- target: SOLUSDT
- direction: SHORT continuation
- primary entry proxy: t0 + 6 minutes
- horizon: 60 minutes
- transfer hurdle: 16 bps
- no reversal rescue

## Locked holdout
- 2025-11-01 00:00 UTC through 2025-12-31 23:59:59.999999 UTC

No event before 2025-11-01 or after 2025-12-31 may be included.
Discovery months MUST NOT be read by the holdout code.

## Holdout PASS rule — frozen before outcomes
HOLDOUT_SURVIVES only if ALL are true:
1. n >= 20;
2. mean gross directional move > 16 bps;
3. median gross directional move > 0 bps;
4. BOTH November and December, when each has >=5 valid events, have positive mean gross directional move;
5. no missing-price rate > 10% relative to eligible holdout BTC ignition events.

If any criterion fails:
HOLDOUT_FAIL.

If n < 20:
HOLDOUT_INSUFFICIENT rather than NO_EDGE.

## Outcome definition
For each eligible BTC ignition event:
- theoretical observable trigger = t0 + 5m
- primary entry proxy = SOLUSDT 1m candle open at t0 + 6m
- exit proxy = SOLUSDT 1m candle open at t0 + 66m
- gross_directional_bps = (entry_open - exit_open) / entry_open × 10,000

This is a coarse cross-venue continuation measure, NOT executable PnL.

Transfer ceiling:
- gross_directional_bps - 16 bps

No spread, slippage, MEXC fill quality, or MEXC transferability is proven by this holdout.

## Single-pass law
The holdout may be opened exactly once for this frozen candidate.

After the first completed outcome run:
- no threshold change;
- no horizon change;
- no target change;
- no direction reversal;
- no exclusion rescue;
- no alternate entry delay rescue.

A failure is final for LICP-HIST-XALT-003 V0.1.

No live trading authority is created by survival.
