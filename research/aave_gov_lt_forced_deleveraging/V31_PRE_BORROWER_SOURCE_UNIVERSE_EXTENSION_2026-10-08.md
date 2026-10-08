# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — V31 pre-borrower source-universe extension

Date: 2026-10-08 UTC
Status: SOURCE ONLY / PRE-BORROWER VALUES / HYPOTHESIS NOT TESTED / 2026 CLOSED

## Purpose

V26 froze a minimum clean set of 12 independent governance shocks before borrower values were opened.
The now-complete Optimism 2025 V24 census was already running before borrower reconstruction and has
returned one additional qualifying LT-decrease shock. This document records that shock before the
corrected V28/V29 borrower-state jobs execute. It is not selected from borrower behavior or any
economic outcome.

This is a source-universe extension, not the PRE-OUTCOME ANALYSIS FREEZE.

## V24 complete 2025 Optimism census

Canonical PoolConfigurator:
`0x8145edddf43f50276641b55bd3ad95944510021e`

V24 Actions run: `37730323297`
Artifact: `11529359263`
Actions artifact digest:
`sha256:8c4d25436e4c32bb4d4481c844450f7c4d11cecc5b04bc884d66c7cb1f9ca285`

Coverage:
- first 2025 block: `130045412`
- terminal block: `145813411`
- terminal timestamp: `1767225599`
- contiguous frontier: `145813411`
- coverage complete: `true`
- configuration/upgrade events: 5
- economic outcomes opened: 0

The five rows consist of two PoolConfigurator upgrades and three parameter events. The later
DAI base-collateral row retains LT 77% while setting LTV to zero and therefore is not a qualifying
LT decrease. The sUSD base-collateral row in the Proposal 256 execution retains LT 70% while
setting LTV 60% -> 0%, and is not independently qualifying under V01. The same transaction also
contains the qualifying eMode LT decrease below.

## Additional independent shock — Governance V3 Proposal 256

Pinned source:
- repository: `aave-dao/seatbelt-gov-v3`
- commit: `a6e52bca30dff5c396f8ad7b452a9890a1f0e68e`
- proposal report: `reports/proposals/256.md`
- Optimism payload report:
  `reports/payloads/10/0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4/67.md`

Proposal 256 title/context: sUSD Risk Parameter Adjustment.

First Core governance queue:
- timestamp: 2025-03-02 12:31:35 UTC
- tx: `0x1ddf8cbb221410d26e6bdf0b7fe7c77a3917be1bd74639af4fc1e06e32b69e7a`

Optimism payload:
- payload id: 67
- created: 2025-02-26 11:50:35 UTC
- queued: 2025-03-02 12:33:05 UTC
- effect: 2025-03-03 12:33:13 UTC
- effect block: `132703208`
- effect tx: `0xf6a812025a70721cbc242cb1035da066344e20daa5ba1ba6ead2a3c060360cba`

Exact pinned payload state diff:
- Stablecoin eMode category 1 LTV: 90.00% -> 0.01%
- Stablecoin eMode category 1 LT: 93.00% -> 87.00%
- sUSD base LTV: 60.00% -> 0.00%
- sUSD base LT: unchanged at 70.00%

Exact emitted configuration evidence:
- `EModeCategoryAdded(categoryId: 1, ltv: 1, liquidationThreshold: 8700, liquidationBonus: 10100, ...)`
- `CollateralConfigurationChanged(sUSD, ltv: 0, liquidationThreshold: 7000, liquidationBonus: 10540)`
- `PayloadExecuted(payloadId: 67)`

Under V01, Proposal 256 qualifies because the pre-existing eMode collateral contribution to HF is
reduced by the LT change 9300 -> 8700. The sUSD LTV-only change is retained as context and is not
misclassified as forced deleveraging.

## Independence and frozen universe consequence

Proposal 256 is a distinct Core Governance V3 proposal and its effect is not part of any of the
12 proposal clusters frozen in V26. It therefore adds one independent source candidate.

Pre-borrower source universe after this audit:
- V26 fixed candidates: 12
- V31 additional candidate: Proposal 256
- total independent source candidates: 13

This does NOT mean SOURCE_GATE_PASS and does NOT authorize dropping a V26 shock after seeing
borrower/economic results. Every accepted final shock must independently satisfy V01 source
requirements. Proposal 256 is admitted now, before corrected borrower-state acquisition, so any
later use is source-driven rather than outcome-driven.

## Still closed

- borrower behavioral outcomes: unopened
- signal-to-effect behavioral values: unopened
- economic outcomes: 0
- Development runs: 0
- 2026 outcomes: closed
- trading/orders/wallets/private authenticated RPCs: forbidden
- main: unchanged

Next source step remains historical pre-signal exposure reconstruction for the frozen source
universe, followed by SOURCE_GATE_PASS only if at least 12 independent shocks are fully defensible.
Only then may a separate PRE-OUTCOME ANALYSIS FREEZE be committed.
