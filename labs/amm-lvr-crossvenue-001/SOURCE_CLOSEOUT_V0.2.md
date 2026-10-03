# AMM-LVR-CROSSVENUE-001 — SOURCE CLOSEOUT V0.2

**Date:** 2026-09-23  
**Authority:** PRE_DISCOVERY_FREEZE_V0.1 + FORWARD_ECONOMIC_FREEZE_V0.1  
**Primary run:** GitHub Actions 35821153542  
**Evidence artifact:** 10733147693  
**Artifact SHA-256:** 218e08d0487d3ea43ff4641086076e9c093600e3a978dd1cc17d0589ad10bacb

## Terminal source findings

### 1. Public paper sample
PASS.
- 4,968 rows / 4,968 unique tx hashes
- 203 pairs
- 19 labels in the sample
- 0 required-column failures
- 0 numeric parse failures

This one-day sample is contaminated external benchmark evidence only.

### 2. Free historical full-cost route
**HISTORICAL_FREE_SOURCE_BLOCKED.**

Observed blockers:
- public Dune query page is reachable;
- direct Dune result CSV API without key returns 401 invalid API key;
- Binance USD-M public historical bookTicker exists for tested 2024 date but not for tested 2025-03-08 object;
- authors' full historical CEX leg uses access-gated Tardis quote data.

Do not fabricate historical BBO from candles/trades.

### 3. Historical Ethereum tx/block replay
The frozen one-day sample was probed across first transaction per non-empty sample label:
- 18/18 historical transactions found;
- 18/18 historical blocks found;
- PublicNode did not serve the old transaction receipts / trace without archive entitlement.

This is an access blocker, not a negative market verdict.

### 4. No-key RPC matrix
Five public RPC routes were tested on one frozen 2023 tx.

**FREE_ARCHIVAL_RECEIPT_PASS**
- Cloudflare: historical transaction receipt available.
- dRPC: historical transaction receipt available.
- dRPC: historical block receipts available (102 receipts in frozen block).

**FREE_ARCHIVAL_TRACE_BLOCKED**
- none of the five tested routes supplied historical parity/debug trace in this gate.

Implication:
- historical gas/log-based DEX reconstruction is feasible without paid data;
- historical internal-call/coinbase-transfer reconstruction remains blocked on the tested no-key routes.

### 5. Executable Uniswap + CEX source routes
**EXECUTABLE_QUOTE_SOURCE_PASS.**

Frozen pairs all have at least one bidirectional executable Uniswap V3 Quoter path:
- WETH-USDC: 4/4 bidirectional fee tiers
- WETH-USDT: 4/4
- WBTC-WETH: 4/4
- LINK-WETH: 3 bidirectional tiers / 4 pools found
- PEPE-WETH: 2 bidirectional tiers / 4 pools found
- SHIB-WETH: 3 bidirectional tiers / 3 pools found

Public Binance BBO route PASS for:
- ETHUSDT
- BTCUSDT
- LINKUSDT
- PEPEUSDT
- SHIBUSDT
- USDCUSDT

Ethereum eth_feeHistory route PASS.

No quote amounts or PnL were persisted in the source probe.

### 6. Prospective registry observability
Published paper registry frozen before the run:
- 23 labels
- 65 contract addresses

120-second read-only observation:
- 11 unique Ethereum blocks
- 126 Binance BBO snapshots
- 0 source errors
- 17 transactions touched frozen registry addresses
  - Wintermute: 14
  - Shen: 3

These 17 are **registry touches only**. They are not classified as CEX-DEX arbitrage until receipt/log/trace criteria are applied.

Verdict:
**FORWARD_MULTI_SEARCHER_OBSERVABILITY_PASS**

## Overall source verdict

- Historical one-package full-cost replication: **BLOCKED**
- Historical on-chain receipt/log reconstruction: **PASS via alternate no-key RPC**
- Historical internal trace / exact direct builder-transfer reconstruction: **BLOCKED on tested no-key routes**
- Live executable DEX quotes: **PASS**
- Live public CEX observable hedge source: **PASS**
- Prospective chain + CEX collection: **PASS**
- Economic Discovery: **NOT YET ADJUDICATED**
- Current lifecycle: **READY_FOR_FORWARD_SHADOW_ENGINEERING**

This document creates no edge, candidate, Tier-2, quasi-diamond, live-trading or main-merge authority.
