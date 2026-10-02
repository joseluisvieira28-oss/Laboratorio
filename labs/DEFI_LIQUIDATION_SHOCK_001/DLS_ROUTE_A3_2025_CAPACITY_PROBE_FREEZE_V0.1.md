# DLS ROUTE A3 — 2025 CAPACITY PROBE FREEZE V0.1

Date: 2026-10-02
Status: SOURCE-ONLY / OUTCOME-BLIND / NO PURCHASE

Prerequisite:
- ROUTE_A3_GTFA_EQUIVALENCE_PASS run 36969189081 / artifact 11210144684.

Purpose:
Measure bounded gTFA program-history volume before any full 2025 acquisition.

Authorized probes, signatures-only:
1. marginfi program, 2025-01-01 <= blockTime < 2025-02-01
2. Solend/Save program, same interval
3. Kamino program, 2025-05-01 <= blockTime < 2025-06-01

Request:
- getTransactionsForAddress
- transactionDetails=signatures
- sortOrder=asc
- limit=1000
- status=succeeded
- exact blockTime filter
- deterministic paginationToken until exhaustion
- hard ceiling: 25 pages per probe

No full transaction bodies.
No discriminator filtering.
No market prices/returns/PnL.
No 2026 data.
No purchase/upgrade.
No trading authority.

Classification:
- ROUTE_A3_CAPACITY_PASS if all three probes terminate <=25 pages.
- ROUTE_A3_CAPACITY_BLOCKED if any probe reaches ceiling or provider rejects capability.

PASS is transport feasibility only.
