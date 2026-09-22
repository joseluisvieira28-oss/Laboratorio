# DEFI-LIQUIDATION-SHOCK-001 — SAVE 0x0c RPC FIRST-SUCCESS FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
Class: `LiquidateObligation`
Native instruction tag: `0x0c`
Source-supported lower boundary: `2021-12-08T00:00:00Z`
Frozen scientific window end exclusive: `2025-01-01T00:00:00Z`

Exclusive post-window upper cursor:
- signature: `4og9qdwnR1hohhbSYuX45oCiYELdDW2rMWV1oPo2V9CLKEGVC6XVXqnaiJm9a7YV6QFwwK7YCj86A1pnME9d6c4c`
- slot: `311143068`
- time: `2025-01-01T07:01:53Z`
- authority: `SAVE0C_POST_WINDOW_UPPER_ANCHOR_RECEIPT_V0.1.json`

The 2025 anchor is cursor-only and MUST NOT be RAW-inspected or included as an eligible event. The walk begins strictly before it, so the event corpus remains inside the frozen 2021-2024 window.

Transport: official public Solana RPC only.
Walk: getSignaturesForAddress newest-to-oldest, 1000 rows/page, maximum 5000 pages per tranche.
Chronology: unique signatures; non-increasing blockTime; fail closed on anomaly.
After crossing the lower boundary: retain only rows in [2021-12-08T00:00:00Z, 2025-01-01T00:00:00Z), successful signatures only, sort oldest-to-newest, RAW getTransaction exact slot/meta.err/program/tag. First exact RAW `0c` match is the boundary.
If 5000 pages are insufficient, HISTORY_BLOCKED with deterministic resume cursor; continuation may change transport state only, never the scientific identity.

Firewall: prices=false; returns=false; pnl=false; direction=false; protected 2025/2026 outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
