# PRESSURE MINING SOURCE GATE CLOSEOUT V0.4

Date: 2026-09-27
Branch: pressure-mining-program-v0.1
Status: SOURCE/MECHANISM PROGRAM ADVANCED — ONE NEW PROTECTED ECONOMIC DISCOVERY READY-BUT-LOCKED

## Executive routing

V0.4 adds one materially new Compound child:
**COMPOUND-REALIZED-DISPOSAL-FLOW-001**.

It passed the source/mechanism gate and the untouched-2025 predictor-only viability census.
A protected 2025 economic Discovery is now fully frozen prospectively but **market outcomes remain unopened**.

No Tier promotion is claimed.

---

## 1. COMPOUND-INVENTORY-LIQUIDATION-001

Current state:
**SOURCE_CENSUS_PASS / PARENT SOURCE-MECHANISM LINEAGE**

Preserved source facts:
- 894 AbsorbCollateral;
- 999 BuyCollateral;
- 505 unique absorbed borrowers lower bound;
- 7 collateral assets;
- protocol-owned seized inventory can persist and later be disposed.

No standalone edge claim.

---

## 2. COMPOUND-INVENTORY-PERSISTENCE-001

Current state:
**DISCOVERY_FAIL_NO_SUPPORT — EXACT 24H CHILD TERMINAL / NO RESCUE**

Frozen 2023-2024 Discovery:
- N=17;
- 4 assets;
- 12 ISO weeks;
- mean REL_24H +165.5784 bps against the frozen bearish sign;
- clustered bootstrap 95% [-16.2838,+373.7313];
- every leave-one-episode-out mean remained positive.

No inverse direction, alternate horizon, ETH-only, duration-threshold or subgroup rescue.
2025+ market outcomes remain unopened for this terminal child.

---

## 3. COMPOUND-REALIZED-DISPOSAL-FLOW-001

### 3.1 Novelty / Negative Map

Current state:
**MATERIALLY_NEW_MECHANISM_PASS / ZERO INHERITED CREDIT**

The lab measures the actual BuyCollateral disposal transaction and recipient/routing path rather than residual protocol inventory.

The failed persistence child gives this lab zero statistical credit and cannot determine direction.

### 3.2 Source / realized-flow gate

Canonical successful run:
- run 36347379578;
- artifact 10940652459;
- artifact digest sha256:69a44dc3c51f67e895fe0c29e2636a03064e7ab07a1820c6a1e4a06ca19b4a30;
- receipt pre-self SHA256 e081b77cdeb6bef1a21fb1d6be2a5b4d5e9fb016fd2872eaf35eb823d6ccf707.

Status:
**SOURCE_REALIZED_FLOW_PASS**

2023-2024 corpus:
- 999 BuyCollateral logs;
- 899 unique transactions;
- 47 buyers;
- 7 assets.

Frozen deterministic receipt probe:
- 64/64 selected transactions usable;
- 68 BuyCollateral events;
- 68/68 recipients inferred = 100%;
- 59/68 recipient paths had a later same-transaction collateral Transfer = 86.7647%;
- event buyer == transaction sender for 0/68.

The 86.7647% onward-transfer statistic is routing evidence only.
It does not by itself prove a DEX sale or market edge.

Historical transport attempts remain preserved:
- V0.1: partial because Blockscout RPC returned HTTP 429 on most receipt calls;
- V0.1.2: public batch RPC returned no usable historical tx/receipt pairs;
- V0.1.3: explorer REST recovered the exact frozen sample and passed without changing any scientific gate.

### 3.3 Mechanism adjudication

Current state:
**SOURCE_REALIZED_FLOW_PASS / MECHANISM_ESTABLISHED / ECONOMIC_FREEZE_JUSTIFIED — NO EDGE CLAIM**

Official Compound semantics support the reconstructed chain:
- base token enters from the BuyCollateral caller;
- discounted collateral leaves Comet to an explicit recipient;
- BuyCollateral records the caller as buyer;
- Compound's public liquidation-bot implementation includes purchase plus possible external sale behavior.

Competing explanations remain alive:
- routing can be custody rather than sale;
- buyer can warehouse/hedge elsewhere;
- the event can be reactive;
- impact can complete before a post-block trade enters;
- source event size may be economically negligible.

### 3.4 Untouched 2025 predictor-only census

Canonical run:
- run 36347729253;
- artifact 10940993512;
- artifact digest sha256:16f11dda66e9ecba6305b3ad4c8b01ee1d4140989ac18c0420e7ccd21957924f;
- receipt pre-self SHA256 ca15407298f5814566ad07246afb99d7fd36e07da4385739e2d6c5b7733a28cc.

Status:
**PREDICTOR_SAMPLE_VIABLE**

Calendar 2025 source only:
- 1,573 BuyCollateral events;
- 1,470 unique transactions;
- 51 buyers;
- 10 assets;
- 35 ISO weeks;
- largest buyer: 418 events = 26.5734%.

All frozen source-viability gates passed.

No 2025 market price, return, PnL, funding, basis or post-event outcome was opened.

### 3.5 Protected economic Discovery freeze

Current state:
**FROZEN / READY-BUT-LOCKED**

Primary asset population frozen before outcomes:
- WETH -> ETHUSDT;
- LINK -> LINKUSDT;
- UNI -> UNIUSDT;
- COMP -> COMPUSDT.

Frozen hypothesis:
- short collateral / long BTC relative response;
- exact 30-minute horizon;
- first complete Binance Spot 1m bar strictly after the Ethereum block;
- BASE all-in research hurdle 20 bps;
- STRESS hurdle 30 bps;
- deterministic same-asset overlap suppression;
- ISO-week clustered bootstrap;
- no size/buyer/recipient threshold.

Frozen no-rescue rule:
no direction, horizon, asset, cost, benchmark, routing-subset or time-subperiod switch after outcomes.

**Protected 2025 market outcomes are still locked and require separate explicit authority.**

---

## 4. PENDLE-PT-MATURITY-CONVERGENCE-001

Current state:
**MECHANISM_DESCRIPTIVE / DISCOVERY_NOT_JUSTIFIED_AS_DEFINED / NOT NO_EDGE**

Raw PT convergence remains contract-mechanics evidence, not an alpha test.
No protected convergence outcome was opened.

---

## 5. PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001

Current state:
**SOURCE_COMPLETENESS_PASS / ECONOMIC_PROVENANCE_INCOMPLETE — DISCOVERY_BLOCKED_PRE_OUTCOME**

Preserved facts:
- 802 markets enumerated;
- 107 Ethereum markets expired pre-2025;
- 34 current-metadata points-free source candidates;
- 10/10 deterministic historical schema probes passed.

The frozen T-30 Discovery remains unexecuted because current empty points metadata does not prove historical absence/value of off-chain points.

No premium outcome opened.

---

## 6. LIDO-WITHDRAWAL-QUEUE-PRESSURE-001

Current state:
**SOURCE_PASS_PROSPECTIVE_ONLY**

Official Lido withdrawal API predictor snapshots are valid source-only observations.

No economic signal, threshold, direction, response asset, horizon or PnL has been defined.

The hourly GitHub schedule remains non-autonomous while the workflow exists only on the feature branch because scheduled workflows execute from the default branch.

---

## 7. Rejected novelty routes

- basic Morpho health-factor/liquidation port: duplicate-risk / insufficient causal novelty;
- generic Hyperliquid funding/carry: duplicate-dense generic carry surface.

---

## 8. Governance state

No:
- merge to main;
- live trading;
- orders;
- exchange mutation;
- wallet mutation;
- capital;
- paid data;
- post-outcome tuning;
- protected 2025 market outcome opening;
- fabricated promotion.

Source/data/provenance/technical/sample blockers remain distinct from NO_EDGE.

## 9. Exact next gate

For COMPOUND-REALIZED-DISPOSAL-FLOW-001 the next scientific action is now singular:

**OPEN AND EXECUTE THE EXACT FROZEN 2025 ECONOMIC DISCOVERY ONLY AFTER SEPARATE EXPLICIT PROTECTED-OUTCOME AUTHORITY.**

Until that authority exists:
**READY-BUT-LOCKED.**
