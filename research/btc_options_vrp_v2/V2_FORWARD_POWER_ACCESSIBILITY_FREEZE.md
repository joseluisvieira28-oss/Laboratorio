# BTC-OPTIONS-VRP-001 — V2 FORWARD POWER & ACCESSIBILITY FREEZE
Date: 2026-10-07
Branch: `btc-options-vrp-v2-forward-2026-10-07`
Status: `UNDERPOWERED_PRE / FORWARD_SOURCE_BUILD_AUTHORIZED`

## Economic claim
Service: sell convexity/insurance.
Compensation: option premium.
Risk carried: short-volatility tail/jump risk plus hedge/execution risk.
Persistence thesis: risk-bearing capital and demand for protection can support a public, known premium without requiring informational secrecy.

## Hurdle and design alternative
Primary estimand: **stress net return on the frozen 1 BTC collateral denominator per seven-day episode**.

Economic hurdle:
- annual compounded hurdle: 10%
- seven-day H = `(1.10)^(7/365)-1`
- H = **0.0018295380282 = 18.2954 bps**

Power design alternative:
- annual compounded design alternative: 20%
- seven-day theta_design = `(1.20)^(7/365)-1`
- theta_design = **0.0035026979608 = 35.0270 bps**
- detectable margin beyond H = **16.7316 bps**

The annual rates are operator research-policy hurdles, not universal scientific constants.
They were frozen before any new 2026 forward performance outcome is opened.

## Nuisance variance
Legacy execution run `35069743562`, artifact `10435985764`,
digest `sha256:b5687c1dcf9aa38e478b0ca875b48e53ef3f315a177cab8ce6d796cd9eb9c465`:
- executable episodes: 19;
- performance was canonically unadjudicated because source liquidity/sample was insufficient;
- sample SD base return = **0.0022903694158**;
- sample SD stress return = **0.0022938068057**.

These old outcomes are used ONLY as nuisance-variance planning evidence.
The mean, hit rate and apparent profitability are not used to promote the forward design.

Source-only geometry audit on 2026-10-07 found no active expiry in the old 25–35 DTE band at the current observation time; the only captured expiry in the 20–45 envelope was ~22.6 DTE. No performance outcome was opened. Therefore a NEW V2 forward MVE freezes expiry selection as the available expiry nearest 30 DTE within 14–60 DTE. This is a pre-outcome source-design correction, not rescue of the old historical MVE.

Because that geometry differs from the legacy 25–35 DTE episodes, conservative planning sigma = stress SD × 1.50 = **0.0034407102085**.

## Analytical planning
For one-sided superiority:
`H0: theta <= H`
`H1: theta > H`

Power is evaluated at `theta_design > H`, never at H itself.

Approximation:
`N_eff ≈ [((z_0.95 + z_0.80) * sigma) / (theta_design-H)]^2`

This gives approximately **26.1 effective observations**.
Freeze target:
- minimum effective N before activation: **30**
- planned power at N_eff=30: **0.8458**
- raw complete-cohort collection target: **36**, providing attrition/dependence buffer.

A blind re-estimation may reduce N_eff for missingness/dependence using only source integrity and nuisance quantities. It may NOT use the observed forward mean.

## Forward source design
- one cohort per Thursday 08:00 UTC;
- point-in-time Deribit public chain/BBO only;
- same expiry + strike call/put;
- active expiry nearest 30 DTE inside a fixed 14–60 DTE envelope;
- closest absolute log-moneyness;
- 0.1 option amount per leg;
- seven-day hold;
- static initial BTC-PERPETUAL delta hedge;
- measured BBO only;
- no mid-price substitution;
- no regime filter;
- no outcome-driven exclusions.

## Current verdict
`UNDERPOWERED_PRE`

This is NOT NO_EDGE.
This is NOT SURVIVES.
The family is authorized to build prospective source evidence only.
No performance outcome may be opened until a separate activation receipt proves:
1. source integrity;
2. at least 36 raw complete cohorts;
3. blind N_eff >= 30;
4. power at the frozen design alternative >= 80%;
5. all V2 freeze hashes unchanged.
