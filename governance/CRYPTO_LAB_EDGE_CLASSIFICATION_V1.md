# CRYPTO LAB — EDGE CLASSIFICATION V1

Status: **FROZEN FRAMEWORK V1 / RESEARCH-ONLY**  
Date: 2026-09-17  
Repository: `joseluisvieira28-oss/Laboratorio`  
Drive board: `CRYPTO_LAB_EDGE_CLASSIFICATION_BOARD_V1 — 2026-09-17` (`1fv3S6nawlOUePlcR7TQXb4aqnois1nxuVeDTeUuS8fM`)

## 1. Purpose

This framework classifies each Crypto Lab on four independent axes:

1. **Economic edge family** — how the mechanism could make money.
2. **Mathematical engine** — the mathematical structure expected to create positive expectancy.
3. **Scientific maturity** — how far the experiment has progressed.
4. **Scientific verdict** — what the evidence currently says.

These axes MUST NOT be collapsed into a single score. A visually attractive backtest, a high win rate, a 3R target, or a mature engineering implementation is not itself an edge.

## 2. Mandatory rule for every new lab

Every new top-level directory under `labs/<LAB_ID>/` must contain:

`EDGE_CLASSIFICATION_V1.json`

before the lab can be merged into the canonical branch.

The classification file must be created **before opening market outcomes** and must include the economic mechanism, primary family, mathematical engine, expected payoff shape, failure mode, regime dependency, source authority and protected holdouts.

The primary family must be chosen prospectively. A secondary family may be recorded, but MUST NOT be used post-outcome to reframe or rescue a failed primary hypothesis.

## 3. Controlled primary edge families

| Code | Family | Economic idea |
|---|---|---|
| `TREND` | Trend / Asymmetry | Persistent directional movement; winners may outrun capped losses. |
| `MR` | Mean Reversion | Temporary deviations revert toward equilibrium. |
| `CARRY` | Carry / Yield | Earn a recurring premium for holding or hedging an exposure. |
| `RV` | Relative Value / Convergence | Related instruments temporarily misprice relative to each other. |
| `EVENT` | Event / Conditional | A discrete event changes the conditional distribution of future outcomes. |
| `MICRO` | Microstructure / Forced Flow | Order-flow imbalance, liquidations or constrained participants create temporary pressure. |
| `LEADLAG` | Lead-Lag / Information Diffusion | One venue or asset incorporates information before another. |
| `VOL` | Volatility / Variance Premium | Implied/expected movement differs from realized movement or term structure. |
| `FLOW` | Capital / Positioning Flow | Persistent institutional, venue or on-chain flow contains information or pressure. |
| `SUPPLY` | Supply / Demand Structural | Issuance, unlocks, staking demand or utility change the inventory balance. |
| `MACRO` | Cross-Asset / Macro Regime | Rates, liquidity or cross-asset stress alter crypto conditional behaviour. |
| `CREDIT` | Credit / DeFi Stress | Borrowing stress, collateral pressure or protocol credit conditions transmit to markets. |
| `ACCESS` | Market Access / Structure Change | Listings, delistings, perpetual launches or migrations change who can trade and how. |

`PORTFOLIO` is deliberately **not** an edge family. Diversification is a later allocation layer applied only after independently eligible standalone candidates exist.

## 4. Mathematical engine vocabulary

The `mathematical_engine` field is free text but should map to one or more of these structures:

- expectancy / payoff asymmetry;
- positive or negative skew;
- conditional probability `P(outcome | state/event)`;
- convergence / spread normalization;
- carry / yield accumulation;
- cross-correlation / lead-lag dependency;
- volatility / variance premium / term structure;
- order-flow imbalance / impact decay;
- hazard / stress-state response;
- regime classification / transmission beta;
- Bayesian or sequential evidence update;
- portfolio correlation / covariance **only after standalone eligibility**.

## 5. Scientific maturity ladder

| Level | Meaning |
|---|---|
| `M0` | Idea only |
| `M1` | Mechanism defined and frozen |
| `M2` | Source / provenance validated or being validated |
| `M3` | Discovery executed |
| `M4` | Independent replication executed |
| `M5` | OOS / protected holdout executed |
| `M6` | Forward shadow / prospective observation |
| `M7` | Micro-live under a separately authorized risk contract |
| `M8` | Production |

Maturity is NOT a quality score. A lab can be `M5` and be a confirmed stone.

## 6. Verdict is a separate field

Use the exact scientific state supported by authority, including where appropriate:

- `NOT_TESTED`
- `ACTIVE`
- `BLOCKED`
- `DATA_FAILURE`
- `TECHNICAL_FAILURE`
- `PROVENANCE_FAILURE`
- `INSUFFICIENT_SAMPLE`
- `NO_EDGE`
- `TIER_3_WATCHLIST`
- `TIER_2_PROMOTED_CANDIDATE`
- `TIER_1_VALIDATED_EDGE`
- `REJECTED_STONE`

Historical labels remain immutable. Later evidence may change the **current** classification while preserving the historical path.

## 7. Required pre-outcome questions

Every new lab must answer, before outcomes:

1. **Who/what is paying the edge and why?**
2. **What exact mathematical structure should produce positive expectancy?**
3. **What observation would falsify the mechanism?**
4. **Which regime should help or hurt it?**
5. **Is the signal available before the future window being tested?**
6. **What is the canonical point-in-time source?**
7. **What costs/execution assumptions apply if the lab is executable?**
8. **Which dates/data are protected holdouts?**
9. **Which existing lab/family is this most similar to?**
10. **Why is this not merely a parameter/timeframe/asset clone of an already-tested mechanism?**

Failure to answer #9-#10 is a duplication warning.

## 8. Family duplication rule

A new indicator, timeframe, asset or threshold is **not automatically a new edge family**.

Examples:

- 20D breakout, 30D breakout and MA momentum may all be one `TREND` mechanism family.
- Raw funding, raw basis and a fee-tuned cash-and-carry variant may all be one saturated `CARRY/RV` family unless the economic mechanism is materially different.
- Another BTC-alt lead-lag window is not a new `LEADLAG` mechanism merely because the lag changes.

A new lab should be preferred when it introduces a materially new information source, causal mechanism, participant constraint or market structure.

## 9. Portfolio firewall

Portfolio combination is allowed only after the applicable frozen promotion policy says standalone candidates are eligible.

Do not combine noisy or failed Tier 3/Tier 4 signals to manufacture an attractive equity curve. Correlation/diversification analysis must itself be prospective and frozen before the portfolio outcome is viewed.

## 10. Current concentration map — initial V1 audit

The 2026-09-16 repository archive plan reconciled 117 branch refs and showed a large concentration in trend/indicator, event and legacy relative-value work, while many credit, volatility-source and forced-flow mechanisms remained blocked or under-developed.

The initial V1 board therefore treats the following as broad research posture, not promotion:

- **Over-covered / saturated generic form:** generic trend/indicator clones, generic BTC-alt lead-lag, raw funding/OI/taker-flow variants.
- **Still high-interest if source-clean:** forced-flow microstructure, DeFi credit stress, point-in-time volatility/VRP/gamma, market-access changes, expectations-aware macro surprise, predictive capital-flow states.
- **Portfolio layer:** deferred until at least two independently eligible standalone candidates exist.

Canonical current statuses remain governed by the underlying lab authority, including the Near-Diamonds V2 registry and individual closeouts. This classification framework must never overwrite a lab verdict.

## 11. Governance

Default posture:

- research-only;
- fail-closed;
- no live trading;
- no exchange mutation;
- no order creation;
- no main merge unless separately authorized;
- no protected holdout opening without the relevant frozen authorization;
- no post-outcome tuning or family relabelling to rescue a result.

The classification framework organizes research. It does not authorize execution or promotion by itself.
