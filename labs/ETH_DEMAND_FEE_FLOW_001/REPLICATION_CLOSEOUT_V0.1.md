# ETH-DEMAND-FEE-FLOW-001 — 45D REPLICATION CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35476638621`
Artifact: `ETH_DEMAND_FEE_FLOW_001_REPLICATION_V0_1`
Artifact digest: `sha256:62183834985faefefb5f2fc2e1465546982ffbf2da0349b321a88a37fc2a3426`

## Source semantics

Coin Metrics Community `FeeTotNtv` is suitable for this literature replication after Dencun: Coin Metrics' Dencun metric-change documentation states that `FeeTotNtv` counts transaction base fees, transaction priority fees, and blob fees. `SplyCur` and `PriceUSD` were available daily without authentication.

## Classification

**LITERATURE_REPLICATION_MIXED**

Frozen formula:
- FI = FeeTotNtv / SplyCur
- 30-day simple moving average of FI
- 90-day trailing median of raw FI
- FD = ln(smoothed FI / reference median)
- single horizon = 45 days
- 2026 remained closed

### 2024 discovery fit
- N = 294
- beta = +0.1562
- HAC t = 1.046
- p = 0.296
- R² = 9.50%

The coefficient sign and R² were positive, but the prospectively required HAC t >= 2 gate failed.

### 2025 fixed-model holdout
- N = 320
- fixed-2024-model OOS R² = **+7.67%**
- fixed-model direction accuracy = **69.38%**
- FD > 0 mean 45d log return = **+14.57%**
- FD <= 0 mean 45d log return = **-14.88%**
- spread = **+29.44 percentage points**
- holdout-only beta = +0.3671
- holdout HAC t = 1.903

The holdout is materially encouraging but cannot erase the failed 2024 inference gate.

### Full opened sample diagnostic (not a gate)
Using the already-opened 614 rows only:
- beta = +0.2320
- HAC t = 1.910
- p = 0.0561
- R² = 9.16%
- FD-positive vs nonpositive 45d return spread = +20.35 percentage points

## Scientific conclusion

The independent Coin Metrics source reproduces the **direction and economically large separation** of the published fee-flow relationship, especially in the 2025 holdout, but it does not satisfy the lab's frozen full replication gate.

This is neither NO_EDGE nor PROMOTED. It remains a **mixed literature replication with a prospective-only next step**.

No 2026 outcomes, PnL, trading rule, live trading, exchange mutation, wallet access or merge to main were opened.
