# DEFI-LIQUIDATION-SHOCK-001 — ARCHIVAL RPC CREDENTIAL READINESS PREFLIGHT V0.1

Date: 2026-09-19
Branch: `defi-liquidation-shock-v0.1`
Status: **FROZEN / ZERO-RPC / SOURCE-READINESS ONLY**

Purpose: determine whether the GitHub Actions runtime already contains an archival Solana RPC credential compatible with the existing frozen source collector, without making any network request or opening any scientific outcome.

Expected source secrets:
- `HELIUS_API_KEY`, or
- `DLS_RPC_URL`.

This preflight:
- must not call Helius, Solana RPC, BigQuery, exchanges, price APIs or any external source;
- must not print, hash, transform, persist or expose secret values;
- may test only empty/non-empty secret presence;
- does not modify the frozen protocol registry, 2021-2024 source window, decoder set or first-success queue;
- does not authorize candidate census, prices, returns, PnL, direction, 2025/2026, trading, wallets or exchange mutation;
- does not imply SOURCE_DATA_PASS.

Terminal states:
- `ARCHIVAL_RPC_CREDENTIAL_PRESENT`
- `ARCHIVAL_RPC_CREDENTIAL_ABSENT`

A PRESENT result only permits separately governed source-only acquisition under the existing collector/runbook. It is not an economic or scientific result.
