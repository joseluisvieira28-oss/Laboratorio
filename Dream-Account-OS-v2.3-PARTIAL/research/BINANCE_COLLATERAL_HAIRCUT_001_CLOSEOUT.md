# BINANCE-COLLATERAL-HAIRCUT-001 — DISCOVERY CLOSEOUT

Date: 2026-09-24
Branch: `binance-collateral-haircut-v0.1`
Canonical source gate: run `35987028847` — PASS
Canonical Discovery: run `35987191375` — SUCCESS
Scientific verdict: **DISCOVERY_NO_SIGNAL**
Maturity: **M3 DISCOVERY — TERMINAL**

## Source

Five official Binance Portfolio Margin collateral-ratio update clusters in 2024 were frozen before outcome access:
- 2024-06-10
- 2024-06-28
- 2024-07-30
- 2024-09-03
- 2024-11-29

Exact source manifest:
- 36 asset-events
- 32 unique assets
- 8 tightening events
- 28 loosening events

Official article identity/release/effective timing passed before market outcomes were opened.

## Frozen hypothesis

`shock_sign = sign(after collateral ratio - before collateral ratio)`

Primary:
`signed_MAR_24h = shock_sign × (asset log return 24h - BTCUSDT log return 24h)`

Positive values would mean collateral loosening preceded relative appreciation and collateral tightening preceded relative depreciation.

## Discovery result

Analyzable:
- 27 asset-events
- 5 independent clusters
- 8 tightening
- 19 loosening
- 9 exclusions solely for frozen >=30-day prior spot-history rule

Primary:
- mean signed MAR24 = **-0.0112421853** (-1.1242%)
- median signed MAR24 = **-0.0125556900**
- cluster-bootstrap 95% = **[-0.0300182523, 0.0051352344]**
- positive / negative = **12 / 15**
- one-sided exact sign-test p = **0.7789658308**
- tightening mean signed MAR24 = **+0.0042182522**
- loosening mean signed MAR24 = **-0.0177518432**

Every leave-one-cluster-out mean remained negative.

Diagnostics:
- mean signed MAR4 = +0.0005773438
- mean pre-event MAR24 = +0.0021000318

No diagnostic rescues the frozen primary.

## Adjudication

The pre-frozen signed access-shock mechanism does not survive Discovery.

The collateral-ratio loosening side is particularly inconsistent with the expected positive relative-price response. The June-10 tightening cluster had a small positive signed mean, but selecting tightening-only after observing the outcome is forbidden.

Therefore:
- no Validation/OOS;
- do not open 2025;
- do not open 2026;
- no sign inversion;
- no tightening-only rescue;
- no horizon/asset/subperiod/control substitution;
- no PnL/live layer;
- archive exact hypothesis.

Source bundle SHA256:
`3f703e523494a7f2a7bbb05859fa823f278edac71e0b9f4184a35124e4a8a8d0`
