# CRYPTO LAB — BRANCH FORENSIC AUDIT V1

Status: **RESEARCH-ONLY / FORENSIC RECONCILIATION**  
Date: **2026-09-17**  
Repository: `joseluisvieira28-oss/Laboratorio`  
Working branch: `crypto-edge-classification-v0.1`  
Companion Drive inventory: `CRYPTO_REPO_ARCHIVE_PLAN_V1`  
Companion classification board: `CRYPTO_LAB_EDGE_CLASSIFICATION_BOARD_V1 — 2026-09-17`

## 1. Mission

Reconcile the current repository branch surface into economic mechanisms rather than treating every branch as an independent strategy.

The repository currently exposes **126 branch refs**. The previous archive inventory reconciled **117**; this audit adds the **9 refs created since that snapshot** and performs targeted authority recovery on previously `HOLD / PENDING AUTHORITY CHECK` lineages.

This document does **not** authorize branch deletion, live trading, exchange mutation, protected-holdout access, or a merge to `main`.

## 2. Core forensic rule

A branch is not an edge. A parameter variant is not an edge. A remediation branch is not an edge. A workflow branch is not an edge.

Branches must be collapsed into the economic mechanism defined by `CRYPTO_LAB_EDGE_CLASSIFICATION_V1`:

`TREND`, `MR`, `CARRY`, `RV`, `EVENT`, `MICRO`, `LEADLAG`, `VOL`, `FLOW`, `SUPPLY`, `MACRO`, `CREDIT`, `ACCESS`.

`PORTFOLIO` remains a later allocation layer, not an edge family.

## 3. Current-repository delta since the 117-ref archive snapshot

The nine newly observed refs are:

1. `archive/crypto-closed-labs-2026-09-16` — evidence/infrastructure snapshot; not an economic hypothesis.
2. `bnb-launchpool-demand-final-holdout-pre2022-v01` — BNB Launchpool canonical historical evidence; Tier 3 remains; historical rescue closed.
3. `bnb-launchpool-demand-forward-shadow-v01` — active forward-only BNB Launchpool evidence path.
4. `bnb-launchpool-demand-v2-oos-2025-v01` — canonical 2025 OOS evidence for the BNB Launchpool lineage.
5. `cross-venue-funding-basis-provenance-v0.5` — source/provenance recovery; technically blocked by rate limit; no scientific verdict.
6. `crypto-edge-classification-v0.1` — governance/infrastructure branch; not an edge.
7. `crypto-edge-radar-aggressive-v0.3` — radar/execution-readiness infrastructure; not an edge.
8. `crypto-edge-radar-render-v0.4` — rendering/monitoring infrastructure; not an edge.
9. `simple4h-recovery-v0.2` — terminal recovery closeout; `REJECTED_STONE`.

The Drive branch inventory has been extended from 117 to 126 refs and now contains dedicated `Forensic Reconciliation` and `Priority Attack Map` tabs.

## 4. High-value forensic corrections

### 4.1 BTC Options VRP — **attention, not stone**

Primary family: `VOL`; secondary: `CARRY`.

The parent Discovery MVE `OVRP-DVOL-RV30-001` is not merely pending authority. Its canonical classification is:

`DISCOVERY_PASS_VRP_EXISTS`

Under the frozen 2021–2024 sample:

- N = 192 weekly observations;
- mean VRP = +1239.50 volatility-%²;
- median VRP = +1133.97 volatility-%²;
- 74.48% of observations had VRP > 0;
- HAC 95% CI for mean VRP = [+674.19, +1804.81];
- moving-block bootstrap 95% CI = [+696.31, +1793.35];
- all four calendar-year means (2021, 2022, 2023, 2024) were positive;
- every prospectively frozen Discovery gate passed.

This proves a Discovery-level **implied-versus-realized variance premium** under the exact frozen definition. It does **not** prove an executable short-options strategy.

The separately frozen execution MVE recovered only 19 executable episodes versus a predeclared minimum of 120 using actual historical direction-matched Deribit public trade prints. The performance firewall therefore correctly prevented strategy PnL from being opened.

Current forensic state:

`DISCOVERY_PASS_VRP_EXISTS` + `EXECUTION_DATA_LIQUIDITY_INSUFFICIENT / NOT NO_EDGE / NO PERFORMANCE VERDICT`.

**Priority: P1.** The scientifically legitimate continuation is a **new** execution MVE only if a genuinely higher-quality historical quote/order-book source can be bound prospectively. No mark/mid substitution, wider windows, strike/DTE rescue, or 2025 opening is permitted under the closed execution MVE.

### 4.2 Aave Credit Stress — **high-interest source blocker**

Primary family: `CREDIT`.

The frozen predictor — change in Aave V3 Ethereum USDC `variableBorrowRate` — remains scientifically untested. Source recovery reached archival-RPC limitations, not a market verdict.

Current state:

`SOURCE_ACQUISITION_TECHNICAL_FAILURE + SOURCE_AUTH_BLOCKED / NOT NO_EDGE`.

Public RPC routes returned 403/429/525, request limits or pruned-history responses. No Aave economic values, BTC returns, regression, PnL, 2025 or 2026 outcomes were opened.

**Priority: P1.** The exact next action is to bind a legitimate reproducible archival Ethereum RPC and rerun the unchanged source gate. No Aave/USDC/window/horizon substitution is allowed to evade the blocker.

### 4.3 Stablecoin Peg Dislocation — **active mean-reversion frontier**

Primary family: `MR`; secondary: `RV`.

The V0.1 source attempt remains recorded as incomplete. V0.2 subsequently achieved:

`SOURCE_DATA_PASS`

and a final pre-Discovery one-shot authority exists for `SPD-USDCUSDT-CROSS25-H60-001`.

This audit did not find a canonical Discovery closeout in Drive/GitHub. Therefore the lab must not be described as passed or failed.

Current state:

`SOURCE_DATA_PASS / PRE-DISCOVERY FROZEN — DISCOVERY CLOSEOUT NOT VERIFIED`.

**Priority: P1.** First determine whether the authorized one-shot was already consumed. If not, execute only the frozen protocol without changing pair, threshold, horizon or event rule.

### 4.4 BNB Launchpool Demand — **real positive evidence, concentration-fragile**

Primary family: `EVENT`; secondary: `SUPPLY`.

The prospectively frozen 2025 OOS produced eight resolved trades with positive BASE and STRESS economics, but the largest winning trade contributed 53.96% of total positive BASE contribution, violating the <=40% concentration gate.

The independent older presample also remained positive but failed the same concentration concept (48.01%).

Canonical status remains:

`TIER 3 — WATCHLIST / NEAR-DIAMOND CANDIDATE`

Historical rescue is closed. Only genuinely prospective future events may advance the lineage.

**Priority: P1-WATCH**, not retrospective research.

### 4.5 BTC DVOL Futures Term Structure — **source-rich but exact gate failed**

Primary family: `VOL`; secondary: `RV`.

Canonical classification:

`LIFECYCLE_SOURCE_DATA_INSUFFICIENT / NOT NO_EDGE`.

The source work recovered 18 contracts, 11,194 public historical trades, 576 active contract-days and seven quarters, but the exact metadata-integrity gate failed 18/19 rather than the frozen 19/19 requirement.

No economic outcome was opened.

**Priority: P2.** A continuation requires a new prospectively justified source-gate design. The failed 1.0 integrity gate cannot be waived retrospectively.

### 4.6 Cross-Venue Funding / Basis V0.5 — **blocker, not new edge**

Primary family: `CARRY`; secondary: `RV`.

Current V0.5 status:

`TECHNICAL_BLOCKED_RATE_LIMIT / NO_SCIENTIFIC_VERDICT`.

The native-oracle source probe was stopped by HTTP 429. Economic outcomes and market numeric values remained unopened.

**Priority: P2.** Transport-only remediation is legitimate; generic funding/basis variants are otherwise already heavily covered and should not be multiplied.

## 5. Newly adjudicated terminal / archive-candidate lineages

These previously ambiguous branches now have sufficient authority to stop treating them as unresolved opportunities:

### Simple Trading 4H

`REJECTED_STONE` after the protected 2025 one-shot.

- 633 completed trades across seven frozen cells;
- 0/7 strong-evidence cells;
- 5/7 negative after 14 bps costs;
- the positive XRP Donchian cell failed statistical/bootstrapped evidence and cannot be isolated post-outcome.

Disposition: **archive candidate / recovery closed**. 2026 remains locked.

### BTC Options Expiry Reversal

The V2 Path 2 independent 2024 replication failed the frozen promotion policy:

- 12 trades;
- BASE mean remained slightly positive;
- STRESS mean was negative;
- minimum leave-one-trade-out BASE mean was negative.

Operational label: `STONE_AFTER_INDEPENDENT_OOS`.

Disposition: **archive candidate**. No 2025/2026 rescue.

### ETF Shortflow

`DISCOVERY_FAIL_NO_PROMOTION`.

- N = 221;
- frozen expected beta sign failed;
- companion strategy gross and net means were negative;
- PF < 1;
- stability/concentration gates failed.

Disposition: **archive candidate**. No direction inversion or ETF/horizon rescue.

### Capitulation Reversion

Canonical label remains deliberately nuanced:

`CLOSED_DATA_OR_TECHNICAL_FAILURE_NOT_NO_EDGE`.

However, 626 resolved economic diagnostics were negative across all windows/base/stress slices and no empirical support survived.

Disposition: **archive candidate while preserving the NOT_NO_EDGE source semantics**. No rescue.

### Treasury Auction Demand

`DISCOVERY_FAIL_NO_PROMOTION`.

The frozen direction showed only a small gross effect and did not survive the net/inference gates.

Disposition: **archive candidate**. No threshold/subperiod rescue.

## 6. Blocked / dormant lineages that must not be mislabeled NO_EDGE

- `ETF-CREATION-FLOW-001` — `SOURCE_FEASIBILITY_BLOCKED`; no outcomes opened; requires exact official point-in-time Shares Outstanding corpus.
- `COINBASE-BINANCE-LEADLAG-001` — `DATA_FAILURE`; synchronized coverage below source gate; not a market rejection.
- `HISTORICAL LIQUIDATIONS` — data unavailable / merged into existing forced-flow program; not negative market evidence.
- `QUARTERLY-BASIS-CONVERGENCE-001` — `DATA_FAILURE`; missing market bars stopped the run.
- `EXCHANGE-DELISTING-SHOCK-001` V0.3 — `INSUFFICIENT_SOURCE_SAMPLE`; zero qualifying events under the exact token-resolution rule; no outcomes opened.
- `AAVE-CREDIT-STRESS-001` — source/auth blocker, not NO_EDGE.
- `BTC-DVOL-FUTURES-TERMSTRUCTURE-001` — exact source gate failed, no outcome.
- `CROSS_VENUE_FUNDING_BASIS` V0.5 — rate-limit blocker, no outcome.

## 7. Repository concentration diagnosis

### Over-covered / low marginal research value

Unless the information source or economic mechanism changes materially:

- generic trend / breakout / indicator variants;
- ADX / VWAP / BB / classic-indicator clones;
- timeframe-only changes;
- generic BTC-alt lead-lag mining;
- raw funding/OI/taker-flow threshold variants;
- generic cash-and-carry fee/threshold rescues.

A new timeframe, threshold or asset is not a new edge family.

### Under-covered / high-interest frontier

1. **VOL** — executable volatility risk premium, term structure, point-in-time gamma/variance sources.
2. **CREDIT** — Aave/DeFi credit stress, health-factor/utilization/bad-debt states.
3. **MICRO** — forced liquidation flow and liquidity-state impact/decay.
4. **MR/RV** — economically anchored convergence such as stablecoin peg dislocations.
5. **MACRO/EVENT** — actual-vs-consensus surprise with point-in-time expectations and rates transmission.
6. **ACCESS** — listings, delistings, perpetual launches, migrations with exact event populations.
7. **FLOW** — predictive capital-flow states, clearly separated from contemporaneous flow.

## 8. Priority Attack Map

### P1 — attack / resolve now

- BTC Options VRP executable-source path — because the **underlying VRP Discovery passed** and only executable-data sufficiency is unresolved.
- DeFi Liquidation Shock — forced-flow microstructure; finish source gate outcome-blind.
- Aave Credit Stress — unique credit mechanism; solve archival RPC only.
- Stablecoin Peg Dislocation — source passed; determine one-shot execution state.
- Macro Surprise Direction — solve point-in-time consensus provenance before outcomes.
- MSEL / Memecoin Structural Edge — continue source reconstruction under outcome lock.

### P1-WATCH — collect genuinely prospective evidence

- ETF-CME Institutional Flow — Tier 2 fragile; forward shadow only.
- BNB Launchpool Demand — Tier 3, positive but concentration-fragile; future events only.

### P2 — worthwhile source/provenance work

- BTC DVOL Futures Term Structure.
- Cross-Venue Funding/Basis provenance.
- Perpetual-launch / listing / delisting structural-access families.
- Token unlock / supply-flow families with point-in-time inventory context.

### P3 — lower marginal value

- Quarterly Basis Convergence source repair.
- ETF Creation Flow exact source recovery.
- generic CARRY/RV variants already represented by stronger lineages.

### P4 / STOP — archive / do not clone

- Simple Trading 4H.
- Classic Indicators family.
- MVE ADX4H.
- closed VWAP / Extreme-MR cells.
- BTC Options Expiry Reversal exact lineage.
- ETF Shortflow exact lineage.
- Treasury Auction Demand exact lineage.
- terminal fee-pressure / settlement-demand / miner-stress variants.

## 9. Portfolio firewall

Do not combine failed, blocked or noisy signals to manufacture an attractive equity curve.

Portfolio/correlation work becomes relevant only when at least two independently eligible standalone candidates satisfy the governing promotion policy. Until then, the correct action is to strengthen independent mechanisms, not blend stones.

## 10. Governance

This audit is organizational and scientific only:

- research-only;
- fail-closed;
- no live trading;
- no exchange mutation;
- no order creation;
- no protected holdout opening unless separately authorized by a frozen protocol;
- no family relabelling or parameter rescue after outcomes;
- no branch deletion in this audit;
- no merge to `main` by this audit.

The draft PR containing this file must remain subject to normal review/adjudication.