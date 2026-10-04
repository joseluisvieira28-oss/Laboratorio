# GLOBAL-ASSET-SP500-BASIS-001 — SEPTEMBER HOLDOUT CLOSEOUT V0.2

Date: 2026-10-04
Run ID: 37191695341
Branch: `mexc-global-assets-sp500-basis-v0.2-sep-holdout-2026-10-04`
Run head: `107551c2540f8347eea0a9620010cf7441fbfb5b`

## Frozen authority

Single cell only:

- symbol: `SPX500_USDT`
- signal: `FADE_BASIS_ONLY`
- absolute threshold: 5 bps
- horizon: 15 minutes
- non-overlap cooldown: 15 minutes
- holdout: `2026-09-01T00:00:00Z <= t < 2026-10-01T00:00:00Z`

No alternate asset, threshold, horizon, direction or subperiod was permitted.

## Provenance

- source gate: `MEXC_MARKET_SOURCE_PASS`
- rule SHA256: `1d385b0ae3ea1b49af4bc5324ce4cd720230a1773e3f0db15d75a70249193af7`
- source receipt SHA256: `d25d776b20bbfdde2b725d41e83ed378ae334adb0367b9d92d63eb95d36ef861`
- holdout artifact ZIP SHA256: `05cc6449a4647d424869303bd2fed60a444e1f06e0b614d9e9bd486f39f030cc`

Governance:
- no October 2026 or later outcome fetch;
- no private endpoints;
- no account reads;
- no orders;
- no exchange mutation;
- no live trading authorization;
- no parameter rescue.

## Holdout coverage

- contract rows: 8,640
- index rows: 8,640
- exact timestamp overlaps: 8,640
- first observable timestamp: 2026-09-01T00:00:00Z
- last observable timestamp: 2026-09-30T23:55:00Z
- contract requests: 6
- index requests: 6

## Frozen holdout result

- N: 654
- wins: 356
- losses: 298
- win rate: 54.4342507645%
- mean gross signed return: +0.5177567737 bps
- median gross signed return: +0.2603421158 bps
- exact one-sided binomial p-value vs 50%: 0.0128735220
- chronological half 1 mean gross: +0.4342271146 bps
- chronological half 2 mean gross: +0.6012864329 bps
- convergence rate: 54.5871559633%
- median absolute entry basis: 11.5452469905 bps

All frozen PASS gates passed:
- N >= 100;
- mean gross > 0;
- win rate > 50%;
- exact one-sided p < 0.05;
- both chronological halves mean gross >= 0.

## Illustrative all-in round-trip cost sensitivity

Costs were NOT used as the scientific signal gate.

| Round-trip cost | Mean net |
|---:|---:|
| 0.00 bps | +0.5177567737 bps |
| 0.25 bps | +0.2677567737 bps |
| 0.50 bps | +0.0177567737 bps |
| 1.00 bps | -0.4822432263 bps |
| 2.00 bps | -1.4822432263 bps |
| 5.00 bps | -4.4822432263 bps |
| 10.00 bps | -9.4822432263 bps |

Descriptive break-even all-in round-trip cost for this holdout is therefore approximately 0.5178 bps.

## Verdict

`HOLDOUT_PASS_FORWARD_SHADOW_ELIGIBLE`

Scientific classification:

`REPLICATED_SIGNAL_SURVIVOR__EXECUTION_FEASIBILITY_UNPROVEN`

The same frozen SP500 5 bps / 15 minute FADE signal was positive in August retrospective OOS and again in the untouched September holdout.

This is stronger than a one-period backtest survivor, but it is NOT yet a live-trading edge because the gross effect is small relative to plausible execution costs.

## Next legitimate gate

Do NOT retune the signal.

Next work must be execution-only and future-forward:

1. prove the exact MEXC fee schedule for the intended execution route;
2. measure live public bid/ask spread and depth for `SPX500_USDT`;
3. define a pre-outcome executable-entry model before observing forward outcomes;
4. run shadow observation from a future boundary with exact signal timestamps, executable quotes, spread/slippage and no orders;
5. promote only if realized shadow all-in cost stays below the available gross edge and forward net performance remains positive.

No live trading authorization is created by this closeout.
