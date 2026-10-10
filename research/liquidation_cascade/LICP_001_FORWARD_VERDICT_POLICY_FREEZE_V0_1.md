> **NON-CANONICAL / SUPERSEDED — DO NOT USE FOR LICP-001 V0.1 VERDICT**
>
> Canonical authority is `LICP_001_FORWARD_ECONOMIC_VERDICT_FREEZE_V0_1.md`, frozen in commit `cfd107cd806a1e662e5a780e4118483d07757c58` at 2026-10-05T12:43:57Z, before any forward outcome receipt was inspected. This later document must not alter, replace, or rescue that pre-registered rule.

# LICP-001 — FORWARD VERDICT POLICY FREEZE V0.1

Date: 2026-10-05
Status: FROZEN BEFORE ELIGIBLE VERDICT EPOCH
Branch: liquidation-cascade-propagation-v0.1

## Purpose

Define the final economic verdict rule for LICP-001 before any forward observation is eligible for the verdict.

Several infrastructure forward runs were already started before this document existed. To avoid post-outcome rule selection, ALL runs whose observation start precedes this freeze commit are permanently excluded from the economic verdict, whether or not their outcomes were inspected.

They may be used only for infrastructure/source-health debugging.

## Primary endpoint — frozen

Only this cell can decide the primary verdict:

- family: BTC_CONFIRMED
- target: MEXC BTC_USDT
- horizon: 60,000 ms
- direction: frozen forced-pressure continuation
- execution: frozen taker/taker executable return
- round-trip base cost hurdle: 16 bps
- 2x-cost stress hurdle: 32 bps
- episode independence: existing 120-second cooldown
- valid episode: entry BBO and 60s exit BBO both valid under the existing freshness/non-crossed rules

Other targets, ALT_SECOND_WAVE records, and 1s/2s/5s/15s/30s horizons are descriptive/robustness only.
They may NOT rescue or overturn the primary endpoint.

Reversal is out of scope and cannot rescue a failed continuation hypothesis.

## Evidence gate

No economic verdict before:
- >=20 valid independent primary episodes;
- >=3 distinct UTC dates represented;
- <=10% primary-outcome missing/unresolved rate among confirmed BTC episodes.

## Frozen sequential checkpoints

Evaluate only when the valid primary-episode count first reaches:
- N = 20
- N = 40
- N = 60

Do not inspect or issue economic verdicts between checkpoints.

## Frozen statistics

At each permitted checkpoint compute on primary net_taker_bps:
- arithmetic mean;
- median;
- positive-net hit rate;
- 95% bootstrap confidence interval for the mean using a fixed deterministic seed;
- UTC-date mean net result;
- 2x-cost net = executable gross_bps - 32 bps.

Bootstrap:
- 10,000 resamples;
- deterministic seed = 20261005;
- percentile 2.5% / 97.5%.

## Terminal verdict rules

### SURVIVES
At an allowed checkpoint, all must hold:
1. mean base-cost net_taker_bps > 0;
2. median base-cost net_taker_bps > 0;
3. bootstrap 95% lower bound for mean base-cost net_taker_bps > 0;
4. mean 2x-cost net_taker_bps > 0;
5. at least 2 UTC dates have positive mean net_taker_bps.

Then stop and classify: SURVIVES_FORWARD.

### NO_EDGE
At an allowed checkpoint, if bootstrap 95% upper bound for mean base-cost net_taker_bps < 0:
- stop and classify: NO_EDGE_FORWARD.

### CONTINUE
If neither terminal rule holds at N=20 or N=40:
- continue collecting to the next frozen checkpoint.

### INCONCLUSIVE
At N=60, if neither SURVIVES_FORWARD nor NO_EDGE_FORWARD holds:
- stop and classify: FORWARD_INCONCLUSIVE.
- do not tune thresholds or open a rescue variant under LICP-001 V0.1.

## Source / technical states

Before the evidence gate, or if data integrity prevents evaluation, use only:
- FORWARD_INSUFFICIENT
- SOURCE_BLOCKED
- TECHNICAL_BLOCKED

These are not NO_EDGE.

## Anti-leakage rule

No run started before the commit that creates this freeze is eligible for the economic verdict.
No threshold, target, horizon, fee, stopping rule, bootstrap rule, direction, or missingness rule may be changed after the first eligible run starts.

## Authority

Research-only.
No orders.
No authentication.
No exchange mutation.
No live capital.
No merge to main.
