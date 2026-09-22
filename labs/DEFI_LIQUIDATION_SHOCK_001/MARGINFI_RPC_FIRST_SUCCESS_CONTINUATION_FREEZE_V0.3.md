# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI RPC FIRST-SUCCESS CONTINUATION FREEZE V0.3

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Parent V0.2:
- run: `35754821042`
- classification: `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`
- reason: `max_pages_reached_before_lower_boundary`
- pages: `5000`
- signatures: `5,000,000`
- oldest time: `2024-01-03T12:26:07Z`

Deterministic V0.3 resume cursor:
- classification: `MARGINFI_RPC_RESUME_CURSOR_EXTRACTED`
- page SHA256: `788fda0abb1dca2dec9db1cd81f39cf2b0a55f7f1960502590a2645576fada47`
- signature: `5stv5fkA5c4oXYfUaXx59oAENDfcvjr9zzZdLwNyevRK68wzZ5BGeKkj6bq8KmgjXUj68qX2NAsaD86aS8d1Cm73`
- slot: `239637875`
- time: `2024-01-03T12:26:07Z`
- cursor tx status: success

Scientific identity unchanged:
- program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
- class: `lending_account_liquidate`
- discriminator: `d6a997d5fba756db`
- lower boundary: `2023-02-07T15:47:04Z`
- transport: official public Solana RPC

Continuation:
- start strictly before the frozen resume signature;
- max 5000 additional pages × 1000 signatures;
- unique signatures and non-increasing blockTime mandatory;
- on crossing the lower boundary, inspect successful RAW transactions oldest-to-newest;
- exact slot, meta.err == null, program ID and discriminator required;
- include the frozen cursor only as the exclusive upper continuity marker;
- first exact RAW match => `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_PASS`;
- page cap before crossing => `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`;
- lower boundary crossed with no match in earliest slice => `MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE`;
- any structural inconsistency => fail closed.

Firewall: prices=false; returns=false; pnl=false; direction=false; protected 2025/2026 market outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
