# STABLECOIN-EXCHANGE-FLOW-001 — SOURCE PROVENANCE DECISION V0.1

STATUS: **SOURCE PROVENANCE PASS / FULL_ACQUISITION_AUTHORIZED**

LAB: `STABLECOIN-EXCHANGE-FLOW-001`  
MVE: `SEF-BINANCE-PUBLIC-USDT-ETH-1D-001`

## Decision

The source/provenance gate is passed for the frozen Binance Public Address Basket USDT flow MVE.

**Authoritative activation classification: `SOURCE_CROSSCHECK_EXACT_PASS`.**

`FULL_ACQUISITION_AUTHORIZED` is granted strictly for the source/data window and semantics frozen in `DATA_ACQUISITION_PROTOCOL_V0.1.md` plus `SOURCE_ONLY_AMENDMENT_001_BLOCKTIMESTAMP.md`.

This decision does **not** authorize BTC outcomes, returns, PnL, 2025, 2026, live trading, exchange mutation, merge to main, or deployment.

## Evidence chain

### 1. Preferred Coin Metrics route rejected pre-outcome

The desired exchange-flow metrics were discoverable in metadata, but Community timeseries did not expose usable USDT 1d rows and the Pro route required authorization. More importantly for strict point-in-time governance, the metric description refers to addresses *currently known* to belong to the entity. The route was therefore not accepted as PIT-defended historical labeling.

Classification remained a source/data problem, not an economic edge verdict.

### 2. Point-in-time basket frozen from Binance's public 2022-11-10 disclosure

Nine Ethereum addresses explicitly published by Binance were frozen prospectively. The basket is intentionally incomplete and is never represented as all Binance or all exchanges. No later address labels are added retroactively.

Earliest complete eligible UTC day: `2022-11-11`.

### 3. Blockchair historical ERC-20 feasibility and dump schema passed

Protected-period USDT rows for the frozen basket were queryable via Blockchair.

The exact Blockchair daily dump route was resolved as:

`https://gz.blockchair.com/ethereum/erc-20/transactions/blockchair_erc-20_transactions_YYYYMMDD.tsv.gz`

Protected 2022-11-11 dump schema gate classified `DUMP_SCHEMA_PASS` with required fields:

`block_id, transaction_hash, time, token_address, token_name, token_symbol, token_decimals, sender, recipient, value`.

The 2022-11-11 compressed dump size was 62,325,135 bytes.

### 4. Historical Ethereum RPC provider matrix identified MEV Blocker

Multiple public providers were tested on protected 2022 and 2024 USDT log windows. `https://rpc.mevblocker.io` served historical `eth_getLogs` without a personal token and passed the protected provider matrix.

### 5. Query range profiled before outcomes

A pre-outcome range profile established **3,200 blocks** as the frozen base chunk. Larger dense queries could hit the provider's 10,000-result ceiling; acquisition therefore uses 3,200-block chunks plus deterministic adaptive splitting.

### 6. Historical batch and log schema passed

MEV Blocker historical JSON-RPC batch requests passed on protected 2022/2024 blocks.

The historical USDT `eth_getLogs` schema includes `blockTimestamp`, allowing direct UTC-day aggregation without thousands of auxiliary block metadata calls. This efficiency change was separately frozen in `SOURCE_ONLY_AMENDMENT_001_BLOCKTIMESTAMP.md` before any BTC outcome access.

### 7. Gzip transport is logically exact

The same protected 3,200-block inbound query returned an identical canonical log result with and without HTTP gzip. Example protected query:

- logical payload: 1,526,819 bytes;
- gzip wire payload: 197,570 bytes;
- result count: 2,406 in both;
- canonical result SHA256 identical.

Classification: `GZIP_EQUIVALENCE_PASS`.

### 8. Independent full-day source cross-check — exact pass

GitHub Actions run: `34889047764`  
Job: `104126816975`  
Protected day: `2022-11-11`  
MEV Blocker block interval: `15943061..15950211`  
Blockchair dump SHA256: `81f2d1ff21196e02add06a00941b553fa1ef6e029731316f30567f1fa679fda8`

After excluding basket-to-basket sweeps, the two independent access routes matched **exactly**:

| Direction | MEV Blocker count | Blockchair count | MEV raw USDT value | Blockchair raw USDT value |
|---|---:|---:|---:|---:|
| External inbound | 5,627 | 5,627 | 625,170,975,702,613 | 625,170,975,702,613 |
| External outbound | 12,339 | 12,339 | 906,760,081,433,071 | 906,760,081,433,071 |

Blockchair additionally identified 17 internal basket-to-basket transfers with raw value 782,417,814,083,501; these are excluded by the frozen MVE semantics.

Result:

- `exact_external_flow_match = true`
- `SOURCE_CROSSCHECK_EXACT_PASS`
- `access_2025 = false`
- `access_2026 = false`
- `btc_market_data_accessed = false`
- `returns_computed = false`
- `pnl_computed = false`

### 9. V0.2 parallel dump transport failure does not alter the decision

A later transport-only parallel Range implementation encountered HTTP 402 while downloading large concurrent pieces. A dedicated sequential Range-access probe subsequently proved byte access at the beginning, 25%, 50%, 75%, and end of the same dump, all HTTP 206. The canonical V0.1 serial full-file cross-check completed and produced the exact pass above. The V0.2 failure is therefore a transport experiment failure, not a source mismatch.

## Authorized next action

Run the fail-closed source-only full acquisition for:

- `2022-11-11` through `2024-12-30` UTC;
- frozen nine-address Binance public basket;
- Ethereum USDT only;
- external inbound/outbound semantics exactly as frozen;
- 3,200-block base chunks with adaptive split;
- direct `blockTimestamp` UTC aggregation;
- gzip transport permitted because canonical-result equivalence passed;
- complete zero-flow date materialization;
- immutable CSV, manifest and acquisition receipt.

No BTC market data or economic outcomes may be opened until the resulting dataset itself passes its data/coverage gate and a separate final pre-Discovery protocol is frozen.

## Governance

Research-only. Fail-closed. No live trading. No exchange mutation. No POST/PUT/PATCH/DELETE exchange actions. No live orders. No merge to main. No Render deployment. No post-outcome tuning. No 2025/2026. No BTC outcome access at this stage.
