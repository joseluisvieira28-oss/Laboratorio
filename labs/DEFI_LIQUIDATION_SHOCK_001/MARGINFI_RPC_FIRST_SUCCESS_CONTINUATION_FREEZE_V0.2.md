# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI RPC FIRST-SUCCESS CONTINUATION FREEZE V0.2

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Parent:
- run: `35715833295`
- classification: `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`
- reason: `max_pages_reached_before_lower_boundary`
- pages: `5000`
- signatures: `5,000,000`
- oldest time: `2024-04-15T08:32:05Z`

Deterministic resume cursor:
- extraction run: `35732854347`
- classification: `MARGINFI_RPC_RESUME_CURSOR_EXTRACTED`
- page SHA256: `874d519e3de696acda80946ec65fb860f92f9bd9dc50b8c884324c33e893e332`
- signature: `2MmsSBLJBdT5mwjNyn5HDKZc5hHXogNP9vSg53CzmXynN95REnyr973Lo6ZWqrthfBjYVw7RyTPTzFsUbS9uYv25`
- slot: `260229711`
- time: `2024-04-15T08:32:05Z`

Scientific identity unchanged:
- program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
- class: `lending_account_liquidate`
- discriminator: `d6a997d5fba756db`
- lower boundary: `2023-02-07T15:47:04Z`
- transport: official public Solana RPC

Continuation:
- start strictly before the frozen resume signature;
- max 5000 additional pages × 1000 signatures;
- enforce unique signatures and non-increasing blockTime;
- on lower-boundary crossing, inspect successful RAW transactions oldest-to-newest;
- exact slot, meta.err == null, program ID and discriminator required;
- the frozen resume row is included as the exclusive upper boundary marker for continuity;
- first exact RAW match => `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_PASS`;
- page cap before crossing => `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`;
- lower boundary crossed with no match in this earliest slice => `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE`;
- structural mismatch => fail closed.

Firewall: prices=false; returns=false; pnl=false; direction=false; protected 2025/2026 market outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
