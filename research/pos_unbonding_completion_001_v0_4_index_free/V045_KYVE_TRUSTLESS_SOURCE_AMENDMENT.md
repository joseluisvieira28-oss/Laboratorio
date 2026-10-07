# V0.4.5 KYVE TRUSTLESS HISTORICAL SOURCE AMENDMENT

Date: 2026-10-07
Parent V0.4 freeze: 71ac365e709b0e0d7074caed7e842f513207aa85
V0.4.4 expansion: 18b742ed57c3f7f85616ceb2f2744ae64e97aa73
Valid materiality/economic outcomes inspected before this amendment: NO
Market outcomes opened: NO

## Purpose

Add a new source capability, not a new economic rule: KYVE finalized Tendermint bundles may serve as an independent historical evidence path when the pool and bundle are verified before event counts are used.

This amendment does not alter the frozen fifth-chain order:
Terra 2 -> Archway -> Coreum -> Axelar.

## KYVE acceptance rule

A KYVE path is source-qualified only when all are true:
1. the official KYVE source registry prospectively identifies the exact chain/network and block-sync pool;
2. pool metadata shows a start/current key covering the required historical anchor/interval;
3. a finalized bundle containing fixed height H is selected by height/index before inspecting unbonding counts;
4. underlying public storage bytes are downloaded without credentials;
5. SHA-256 of the compressed bundle bytes equals the finalized bundle data_hash;
6. bundle is decompressed according to compression_id;
7. the data item keyed by H is extracted;
8. its canonical block header/hash/time is reconciled with an independently operated archive source at H;
9. where the runtime includes block_results, lifecycle event evidence is retained from the bundle and compared at fixed audit heights to canonical archive block_results;
10. continuous bundle key coverage must be demonstrated before KYVE can establish census completeness.

KYVE metadata alone is not enough. A pool label alone is not enough. A state-sync snapshot alone is not enough.

## Frozen pool mapping from official source registry

- Osmosis / osmosis-1: KYVE mainnet block-sync pool 1
- Archway / archway-1: KYVE mainnet block-sync pool 2
- Axelar / axelar-dojo-1: KYVE mainnet block-sync pool 3
- Celestia / celestia: KYVE mainnet block-sync pool 9

Pool mappings are source facts, not event-count selections.

## Independence

KYVE is an independent path relative to third-party RPC archive operators only if:
- KYVE finalized bundle proof/storage path is used directly; and
- the comparison archive is not merely proxying KYVE.

## Gates unchanged

Materiality remains 10 bps of historical bonded stake.
Sample bar remains >=40 MATERIAL chain-days TOTAL across >=5 chains.
No market prices/returns/PnL/outcomes.
No post-count threshold, chain-order, sign or horizon changes.
