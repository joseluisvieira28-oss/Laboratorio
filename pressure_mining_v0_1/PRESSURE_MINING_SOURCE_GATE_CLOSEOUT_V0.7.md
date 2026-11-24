# CRYPTO LAB — PRESSURE MINING CLOSEOUT V0.7

Date: 2026-09-28
Branch: pressure-mining-program-v0.1
Status: COMPOUND REALIZED-DISPOSAL 30M DISCOVERY TERMINAL / NO PROMOTION

This V0.7 supersedes V0.6 routing for COMPOUND-REALIZED-DISPOSAL-FLOW-001 while preserving every earlier source, preflight, authority and technical receipt.

## 1. COMPOUND-REALIZED-DISPOSAL-FLOW-001 — FINAL SCIENTIFIC STATE

**DISCOVERY_FAIL_NO_PROMOTION — EXACT CANONICAL 30M CHILD CLOSED / NO RESCUE**

The mechanism/source layer remains valid:
- MATERIALLY_NEW_MECHANISM_PASS / ZERO INHERITED CREDIT;
- SOURCE_REALIZED_FLOW_PASS;
- DEX_ROUTE_EVIDENCE_STRONG;
- DIRECT_DEX_LINK_STRONG;
- 2025 PREDICTOR_SAMPLE_VIABLE.

Those source/mechanism facts did not translate into a frozen 30-minute economic edge.

## 2. DIRECT DEX LINK V0.2

Canonical source-only direct-link run:
- GitHub Actions run: 36393332840
- artifact: 10957361068
- artifact ZIP digest: sha256:2e533bf84bdb38d2b88a15b54b7f99e554853110cb2b537b836b2a6af8d3f6d4
- receipt pre-self SHA256: 3131e9964164ea66cb07e3f1068324c6b0f3a18534ef259d65bdbf29917a5f91
- status: DIRECT_DEX_LINK_STRONG

Frozen 64-transaction sample:
- 68 BuyCollateral events with reconstructed recipients;
- 59 events had same-transaction onward transfer of the sold collateral;
- 59/59 onward-transfer events had recognized DEX swap evidence after BuyCollateral;
- 57/59 onward-transfer events had a direct collateral Transfer to the same address that emitted a recognized DEX swap event;
- direct-link share: 96.6102%.

Interpretation:
Compound realized disposal frequently routes directly into recognized DEX swap infrastructure in the sampled historical receipts.
This establishes a strong source/mechanism path, not an economic edge or guaranteed net directional sell.

## 3. PROTECTED 2025 AUTHORITY

Operator authority was explicitly granted and preserved in:
pressure_mining_v0_1/COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_OPERATOR_AUTHORITY_RECEIPT_V0.1.md

Authority receipt commit:
b539ddffafea80a115a67d0eebf87b523ddb0e38

The exact protected authority marker was subsequently created without changing the canonical freeze:
.github/authorities/compound-realized-disposal-flow-001-2025.authorized

Trigger commit:
58ed11f626c76317e0805d99dce2f93b7e40ffe7

## 4. CANONICAL PROTECTED 2025 DISCOVERY

Canonical frozen authority remained unchanged:
- freeze commit: 2191bbf741ced5f801d8ae4034bd126c3b91cbc8
- freeze Git blob: d36c24bffd8a0f16787e0b7cf72b2d7b60e2f430
- WETH/ETHUSDT, LINK/LINKUSDT, UNI/UNIUSDT, COMP/COMPUSDT
- short collateral / long BTC relative response
- exact 30-minute horizon
- BASE20 / STRESS30
- deterministic same-asset 30-minute overlap suppression
- ISO-week clustered bootstrap, 10,000 resamples, seed 20260927
- all original 12 PASS gates
- no post-outcome rescue.

Canonical protected run:
- GitHub Actions run: **36393478777**
- workflow conclusion: SUCCESS
- artifact: **10957865022**
- artifact ZIP digest: **sha256:58572307983a4264b32877762545c92854c57b9a6cf316f3657b12bcea30ffab**
- receipt pre-self SHA256: **eb5dd9e5b586c8b913872e21ca79dbe248c8b13210b729f795d398bc757d1600**

Scientific verdict:
**DISCOVERY_FAIL_NO_PROMOTION**

## 5. PRIMARY RESULT

Sample:
- N = 373
- unique ISO weeks = 35
- invalid exact-bar events = 0
- ETHUSDT 167
- LINKUSDT 93
- UNIUSDT 78
- COMPUSDT 35

Pooled economics:
- gross mean = **+9.8696407 bps/trade**
- gross median = **-1.1156339 bps**
- BASE20 net mean = **-10.1303593 bps/trade**
- BASE20 median = **-21.1156339 bps**
- BASE20 PF = **0.8511858**
- BASE20 win rate = **36.4611%**
- STRESS30 net mean = **-20.1303593 bps/trade**
- STRESS30 PF = **0.7303816**
- ISO-week bootstrap 95% CI for BASE20 mean = **[-26.6280270, +9.9269536] bps**

Concentration:
- largest positive event share = **19.8189%** — PASS under <=25% gate;
- largest positive ISO-week share = **44.0677%** — FAIL under <=35% gate.

## 6. ASSET DIAGNOSTICS — NO SUBSET RESCUE

COMPUSDT:
- N 35
- gross mean -216.4031 bps
- BASE20 mean -236.4031 bps
- BASE PF 0.18184

ETHUSDT:
- N 167
- gross mean +16.8289 bps
- BASE20 mean -3.1711 bps
- BASE PF 0.91488

LINKUSDT:
- N 93
- gross mean +47.6460 bps
- BASE20 mean +27.6460 bps
- BASE PF 1.52236

UNIUSDT:
- N 78
- gross mean +51.4612 bps
- BASE20 mean +31.4612 bps
- BASE PF 1.59349

Leave-one-asset-out BASE20 pooled means:
- remove COMP: +13.30025 bps
- remove ETH: -15.77209 bps
- remove LINK: -22.67752 bps
- remove UNI: -21.12746 bps

The favorable LINK/UNI diagnostics and positive remove-COMP diagnostic are not admissible rescue paths. Asset set was frozen before outcomes and every-asset positivity was an explicit PASS gate.

## 7. CALENDAR DIAGNOSTICS

2025-Q1:
- N 116
- BASE20 mean +12.6692 bps

2025-Q2:
- N 92
- BASE20 mean -0.5246 bps

2025-Q3:
- N 59
- BASE20 mean -40.1318 bps

2025-Q4:
- N 106
- BASE20 mean -26.7190 bps

Quarter selection is diagnostic only and cannot be used for rescue.

## 8. FROZEN GATE ADJUDICATION

PASS:
- N >= 100
- >=20 ISO weeks
- all four assets >=10 events
- largest positive event share <=25%

FAIL:
- pooled BASE20 net mean >0
- pooled BASE20 PF >1
- pooled STRESS30 net mean >0
- pooled STRESS30 PF >1
- cluster-bootstrap lower 95% >0
- every asset BASE20 mean >0
- every leave-one-asset-out pooled BASE20 mean >0
- largest positive ISO-week share <=35%

Eight of twelve frozen promotion gates failed.

## 9. TERMINAL DECISION

Close the exact 30-minute realized-disposal child.

Forbidden rescue:
- remove COMP;
- promote LINK-only or UNI-only;
- reverse direction;
- use 5m/15m/60m/4h/24h;
- reduce costs;
- change benchmark;
- introduce size/buyer/recipient/route filters;
- select Q1 or other favorable calendar regimes;
- post-hoc clustering or threshold changes.

The source mechanism remains informative:
**forced protocol disposal -> explicit recipient -> frequent DEX routing is real.**

But the frozen tradable claim is rejected:
**the post-confirmation 30-minute short-collateral / long-BTC continuation effect does not survive the frozen economics and robustness gates.**

Any future Compound experiment requires a materially new mechanism, new LAB_ID, prospective freeze and genuinely fresh evidence. It receives zero inherited edge credit from this failed child.

## 10. FIREWALL

protected_2025_market_outcomes_opened=true
protected_2026_market_outcomes_opened=false
live_trading=false
orders=false
exchange_mutation=false
wallet_mutation=false
capital=false
paid_data=false
main_merge=false
post_outcome_tuning=false
rescue=false

## 11. OTHER PRESSURE MINING TRACKS

COMPOUND-INVENTORY-PERSISTENCE-001:
DISCOVERY_FAIL_NO_SUPPORT / TERMINAL.

PENDLE-PT-MATURITY-CONVERGENCE-001:
MECHANISM_DESCRIPTIVE / CLOSED AS ALPHA QUESTION.

PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001:
SOURCE_COMPLETENESS_PASS / ECONOMIC_PROVENANCE_INCOMPLETE / DISCOVERY_BLOCKED_PRE_OUTCOME.

LIDO-WITHDRAWAL-QUEUE-PRESSURE-001:
SOURCE_PASS_PROSPECTIVE_ONLY.
