# DEFI-LIQUIDATION-SHOCK-001 — ON-CHAIN FIRST-SUCCESS BOUNDARY PLAN V0.1

Date: 2026-09-18  
Branch: `defi-liquidation-shock-v0.1`  
Posture: `SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED`

## Purpose

Pin the earliest successful on-chain liquidation candidate at or after each prospectively recovered source-code decoder boundary, without using market prices, returns, PnL, direction or profitability.

This closes historical applicability authority only. It does not establish an economic edge.

## Frozen class boundaries

### Save / Solend

Program:
`So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

- `LiquidateObligation` / `0c`
  - source-supported from: `2021-12-08T00:00:00Z`
- `LiquidateObligationAndRedeemReserveCollateral` / `11`
  - source-supported from: `2024-07-19T17:54:33Z`

### marginfi v2

Program:
`MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`

- `lending_account_liquidate` / `d6a997d5fba756db`
  - source-supported from: `2023-02-07T15:47:04Z`

### Kamino Lend

Program:
`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

- `liquidate_obligation_and_redeem_reserve_collateral`
- correct discriminator: `b1479abce2854a37`
- source-supported from: `2023-11-17T13:25:35Z`

The retired wrong value `b1479acce2854a37` is forbidden.

### Drift v2

Program:
`dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

All four core classes are source-supported from `2022-11-04T15:17:54Z`:

- `liquidate_perp` / `4b2377f7bf128b02`
- `liquidate_spot` / `6b00802923e5fb12`
- `liquidate_borrow_for_perp_pnl` / `a911205acf94d11b`
- `liquidate_perp_pnl_for_deposit` / `ed4bc6ebe9ba4b23`

Drift spot-with-swap classes introduced in 2025 remain excluded from the frozen 2021-2024 window.

## Search order — frozen

The first-success search is chronological from each program's earliest active source-supported boundary toward 2025-01-01.

Exact authoritative probe:
`source/BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_3.sql`

Maximum chunk:
**7 UTC days**, unchanged from the already frozen bounded-census plan.

For each protocol:
1. start at its earliest source-supported boundary;
2. run chunks in strictly ascending UTC order;
3. dry-run every chunk;
4. hard stop if estimated bytes >100 GB;
5. export each result unchanged;
6. apply transaction-success semantics exactly as frozen;
7. record earliest successful candidate per class;
8. once a class has a successful candidate, it may be removed from that class's pending-boundary set;
9. continue the protocol only while at least one historically applicable class remains unresolved.

No chunk may be skipped because it is inconvenient or contains many/few candidates.

## Within-chunk earliest-success refinement

If a 7-day chunk contains one or more successful candidates for an unresolved class:
- the earliest successful row in UTC order is the provisional first-success candidate;
- RAW archival verification is mandatory before the boundary is accepted;
- if RAW verification fails structural identity, fail closed and continue source reconciliation rather than silently taking the next row;
- if RAW verification succeeds, the exact transaction timestamp becomes the on-chain first-success boundary for that class.

A successful discriminator match is not enough without exact program/instruction location and RAW reconciliation where required.

## Kamino special remediation

Before starting the longer Kamino boundary walk, execute the already frozen corrected 2024-12-15 smoke V0.2.

That smoke test validates the corrected candidate path; it does not replace the chronological first-success search from 2023-11-17.

## Chunking is not tuning

Chunk boundaries are infrastructure only. They must never depend on market outcomes.

The deterministic generator:
`source/generate_first_success_probe_queue_v0_1.py`

creates the chronological program-level queue. The generated queue is not evidence until each row is actually executed and its unchanged result is adjudicated.

## Stop conditions

No SOURCE_DATA_PASS until:
- required first-success boundaries are pinned and reconciled;
- corrected Kamino path is validated;
- bounded census completeness is audited;
- realized successful event population is complete for authoritative intervals;
- required RAW class validation is complete;
- numerical sample gate is frozen;
- FINAL PRE-DISCOVERY AUTHORITY is written.

## Firewall

No prices. No returns. No PnL. No future-direction tests. No event-size threshold tuning. No protocol winner selection. No live trading. No orders. No wallets. No exchange mutation. No alerts/webhooks. No merge to main.
