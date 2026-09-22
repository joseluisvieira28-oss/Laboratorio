# DEFI-LIQUIDATION-SHOCK-001 — SAVE 0x11 RPC FIRST-SUCCESS FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
Class: `LiquidateObligationAndRedeemReserveCollateral`
Native instruction tag: `0x11`
Source-supported lower boundary: `2024-07-19T17:54:33Z`

Frozen upper cursor:
- signature: `5w2cjBXo88QVX3yaBqCrkmd9aHf8ms6MjMyqMXr7J996utdbNJ8pHdd7CeUhva9uFHQYz8fmEKDS89gfvw63aHiT`
- slot: `307731998`
- time: `2024-12-16T00:00:06Z`
- authority: `SAVE_MARGINFI_UPPER_ANCHOR_RECEIPT_V0.1.json`

Transport: official public Solana RPC only.
Walk: getSignaturesForAddress, newest-to-oldest, limit 1000, maximum 5000 pages per tranche.
Chronology: signatures unique; blockTime non-increasing; fail closed on violation.
After lower-boundary crossing: successful signatures only, sort oldest-to-newest; RAW getTransaction required; exact slot; meta.err == null; exact program ID; Base58 instruction bytes must start with `11`.
First exact RAW match is the first-success boundary.
If 5000 pages are insufficient, classify HISTORY_BLOCKED and resume only from the deterministic final cursor with identical scientific contract.

Firewall: prices=false; returns=false; pnl=false; direction=false; market outcomes=false; 2025/2026 protected outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
