# DEFI-LIQUIDATION-SHOCK-001 — SQD EVENT CENSUS EXECUTOR IMPLEMENTATION FREEZE V0.4.2

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Prerequisites satisfied:
- Kamino boundary control PASS inside V0.3 calibration;
- Save11 inner-CPI calibration V0.3.1 PASS;
- timestamp/slot resolver V0.4.2 PASS;
- V0.4 execution population and semantics unchanged;
- V0.4.1 authority addendum active.

Implementation invariants:
- exactly one UTC calendar day per source chunk;
- first day starts at the authoritative first-success slot;
- final cutoff is first finalized block at/after 2025-01-01T00:00:00Z;
- Kamino server filter = exact program + d8 discriminator;
- Save11 server filter = exact program only, followed by local base58 first-byte == 0x11;
- requested fields remain only block number/time, transaction index/signatures/err and instruction identity/path/commit/error;
- no accounts, balances, amounts, token balances, fees, prices, returns, PnL or direction;
- each day writes a durable receipt and exact-match ledger fragment;
- completed chunks may be reused only if their persisted ledger SHA256 matches the receipt;
- blocked/anomalous chunks stop that protocol fail-closed;
- global manifest is sorted chronologically and cannot pass with a missing day;
- successful instruction dedup key: protocol + signature + instructionAddress;
- RAW queue dedup key: protocol + signature;
- deterministic RAW sample rule is exactly the one frozen in V0.4.

The executor may resume transport work after interruption. Resume is not scientific tuning because source population and event identity remain unchanged.
