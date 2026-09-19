# ETH-BLOCKSPACE-DEMAND-001 — FULL SOURCE/DATA GATE V0.2A — SOURCE SEMANTICS + TRANSPORT AMENDMENT

Date: 2026-09-19
Status: **FROZEN PRE-RERUN / OUTCOME-BLIND**

Supersedes only the V0.2 source-transport/schema implementation where stated below. The scientific/source grid remains unchanged.

## Evidence forcing this amendment

V0.2 run 35445718239 exposed two source-stage failures before any market outcome was opened:

1. Some exact target blocks failed the implementation check `gasUsed > 0`.
2. Cross-provider audit requests encountered HTTP 429 transport throttling.

A dedicated source-only diagnostic run **35445913533** checked representative failed blocks 13,158,400; 13,756,000; and 20,941,600 on both qualified providers.

For all three blocks and both providers:
- exact block number matched;
- block hash agreed;
- gasLimit > 0;
- **gasUsed == 0**;
- gasUsed <= gasLimit;
- baseFeePerGas > 0;
- timestamp < 2025-01-01.

Therefore these are valid empty Ethereum blocks, not malformed source records.

No prices, returns or PnL were opened by the diagnostic.

## Exact schema correction

V0.2A header sanity becomes:

- `gasLimit > 0`
- **`gasUsed >= 0`**
- `gasUsed <= gasLimit`
- `baseFeePerGas > 0`

A valid `gasUsed == 0` block is retained with:
- `gas_utilization = 0`
- `sample_block_base_fee_burn_wei = 0`

This is a source-schema correction, not a threshold search or economic rescue.

## Exact transport hardening

Unchanged providers:
- DRPC
- Flashbots

Unchanged grid:
- 13,000,000 through 21,500,000
- stride 1,800
- 4,723 deterministic targets
- audit index mod 20 == 0
- 237 cross-provider audits

Transport-only changes:
- bounded RPC retries increased from 4 to 8;
- HTTP 429 honors Retry-After when present, otherwise deterministic exponential backoff;
- inter-request pacing added;
- workflow matrix max-parallel reduced from 4 to 2.

No provider, target, audit target, metric, aggregation rule, coverage threshold or safety boundary changes.

## Governance

V0.2 run 35445718239 is non-canonical source evidence and cannot adjudicate the mechanism.
V0.2A remains source/data only and outcome-blind.
2025/2026, market prices, returns, PnL, trading direction, costs, horizon, orders, wallets, exchange mutation, alerts/webhooks, Render and main remain closed.
