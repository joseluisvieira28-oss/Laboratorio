# DEFI-LIQUIDATION-SHOCK-001 — SAVE 0x0c EARLY-BOUNDARY SEARCH FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Scientific identity is unchanged:
- program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- instruction: `LiquidateObligation`
- native tag: `0x0c`
- lower source boundary: `2021-12-08T00:00:00Z`

## Reason for transport supersession

Backward enumeration from the end of the frozen window is scientifically valid but transport-inefficient. V0.1 + V0.2 already enumerated 10,000,000 signatures; V0.3 was operationally cancelled after further checkpointed work.

For the first-success boundary, an equivalent chronological method is to anchor shortly after the frozen source boundary and adjudicate the earliest interval first.

No source result has been viewed for the early windows below.

## Prospectively frozen expansion schedule

Upper target timestamps, in order:
1. `2021-12-15T00:00:00Z`
2. `2022-01-08T00:00:00Z`
3. `2022-03-08T00:00:00Z`
4. `2022-06-08T00:00:00Z`
5. `2022-12-08T00:00:00Z`
6. `2023-12-08T00:00:00Z`
7. `2025-01-01T00:00:00Z` exclusive scientific-window cap

Execution must begin with target 1 only. Advance in this exact order only if the complete earlier interval contains no RAW-verified successful `0x0c` liquidation.

## Anchor probe

For each target:
- official public Solana RPC only;
- find first produced block at/after target timestamp;
- scan forward only until one transaction references the frozen Save/Solend program;
- cursor-only; no liquidation assumption;
- persist signature, slot, blockTime, status and raw block-response SHA256.

## Boundary adjudication after anchor

- enumerate strictly backward from anchor to lower boundary;
- preserve failed attempts separately;
- successful transactions RAW-inspected oldest-to-newest;
- exact program + native tag `0x0c` required;
- first exact RAW successful match closes the boundary.

No economic outcome is opened.

Firewall: prices=false; returns=false; pnl=false; direction=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
