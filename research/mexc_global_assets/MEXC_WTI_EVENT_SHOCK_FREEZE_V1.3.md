# MEXC-WTI-EVENT-SHOCK-001 — PRE-OUTCOME FREEZE V1.3

Date: 2026-10-04
Status: FROZEN BEFORE HISTORICAL WTI RETURNS

## Source authority

MEXC contract: `USOIL_USDT` (display OIL(WTI))
Event authority: official EIA Weekly Petroleum Status Report schedule

Source verdict:
`MEXC_WTI_EIA_SOURCE_PASS`

No WTI/EIA family existed in the repository before this source gate.

## Event set

35 official release timestamps are frozen.

Discovery:
- 30 releases from 2026-02-04 through 2026-08-26.

Retrospective OOS:
- exactly 5 September releases:
  - 2026-09-02T14:30:00Z
  - 2026-09-10T16:00:00Z
  - 2026-09-16T14:30:00Z
  - 2026-09-23T14:30:00Z
  - 2026-09-30T14:30:00Z

September 10 uses the official holiday exception of 12:00 ET.

No data at or after 2026-10-01T00:00:00Z is authorized.

## Clock

MEXC one-minute K-line timestamps are treated as bucket starts.

A raw one-minute candle starting at `s` has its close observable only at `s + 60s`.

## Frozen shock

For an EIA release at `T0`:

- shock start = MEXC open of the candle beginning exactly at T0;
- shock end = MEXC close after the first 5 full minutes;
- `shock_bps = 10000 * (close_5m / open_T0 - 1)`.

The shock becomes observable only at `T0 + 5m`.

## Anti-lookahead entry

V1.3 waits one additional full minute after the shock becomes known.

Entry proxy:
`MEXC open at T0 + 6 minutes`.

This deliberately sacrifices the first post-signal minute.

## Frozen modes

Both directions are pre-authorized before outcomes:

1. `CONTINUATION`
   - positive shock => LONG
   - negative shock => SHORT

2. `REVERSAL`
   - positive shock => SHORT
   - negative shock => LONG

No third mode may be added after outcomes.

## Frozen shock thresholds

- 0 bps (all non-zero event shocks)
- 10 bps
- 20 bps
- 40 bps

## Frozen holding horizons

Measured from the delayed entry proxy:

- 5 minutes
- 15 minutes
- 30 minutes
- 60 minutes

32 cells total:
4 thresholds × 2 modes × 4 horizons.

Each EIA release contributes at most one observation per cell.

## Discovery gate

A cell is eligible only if:
- N >= 12;
- mean gross signed return > 0;
- win rate > 50%;
- mean gross signed return > 0 in all three chronological thirds;
- exact one-sided binomial p-value vs 50% is defined.

Apply Holm-Bonferroni family-wise alpha 0.05 across all eligible cells.

Only Holm-selected cells may open September OOS.

## OOS gate

Frozen cell only, no retuning.

Required:
- N >= 5;
- mean gross signed return > 0;
- win rate > 50%;
- exact one-sided binomial p < 0.05;
- both chronological OOS half means >= 0.

With five September events, this is intentionally severe: a weak or mixed result will not pass.

## Economics

Scientific edge and execution economics remain separate.

Current source-gate MEXC metadata snapshot:
- maker fee rate: 0
- taker fee rate: 0.0001

Therefore V1.3 reports current fee-only scenarios:
0 / 1 / 2 / 3 / 5 / 10 bps round trip.

The current snapshot is NOT assumed to be the historical fee schedule.

Gross mean clearing 1 or 2 bps is reported separately. Spread/slippage are not yet modeled.

## Deliberate exclusions

V1.3 does NOT use:
- EIA inventory actual values;
- inventory changes;
- analyst consensus;
- surprise sign;
- API petroleum inventory data;
- post-outcome news labels.

This avoids repeating the unresolved pre-T0 consensus problem from News Shock V0.3.

## No rescue

After historical outcomes open, do not:
- alter event timestamps;
- change shock window;
- change the +1 minute wait;
- add thresholds;
- change modes;
- change horizons;
- weaken N;
- weaken Holm;
- choose a favorable month.

Any failed cell remains failed.

## Promotion ceiling

OOS PASS =>
`WTI_EIA_EVENT_SHOCK_OOS_SIGNAL_CANDIDATE`

No live trading, private endpoints, account reads, wallets, orders, exchange mutation, or merge to main.
