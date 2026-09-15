# MEMECOIN STRUCTURAL EDGE LAB — MSEL-001

## PRE-SOURCE PROTOCOL V0.1

Status: RESEARCH-ONLY / FAIL-CLOSED / OUTCOME-BLIND DESIGN
Branch: `memecoin-structural-edge-v0.1`
Date: 2026-09-15

## 1. Mission

Test whether memecoin launch structure observable before the decision time contains reproducible information about future downside risk and survivor quality.

This lab is not authorized to trade live, create exchange orders, mutate exchange state, deploy to Render, merge to main, or tune rules after outcomes are opened.

Primary thesis to falsify:

> The identity and structure of early flow — concentration, wallet relationships, buyer diffusion, creator history, bundle/sniper exposure and genuine liquidity participation — contains more forward information than price/volume alone.

The lab must accept NO_EDGE if this does not survive point-in-time validation, temporal holdout, realistic costs and regime checks.

## 2. Why the first attack is NOT ML and NOT 100x prediction

The first scientific problem is source integrity and leakage control, not model capacity. A complex model can easily learn survivorship, platform regime, observer-window artifacts, duplicated creator/wallet identities or post-outcome information.

Therefore MSEL-001 starts with a transparent Killer Filter MVE using simple rules / logistic or shallow-tree baselines. ML rankers are forbidden until the MVE proves that early features separate future bad outcomes in temporal out-of-sample data.

## 3. Lifecycle populations — MUST remain separate

1. Launch / first buyer window.
2. Bonding curve.
3. Graduation / migration event.
4. Early DEX.
5. Mature meme.

No model may mix these populations without an explicit transition design. A feature that is only available after graduation is forbidden in a pre-graduation model.

## 4. Decision snapshots

Frozen candidate snapshots:

- T+1 minute
- T+3 minutes
- T+5 minutes

Primary MVE snapshot: **T+5m**.

All features used by a T+5m decision must have event timestamps <= decision timestamp.

## 5. Initial feature families

### 5.1 Buyer diffusion
- unique buyers by T+1/T+3/T+5
- buyer arrival rate
- new-buyer acceleration
- repeat-buyer share
- buyers-to-transactions ratio
- median and dispersion of buyer size

### 5.2 Concentration
- top-1/top-3/top-5/top-10 holder share at decision time
- Gini / HHI style concentration
- early-buyer token share
- concentration excluding protocol/bonding-curve accounts

### 5.3 Wallet linkage / economic concentration
- same-funder relationships where observable point-in-time
- repeated co-occurrence among early buyers across prior launches only
- creator-linked wallets using only prior on-chain history
- bundle/cohort exposure known by decision time

Important: cluster membership derived from future launches is leakage and forbidden.

### 5.4 Creator/deployer history
- count of prior launches
- count/share of prior launches that graduated / collapsed, using only outcomes already completed before current launch
- creator age and prior activity
- creator sell behavior in prior launches

### 5.5 Flow quality
- buy vs sell counts and notional
- net inflow
- unique-buyer-adjusted volume
- volume concentration by wallet
- churn / round-trip / wash-like patterns

### 5.6 Liquidity / curve state
- curve progress at snapshot
- implied depth / price impact under deterministic curve state
- migration proximity if calculable without future info

Price-only momentum features may be included only as a benchmark/control, not as the thesis.

## 6. Outcome labels

Evaluate separately:

- graduation / migration
- -50% from executable entry
- -80% / catastrophic collapse
- +50%
- +100%
- MFE
- MAE
- survival / tradability at +15m, +1h, +6h, +24h

The operational rug label must be defined mechanically before opening outcomes. Do not use vague/manual labels unless blind and independently adjudicated.

## 7. Data-source gate — current findings

### Source A — Pump.fun official documentation
Authoritative for bonding-curve mechanics, automatic graduation and fee schedule. As of the current documentation, bonding-curve trading fee is 1.25% per trade. Entry+exit therefore starts at ~2.5% platform fee before slippage/priority fees/impact.

### Source B — MemeTrans
Useful for feature taxonomy and migrated-token risk research. Covers >40k launches that successfully migrated, >30M launchpad transactions and ~180M post-migration transactions, with 122 features and bundle-level data. NOT acceptable as the sole universe for the launch-level Killer Filter because successful migration creates survivorship selection.

### Source C — RED-PUMP-2026-v1
Large public launch universe (860k+ observed launches), but v1.4 explicitly retracts the original interpretation of the 0.198% figure as a 24-hour graduation rate. The collector effectively observed each mint for only roughly minutes because of a top-50 newest-token buffer. The rate is therefore a fast-window lower bound, not a 24h graduation estimate. Raw data may be useful for launch metadata / source-audit work, but its TIMEOUT field MUST NOT be treated as a clean 24h negative label.

### Source D — RED-COHORT-2026-v1
Public catalogue of 1,012 persistent early-buyer wallet cohorts derived from 1.58M buyer events / 166k launches. Important negative lesson: cohort-touched launches showed much higher buyer flow, but activity-matched placebo wallets showed an even larger lift; therefore repeated-wallet presence alone is NOT causal evidence of an edge. Cohort features require launch-quality controls and temporal construction.

### Source E — Catching the Rug (2026)
Large 6.4M-token study reports that first-five-minute trading data can classify rug-risk with classic ML and that cross-platform domain shift matters. Valuable as external plausibility evidence; not accepted as proof of tradable alpha until labels, features, sampling and execution assumptions are reproduced independently.

### Source F — Meme Coin Factories (2026)
Large-scale pump.fun study covering ~15M coins identifies manipulation classes including wash trading, creator-address obfuscation, coordinated sells, copycats and social-media manipulation. This directly supports adding manipulation-specific structural controls to the source gate.

## 8. Source-gate requirements before outcomes

A dataset may enter MSEL-001 only if we can document:

1. universe inclusion rule;
2. launch timestamp authority;
3. event timestamp authority;
4. creator identity derivation;
5. trade reconstruction method;
6. bonding-curve vs post-migration venue classification;
7. known missingness / endpoint truncation;
8. duplicate token / duplicate launch handling;
9. snapshot reproducibility at T+5m;
10. outcome reconstruction independent of feature data;
11. temporal split boundaries;
12. transaction-cost model.

Any source failing these requirements is QUARANTINED, not silently repaired.

## 9. MVE — Killer Filter

### Objective
Determine whether T+5m structural information can materially reduce catastrophic-loss exposure without using future information.

### Baselines
- random selection
- price/volume-only baseline
- simple launch-age/curve-progress baseline

### Candidate simple models
- fixed pre-registered rules
- regularized logistic regression
- shallow decision tree

No XGBoost/NN/GNN until the simple gate survives.

## 10. Temporal validation

Use chronological train/dev/test. No random split as primary evidence.

Wallet/creator reputation features must be recomputed as-of each launch time. A wallet's later success/failure must never leak backward.

A second regime-separated holdout is required before SURVIVES.

## 11. Costs / execution realism

Backtest must include, at minimum:
- Pump.fun / venue fees applicable at historical timestamp
- slippage from curve/AMM state
- price impact
- priority/network fees
- latency delay scenarios
- failed/missed transaction sensitivity
- liquidity/capacity limits

A classification win without executable PnL is not a trading edge.

## 12. STOP / SURVIVES criteria

### STOP / NO_EDGE
Stop if, in temporal OOS:
- structural features do not materially outperform price/volume-only baselines;
- apparent lift disappears after creator/wallet leakage controls;
- lift depends on one regime/week/source artifact;
- realistic execution costs erase economic value;
- result is only a tiny AUC improvement with no meaningful tail-risk reduction.

### SURVIVES MVE
Advance only if the T+5m Killer Filter shows all of:
- stable OOS separation of catastrophic outcomes;
- meaningful reduction in -80% / ruin incidence or MAE versus baseline;
- retention of a non-trivial share of future +50%/+100% winners;
- stability across chronological subperiods;
- no dependence on future-derived wallet clusters;
- positive economic value under conservative costs.

No fixed numeric performance threshold is retroactively tuned after outcomes. Before outcome opening, the implementation must freeze the exact quantitative gate.

## 13. Immediate next action

Build `SOURCE_GATE_RECEIPT_V01.json` for candidate public sources and determine which source can support a leakage-safe all-launch universe with T+5m transactions and independently reconstructed +24h outcomes.

Do NOT train ML yet.
Do NOT open a protected future holdout yet.
Do NOT perform live trading.
Do NOT merge to main.
