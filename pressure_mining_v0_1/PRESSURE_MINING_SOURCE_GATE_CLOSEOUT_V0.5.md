# CRYPTO LAB — PRESSURE MINING SOURCE / PRE-OUTCOME CLOSEOUT V0.5

Date: 2026-09-28
Branch: pressure-mining-program-v0.1
Status: CANONICAL PRE-OUTCOME STATE / ONE PROTECTED DISCOVERY READY-BUT-LOCKED

V0.5 preserves all V0.4 evidence and resolves the temporary pre-outcome authority ambiguity discovered on 2026-09-28.

## 1. COMPOUND-INVENTORY-LIQUIDATION-001

Unchanged:
SOURCE_CENSUS_PASS / PARENT SOURCE-MECHANISM LINEAGE / NO STANDALONE EDGE CLAIM.

Historical source facts:
- 894 AbsorbCollateral;
- 999 BuyCollateral;
- 505 unique absorbed borrowers lower bound;
- 7 collateral assets.

## 2. COMPOUND-INVENTORY-PERSISTENCE-001

Unchanged:
DISCOVERY_FAIL_NO_SUPPORT — EXACT 24H CHILD TERMINAL / NO RESCUE.

The opened 2023-2024 24h result gives zero credit to successors.
No inversion, alternate horizon, threshold or asset-subset rescue.

## 3. COMPOUND-REALIZED-DISPOSAL-FLOW-001

### 3.1 Novelty

MATERIALLY_NEW_MECHANISM_PASS / ZERO INHERITED CREDIT.

The state variable is realized Compound BuyCollateral disposal plus recipient/routing path, not residual seized inventory.

### 3.2 Historical realized-flow source gate

Canonical run:
- 36347379578
- artifact 10940652459
- artifact digest sha256:69a44dc3c51f67e895fe0c29e2636a03064e7ab07a1820c6a1e4a06ca19b4a30
- receipt pre-self SHA256 e081b77cdeb6bef1a21fb1d6be2a5b4d5e9fb016fd2872eaf35eb823d6ccf707

Verdict:
SOURCE_REALIZED_FLOW_PASS.

2023-2024 source corpus:
- 999 BuyCollateral logs;
- 899 unique transactions;
- 47 buyers;
- 7 assets.

Frozen 64-transaction source sample:
- 64/64 transactions usable;
- 68 BuyCollateral events;
- 68/68 recipients reconstructed;
- 59/68 same-transaction onward collateral transfers.

### 3.3 DEX route evidence

Initial V0.1 and V0.1.1 route receipts are retained as technical evidence only.
V0.1 contained an invalid derived denominator.
V0.1.1 correctly failed an invariant after an implementation omission.

Canonical corrected route run:
- 36381340442
- artifact 10953181513
- artifact digest sha256:4f2b44df87ab93687115af4984131f2d2b5935577331f74e2148939d78496269
- receipt pre-self SHA256 d4c69da0e49687321ed7f498ca080aa9627b7161a7cae45eb7119d44c167e8bb

Verdict:
DEX_ROUTE_EVIDENCE_STRONG.

Corrected sample:
- 68 recipient-inferred events;
- 59 onward-transfer events;
- 64 events with >=1 recognized DEX swap event after BuyCollateral;
- 59/59 onward-transfer events also had recognized DEX swap evidence = 100%.

Boundary:
recognized DEX logs demonstrate exchange interaction, not guaranteed net collateral sale and not market edge.

### 3.4 Untouched 2025 predictor census

Canonical run:
- 36347729253
- artifact 10940993512
- artifact digest sha256:16f11dda66e9ecba6305b3ad4c8b01ee1d4140989ac18c0420e7ccd21957924f
- receipt pre-self SHA256 ca15407298f5814566ad07246afb99d7fd36e07da4385739e2d6c5b7733a28cc

Verdict:
PREDICTOR_SAMPLE_VIABLE.

2025 predictor-only corpus:
- 1,573 BuyCollateral events;
- 1,470 unique transactions;
- 51 buyers;
- 10 assets;
- 35 ISO weeks;
- top buyer share 26.5734%.

No protected market outcome was opened.

### 3.5 Economic authority reconciliation

The first protected economic freeze is canonical:

`COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1.md`

- commit 2191bbf741ced5f801d8ae4034bd126c3b91cbc8
- frozen 2026-09-27T20:25:02Z
- four primary assets: WETH/ETH, LINK, UNI, COMP
- BTC benchmark
- short collateral / long BTC
- exact 30-minute horizon
- deterministic same-asset 30m overlap suppression
- BASE 20 bps / STRESS 30 bps
- ISO-week cluster bootstrap
- full frozen economics/statistical/concentration gates.

A later 5-minute document created on 2026-09-28 was discovered during reconciliation.
Because no market outcome had been opened, there is no outcome contamination, but governance resolves the conflict conservatively:

**FIRST FREEZE WINS.**

The later 5-minute document is:
NON-CANONICAL PRE-OUTCOME DRAFT / DO NOT EXECUTE / ZERO SCIENTIFIC AUTHORITY.

Governance reconciliation:
`COMPOUND_REALIZED_DISPOSAL_FLOW_001_GOVERNANCE_RECONCILIATION_V0.1.md`.

### 3.6 Canonical 30m predictor readiness

Canonical source-only readiness run:
- 36382234645
- artifact 10952818650
- artifact digest sha256:68824f4f1ff67a98964f5f1301f34cdcdcc5e1982329ea6b0ff577ad5d3892ef
- receipt pre-self SHA256 c1d6f87a76476140f5216255a97215ac35870fbf0764898845132aecf91350de

Verdict:
CANONICAL_30M_PREDICTOR_READY.

Exact frozen event-construction counts:
- 1,157 eligible raw logs in WETH/LINK/UNI/COMP;
- 1,148 transaction+asset aggregated events;
- 373 kept events after deterministic same-asset 30m overlap suppression;
- 775 overlap events suppressed;
- 35 unique ISO weeks.

Kept events by proxy:
- ETHUSDT 167
- LINKUSDT 93
- UNIUSDT 78
- COMPUSDT 35

Therefore all frozen sample gates pass pre-outcome:
- N >= 100: PASS
- >=20 ISO weeks: PASS
- all four assets >=10 events: PASS

These are predictor/source counts only.

### 3.7 Current exact state

**DISCOVERY_READY-BUT-LOCKED / PROTECTED 2025 MARKET OUTCOMES UNOPENED.**

No BTCUSDT, ETHUSDT, LINKUSDT, UNIUSDT or COMPUSDT 2025 price value has been joined to the events.
No relative return, net return, PF, bootstrap performance statistic or PnL has been computed.

The next scientific action is singular:

**execute the exact frozen 30-minute protected 2025 Economic Discovery only after separate explicit protected-outcome authority naming COMPOUND-REALIZED-DISPOSAL-FLOW-001 / its protected 2025 economic test.**

Generic continuation permission does not release this gate.

If the exact 30m Discovery fails, its no-rescue firewall applies.
If it passes, it is Discovery evidence only and still requires genuinely independent evidence plus execution/capacity validation.

## 4. PENDLE-PT-MATURITY-CONVERGENCE-001

Unchanged:
MECHANISM_DESCRIPTIVE / DISCOVERY_NOT_JUSTIFIED_AS_DEFINED / NOT NO_EDGE.

## 5. PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001

Unchanged:
SOURCE_COMPLETENESS_PASS / ECONOMIC_PROVENANCE_INCOMPLETE / DISCOVERY_BLOCKED_PRE_OUTCOME.

No premium outcome opened.

## 6. LIDO-WITHDRAWAL-QUEUE-PRESSURE-001

Unchanged:
SOURCE_PASS_PROSPECTIVE_ONLY.

No threshold, direction, horizon or market outcome opened.

## Governance

No:
- merge to main;
- live trading;
- orders;
- exchange or wallet mutation;
- capital;
- paid data;
- protected 2025 market outcome opening;
- protected 2026 outcome opening;
- post-outcome tuning;
- fabricated promotion.
