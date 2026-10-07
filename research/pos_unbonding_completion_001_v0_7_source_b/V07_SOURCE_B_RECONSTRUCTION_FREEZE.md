# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.7 BUILD-OUR-OWN-SOURCE-B FREEZE

Date: 2026-10-07
Parent V0.6 closeout: d80bac3e5ef55384a9d5e73541ab650d424d4f5f
Market outcomes opened: NO

## Purpose

Construct an independently reproducible historical Source B rather than requiring two currently-live archive RPC operators.

## Frozen target order

1. Coreum / coreum-mainnet-1
2. Crypto.org Chain / crypto-org-chain-mainnet-1
3. Kava / kava_2222-10

Advance to the next target only if the earlier target cannot produce an independent reconstructed historical path.

## Source-B admissibility

A reconstructed Source B must originate from material operationally independent of Source A and must preserve enough historical consensus/block-store data to reproduce canonical historical evidence.

Admissible examples:
- independently operated archive snapshots or full block-store backups;
- public bulk historical exports;
- IPFS/Filebase/S3/object-storage snapshots from another operator;
- independently maintained block/header datasets with verifiable canonical hashes;
- restoration from independent snapshots plus version-pinned binary/genesis sufficient to query historical blocks/results.

Not admissible:
- a pruned/current snapshot that cannot reproduce frozen historical heights;
- another hostname controlled by the same Source-A operator;
- current state-sync trust data only;
- a third-party page that merely republishes Source-A output without independent provenance;
- market or economic outcomes.

## Coreum fixed-height verification anchors

Source A already proved:
- H=5,000,000 hash D8A6B584C70FE38CD7D160A7F5151974E595AD9E241700F80D45AF15F53B0FF9
- H=10,000,000 hash 227EE3C00731C6544D88478F9022100214767E0DF8779C66433BF5C0BB810F47
- H=15,000,000 hash DE285C3282D4EAC0EA6AF0FDAB0EF3F45273D5BB96289A76EA501CEDB52B1516

A candidate reconstructed Source B must reproduce at least two of these anchors, including time and app-hash when the source format carries them, and demonstrate historical-range provenance independent of Source A.

## Inherited science

Completion interval remains 2023-01-01..2024-12-31 UTC.
Materiality remains >=10 bps of historical bonded native stake.
Sample bar remains >=40 MATERIAL chain-days TOTAL across >=5 chains.
Actual complete_unbonding remains T_completion.
Cancellation/slash/hold reconciliation remains mandatory.

## Firewall

No prices, returns, PnL, market outcomes, live trading, orders, wallets, account reads, private exchange endpoints, spending or main changes.

No candidate unbonding-event census is opened in V0.7 until a Source B passes this reconstruction gate.

Allowed V0.7 verdicts are source-only.
