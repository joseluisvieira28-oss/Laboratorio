# GLOBAL-ASSET-INDEX-BASIS-001 — PRE-OUTCOME FREEZE V0.1

Date: 2026-10-04
Status: FROZEN / INACTIVE UNTIL SOURCE RECEIPT PASS
Outcomes opened at freeze time: 0

## Hypothesis

When the MEXC Global Asset Futures traded contract deviates materially from the contemporaneous MEXC index price, the traded contract tends to converge toward the index over a short fixed horizon.

Only the convergence direction is permitted:

- contract premium to index -> SHORT contract;
- contract discount to index -> LONG contract.

`FOLLOW_BASIS` is not in the family and may not be added after outcomes are seen.

## Assets

- NAS100: `NAS100_USDT`
- SP500: `SPX500_USDT`
- GOLD: `XAU_USDT`
- NVIDIA: `NVIDIA_USDT`

## Source

Public/no-auth MEXC Futures REST:

- contract Min5 kline;
- index-price Min5 kline.

A raw bucket with start timestamp `s` is considered observable only at `s + 300 seconds`.

The two legs must share the same mapped observable timestamp.

## Frozen basis

`basis_bps = 10_000 * (contract_close / index_close - 1)`

## Frozen trigger thresholds

Absolute basis thresholds:

- 5 bps
- 10 bps
- 20 bps
- 40 bps

No percentile, z-score, quantile, or asset-specific threshold may be introduced in V0.1 after outcomes are opened.

## Frozen horizons

- 5 minutes
- 15 minutes
- 30 minutes
- 60 minutes

## Frozen signal

At observable time `t`:

- if `basis_bps >= +threshold`: signal SHORT;
- if `basis_bps <= -threshold`: signal LONG;
- otherwise: no signal.

Outcome is signed contract return from contract close at `t` to contract close at `t+horizon`.

Primary scientific edge metric is GROSS signed return in basis points. Execution feasibility is a separate gate.

## Overlap rule

For each asset/threshold/horizon cell, after a signal is accepted no further signal in that cell may be accepted until `t + horizon`.

## Historical windows

For NAS100, SP500 and GOLD:

Discovery:
`2026-06-01T00:00:00Z <= t < 2026-08-01T00:00:00Z`

Retrospective OOS:
`2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z`

September 2026 and later are not fetched by V0.1.

NVIDIA is source-gated but is NOT eligible for retrospective OOS promotion in V0.1 because prior Event Futures research already inspected NVIDIA-linked historical outcomes in overlapping periods. NVIDIA may be descriptive discovery only and future-forward research only.

## Discovery gate

Per cell:

- N >= 30 non-overlapping signals;
- mean gross signed bps > 0;
- win rate > 50%;
- one-sided exact binomial p-value vs 50% is defined;
- mean gross signed bps > 0 in each chronological discovery third.

Multiple testing:
Holm-Bonferroni family-wise alpha 0.05 across all eligible discovery cells.

Only Holm-selected cells in NAS100/SP500/GOLD may open August OOS.

## OOS gate

Without changing asset, threshold, horizon, direction or overlap rule:

- N >= 10;
- mean gross signed bps > 0;
- win rate > 50%;
- one-sided exact binomial p-value vs 50% < 0.05;
- mean gross signed bps >= 0 in each chronological OOS half.

Any survivor is only:

`GLOBAL_ASSET_SIGNAL_CANDIDATE`

It is NOT a live-trading authorization.

## Cost reporting

To avoid repeating the prior mistake of killing candidates with guessed fees, V0.1 does NOT use an assumed fee as the scientific signal gate.

Every result must additionally report mean net bps under fixed illustrative round-trip cost scenarios:

- 0 bps
- 2 bps
- 5 bps
- 10 bps
- 20 bps

Execution promotion requires a later account/exchange-specific cost authority based on observed fees/slippage/minimum-notional constraints.

## Hard fail conditions

- source receipt missing or not PASS;
- timestamp mismatch between contract and index;
- any fetch at or after 2026-09-01;
- post-outcome threshold/horizon/direction changes;
- use of Yahoo/CME delayed web data as the primary signal;
- private/authenticated MEXC call;
- live order or account mutation.

## Freeze rule hash

The authoritative rule object is stored in `GLOBAL_ASSET_INDEX_BASIS_RULE_V0.1.json`.
The runner must print and persist its SHA-256 before fetching historical outcomes.
