# HTF-DH03-12H — 2025 ONE-SHOT OOS CLOSEOUT V0.1

Date: 2026-10-08
Status: **INDEPENDENT_2025_OOS_INSUFFICIENT_SAMPLE**

## Frozen authority

The 2025 one-shot OOS freeze was committed before any exact-DH03 2025 source/outcome access.
2026 remained unopened. No parameter, asset, subperiod, cost, stop, target, timeframe or source rescue was permitted.

## Canonical runs

Source gate:
- run: `37730638628`
- artifact id: `11528829916`
- artifact digest: `sha256:1235526af446c232d06bef9b952e4c51c715fd34d5790fd62315c78a41a8976a`

OOS evaluation:
- run: `37731155877`
- artifact id: `11530646229`
- artifact digest: `sha256:8c121c39b8be534aa0d87a56ec91ed1483de01bd72d558b3c2acde767b85988e`

## 2025 independent result

- selected trades: **53**
- resolved trades: **53**
- unresolved execution paths: **0**
- base expectancy: **+0.5242028091 R/trade**
- base profit factor: **1.8869268830**
- stress expectancy: **+0.4883354645 R/trade**
- stress profit factor: **1.8264377040**
- H1 expectancy: **+0.3575695435 R/trade**
- H2 expectancy: **+0.6098999171 R/trade**
- block-bootstrap 95% CI: **[-0.0674090521, +1.1172792766] R/trade**
- max single-symbol positive-net contribution share: **27.62%**
- max single-quarter positive-net contribution share: **65.55%**
- 2026 accessed: **false**

## Frozen gates

PASS:
- base expectancy > 0
- base PF > 1
- stress expectancy > 0
- H1 expectancy > 0
- H2 expectancy > 0
- symbol concentration <=70%
- quarter concentration <=70%
- unresolved execution paths = 0

FAIL:
- resolved trades >= 60: **53 < 60**
- bootstrap 95% lower bound > 0: **-0.0674 <= 0**

## Verdict

`INDEPENDENT_2025_OOS_INSUFFICIENT_SAMPLE`

The point economics are strong and directionally consistent across both calendar halves, but the prospectively frozen sample floor was not reached and statistical lower confidence bound remains below zero.

This is **not NO_EDGE** and **not RESEARCH_GRADE_DIAMOND**.

The 2025 one-shot is closed. It cannot be rescued by lowering the sample floor, changing symbols, selecting quarters, altering costs or opening 2026 under this experiment identity.

No live trading, order, authentication, wallet, exchange mutation or main merge.
