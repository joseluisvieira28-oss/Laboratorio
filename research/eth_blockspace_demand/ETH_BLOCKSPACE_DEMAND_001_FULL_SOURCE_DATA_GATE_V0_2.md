# ETH-BLOCKSPACE-DEMAND-001 — FULL HISTORICAL SOURCE/DATA GATE V0.2

Date: 2026-09-19
Branch: `eth-blockspace-demand-v0.1`
Status: **FROZEN PRE-RUN / SOURCE-DATA ONLY / OUTCOME-BLIND**

Authority lineage:
- V0.1B source schema run: **35445555933 — SOURCE_SCHEMA_PASS**
- Artifact: **10584428775**
- Artifact digest: **sha256:58159169bc744ffd69ffee1604d0613787d399cf056a83479c9436d6c07d10dd**

## Mission

Build a reproducible pre-2025 Ethereum blockspace-demand source series from protocol block headers only.

This stage may persist Ethereum protocol variables. It may **not** access crypto market prices, returns, PnL, a trading direction, predictive thresholds, an outcome horizon, 2025/2026 data, live trading, orders, wallets, exchange mutation, alerts/webhooks, Render, or main.

## Frozen historical grid

Ethereum mainnet exact block-number grid:

- first block: **13,000,000**
- last allowed block: **21,500,000**
- stride: **1,800 blocks**
- target rule: Python-equivalent `range(13_000_000, 21_500_000 + 1, 1_800)`
- expected target count: **4,723**

This grid is frozen by block number, not by observed field values. Block 21,500,000 is a conservative pre-2025 ceiling; every returned timestamp must additionally satisfy the protected-period firewall.

## Qualified providers

Exactly:
- `https://eth.drpc.org`
- `https://rpc.flashbots.net`

Primary assignment is deterministic by global target index:
- even index → DRPC
- odd index → Flashbots

Transport fallback after bounded retry failure is permitted only to the other already-qualified provider and must be recorded.

## Cross-provider identity audit

For every global target whose index mod 20 == 0, both providers must return the block.

For every audit block:
- block number must match;
- block hash must match exactly;
- timestamp must match exactly.

Audit disagreement is `PROVENANCE_FAILURE`.

## Required fields

Persist exactly:
- block number
- block hash
- parent hash
- timestamp
- gasLimit
- gasUsed
- baseFeePerGas
- primary provider used
- whether fallback was used
- whether cross-provider verification was required/passed

No transaction bodies, addresses, calldata, logs, receipts, balances or market data.

## Mechanical source metrics

Per sampled block:
- `gas_utilization = gasUsed / gasLimit`
- `sample_block_base_fee_burn_wei = baseFeePerGas * gasUsed`

The second metric is the protocol base-fee burn for that **sampled block only**. It must never be relabelled as total daily ETH burn.

## Frozen daily aggregation

Group sampled blocks by UTC date from the block timestamp.

For each UTC date persist:
- sample_count
- mean_gas_utilization
- median_base_fee_gwei
- mean_sample_block_base_fee_burn_eth
- max_sample_block_base_fee_burn_eth

No smoothing, z-score, signal threshold, direction or predictive transform is authorized here.

## Missing-data rules

- no interpolation;
- no synthetic block;
- no nearest-block substitution;
- repeated target identities are forbidden;
- global sampled-block coverage must be **>=99.5%**;
- every deterministic cross-provider audit target must pass;
- dates with fewer than 3 sampled blocks are retained in the raw ledger but excluded from the canonical daily series and counted explicitly;
- canonical daily-date retention must be **>=95%** of represented UTC dates.

## Protected-period firewall

Every accepted timestamp must be strictly before **2025-01-01T00:00:00Z**.

Any timestamp at or after that boundary is a hard `PROVENANCE_FAILURE`; the row is not accepted and the run cannot PASS.

## PASS

`SOURCE_DATA_PASS` requires:
1. both providers chain-id mainnet PASS;
2. target coverage >=99.5%;
3. 100% cross-provider audit identity agreement;
4. required fields and economic-source sanity pass;
5. zero protected-period accepted rows;
6. canonical daily-date retention >=95%;
7. no duplicate target rows;
8. firewall confirms market_prices_opened=false, returns_opened=false, pnl_opened=false.

## What PASS authorizes

Only preparation of a separate **FINAL PRE-DISCOVERY protocol** that freezes a falsifiable predictive hypothesis, transforms, costs, horizon, validation split, multiplicity and holdout policy **before any market outcome is opened**.
