# STETH-REDEMPTION-BASIS-002 — NON-CANONICAL EXECUTION CLOSEOUT — RUN 35397519516

Date: 2026-09-18
Status: **SCIENTIFICALLY INADMISSIBLE / DO NOT ADJUDICATE / DO NOT READ OUTCOME FOR DECISION**

## Scope

This closeout is based on prospective authority comparison only.
The economic/result artifact from run `35397519516` is not required and must not be used for scientific adjudication.

## Why the execution is non-canonical

Run `35397519516`, head `5967745ddd767f0642373ed65834e9868a300b9f`, was launched from
`steth-redemption-basis-002-source-v0.1` using a later implementation path.

An earlier canonical implementation freeze already existed on
`steth-redemption-basis-002-discovery-v0.1` before the first Discovery execution.

That earlier authority freezes, among other details:

- trailing APR annualization:
  `G_7d^(365/7) - 1`;
- next-block rebasing-token request semantics;
- circular moving-block bootstrap;
- 10,000 replications;
- seed 20260918;
- block length `max(2, ceil(n^(1/3)))`;
- empirical 2.5th-percentile lower bound.

The later source-branch implementation used materially different APR/bootstrap semantics.
Therefore it is not a transport retry of the frozen Discovery and cannot create a valid V0.1 scientific verdict.

## Canonical lineage

Canonical first Discovery:
- run `35387691310`
- result: `DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE`
- exact cause: RPC/provider throughput 429
- no valid scientific verdict.

Canonical transport remediation:
- file `STETH_REDEMPTION_BASIS_002_DISCOVERY_RPC_THROUGHPUT_REMEDIATION_V0_1A.md`
- transport only: retry/split exact RPC requests while preserving exact frozen science.

Canonical remediation retry:
- branch `steth-redemption-basis-002-discovery-v0.1`
- run `35398364376`
- head `6acb229448c61922ca2c2016feb9866ae27c18d9`.

## Governance

Regardless of whether run `35397519516` completes successfully, fails, or emits attractive numbers:

- do not classify edge/no-edge from it;
- do not use it to tune or select parameters;
- do not use it as replication;
- do not compare its outcome against the canonical retry;
- do not promote from it.

Only the canonical transport-remediated lineage may adjudicate STETH-REDEMPTION-BASIS-002 V0.1.

No live trading, wallet, order, exchange mutation or main merge is authorized.
