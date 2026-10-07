# V0.7.2 CROSS-CHAIN IBC LIGHT-CLIENT SOURCE-B AMENDMENT

Date: 2026-10-07
Parent V0.7 freeze: d955b69661380462c4e5c2f699b41e46e7086893
Coreum unbonding/completion event counts inspected: NO
Market outcomes opened: NO

## Motivation

The live TX explorer backend is hosted under tx.org and is not independent from the TX/Coreum Source-A operational sphere. It is therefore not eligible as Source B.

Before inspecting any historical IBC consensus-state values, V0.7.2 prospectively permits a cryptographically independent cross-chain reconstruction path.

## Admissible cross-chain Source B

An IBC Tendermint light client hosted in the canonical state/history of a different production chain may qualify as Source B if:

1. the counterparty chain consensus/operator set is independent of Coreum/TX Source A;
2. the client is proven to track coreum-mainnet-1 for the relevant era;
3. the evidence is retrieved from canonical counterparty-chain history, not from a TX-hosted mirror;
4. the IBC consensus state or verified update carries Coreum consensus height plus timestamp and commitment root/app-hash (and any additional header hash fields available);
5. at least two deterministic historical checkpoints in the frozen 2023-2024 interval reconcile exactly with Coreum Source A at the referenced Coreum heights;
6. evidence spans at least two separated calendar quarters, demonstrating range rather than one isolated moment.

## Deterministic checkpoint selection

Because IBC clients update at sparse, relayer-selected heights rather than preselected round block numbers, fixed H=5M/10M/15M anchors remain valid when available but are not required for this sparse-source route.

Before reading any consensus values, select checkpoints mechanically:
- first valid Coreum consensus height recorded by the eligible counterparty client on or after 2023-07-01 UTC;
- first valid Coreum consensus height recorded by the same client on or after 2024-01-01 UTC.

If either cannot be reconstructed canonically, this route fails. No choosing checkpoints based on whether hashes match.

For each selected checkpoint, fetch the corresponding Coreum Source-A block and reconcile timestamp plus app-hash/commitment root exactly.

## Candidate counterparty order

Frozen before historical consensus retrieval:
1. Osmosis
2. Cosmos Hub
3. dYdX Chain

Stop at the first counterparty that proves two separated checkpoints and historical query provenance.

## Limits

IBC evidence may establish independent canonical consensus verification, but it does not by itself establish full unbonding census completeness. If Source B passes, a separate census freeze must define how Source A raw-block/event enumeration is completeness-audited against independent checkpoints before counts are opened.

No unbonding event counts or market outcomes in this amendment.
