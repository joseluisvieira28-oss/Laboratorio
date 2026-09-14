# STABLECOIN-EXCHANGE-FLOW-001 — OFFICIAL DISCOVERY CLOSEOUT

LAB: `STABLECOIN-EXCHANGE-FLOW-001`  
MVE: `SEF-BINANCE-PUBLIC-USDT-ETH-1D-001`  
Discovery run: `34898172236`  
Discovery artifact: `stablecoin-exchange-flow-001-discovery-34898172236-1`  
Final classification: **NO_STATISTICAL_EDGE**  
Economic companion classification: **NEGATIVE_EXPECTANCY**  
Promotion: **FALSE**

## Immutable evidence chain

- Original source run: `34896944142` — original `DATA_FAILURE` receipt preserved because 23/243 independent sequential QA calls were HTTP 429.
- Pre-outcome QA remediation run: `34897999268` — `SOURCE_DATASET_PASS`, 243/243 exact state matches, 0 errors, 0 mismatches.
- Source CSV SHA256: `726da5681b1f135e8e69a95cd6b11296aaa6e344de857376b9271cabdd48804a`.
- QA comparison SHA256: `3ea784058ba5cd5599d1b29d24d53157874a0a1eb48fda1968ea4fecdcb0961e`.
- Discovery observations SHA256: `11fd0e0f0a92fc55c829e2f6b043b8594f8bd713c441f025b24489aac4283412`.
- Binance archive manifest SHA256: `db548a5fd2fc2ad4755fe556a3edbf782a6355b67a1191b172e7bc7a9e84d75d`.

## Frozen primary result

- N: `779`
- beta: `+6.7017962879 bps` BTC return per `+$1bn` USDT basket net flow
- one-sided 7-day moving-block bootstrap p: `0.1628418579`
- alpha: `0.05`
- beta-positive gate: PASS
- statistical-significance gate: **FAIL**

## Companion economics

- mean gross: `-1.2520052095 bps/trade`
- mean NET10: `-11.2520052095 bps/trade`
- mean NET14: `-15.2520052095 bps/trade`
- PF NET14: `0.4038130582`
- economic gate: **FAIL**

## Calendar stability — NET14

- 2022 partial: N=50, mean `-22.1376653966 bps/trade`
- 2023: N=365, mean `-18.2133818565 bps/trade`
- 2024: N=364, mean `-11.3366604690 bps/trade`
- non-negative calendar partitions: `0`
- stability gate: **FAIL**

## Final scientific decision

The fitted relationship has the hypothesized positive sign but does not provide sufficient statistical evidence under the frozen primary test, and the frozen sign strategy is economically negative before and after costs.

The exact MVE is closed. No post-outcome threshold, lag, time-window, address-basket, normalization, regime, nonlinear transformation, cost, or ML rescue is authorized.

## Governance

- 2025 accessed: NO
- 2026 accessed: NO
- live trading: NO
- exchange mutation: NO
- merge to main: NO
- deployment: NO
- post-outcome tuning: NO
