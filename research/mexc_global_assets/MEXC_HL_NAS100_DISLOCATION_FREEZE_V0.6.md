# MEXC-HL-NAS100-DISLOCATION-001 — PRE-OUTCOME FREEZE V0.6

Date: 2026-10-04
Status: FROZEN BEFORE NAS100 HISTORICAL OUTCOMES

## Source binding

MEXC: `NAS100_USDT`
Hyperliquid HIP-3: `xyz:XYZ100`

Authority:
`HYPERLIQUID_NAS100_SOURCE_PASS__XYZ_XYZ100`

The source-only proof opened zero historical outcomes.

## Mechanism

MEXC explicitly reports `indexOrigin=["HYPERLIQUID"]` for NAS100.

Hypothesis:

> when the MEXC traded NAS100 contract is materially displaced from the contemporaneous Hyperliquid `xyz:XYZ100` close, the MEXC contract tends to move back toward the Hyperliquid level.

This is a level-dislocation/convergence family, distinct from the failed SP500 1-minute shock/underreaction family.

## Frozen signal

At observable closed minute `t`:

`gap_bps = 10000 * (MEXC_contract_close[t] / HL_close[t] - 1)`

- gap >= +threshold => SHORT MEXC
- gap <= -threshold => LONG MEXC
- otherwise no signal.

Direction is fixed to `FADE_LEVEL_DISLOCATION`.

Thresholds:
- 10 bps
- 20 bps
- 40 bps
- 80 bps

The source-only snapshot (~30.9 bps MEXC-index vs HL mid) was used only to establish scale plausibility. No historical outcome informed these thresholds. Thresholds span below/near/above the public 12–16 bps standard API round-trip fee hurdle.

## Anti-lookahead execution proxy

The signal uses a fully closed minute at `t`.

V0.6 does NOT pretend the trader can enter at that already-completed close.

Frozen entry proxy:
- wait one full minute;
- enter at MEXC closed price at `t + 1 minute`.

Frozen outcome horizons measured from that delayed entry:
- 1 minute
- 2 minutes
- 5 minutes
- 15 minutes.

This deliberately sacrifices speed to avoid same-close execution bias.

## Frozen historical windows

Discovery:
`2026-09-01T00:00:00Z <= signal t < 2026-09-20T00:00:00Z`

Retrospective OOS:
`2026-09-20T00:00:00Z <= signal t < 2026-10-01T00:00:00Z`

Hard fetch boundary:
`2026-10-01T00:00:00Z`

October 2026 is NOT opened in V0.6.

## Discovery gate

For each threshold × horizon cell:

- N >= 30 non-overlapping signals;
- mean gross signed MEXC return > 0;
- win rate > 50%;
- mean gross signed return > 0 in every chronological discovery third;
- exact one-sided binomial p-value vs 50% defined.

Holm-Bonferroni controls family-wise alpha at 0.05 across eligible cells.

Only Holm-selected cells may open retrospective OOS.

## OOS gate

Frozen cell only, no retuning:

- N >= 15;
- mean gross signed return > 0;
- win rate > 50%;
- exact one-sided binomial p < 0.05;
- both chronological half means >= 0.

## Economic reporting

Scientific existence and execution feasibility remain separate.

Report mean net after fixed round-trip cost scenarios:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Also classify whether OOS mean gross clears:
- 12 bps: maker-maker published standard API fee floor;
- 14 bps: maker-taker;
- 16 bps: taker-taker.

Clearing a fee-only hurdle still does NOT prove executability because spread/slippage remain unmeasured.

## No rescue

After outcomes open V0.6 may not:
- change binding;
- change thresholds;
- change direction;
- change the 1-minute entry delay;
- change horizons;
- choose a subperiod;
- weaken Holm/stability gates.

Any failed cell stays failed.

## Promotion ceiling

OOS PASS => `NAS100_CROSSVENUE_OOS_SIGNAL_CANDIDATE`

October remains untouched and requires a separate activation freeze.

No live trading, private endpoint, account read, wallet, order or exchange mutation is authorized.
