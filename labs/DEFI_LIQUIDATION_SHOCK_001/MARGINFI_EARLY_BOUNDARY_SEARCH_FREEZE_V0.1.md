# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI EARLY-BOUNDARY SEARCH FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Scientific identity is unchanged:
- program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
- instruction: `lending_account_liquidate`
- discriminator: `d6a997d5fba756db`
- lower source boundary: `2023-02-07T15:47:04Z`

## Reason for transport supersession

Backward enumeration from late 2024 is scientifically valid but transport-inefficient. V0.1 + V0.2 already enumerated 10,000,000 signatures, while V0.3 was operationally cancelled after additional checkpointed work.

For a first-success question, an equivalent and cheaper chronological route is to establish an upper program-activity cursor shortly after the frozen lower boundary and completely adjudicate that earliest interval first.

No source result has been viewed for the early windows below.

## Prospectively frozen expansion schedule

Upper target timestamps, in order:
1. `2023-02-14T00:00:00Z`
2. `2023-03-07T00:00:00Z`
3. `2023-05-08T00:00:00Z`
4. `2023-08-08T00:00:00Z`
5. `2024-02-07T00:00:00Z`
6. `2025-01-01T00:00:00Z` exclusive scientific-window cap

Execution must begin with target 1 only. If the complete interval from the lower boundary through target 1 contains no RAW-verified successful matching instruction, advance to target 2, preserving all prior evidence and without skipping/reordering windows. Repeat only as needed.

## Anchor probe

For each target:
- official public Solana RPC only;
- find first produced block at/after target timestamp;
- scan forward only until one transaction references the frozen marginfi program;
- that transaction is cursor-only and is not itself assumed to be a liquidation;
- persist signature, slot, blockTime, status, raw block-response SHA256.

## Boundary adjudication after anchor

- `getSignaturesForAddress` strictly backward from the cursor until the lower boundary is crossed;
- exact chronological completeness;
- failed transactions retained as attempts, never realized events;
- successful signatures RAW-inspected oldest-to-newest;
- exact program + discriminator required;
- first exact RAW successful match closes the boundary.

No economic outcome is opened.

Firewall: prices=false; returns=false; pnl=false; direction=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
