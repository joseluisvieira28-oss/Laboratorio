# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.7 KYVE SOURCE REMEDIATION FREEZE

Date: 2026-10-07
Parent V0.6 closeout: d80bac3e5ef55384a9d5e73541ab650d424d4f5f
Parent verdict: SOURCE_HISTORICAL_COVERAGE_BLOCKED
Market outcomes opened before V0.7: NO
Valid materiality/event census opened before V0.7: NO
Main baseline remains: f263c6c6f3a57f26666a7aee28e782f2cbd08418

## Reopening authority

V0.6 permits reopening only on genuinely new pre-outcome source capability.

After the V0.6 closeout, V0.4.5 independently proved a new capability at commit
7a54cb7cf0edee1dcdea0b70ddeed215c42d2fc0:

- KYVE mainnet finalized Tendermint bundles are publicly retrievable without credentials;
- underlying storage bytes can be downloaded directly;
- SHA-256 of compressed bytes is verified against KYVE data_hash;
- the bundle can be decompressed and a fixed-height item extracted;
- each item includes canonical block and block_results;
- Osmosis H=15,000,000 and Celestia H=2,500,000 matched independent historical archive block hash, time and app-hash exactly.

This is a new source capability, not a relaxation of a gate.

## Scope

V0.7 is source-only. No market prices, returns, PnL, market-volume outcomes, live trading, orders, wallets, account reads, private exchange endpoints, exchange mutation, spending or main merge.

Frozen completion interval remains 2023-01-01 through 2024-12-31 UTC.
Materiality remains 10 bps of historical bonded stake.
Hard sample bar remains >=40 MATERIAL chain-days TOTAL across >=5 qualifying chains.
Actual complete_unbonding remains T_completion.

## Qualified four-chain base

For source remediation purposes the four-chain base is:
1. Cosmos Hub / ATOM
2. Osmosis / OSMO
3. Celestia / TIA
4. dYdX Chain / DYDX

ATOM and DYDX retain prior dual independent historical index/archive evidence.
OSMO and TIA may use the newly proven KYVE trustless bundle path plus an independently operated archive path, subject to continuous-coverage audits before census PASS.

## Fifth-chain order

Do not reopen an unbounded chain search.

The only fifth-chain candidates in V0.7 are chains already prospectively frozen before any valid event census and for which the new KYVE capability is directly relevant:

1. Archway / ARCH — KYVE mainnet block pool 2
2. Axelar / AXL — KYVE mainnet block pool 3

Terra and Coreum are not re-tested in V0.7 because the new KYVE capability does not cover them. V0.4.5 official-RPC sweep b9f682a436f1cd1f5ccf35b0a27ab842ca7aed29 remains evidence that Terra lacked a reproducible second raw archive across all tested official RPCs.

Stop at the first V0.7 candidate satisfying all source-only requirements. No candidate completion-event frequency may be inspected to choose between them.

## KYVE source acceptance

For each fixed source anchor H:
- use official KYVE source-registry commit 7cb8e3abd7fb5788b299c270380f1ea36715e2a0;
- use the prospectively mapped mainnet block-sync pool;
- verify pool start/current keys cover H;
- retrieve finalized bundle metadata by height index;
- fetch public storage bytes;
- require SHA-256(compressed bytes) == data_hash;
- decompress using the declared compression;
- extract the exact H data item;
- require block height, chain-id and block_results height == H;
- retain block hash/time/app-hash and response evidence.

## Independent source acceptance

The second path must be independently operated from KYVE and must reproduce the same canonical fixed-height block.

Transport TLS validity is not itself a scientific gate. If a publicly documented endpoint has a certificate/hostname failure, a retry with TLS verification disabled is permitted only for source diagnosis and counts as evidence only when:
- the endpoint identity is preserved in the receipt;
- no credentials/private access are used;
- block height, chain-id, block hash, timestamp and app-hash exactly match the verified KYVE bundle;
- block_results for the same height is returned successfully.

A matching canonical consensus hash is authority; an insecure transport match is explicitly flagged in provenance.

## Continuous coverage requirement

A fixed-height pair is only source qualification, not census completeness.

Before any event census:
- KYVE pool start/current keys must cover the required interval;
- finalized bundle ranges must be continuous across deterministic audit checkpoints;
- independent archive coverage must be shown at frozen checkpoints sufficient to support lifecycle reconciliation or an equivalent second independently verifiable path;
- no completion/materiality counts may be used to alter checkpoints or source choice.

## Gates

G1 >=5 comparable version-pinned chains.
G2 >=2 independent historical evidence paths per selected chain.
G3 complete 2023-2024 census or independently verifiable complete equivalent.
G4 cancellation/slash/hold lifecycle reconciled.
G5 >=40 MATERIAL chain-days TOTAL across >=5 chains.
G6 >=12 consecutive months pre-2026 market-source capability metadata for each selected native token, without outcome values.
G7 reproducible receipts/digests and firewall compliance.

Allowed verdicts remain source/data verdicts only. NO_EDGE is impossible in V0.7.
