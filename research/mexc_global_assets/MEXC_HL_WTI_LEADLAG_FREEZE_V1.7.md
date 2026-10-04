# MEXC-HL-WTI-LEADLAG-001 — PRE-OUTCOME FREEZE V1.7

Date: 2026-10-04
Status: FROZEN BEFORE CROSS-VENUE HISTORICAL OUTCOMES

## Source binding

MEXC:
`USOIL_USDT` / OIL(WTI)

Hyperliquid HIP-3:
`xyz:CL` / Crude Oil (WTI)

Source authority:
`HYPERLIQUID_WTI_SOURCE_PASS__XYZ_CL`

The targeted binding opened zero historical outcomes.

## Mechanism

Hypothesis:

> when `xyz:CL` makes a sufficiently large one-minute WTI move and the MEXC WTI contract moves less in the same direction during that completed minute, MEXC may continue catching up in the Hyperliquid direction after the signal is observable.

This is economically distinct from:
- EIA price-shock continuation/reversal V1.4;
- EIA inventory BUILD/DRAW V1.5.

## Frozen clock

Both one-minute sources are treated as raw bucket-start timestamps.

A close for raw minute start `s` is observable only at:
`s + 60 seconds`.

Signals use only fully completed aligned minutes.

## Frozen signal

At observable minute `t`:

`hl_ret_bps = 10000 * (HL_close[t] / HL_close[t-1m] - 1)`

`mexc_ret_bps = 10000 * (MEXC_close[t] / MEXC_close[t-1m] - 1)`

`lag_gap_bps = hl_ret_bps - mexc_ret_bps`

Signal only if:

1. `abs(hl_ret_bps) >= shock_threshold`;
2. `sign(lag_gap_bps) == sign(hl_ret_bps)`;
3. `abs(lag_gap_bps) >= lag_gap_threshold`.

Direction:
`FOLLOW_HL`

No fade mode is authorized.

## Frozen thresholds

Hyperliquid shock:
- 5 bps
- 10 bps
- 20 bps
- 40 bps

MEXC underreaction lag gap:
- 2 bps
- 5 bps
- 10 bps
- 20 bps

Horizons:
- 1m
- 2m
- 5m
- 15m

64 cells total.

Thresholds are frozen from economic scale before historical outcomes:
the current MEXC taker snapshot is 1 bp per side, so the fee-only taker/taker round trip is approximately 2 bps.

## Anti-lookahead entry

The signal is known only after the minute closes.

Entry proxy:
MEXC OPEN of the immediately following one-minute candle.

No same-close entry is permitted.

## Windows

Discovery:
`2026-09-10T00:00:00Z <= signal t < 2026-10-01T00:00:00Z`

Retrospective OOS:
`2026-10-01T00:00:00Z <= signal t < 2026-10-04T09:00:00Z`

Hard fetch boundary:
`2026-10-04T09:00:00Z`

This OOS ends before the V1.6/V1.6.1 live source snapshots on 4 October.

No price at or after 09:00 UTC on 4 October is authorized in V1.7.

## Discovery gate

Per cell:
- N >= 50 non-overlapping signals;
- mean gross signed return > 0;
- win rate > 50%;
- every chronological third mean > 0;
- exact one-sided binomial p-value vs 50% defined.

Apply Holm-Bonferroni FWER 0.05 across all eligible cells.

Only Holm-selected cells may open OOS.

## OOS gate

Frozen cell only:
- N >= 20;
- mean gross signed return > 0;
- win rate > 50%;
- exact one-sided binomial p < 0.05;
- both chronological half means >= 0.

## Economics

Current MEXC contract metadata snapshot:
- maker: 0
- taker: 0.0001 per side

Report round-trip scenarios:
0 / 1 / 2 / 3 / 5 / 10 bps.

Report whether gross mean clears:
1 / 2 / 3 bps.

Fees do not determine the scientific gate.
Spread/slippage are still unmeasured.

## No rescue

After outcomes open, V1.7 may not:
- change venue binding;
- add FADE;
- lower thresholds;
- change next-minute-open entry;
- change horizons;
- choose favorable sessions/subperiods;
- weaken N;
- weaken Holm/OOS gates.

## Promotion ceiling

OOS PASS =>
`WTI_CROSSVENUE_OOS_SIGNAL_CANDIDATE`

Even a PASS is not live-trading authorization.

No private endpoints, accounts, wallets, orders, exchange mutation, or merge to main.
