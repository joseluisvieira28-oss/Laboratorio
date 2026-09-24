# BINANCE-COLLATERAL-HAIRCUT-001 — DISCOVERY PROTOCOL PRE-FREEZE

Date frozen: 2026-09-24
Status: DISCOVERY_PRE_FROZEN / OUTCOMES CLOSED
Discovery window: 2024 only
2025: SEALED OOS
2026: SEALED

## Hypothesis

Portfolio Margin collateral-ratio changes create a signed access shock.

For each source-valid asset-event:

`shock_sign = sign(after_ratio - before_ratio)`

Primary outcome:
`signed_MAR_24h = shock_sign * (asset_log_return_24h - BTCUSDT_log_return_24h)`

A positive value means:
- collateral loosening was followed by relative appreciation, or
- collateral tightening was followed by relative depreciation.

No sign inversion after outcomes.

## Market source

Binance Data Vision public SPOT klines.

Asset eligibility:
- exact `ASSETUSDT` spot pair;
- pair must have public Binance Spot data at least 30 calendar days before event effective time;
- BTCUSDT is the frozen market-control pair;
- no USDC/FDUSD/BTC cross substitution;
- no synthetic prices.

Sampling:
- 5-minute klines;
- entry = close of last completed 5m bar strictly before effective timestamp;
- 4h diagnostic exit = same rule at effective+4h;
- primary 24h exit = same rule at effective+24h;
- pretrend diagnostic = last completed bar before effective-24h to entry.

If exact source bars are unavailable, exclude as SOURCE_INELIGIBLE and record the reason.

## Independence

Asset-events from the same canonical article/effective timestamp form one cluster.
Inference bootstrap resamples clusters, preserving every asset-event inside selected clusters.

## Frozen Discovery gate

Minimum:
- >=20 analyzable asset-events;
- >=4 independent clusters;
- >=5 analyzable tightening events;
- >=5 analyzable loosening events.

Primary mechanism survives only if all pass:
1. mean signed MAR24 > 0;
2. cluster-bootstrap 95% lower bound of mean signed MAR24 > 0;
3. one-sided exact sign-test p < 0.05 for signed MAR24 > 0;
4. mean signed MAR24 among tightening events > 0;
5. mean signed MAR24 among loosening events > 0;
6. every leave-one-cluster-out mean signed MAR24 > 0.

Bootstrap:
- 10,000 reps;
- seed 20261003.

Classification:
- `DISCOVERY_MECHANISM_SURVIVES`
- `DISCOVERY_NO_SIGNAL`
- `DISCOVERY_INSUFFICIENT_SAMPLE`
- source/technical failures remain separate.

## Diagnostics only

- mean/median signed MAR 4h;
- unsigned/raw MAR24 by tightening vs loosening;
- pre-event 24h market-adjusted return;
- per-cluster results;
- per-asset results.

Diagnostics cannot rescue the primary result.

## No-rescue firewall

Do not:
- change horizon;
- invert sign;
- select only tightening or loosening after outcome;
- select assets/subperiods;
- change BTC control;
- replace missing USDT pairs;
- alter minimum sample;
- use 2025 or 2026;
- compute live orders;
- merge to main.
