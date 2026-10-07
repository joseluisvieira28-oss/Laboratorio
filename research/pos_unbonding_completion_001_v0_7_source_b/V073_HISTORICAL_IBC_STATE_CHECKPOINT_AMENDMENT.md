# V0.7.3 HISTORICAL IBC-STATE CHECKPOINT AMENDMENT

Date: 2026-10-07
Parent V0.7.2: 2857e56e85555fcd6356e2264f4687f6cd81b416
Coreum unbonding/completion counts inspected: NO
Market outcomes opened: NO
IBC consensus-state values inspected before this amendment: NO

## Reason

Osmosis archive block_search is suitable for block lifecycle events, but IBC update_client is a transaction event and historical tx-index discovery is not required to prove the cross-chain state route.

Historical chain-registry metadata shows the current Coreum-on-Osmosis client 07-tendermint-2929 was registered on 2023-08-10, superseding 07-tendermint-2924.

## Frozen checkpoint method

Query canonical historical Osmosis application state at two fixed host timestamps:

A. first Osmosis block at/after 2023-08-11T00:00:00Z
B. first Osmosis block at/after 2024-01-02T00:00:00Z

At each host block:
1. query client state 07-tendermint-2929 and require chain_id=coreum-mainnet-1;
2. query all consensus states retained for that client at exactly that historical Osmosis state;
3. choose the consensus state with the greatest timestamp not later than the host block timestamp;
4. use its revision_height as the Coreum checkpoint;
5. fetch the same Coreum height from Source A;
6. require exact timestamp equality and exact IBC root hash == Coreum app_hash.

The two selected Coreum checkpoints must be distinct and separated by the two fixed host dates above.

No selection based on whether a candidate hash matches is allowed. If the historical REST/state query is unavailable or the deterministic selected states fail to reconcile, Osmosis IBC Source B fails and V0.7.2 proceeds to the next frozen counterparty.

This amendment supersedes only the sparse checkpoint-selection mechanic in V0.7.2. All independence, provenance and firewall rules remain unchanged.
