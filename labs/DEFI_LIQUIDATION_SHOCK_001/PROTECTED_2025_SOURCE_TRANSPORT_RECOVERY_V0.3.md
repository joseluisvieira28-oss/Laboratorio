# DEFI-LIQUIDATION-SHOCK-001 — PROTECTED 2025 SOURCE TRANSPORT RECOVERY V0.3

Date: 2026-09-30
Status: TRANSPORT/INFRASTRUCTURE ONLY — NO SCIENTIFIC CHANGE

## Live diagnosis
Canonical legacy run 36547754265, attempt 4, marginfi 2025Q1 spent approximately 2h11m in the collector and terminated with SQD HTTP 503 availability_error / retries_exhausted / transport_exhausted. The remaining quarterly collectors were cancelled and no partition receipt survived that attempt. The source-authority artifact remained BLOCKED.

## Structural transport defects
1. Large SQD range requests can be routed to workers without chunks for the requested range and exhaust retries.
2. The collector treated HTTP 204 or HTTP 200 with an empty NDJSON body as termination of the entire scientific partition. Under bounded/sparse transport this can discard later source data.
3. Concurrent pressure was unnecessarily high for a source already returning availability failures.

## Recovery
- Preserve the frozen 2025 interval, four protocols, program IDs, discriminators, fields, account-role rules, mint/unit resolution, success conditions and 60-second clustering.
- Bound each SQD transport request to at most 250,000 slots. The deterministic union of consecutive slot windows exactly reconstructs the original scientific interval.
- Treat 204/empty-200 as an empty bounded transport window and advance to the next contiguous slot window; do not terminate the scientific partition.
- Respect Retry-After when supplied and retain bounded retry/backoff for 429/5xx.
- Reduce workflow max-parallel from 4 to 2 and raise per-job operational timeout from 120 to 180 minutes.
- Retain monthly V0.2 partitioning already frozen by PROTECTED_2025_SOURCE_PARTITIONING_ADDENDUM_V0.2.md; the finalizer still requires all 48 monthly receipts and performs global duplicate checks and global clustering.

## Firewall
No 2025 prices/returns/PnL/funding/direction are opened by source collection. No 2026 data, post-outcome tuning, trading, orders, wallets, exchange mutation or merge to main.

TRANSPORT/INFRASTRUCTURE ONLY — NO SCIENTIFIC CHANGE.
