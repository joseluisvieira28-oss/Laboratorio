# AAVE-LIQUIDATION-OVERHANG-001 — 2024 REPLICATION EXECUTION AUTHORITY V0.1

Status: **FROZEN BEFORE 2024 PREDICTOR OR OUTCOME OPENING / FAIL-CLOSED**
Date: **2026-09-19**

## Activation

The prospectively frozen Final Pre-Discovery Protocol V0.1 defined:
- Discovery: 2023-02-01..2023-12-31;
- Replication: 2024-01-01..2024-12-31;
- 2024 must remain unopened until the complete 2023 Discovery receipt is persisted.

That condition is now satisfied.

Canonical 2023 Discovery:
- run: `35436923688`
- canonical artifact: `AAVE_DISCOVERY_2023_CANONICAL_V0_1_CONTINUATION`
- artifact ID: `10582547257`
- artifact digest: `sha256:9c80c3b64f540eee2a2e1f02b3b64867b584872195456afcc3a6214972fe5860`
- classification: `DISCOVERY_MECHANISM_PASS`
- snapshots: 334
- overhang-positive days: 334
- positive-outcome days: 145
- Spearman rho: 0.2580235336860782
- stationary-bootstrap one-sided 95% lower bound: 0.1394215970156347
- largest-outcome-day removed rho: 0.2640034879723874
- market edge proven: false
- next authorized phase: `2024_REPLICATION_PROTOCOL_EXECUTION`

An independent recovery path produced the same predictor digest and exact same canonical scientific receipt, providing deterministic implementation agreement.

## Exact replication

Open exactly the already-frozen replication partition:
- snapshots: 2024-01-01 through 2024-12-31 inclusive;
- one snapshot at first canonical Ethereum block >= 00:00:00 UTC;
- same exact 37-reserve canonical master with point-in-time eligibility;
- same borrower reconstruction semantics;
- same Aave oracle semantics;
- same eMode semantics;
- same baseline HF;
- same primary 10% collateral haircut;
- same primary predictor `OVERHANG_DEBT_10`;
- same next-24h Aave liquidation debt-notional outcome;
- same Spearman statistic;
- same stationary bootstrap, mean block length 7, 10,000 resamples, seed 20260918;
- same largest-outcome-day removal sensitivity;
- same eligibility gates and same pass gates.

No parameter, sign, shock, threshold, clock, horizon, reserve, borrower, outcome or statistic may change.

## Source/outcome firewall

The complete 2024 predictor MUST be persisted and cryptographically bound before any 2024 LiquidationCall outcome is opened.

No 2025/2026 data may be opened.

## Replication classification

If frozen eligibility fails:
`REPLICATION_INSUFFICIENT_SAMPLE`.

If eligible but any frozen signal gate fails:
`REPLICATION_NO_SIGNAL`.

If every frozen signal gate passes:
`REPLICATION_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE`.

Even a replication pass proves only the protocol forced-flow mechanism. It does not prove an executable market edge and does not authorize trading.

## Safety

Forbidden:
- market-return opening in this replication;
- trading PnL;
- live trading;
- orders;
- wallets;
- exchange mutation;
- alerts/webhooks;
- main merge;
- 2025/2026 access;
- post-result tuning or rescue.
