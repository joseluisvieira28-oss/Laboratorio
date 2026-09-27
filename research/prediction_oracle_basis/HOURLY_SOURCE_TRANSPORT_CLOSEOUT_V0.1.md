# PREDICTION-ORACLE-BASIS-001 — HOURLY SOURCE/TRANSPORT CLOSEOUT V0.1

Date: 2026-09-27
Branch: prediction-oracle-basis-v0.1
Draft PR: #143
Status: SOURCE_FEASIBILITY_PARTIAL_PASS / HOURLY_SOURCE_TRANSPORT_PASS / BRTI_REFERENCE_ACCESS_BLOCKED
Scientific verdict: NONE — NO ECONOMIC EDGE TEST AUTHORIZED

## 1. Scope

This closeout covers the hourly fixed-strike child of PREDICTION-ORACLE-BASIS-001 only.

Mechanism under source investigation:
same BTC underlying + same nominal strike + same resolution instant, with:
- Polymarket settlement from Binance BTC/USDT 1h candle close;
- Kalshi KXBTCD settlement from CF Benchmarks BRTI;
- explicit one-cent boundary difference preserved in classification.

The child is intentionally not labeled EXACT_EXCEPT_ORACLE because the Kalshi encoded threshold is one cent below the displayed nominal strike.

## 2. Hourly source-shape gate — PASS

Canonical run:
- workflow: POB Hourly Explicit Strike Source Probe
- run: 36339166888
- job: 108675728946
- artifact: 10938710472
- artifact ZIP SHA256: a127636dfaf8c4662e754312f6933dbf2673752dbaf066496577ea69c600d0d0

Result:
- classification: SOURCE_SHAPE_PASS_MATCHED_HOURLY_STRIKE_TIME
- Kalshi future candidates: 268
- unique future resolution times: 2
- Polymarket hourly candidates: 20
- matched same-time + same-nominal-strike pairs: 20
- matched pairs with public book routes: 20
- matured outcomes read: false
- economic outputs computed: false
- future-nearest joins: 0
- silent imputations: 0

## 3. First synchronized capture — transport failure only

Authority:
POB_HOURLY_SYNC_CAPTURE_AUTHORITY_V0.1.md

First run:
- run: 36341635466
- job: 108682746747
- artifact: 10938609609
- artifact ZIP SHA256: adecf6ac15edb6c23ba4d65f161da79ed8ad97abda83c8589bc9e588436ae0d9

Frozen schedule:
- 3 deterministic pairs: earliest future resolution, minimum / median_floor / maximum nominal strike
- 10 bundles
- 15 seconds between bundle starts
- max allowed bundle span: 3000 ms

Observed:
- prediction-market public books were readable;
- bundle latency itself was low;
- Binance api.binance.com bookTicker returned HTTP 451 from the GitHub hosted runner;
- complete bundles: 0/10;
- max bundle span: 291 ms;
- scientific firewall: PASS.

Adjudication:
SOURCE_TRANSPORT_BLOCKED due to provider-host geography, not scientific/economic failure.

## 4. Frozen transport remediation

Authority:
POB_HOURLY_SYNC_TRANSPORT_REMEDIATION_V0.1.md

Only authorized change:
- FROM https://api.binance.com/api/v3/ticker/bookTicker
- TO https://data-api.binance.vision/api/v3/ticker/bookTicker

Path, query, symbol, sample selection, schedule and gates remained unchanged.

Transport remediation commit:
53699cfea98d4cb0a39ab0707c063b58434ad337

## 5. Synchronized capture rerun — PASS

Canonical rerun:
- workflow: POB Hourly Synchronized Capture V0.1
- run: 36341997042
- job: 108683771628
- artifact: 10938928863
- artifact digest: sha256:1d7942c0510a243d4ad9929c3f7a97d5fa818b296ef8f7b408369833babf7543

Result:
- sync_capture_pass: true
- complete bundles: 10/10
- required bundles: 10
- max bundle span observed: 616 ms
- max bundle span allowed: 3000 ms
- authenticated trading endpoints: false
- orders: false
- matured outcomes read: false
- economic outputs computed: false
- future-nearest joins: 0
- silent imputations: 0

Adjudication emitted by frozen code:
SOURCE_TRANSPORT_READY_BRTI_ROUTE_UNRESOLVED

This proves the public cross-venue book/reference-transport geometry is operationally capturable under the frozen source rules. It does NOT prove an edge.

## 6. Public Kalshi event live-data probe

Authority:
POB_HOURLY_KALSHI_LIVE_DATA_AUTHORITY_V0.1.md

Canonical run:
- workflow: POB Kalshi Event Live Data Source Probe
- run: 36342299593
- job: 108684623538
- artifact: 10939431189
- artifact ZIP SHA256: 62dd9c8074aeabf7a1ed7f175547871650712f8e194ed4651bb8c0ba021488e2

Target:
- event: KXBTCD-26SEP2715
- deterministic earliest future KXBTCD event at probe start

Public response:
- machine-readable: yes
- type: crypto
- BTC label: present
- 1M candlesticks: 181
- 15M candlesticks: 12
- timeseries points: 10801
- explicit BRTI label: absent
- explicit CF Benchmarks label: absent
- numerical reference values persisted: false

Adjudication:
KALSHI_EVENT_LIVE_DATA_PUBLIC_REFERENCE_UNPROVEN

The public endpoint is useful and dense, but source identity may not be upgraded by inference.

## 7. Remaining source blocker

First-party documentation establishes:
- Kalshi exposes a CF Benchmarks REST passthrough using existing Kalshi API credentials;
- Kalshi exposes authenticated WebSocket channel cfbenchmarks_value for BRTI and related indices;
- CF Benchmarks' direct REST values endpoints use HTTP Basic authentication.

No legitimate Kalshi API credentials or CF Benchmarks entitlement are present in the current connected research tooling, and no credential guessing or paid access is authorized.

Therefore the causal BRTI reference feed remains:
BRTI_REFERENCE_ACCESS_BLOCKED

This is a source-access state, not NO_EDGE.

## 8. Final source-state

Parent family:
PREDICTION-ORACLE-BASIS-001

Hourly child:
POB-HOURLY-STRIKE-BINANCE-CFRTI-001

Current state:
- source population: PASS
- exact time + nominal strike geometry: PASS
- public prediction-market books: PASS
- synchronized public transport: PASS
- source latency gate: PASS
- BRTI settlement provenance: PASS at rule level
- anonymous/public BRTI causal machine feed: NOT PROVEN
- public Kalshi crypto live-data: AVAILABLE but BRTI identity UNPROVEN
- authenticated BRTI route: DOCUMENTED but CREDENTIAL/ACCESS BLOCKED
- economic outcomes: UNOPENED
- PnL / expected value / arbitrage economics: UNCOMPUTED
- scientific edge verdict: NONE

## 9. Next legitimate action

Only one source action can materially advance this exact child:
obtain/use a legitimate READ-ONLY Kalshi API credential or CF Benchmarks entitlement and prove point-in-time BRTI acquisition under a separately frozen source-access authority.

If that source gate passes, then and only then freeze a new economic protocol covering:
- exact oracle-state mapping;
- 1-cent boundary treatment;
- synchronized executable book prices/sizes;
- per-market fees;
- one-leg execution stress;
- capacity;
- timestamp-shift placebo;
- untouched prospective sample;
- inference and Diamond Test gates.

No economic test is authorized by this closeout.

## 10. Governance

- no live trading
- no authenticated trading endpoint used
- no orders
- no capital
- no exchange mutation
- no main merge
- no matured outcomes
- no post-outcome tuning
- no scientific promotion

Conclusion:
The mine is operationally real and materially distinct, but the exact causal BRTI feed is still access-blocked. Preserve as SOURCE_FEASIBILITY_PARTIAL_PASS, not as an edge and not as NO_EDGE.
