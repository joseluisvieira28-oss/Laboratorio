# DEFI-LIQUIDATION-SHOCK-001 — SAVE 0x0c RPC FIRST-SUCCESS CONTINUATION FREEZE V0.2

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Parent:
- run: `35716197055`
- classification: `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`
- reason: `max_pages_reached_before_lower_boundary`
- pages: `5000`
- signatures: `5,000,000`
- oldest time: `2023-12-10T21:21:20Z`

Deterministic resume cursor:
- extraction run: `35732854347`
- classification: `SAVE0C_RPC_RESUME_CURSOR_EXTRACTED`
- page SHA256: `00ea8f13874c2520622d0991c9ae7179456a6278d4463be44ba08a1109e1f056`
- signature: `44b86ujEfT2EvYnXSV47pct5wv2dJQD3T8KkVePPaPcNPx9zRpkPxmorPjLn64FUovmnYSL1mU4qguV9ykZazB9P`
- slot: `235155834`
- time: `2023-12-10T21:21:20Z`
- cursor tx status: failed (retained only as pagination boundary, never counted as realized event)

Scientific identity unchanged:
- program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- class: `LiquidateObligation`
- native tag: `0x0c`
- lower boundary: `2021-12-08T00:00:00Z`
- scientific window: `[2021-12-08T00:00:00Z, 2025-01-01T00:00:00Z)`
- transport: official public Solana RPC

Continuation:
- start strictly before the frozen resume signature;
- max 5000 additional pages × 1000 signatures;
- enforce unique signatures and non-increasing blockTime;
- on lower-boundary crossing, inspect successful RAW transactions oldest-to-newest;
- exact slot, meta.err == null, program ID and native tag required;
- include the frozen cursor row only for continuity; its failed status prevents realized-event counting;
- first exact RAW match => `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_PASS`;
- page cap before crossing => `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`;
- lower boundary crossed with no match in this earliest slice => `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE`;
- structural mismatch => fail closed.

Firewall: prices=false; returns=false; pnl=false; direction=false; protected 2025/2026 market outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
