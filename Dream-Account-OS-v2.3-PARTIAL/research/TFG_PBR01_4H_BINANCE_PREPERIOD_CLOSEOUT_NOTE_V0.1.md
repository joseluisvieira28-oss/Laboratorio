# TFG-PBR01-4H-BINANCE-PREPERIOD-001 — Closeout Note V0.1

Date: 2026-09-16

## Immutable execution identity

- Branch: `pbr01-4h-binance-preperiod-v0.1`
- Frozen authority commit: `bd22cd68765f73f4a644a3bb93515f8f0b406634`
- Execution head: `c288a467396424ac9aaac9fe0117c2223182435c`
- GitHub Actions run: `35126364350`
- Closeout artifact ID: `10459571979`
- Closeout artifact digest: `sha256:4e21223a03c79fb34a64b50a2a1e94e30c0e5eab7a975ea54266049be1e06a2a`
- Source artifact ID: `10459537013`
- Source artifact digest: `sha256:5b2a082c4b91be09a0022ada134c3580db2f3039207153a6c850ffa3fb41d90a`

## Frozen test

Independent non-overlapping historical pre-period replication on Binance Spot only. Exact PBR01 4H geometry, exact six-asset universe and exact cost assumptions were retained. Window: `2021-01-01T00:00:00Z` inclusive through `2023-02-01T00:00:00Z` exclusive. This was explicitly not a forward OOS and was not allowed to pool with the prior 88-trade Binance cross-venue sample for gate passing.

## Source gate

`SOURCE_AUDIT_PASS`

150/150 frozen monthly archives were accepted (25 months × six symbols). Protected years 2025 and 2026 were not accessed.

## Terminal scientific classification

`INSUFFICIENT_SAMPLE`

The frozen minimum was 100 resolved trades. The run produced 77 resolved trades, 78 selected trades and one unresolved trade. Under the pre-frozen adjudication this prevents an economic PASS/FAIL classification even though descriptive economics can and must be reported.

## Descriptive economics

### Base — 20 bps round trip

- Resolved trades: 77
- Net expectancy: `-0.3005690596 R/trade`
- Profit factor: `0.6267126195`
- Win rate: `19.4805%`
- Median net result: `-1.0 R`
- TP1 reach rate: `48.0519%`

### Stress — 30 bps round trip

- Net expectancy: `-0.3332680198 R/trade`
- Profit factor: `0.5861026206`

### Day-block bootstrap

- Repetitions: 5,000
- Seed: 230911
- 95% interval: `[-0.5937607928, +0.0164601442] R/trade`
- Point estimate: `-0.3005690596 R/trade`

## Interpretation

This pre-period sample does not meet the frozen sample floor, so it must not be relabeled as a formal economic failure. Nevertheless, it is materially adverse robustness evidence: the same exact PBR01 4H geometry that produced positive point estimates in the later MEXC and Binance 2023–2024 blocks produced a negative point estimate, PF below 1 and negative stress economics in the non-overlapping 2021–January 2023 block.

The scientifically defensible interpretation is therefore **time/regime dependence remains a serious concern**. The prior positive samples remain historically valid, but this result does not justify promotion, shadow trading, 2025/2026 access, or parameter rescue.

## Governance

- Do not pool these 77 trades with prior samples to manufacture the 100-trade gate.
- Do not select favorable subperiods, assets or regimes after seeing this result.
- Do not alter costs, thresholds, hold, stop, target or PBR geometry to rescue the family.
- 2025 and 2026 remain locked for this replication.
- No live trading.
- No exchange mutation.
- No orders, alerts or webhooks.
- No merge to main.
- No deployment.
