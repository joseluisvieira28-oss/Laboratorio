# CMM-001 — CROSS-MARKET MISPRICING LAB
## PRE-DISCOVERY FREEZE V0.1 — 2026-09-25

STATUS: M1 MECHANISM / M2 SOURCE GATE ONLY
GOVERNANCE: ND-PROMOTION-POLICY-V3.0-FROZEN applies to any later adjudication.
BRANCH: cross-market-mispricing-001-source-gate-v0.1

## 1. PURPOSE
Test whether extreme disagreement between BTC spot state and independent non-spot information states resolves systematically through later spot convergence.

This lab does NOT assume that spot is wrong. It measures disagreement first, then later classifies which side moved to close the gap.

## 2. CLASSIFICATION
Primary Edge Family: RV — Relative Value / Convergence.
Secondary Family: MACRO.
Mathematical engine: cross-market state divergence + convergence.
Payoff shape: convergence / conditional directional return.
Evidence maturity at freeze: M1/M2 only.

Mechanism statement:
Different markets incorporate information with different participant sets, constraints and speeds. Options, rates, liquidity and positioning can therefore disagree materially with BTC spot. If the disagreement is not random, extreme gaps may resolve with a reproducible ordering of repricing.

Failure modes:
- non-spot states merely follow spot with no predictive content;
- source histories are incomplete or not point-in-time defensible;
- disagreement is regime-specific and unstable;
- option trade tape is too sparse or selection-biased to form a robust IV state;
- public positioning history is unavailable;
- apparent effect disappears after realistic costs and non-overlapping sampling.

## 3. PROTECTED PERIODS
Discovery candidate period: 2021-01-01 through 2024-12-31.
2025: LOCKED. No market outcomes, returns, PnL or strategy evaluation in this source gate.
2026: LOCKED.
No protected-period rescue is permitted.

## 4. SOURCE-GATE LAYERS
Core layers required for SOURCE_DATA_PASS:
A. OPTIONS — Deribit official historical trade/instrument endpoints.
B. RATES — Federal Reserve/FRED DGS2 daily 2Y Treasury yield.
C. STABLECOIN LIQUIDITY — DefiLlama historical aggregate stablecoin supply.
D. DERIVATIVES CROWDING — Binance BTCUSDT perpetual funding history.
E. POSITIONING — CFTC Traders in Financial Futures historical Bitcoin CME records.

Historical Binance open-interest statistics are explicitly NOT part of V0.1 because the public endpoint documents only the latest ~1 month. It may not be substituted with reconstructed or scraped values after outcomes.

## 5. OPTIONS SOURCE MODEL
No claim of historical order-book skew is allowed in V0.1.

If the source gate passes, the options state may be built only from timestamped historical OPTION TRADES that expose:
- timestamp
- instrument_name
- index_price
- trade price
- implied volatility (iv)
- option side derived from instrument name
- strike derived from instrument name

Planned options proxy:
daily median IV of OTM puts minus daily median IV of OTM calls,
using only contracts with:
- 7 to 45 calendar days to expiry;
- 5% to 20% out-of-the-money moneyness;
- valid trade IV and index price.

This is a trade-implied skew proxy, NOT a quoted 25-delta risk reversal.

## 6. FROZEN DAILY ALIGNMENT
Target frequency: daily.

Every signal timestamp must use only information available before the decision timestamp.
Publication-lagged series must be carried forward only after their official release time.

Planned oriented states, if Source Gate passes:
S_t = BTC spot state: trailing 7-day log return, rolling robust z-score.
O_t = options state: negative of trade-implied put-minus-call IV proxy z-score.
R_t = rates state: negative of trailing 5-business-day change in DGS2 z-score.
L_t = liquidity state: trailing 30-day change in aggregate stablecoin supply z-score.

Non-spot consensus:
N_t = median(O_t, R_t, L_t), requiring at least 2 of 3 valid components.

Primary divergence:
G_t = S_t - N_t.

Crowding modifiers are diagnostics/strata only and are NOT allowed to create the primary trigger:
F_t = BTCUSDT funding z-score.
C_t = CFTC Bitcoin positioning z-score using publication-lagged official data.

## 7. FROZEN PRIMARY TRIGGER
A candidate divergence event occurs when:
- at least 180 prior valid daily observations exist;
- at least 2 of 3 non-spot core states are available;
- |G_t| is above the expanding 95th percentile computed strictly from prior observations;
- events are clustered with a 72-hour cooldown; earliest qualifying event wins.

Direction for later Discovery:
fade the spot/non-spot gap.
If G_t > 0 => SHORT-aligned.
If G_t < 0 => LONG-aligned.

## 8. FROZEN PRIMARY OUTCOME — NOT OPENED IN SOURCE GATE
Primary horizon: 3 calendar days using next eligible UTC daily open conventions.
Primary economic metric: signed BTC return in the frozen convergence direction after 10 bps round-trip cost.

Diagnostics only:
1-day and 7-day horizons;
funding/crowding strata;
CFTC positioning strata;
who-capitulated resolution decomposition.

No horizon, threshold, sign, component or cost may be changed after protected outcomes are opened.

## 9. SOURCE-GATE PASS RULE
SOURCE_DATA_PASS requires ALL five core source layers A-E to pass deterministic coverage/provenance checks.

A source failure is classified SOURCE_BLOCKED / DATA_FAILURE as appropriate.
It is NOT NO_EDGE.

Only after SOURCE_DATA_PASS may a separate pre-Discovery execution authority be created.
This document does not authorize Discovery.

## 10. HARD PROHIBITIONS
- no 2025/2026 outcomes;
- no BTC forward returns or PnL in the source workflow;
- no live trading;
- no orders;
- no authenticated exchange mutation;
- no wallet;
- no merge to main;
- no Render deployment;
- no paid data purchase;
- no post-outcome tuning;
- no silent replacement of missing historical fields;
- no relabeling a source blocker as scientific failure.

## 11. ANTI-DUPLICATION
CMM-001 is not a clone of OPTIONS-SPOTPERP-001, MACRO-TRANSMISSION-001, ETF-CME-INSTFLOW-001 or the stablecoin peg lab.
Those families test standalone mechanisms.
CMM-001 tests cross-market disagreement itself as the state variable and preserves every component lineage separately.

END OF PRE-DISCOVERY FREEZE V0.1
