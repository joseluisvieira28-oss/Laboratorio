# ETH-BLOCKSPACE-DEMAND-001 — SOURCE TRANSPORT REMEDIATION V0.1B

Date: 2026-09-19
Branch: `eth-blockspace-demand-v0.1`
Status: **FROZEN PRE-RUN / SOURCE-ONLY / OUTCOME-BLIND**

## Reason

The V0.1A remediated source probe (run 35440365756) reached provider quorum and exact block identity PASS on all four frozen blocks, but the global receipt remained `SOURCE_ACQUISITION_TECHNICAL_FAILURE` because some optional public RPC candidates failed transport / chain-id checks.

This amendment changes **transport membership only**. It is based solely on source availability and identity results, not on base fee, gas usage, market prices, returns, PnL, direction or any economic outcome.

## Qualified transport set

Exactly two independently reachable public Ethereum JSON-RPC endpoints are frozen for V0.1B:

1. `https://eth.drpc.org`
2. `https://rpc.flashbots.net`

Both returned:
- Ethereum mainnet chain id `0x1`;
- all four frozen historical blocks;
- exact identity agreement with the accepted quorum in V0.1A;
- complete required header semantics.

The following V0.1A candidates are excluded from V0.1B **only because of source transport qualification failures**:
- `https://1rpc.io/eth`
- `https://eth.llamarpc.com`
- `https://ethereum-rpc.publicnode.com` (partial historical availability on the two oldest frozen blocks)

No excluded provider is removed because of any economic field value.

## Scientific identity unchanged

Frozen blocks remain exactly:
- 13,000,000
- 15,000,000
- 18,000,000
- 21,000,000

Allowed fields remain exactly:
- number
- hash
- parentHash
- timestamp
- gasLimit
- gasUsed
- baseFeePerGas

No transaction bodies, logs, receipts, balances, prices, returns or PnL.

## V0.1B PASS gate

`SOURCE_SCHEMA_PASS` requires:

1. both qualified providers return `eth_chainId == 0x1`;
2. both providers return all four exact frozen blocks;
3. both providers agree exactly on block hash and timestamp for every block;
4. all required fields exist and parse;
5. header sanity passes: baseFeePerGas>0, gasUsed>0, gasLimit>0, gasUsed<=gasLimit;
6. every block timestamp is strictly before 2025-01-01T00:00:00Z;
7. economic field values are not printed or persisted.

Any failure remains fail-closed.

## What PASS authorizes

Only a **separate full historical Source/Data Gate freeze** ending no later than 2024-12-31. It does not authorize prices, returns, PnL, predictive thresholds, direction, live trading, orders, wallets, alerts/webhooks, Render deployment or merge to main.
