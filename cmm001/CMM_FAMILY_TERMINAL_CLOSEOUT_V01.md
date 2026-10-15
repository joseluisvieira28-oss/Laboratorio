# CROSS-MARKET MISPRICING / CONVERGENCE FAMILY — TERMINAL CLOSEOUT V0.1
Date: 2026-09-25

## Scope of this closeout
This closes the exact composite-convergence research lineage built from BTC spot state plus the already frozen Deribit options, DGS2 rates and stablecoin-liquidity states.

It does NOT claim that every possible form of cross-market relative value, options/spot-perp dislocation, direct arbitrage parity or information diffusion is invalid.

It DOES prohibit cosmetic rescue of this exact lineage.

## Lineage

### 1. CMM-001 — static cross-market state gap
Source/Data Gate: PASS 5/5 after transport-only Binance funding remediation.
Discovery terminal state: INSUFFICIENT_SAMPLE because 2024 had N=4 below the frozen per-block minimum 8.

Economic evidence leaned negative:
- pooled N=35
- mean NET10 -32.8199 bps
- PF 0.8205
- median NET10 -47.3048 bps
- 2021H2-2022 mean -15.9743 bps
- 2023 mean -12.4893 bps
- 2024 mean -177.3134 bps

No static-fade rescue authorized.

### 2. CMM-RM-001 — exploratory resolution map
Diagnostic only / zero promotion authority.

The standardized state gap shrank frequently:
- 1d: 77.14%
- 3d: 94.29%
- 7d: 97.14%

At 7d, 76.47% of shrinking state gaps were labelled SPOT_LED.

This initially looked mechanistically interesting but was not trading evidence.

### 3. CMM-DRV-001 — dynamic spot-led confirmation child
New identity frozen before candidate-specific 2025 outcome.

Funnel:
- 9 initial extreme-gap cycles
- 3 confirmed entries
- 3/3 losses

Economics:
- mean NET10 -136.6528 bps
- median NET10 -138.9890 bps
- PF 0
- positive fraction 0%

Formal state: INSUFFICIENT_SAMPLE because N=3 < frozen minimum 8.
Economic lean: strongly negative.
No rescue / no 2026 historical opening.

### 4. CMM-MECH-001 — zero-PnL roll-off decomposition
Diagnostic only.

The retired spot state was:
S_raw(d) = ln(P[d]/P[d-7])

The audit proved that apparent SPOT_LED state convergence was materially contaminated by the t-7 return rolling out:

Among state-space SPOT_LED cases:
- 1d: |roll-off| > |actual BTC move| in 60.00%; actual BTC moved against closure in 20.00%
- 3d: |roll-off| > |actual BTC move| in 80.95%; actual BTC moved against closure in 47.62%
- 7d: |roll-off| > |actual BTC move| in 84.62%; actual BTC moved against closure in 42.31%

Decision:
retire trailing-7d BTC state as a direct spot-mispricing proxy.

### 5. CMM-PR-001 — direct causal BTC price residual
Materially new mechanism created specifically to remove the roll-off flaw.

Definition:
- direct BTC 24h return, not 7d rolling return
- causal walk-forward OLS on O_z/R_z/L_z using exactly prior 365 valid observations
- residual normalized on prior 180 causal residuals
- future target exact Binance Spot 18:00 -> next-day 18:00
- primary hypothesis beta(residual_z -> future return) < 0
- 2021-2025 development only / ZERO promotion credit
- 2026 not accessed

Result:
- N=1,035
- beta +6.1716 bps per residual-z (opposite expected sign)
- Spearman +0.007432
- mean mean-reversion gross -8.5471 bps/day
- mean NET10 diagnostic -18.5471 bps/day
- 7-observation moving-block bootstrap beta:
  - p05 -5.3106
  - median +5.5107
  - p95 +15.6521
  - 79.86% beta >= 0
- 2023 beta +14.9261
- 2024 beta +3.6742
- 2025 beta -3.1141

Frozen development survival gates:
- sample N>=500: PASS
- overall beta<0: FAIL
- bootstrap p95<0: FAIL
- Spearman<0: FAIL
- mean MR gross>0: FAIL
- >=2 years N>=100 with beta<0: FAIL

Terminal classification:
DEV_MECHANISM_FAIL__CLOSE_EXACT_RESIDUAL

No forward is authorized.

## Scientific conclusion
The tested composite idea:

> "BTC spot materially disagrees with a combined options/rates/stablecoin state, therefore BTC will subsequently converge toward that non-spot consensus"

is NOT supported under either:
1. the original standardized state-gap formulation, or
2. the corrected direct causal price-residual formulation.

The most visually impressive diagnostic — frequent gap closure — was partly an artifact of the rolling spot-state definition and did not translate into stable next-period BTC convergence after that artifact was removed.

## Anti-rescue rule
Do NOT continue this family by:
- changing 7d/24h/48h/72h windows;
- changing q95 or adding a residual threshold;
- removing the losing years;
- choosing long-only or short-only;
- selecting only stablecoin/rates/options after seeing results;
- changing OLS to ridge/lasso/Huber because of the observed result;
- adding funding/CFTC/OI to cosmetically create a "new" composite;
- opening 2026 historical outcomes as rescue.

Any future "market is wrong" research must use a materially different economic observable or market identity with its own causal mechanism, new LAB_ID and pre-outcome freeze.

## Preserved positive knowledge
This closeout does not invalidate already independent/direct families such as OPTIONS-SPOTPERP or other explicit parity/relative-value mechanisms. Direct instrument-level dislocation is a different hypothesis from heterogeneous macro/options/liquidity state aggregation.

## Canonical evidence
- CMM-001 Source/Data Gate V0.2 run: 36111573403
- CMM-001 terminal technical closeout run: 36108372138
- CMM-001 event ledger SHA256: 8c79b4287d5a0bc7ab263b856b56bded638d75e2ea14c25434156a4eb20909d8
- CMM-RM-001 resolution map run: 36112118277
- CMM-DRV-001 authority commit: 42070887e09aee0560522c4d1f1b809804cf82f1
- CMM-DRV-001 2025 run: 36112980562
- CMM-MECH-001 roll-off audit run: 36113306142
- CMM-PR-001 authority commit: 4c06dd154fe95cd24f3a91ec1c6e073a35deca76
- CMM-PR-001 development run: 36114311971
- Drive scientific closeout: 1jEAzSvQDbwM7H5PGLgvfJgpFjoEM8ej1sqOVC8aLrjk
- Classification Board updated with CMM-001, CMM-DRV-001 and CMM-PR-001.

## Governance
No live trading.
No micro-live.
No orders.
No exchange mutation.
No wallet.
No alerts/webhooks.
No Render deployment.
No merge to main.
2026 historical outcomes remain sealed for this lineage.
