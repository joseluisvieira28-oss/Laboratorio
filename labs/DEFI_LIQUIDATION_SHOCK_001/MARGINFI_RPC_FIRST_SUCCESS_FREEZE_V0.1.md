# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI RPC FIRST-SUCCESS FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
Class: `lending_account_liquidate`
Anchor discriminator: `d6a997d5fba756db`
Source-supported lower boundary: `2023-02-07T15:47:04Z`

Frozen upper cursor:
- signature: `4uLD92ZZK1yecPQ7C6oKLtgrBD2QiPM4h9HCcgrxQKsw6dTsDZ9LkCucuusAAH27J1PhB1sAXpeTUqXRjdCdJcFe`
- slot: `307732019`
- time: `2024-12-16T00:00:16Z`
- authority: `SAVE_MARGINFI_UPPER_ANCHOR_RECEIPT_V0.1.json`

Transport: official public Solana RPC only.
Walk: getSignaturesForAddress, newest-to-oldest, limit 1000, maximum 5000 pages per tranche.
Chronology: signatures unique; blockTime non-increasing; fail closed on violation.
After lower-boundary crossing: successful signatures only, sort oldest-to-newest; RAW getTransaction required; exact slot; meta.err == null; exact program ID; Base58 instruction bytes must start with `d6a997d5fba756db`.
First exact RAW match is the first-success boundary.
If 5000 pages are insufficient, classify HISTORY_BLOCKED and resume only from the deterministic final cursor with identical scientific contract.

Firewall: prices=false; returns=false; pnl=false; direction=false; market outcomes=false; 2025/2026 protected outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
