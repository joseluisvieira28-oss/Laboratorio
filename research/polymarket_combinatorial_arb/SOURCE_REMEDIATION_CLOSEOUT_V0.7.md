# POLY-COMBINATORIAL-ARB-001 — SOURCE REMEDIATION CLOSEOUT V0.7

Date: 2026-09-27
Status: SOURCE_REMEDIATION_PASS / ECONOMICS SEALED
Branch: prediction-combinatorial-arb-v0.7-source-remediation

## Canonical run
Workflow: POLY-COMB Source Remediation V0.7
Run ID: 36334078724
Job ID: 108661463964
Conclusion: SUCCESS
Head commit: 7e907fdefa1dc95a6aa1cbdd22c794c7f1e970ea
Artifact ID: 10936258874
Artifact ZIP SHA256: 84b075133e8912d7526fa65ec2ff167aa99414bc83439917b0710f1e5f949043

## Pinned first-party implementation
Polymarket py-clob-client-v2 commit:
292c11005d748c21342a9457d7c0ac89afc2e3f2

The pinned client proves:
- market fee metadata is loaded from GET /clob-markets/{condition_id};
- fd.r maps to FeeInfo.rate;
- fd.e maps to FeeInfo.exponent;
- absent fd defaults to rate=0 / exponent=0;
- BUY fee handling is price-dependent through the pinned fees.py implementation.

## Fee provenance result
PASS.

- frozen condition IDs: 25/25 resolved;
- frozen YES token mapping: 25/25;
- invalid fee descriptors: 0;
- errors: 0.

Observed source descriptor classes:
- 13 conditions: r=0.05, e=1;
- 12 conditions: r=0.04, e=1.
Tick-size differences were preserved as source metadata but do not alter the fee descriptor identity.

No fee dollars were computed in V0.7.

## Book-current-state result
PASS.

- REST batch current books: 25/25;
- WebSocket current books: 25/25;
- common states: 25;
- exact provider hash equality: 23/25 = 92%;
- remaining 2/25: WebSocket delivered a newer provider state than the immediately preceding REST batch;
- current-state compatible: 25/25 = 100%.

This demonstrates that large per-book provider timestamp dispersion in V0.6 cannot be treated as proof that a one-request current REST batch is cross-leg stale. The provider hash/state can remain unchanged until the underlying book updates.

V0.6 remains immutable: its 2-second provider-timestamp gate is not reinterpreted retroactively.

## Safety / outcome firewall
PASS:
- prices serialized = false;
- sizes serialized = false;
- package sums = false;
- fee-dollar calculations = false;
- arbitrage labels = false;
- authenticated endpoints = false;
- orders = false;
- capital = false.

## Adjudication
FEE_PROVENANCE_PASS.
SYNC_SOURCE_PASS.
SOURCE_REMEDIATION_PASS.

This authorizes only a new separately frozen prospective economic MVE.
It does not authorize any V0.6 rescue, live trading, orders, capital or main merge.
