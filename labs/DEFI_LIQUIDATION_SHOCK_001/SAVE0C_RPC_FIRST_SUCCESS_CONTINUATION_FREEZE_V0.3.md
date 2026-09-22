# DEFI-LIQUIDATION-SHOCK-001 — SAVE 0x0c RPC FIRST-SUCCESS CONTINUATION FREEZE V0.3

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Parent V0.2:
- run: `35754815474`
- classification: `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`
- reason: `max_pages_reached_before_lower_boundary`
- pages: `5000`
- signatures: `5,000,000`
- oldest time: `2023-02-04T05:28:20Z`

Deterministic V0.3 resume cursor:
- classification: `SAVE0C_RPC_RESUME_CURSOR_EXTRACTED`
- page SHA256: `f7a1d4d00698c8f51f92a4fafb99cdc3eb59ff298fdd49e2332dd94701c57864`
- signature: `4amYSo5KXHFHmqH8oFgjeBZhzb4PQFBHfhHH57rNf9MNYmKCxzf15gZVmYzMjMF2Ey9FS2k7PWdzenyr2B6mLQm3`
- slot: `175932243`
- time: `2023-02-04T05:28:20Z`
- cursor tx status: failed with InstructionError; cursor-only, never a realized event

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
- unique signatures and non-increasing blockTime mandatory;
- on crossing the lower boundary, inspect successful RAW transactions oldest-to-newest;
- exact slot, meta.err == null, program ID and native tag required;
- frozen cursor is continuity metadata only and is never counted as realized event;
- first exact RAW match => `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_PASS`;
- page cap before crossing => `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED`;
- lower boundary crossed with no match in earliest slice => `SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE`;
- any structural inconsistency => fail closed.

Firewall: prices=false; returns=false; pnl=false; direction=false; protected 2025/2026 market outcomes=false; live trading=false; orders=false; wallets=false; exchange mutation=false; paid source=false; merge main=false.
