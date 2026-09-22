# DEFI-LIQUIDATION-SHOCK-001 — KAMINO RPC FIRST-SUCCESS CONTINUATION FREEZE V0.1B

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Parent evidence

Parent crawl:
- run 35689367726
- classification: KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED
- reason: max_pages_reached_before_lower_boundary
- 5,000 pages / 5,000,000 signatures
- oldest observed time: 2024-04-16T15:14:44Z

Resume-cursor extraction:
- run 35702234721
- classification: KAMINO_RPC_RESUME_CURSOR_EXTRACTED
- parent page: signatures_page_5000.json
- page SHA256: 26a782c34ce39be0d9542a0bbe3fb16387636b5a070bf7b9ee7ae5aaa41a16d9
- before signature: 47XL1cg6q8WtXxgAhoQGhtRMRm7EnrTtHZUR4QarxxuvpXTxCQANAnrDku7mHukz7JYxSYAquSyWAnH4DKSDiAis
- slot: 260478524
- block time: 2024-04-16T15:14:44Z

## Scientific contract — unchanged

RPC endpoint: https://api.mainnet-beta.solana.com
Program: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
Instruction: liquidate_obligation_and_redeem_reserve_collateral
Discriminator: b1479abce2854a37
Source-supported lower boundary: 2023-11-17T13:25:35Z

## Continuation rule

1. Start strictly older than the frozen resume signature using getSignaturesForAddress(before=resume_signature).
2. Maximum 5,000 additional pages, 1,000 rows/page.
3. Enforce unique signatures and non-increasing blockTime.
4. Stop Phase A as soon as a returned row crosses below 2023-11-17T13:25:35Z.
5. If the lower boundary is crossed, retain only rows at/after the lower boundary, append the resume cursor as the exclusive upper boundary marker, sort by (blockTime, slot, signature), and inspect successful signatures oldest-to-newest with getTransaction.
6. A realized liquidation requires exact slot, meta.err == null, exact Kamino program ID and instruction data whose decoded bytes begin with b1479abce2854a37.
7. Stop on the first RAW-verified match. Because this scan begins at the source-supported lower boundary and advances chronologically, that match is the global first-success boundary.
8. Any missing RAW transaction before the first match, chronology violation, duplicate signature, content mismatch or RPC inconsistency fails closed.
9. If the lower boundary is crossed but no liquidation exists between the lower boundary and the 2024-04-16 resume cursor, classify the slice as NO_MATCH_IN_EARLIEST_SLICE and continue later with the preserved parent 2024-04-16→2024-12-15 corpus. This is not NO_EDGE and not a source anomaly.

## Routing

- earliest RAW match found: KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_PASS
- another 5,000 pages without lower-boundary crossing: KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED
- lower boundary crossed, no match in earliest slice: KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE
- structural inconsistency: KAMINO_FIRST_SUCCESS_BOUNDARY_SOURCE_ANOMALY_FAIL_CLOSED

## Firewall

prices=false; returns=false; pnl=false; direction=false; 2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; merge_main=false.
