# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.4.3 FIFTH-CHAIN SOURCE EXTENSION

Date: 2026-10-07
Parent freeze: 71ac365e709b0e0d7074caed7e842f513207aa85
Prior frozen candidates KAVA -> INJ -> SEI did not establish a fifth two-source historical chain.
Economic outcomes opened: NO.
V0.4.2 completion counts have not been inspected at the time of this amendment.

## Purpose

Extend the fifth-chain source-only qualification order without using event counts or market outcomes.

The next deterministic candidate order is frozen as:
5d. Akash / AKT
5e. Secret Network / SCRT
5f. Axelar / AXL

This order is based on prior Cosmos-family mechanism/source work and is fixed before inspecting V0.4.2 completion counts.

## Qualification rule

Use the first candidate in this order that proves all of:
- native production staking lifecycle comparable to Cosmos x/staking for the frozen 2023-2024 era;
- chain/version/fork semantics pinned for undelegation initiation, cancellation and completion;
- two independently operated public/free historical sources with bounded archive coverage in the frozen interval;
- canonical fixed-height reconciliation across the two sources;
- a viable census route satisfying the same completeness rules as the selected V0.4 method.

Do not skip a qualifying earlier candidate because a later chain has more events or easier market coverage.

If all three fail, the >=5-chain source gate remains blocked unless another source-only extension is frozen before any additional candidate event counts are inspected.

Materiality remains 10 bps of historical bonded stake. Hard sample bar remains >=40 material chain-days TOTAL across >=5 chains. No market outcomes may be opened.
