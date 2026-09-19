# ETH-BLOCKSPACE-DEMAND-001 — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-19
Branch: `eth-blockspace-demand-v0.1`
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**

## 1. Purpose

Test only whether Ethereum mainnet block-header data can support a reproducible historical blockspace-demand research series without any protected-period access.

This authority does **not** authorize a return predictor, trading rule, market outcome, PnL, threshold, horizon or directional hypothesis.

## 2. Economic mechanism family

Primary family: **SUPPLY / FLOW — protocol blockspace demand**.

EIP-1559 defines a protocol base fee per gas that adjusts with block gas usage relative to target and is burned. Historical block headers expose the ingredients required to reconstruct blockspace usage and protocol base-fee burn without relying on a third-party fees/revenue aggregator.

Potential later information variables may include:
- gas utilization;
- base-fee level/change;
- base-fee burn = baseFeePerGas × gasUsed.

No transform or predictive use is authorized at this stage.

## 3. Anti-duplication

Drive and GitHub searches on 2026-09-19 found no canonical `ETH-BLOCKSPACE-DEMAND-001`, Ethereum base-fee burn, EIP-1559 burn-demand, or equivalent direct block-header lab.

Closest prior work:
- `PROTOCOL-DEMAND-001`: DefiLlama protocol fees/revenue family, blocked because public full-history payload could expose 2025/2026.
- BTC fee/settlement labs: Bitcoin-specific and historically closed.

Classification: **NEW SOURCE ARCHITECTURE / MATERIALLY DISTINCT MVE**.

## 4. Frozen source

Chain: Ethereum mainnet.

Canonical method:
- JSON-RPC `eth_chainId`;
- JSON-RPC `eth_getBlockByNumber` with `full_transactions=false`.

Frozen independent public endpoints:
1. `https://ethereum-rpc.publicnode.com`
2. `https://eth.drpc.org`
3. `https://1rpc.io/eth`

No authenticated provider credential is required or authorized.

## 5. Frozen deterministic source probes

Exactly four historical post-London blocks:

- 13,000,000
- 15,000,000
- 18,000,000
- 21,000,000

These blocks were selected administratively before reading economic field values and span the intended pre-2025 source era.

No `latest`, `safe`, `finalized`, timestamp-search, or unbounded endpoint is permitted.

## 6. Allowed fields

For each exact block the source gate may inspect only:
- block number;
- block hash;
- parent hash;
- timestamp;
- gasLimit;
- gasUsed;
- baseFeePerGas.

Transaction bodies, addresses, calldata, logs, receipts, market prices and balances are prohibited.

The probe may verify field presence, parseability, sign/range sanity and cross-provider equality. It must not persist or summarize an economic time series.

## 7. PASS rules

`SOURCE_SCHEMA_PASS` requires ALL:

1. all three providers report chain id `0x1`;
2. all four exact blocks are returned by at least two independent frozen providers;
3. every usable provider agrees exactly on block hash for each block;
4. required fields exist and are parseable on all accepted block responses;
5. `baseFeePerGas > 0`, `gasUsed > 0`, `gasLimit > 0`, and `gasUsed <= gasLimit`;
6. all returned timestamps are strictly before 2025-01-01T00:00:00Z;
7. no request uses a protected 2025/2026 block or dynamic/latest tag.

Otherwise:
- insufficient provider quorum → `SOURCE_ACQUISITION_TECHNICAL_FAILURE`;
- provider disagreement / protected-period breach / malformed identity → `PROVENANCE_FAILURE`;
- missing required block-header semantics → `SOURCE_SCHEMA_INSUFFICIENT`.

No source-stage result may be called NO_EDGE.

## 8. What PASS authorizes

Only preparation of a separate full historical Source/Data Gate that prospectively freezes:
- exact block/date aggregation cadence;
- exact source envelope ending no later than 2024-12-31;
- missing-block rules;
- daily aggregation formula;
- checksum/hash receipts.

No market outcome may be opened until a separate FINAL PRE-DISCOVERY protocol is frozen after full source-data pass.

## 9. Firewall

Forbidden:
- ETH/BTC market prices;
- returns;
- PnL;
- win rate / PF / drawdown;
- 2025 or 2026 source data;
- live trading;
- orders;
- wallets;
- exchange mutation;
- authenticated exchange endpoints;
- alerts/webhooks;
- merge to main;
- post-outcome tuning.

