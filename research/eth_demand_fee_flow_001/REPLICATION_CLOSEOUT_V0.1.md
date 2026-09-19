# ETH-DEMAND-FEE-FLOW-001 — SOURCE + REPLICATION CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35476370361`
Canonical workflow head: `861a3953be6b9e6ef0accdbea24d60d5bb3070ab`
MVE: `EDFF-FD45-REPLICATION-001`

## Source gate

**EDFF_SOURCE_FULL**

Bounded Coin Metrics Community API request:
- ETH `FeeTotNtv`
- ETH `SplyCur`
- 2022-12-01 through 2024-12-31
- 762 daily rows
- 100% non-null fee observations
- 100% non-null supply observations
- 294 post-Dencun days
- no credentials
- zero cash spend
- no 2025/2026 request

This prospectively unblocks the older `PROTOCOL-DEMAND-001` source-governance blocker because the source supports explicit server-side start/end bounds.

## Replication verdict

**REPLICATION_MIXED**

Primary post-Dencun 2024 test:
- N = 248
- 45-day beta = +0.179882
- HAC t = +1.3104
- HAC two-sided p = 0.1901
- R² = 13.9612%
- directional accuracy = 63.31%
- mean future 45d log return when FD > 0 = +12.1382%
- mean future 45d log return when FD < 0 = -6.5783%

Frozen secondary horizons:
- 30d beta = +0.080880, R² = 4.3928%, directional accuracy = 57.41%
- 60d beta = +0.223007, R² = 17.5318%, directional accuracy = 65.67%

Pre-Dencun/placebo-style 2023 window:
- beta = -0.064005
- HAC p = 0.6024
- R² = 2.6071%

## Interpretation

The sign/shape is consistent with the published post-Dencun mechanism: the primary 2024 coefficient is positive, both frozen secondary horizon coefficients are positive, and the 2023 placebo coefficient is negative/insignificant.

However, the primary frozen significance gate fails because HAC p = 0.1901. Therefore the correct terminal status for this exact replication is **REPLICATION_MIXED**, not SURVIVES and not PROMOTED.

The observed 2024 R² is close in magnitude to the 14.4% expanding-window OOS R² reported by the external study, but the samples and alignment are not identical and this overlap must not be treated as independent proof.

No PnL, live trading, 2025/2026 outcome, wallet access, exchange mutation or merge to main was opened.
