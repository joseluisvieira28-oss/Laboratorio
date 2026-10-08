# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — V24 Optimism 2025 source audit

Date: 2026-10-08 UTC
Mode: SOURCE-ONLY. Hypothesis NOT_TESTED. Economic outcomes 0. 2026 closed.

## Provenance

- Run: 37729211004
- Head: 4d1971a3c80012a80e707a1bb5c1bc9620875811
- Artifact: aave-gov-lt-optimism-2025-v24, ID 11529174128
- Artifact digest: sha256:fa4d09405064d4e175c39a221d0dc2b3c45873776b5c635d9fc605881df83855
- Public unauthenticated sources only.
- PoolConfigurator: 0x8145edddf43f50276641b55bd3ad95944510021e

## Coverage/integrity

- Stitch: audited V11 terminal block 130045411 -> V24 first block 130045412.
- Terminal block: 145813411
- Terminal timestamp: 1767225599 = 2025-12-31 23:59:59 UTC.
- Coverage complete: true.
- Accepted intervals: 158.
- Coverage gaps/overlaps: 0.
- Configurator events: 5.
- Referenced raw response bodies missing: 0.
- Decompressed SHA-256 mismatches: 0.
- Rejected/error responses were preserved in the request ledger and never accepted as absence.

## 2025 mechanism-relevant change

Transaction 0xf6a812025a70721cbc242cb1035da066344e20daa5ba1ba6ead2a3c060360cba at block 132703208:
- Stablecoin eMode category 1 liquidation threshold: 9300 -> 8700.
- eMode LTV: 9000 -> 1.
- sUSD base liquidation threshold remains 7000 in the same effect tx.
- Canonical Seatbelt payload: Optimism payload 67.
- Canonical Governance V3 proposal: Proposal 256, "sUSD Risk Parameter Adjustment".
- Proposal queue: 2025-03-02 12:31:35 UTC.
- L2 payload queue: 2025-03-02 12:33:05 UTC.
- Effect: 2025-03-03 12:33:13 UTC, block 132703208.

This is an additional independent provisional governance shock in the complete universe. It is not used to replace or rescue any member of the V26 pre-borrower fixed 12-shock set.

The other 2025 configurator events do not add a sequential LT decrease: two are upgrades; the sUSD base LT is unchanged at 7000 in the Proposal 256 tx; the December DAI configuration is not below its previously observed LT.

Source gate remains pending until full borrower-state reconstruction and all remaining universe audits are complete.
