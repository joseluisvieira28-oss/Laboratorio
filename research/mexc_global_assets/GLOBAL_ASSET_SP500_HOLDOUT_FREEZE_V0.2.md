# GLOBAL-ASSET-SP500-BASIS-001 — SEPTEMBER HOLDOUT ACTIVATION FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE SEPTEMBER OUTCOME ACCESS

## Why this cell exists

V0.1.1 discovery used June-July 2026 and retrospective OOS used August 2026.

Exactly one retrospective OOS cell survived:
- asset: SP500
- MEXC symbol: `SPX500_USDT`
- signal: FADE_BASIS_ONLY
- threshold: 5 bps absolute contract/index basis
- horizon: 15 minutes

No other cell may enter this holdout.

## Holdout

Observable-time window:
`2026-09-01T00:00:00Z <= t < 2026-10-01T00:00:00Z`

A Min5 raw bucket starting at `s` is observable at `s + 300s`.

The acquisition layer must:
- request no raw bucket that maps to an observable timestamp at or after 2026-10-01T00:00:00Z;
- check timestamp before parsing its price;
- fail closed on any timestamp outside the exact requested raw range.

## Frozen signal

`basis_bps = 10000 * (contract_close / index_close - 1)`

- basis >= +5 bps => SHORT
- basis <= -5 bps => LONG
- otherwise no signal.

Entry price is the contract close at observable signal time.
Exit is the contract close exactly 15 minutes later.
Signals use a 15-minute per-cell cooldown to prevent overlap.

## Frozen PASS gate

All conditions are required:
- N >= 100;
- mean gross signed return > 0 bps;
- win rate > 50%;
- exact one-sided binomial p-value vs 50% < 0.05;
- mean gross signed return >= 0 in each chronological half.

No multiple-testing correction is required because this is one preselected cell.

## Costs

Costs are NOT a scientific signal gate.

Report mean net bps under fixed illustrative round-trip costs:
0, 0.25, 0.5, 1, 2, 5, 10 bps.

Actual execution feasibility remains unproven until an account/route-specific fee + spread + slippage authority exists.

## No rescue

If this holdout fails, V0.2 cannot:
- change threshold;
- change horizon;
- change direction;
- choose a different asset;
- choose a subperiod;
- change the overlap rule;
- add conditioning variables.

Any such work would be a new hypothesis with a new untouched future sample.

## Promotion ceiling

PASS => `HOLDOUT_PASS_FORWARD_SHADOW_ELIGIBLE`

FAIL => `HOLDOUT_FAIL_NO_PROMOTION`

Neither result authorizes live trading, orders, private endpoints, account reads or exchange mutation.
