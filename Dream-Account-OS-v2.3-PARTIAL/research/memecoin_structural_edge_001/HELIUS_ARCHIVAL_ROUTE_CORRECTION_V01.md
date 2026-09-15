# MSEL-001 — HELIUS ARCHIVAL ROUTE CORRECTION V0.1

Status: FROZEN / SOURCE-GATE CORRECTION  
Date: 2026-09-15

## Discovery

The June 2025 pilot cannot rely on Helius `getTransfersByAddress` for transfer closure.

Current Helius documentation states:

- `getTransactionsForAddress` on Mainnet has unlimited retention and supports chronological sorting, time/slot/status filters, full transactions, transaction indexes and pagination.
- `getTransfersByAddress` currently retains only the most recent 1 year of transfer history.

The frozen pilot starts on `2025-06-13`, which is more than one year before the current lab date (`2026-09-15`). Therefore `getTransfersByAddress` is not an admissible primary source for this cohort.

## Corrected route

For June 2025:

1. Use archival `getTransactionsForAddress` for Pump program cohort discovery and Pump trade history.
2. For target-mint holder-transfer closure, reconstruct transfers from full historical transaction payloads involving relevant token accounts / mint-related addresses, using archival transaction history and raw Solana token-program instructions.
3. Where address-history coverage is insufficient, use standard archival Solana methods (`getSignaturesForAddress` + `getTransaction`, or `getBlock` for bounded slots) as a deterministic fallback.
4. Never interpret an empty `getTransfersByAddress` result for June 2025 as “no transfers.” That would be a retention artifact.

## Positive source property

Helius `getTransactionsForAddress` returns `transactionIndex`, providing a canonical intra-slot transaction position. This resolves the pre-registered ordering concern for multiple selected creates in the same slot, subject to normal source reconciliation.

## Gate consequence

`transfer_closure_pass` remains blocked until historical transfer reconstruction is proven against full archival transaction data. A convenient parsed endpoint with insufficient retention cannot be used to manufacture a pass.

This correction changes only the data-access route. It does not modify the frozen cohort, features, outcomes or quantitative MVE gate.
