# DIAMOND TEST V1 — RUNTIME SNAPSHOT — 2026-09-24T17:18:22Z

Canonical runtime: `crypto-edge-radar-v05-canary`  
Canonical branch: `crypto-edge-radar-postgres-v0.5`  
Deployed commit: `f449f587bcc0da48c451dbad0f65c8273c5d8463`  
Runtime health: `OK`  
Evidence chain: `verified 741 events via postgres` / `evidence_chain_ok=true`

This snapshot is descriptive and immutable evidence of what was known at the time. It does not alter any frozen gate.

## OPTIONS-SPOTPERP-001 / V2.1

State: `FORWARD_EVIDENCE_ACCUMULATING_TIER1_GATE_FROZEN`

- signal days observed: 5
- valid signal days: 5
- directional signal days: 5
- resolved forward trades: 4 / 50 final gate
- integrity: PASS
- BASE10 mean: **-106.1543555365 bps/trade**
- BASE10 PF: **0.3566417619**
- BASE total: **-424.6174221459 bps**
- current additive max drawdown: **-660.0015310034 bps**
- STRESS20 mean: **-116.0633444912 bps/trade**
- STRESS20 PF: **0.3172759813**
- current positive-trade concentration diagnostic: **84.2953%**
- 50-trade window locked: false
- operational 10-trade sample ready: false

Interpretation: the first four resolved forward observations are materially negative, but the prospectively frozen adjudication requires 50 resolved trades. No early fail, no early rescue and no parameter change are permitted.

## CED1D-0031 AVAX20

Runtime state: `WAITING_SOURCE_READINESS`

- first eligible signal day: 2026-09-22
- first eligible completion: 2026-09-23T00:00:00Z
- first eligible reference entry: 2026-09-23T00:01:00Z
- latest mature signal day: null
- retrospective backfill: false
- resolved mature prospective events visible at this snapshot: 0

Separate frozen 2025 cross-venue causal decomposition is already closed as:
`FOUR_OF_FOUR_CROSS_EXECUTION_SURVIVAL`, with 357/357 exact directional concordance between Binance and OKX signal sources.

Interpretation: mechanism/transport fingerprint is supportive, but the decisive 60-event / 8-week prospective gate has not started resolving yet.

## ETF-CME-INSTFLOW-001

Exact scheduler state: `WAITING_NEW_CFTC_AS_OF_AFTER_BOUNDARY`

- frozen boundary as-of date: 2026-09-15
- current as-of date: 2026-09-15
- preserved missed expected observation: 1
- missed state: `MISSED_EXPECTED_OBSERVATION_NO_CHASE`
- late chase: forbidden
- current signal direction for the missed key: LONG
- source status: OK
- scheduler latest error observed: `HTTPError: HTTP Error 500: Server Error`

Public execution preflight:
- classification: `PUBLIC_PREFLIGHT_ONLY`
- authenticated transport ready: false
- execution authority present: false
- account-specific fee verified: false
- same-book SHORT taker round-trip proxy: **16.0118273141 bps**
- historical break-even estimate: **21.2 bps**
- spot BTCUSDT public mapping: available
- live capital/orders/exchange mutation: false

Interpretation: scientific forward Diamond block is armed only for information-safe observations strictly after the 2026-09-24 Diamond freeze. The older missed observation remains immutable and cannot be backfilled.

## BNB-LAUNCHPOOL-DEMAND-001

- eligible prospective events visible: 0
- clusters: 0
- missed prospective observations: 0
- duplicate events/resolutions: 0
- status: OK
- public shadow only

Diamond V0.2 therefore remains waiting for its first genuinely prospective eligible Launchpool event.

## Governance

No line above authorizes:
- live trading;
- orders;
- exchange mutation;
- authenticated trading transport;
- wallets;
- leverage;
- capital deployment;
- main merge.

Early small-N observations are descriptive only. Frozen final gates remain authoritative.
