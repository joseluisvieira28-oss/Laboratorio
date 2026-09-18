# STETH-REDEMPTION-BASIS-001 — SOURCE PROVENANCE TERMINAL CLOSEOUT V0.2

Date: 2026-09-18
Branch: empty-territory-hunt-v0.1
Status: TERMINAL FOR EXACT FROZEN V0.1 / SOURCE-ONLY / OUTCOME-BLIND

## Final classification

FROZEN_SOURCE_BOUNDARY_PROVENANCE_FAILURE

This supersedes the earlier operational description SOURCE_ACQUISITION_TECHNICAL_FAILURE for the exact frozen V0.1 experiment.

It is NOT NO_EDGE and it is NOT an economic-performance verdict.

## Immutable frozen V0.1 boundary

The original authority froze:
- source start: 2023-05-15T00:00:00Z;
- later Discovery clock: one daily snapshot at 12:00 UTC;
- expected snapshot population: 597;
- WithdrawalQueue proxy: 0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1;
- historical queue-state method getLastRequestId();
- no change to source window or timing as a source rescue.

## Decisive provenance probe

Workflow run: 35385142825
Head SHA: c17570a50f88b11cab63c9b994737fb3723b45c5
Artifact: 10563801890
Artifact digest: sha256:a1a47e2c1026cccfc068b6d42a0f699dfd527aa038d4b2f74a2d904a6089d741

Classification:
FROZEN_SOURCE_BOUNDARY_PROVENANCE_FAILURE

At the exact frozen first daily snapshot:
2023-05-15T12:00:00Z

three independent archive-capable providers mapped the timestamp consistently to:
block 17,265,042

At that exact block:
- WithdrawalQueue proxy bytecode was non-empty on 3/3 providers;
- getLastRequestId() reverted / was unavailable on 3/3 providers.

The exact V2 activation/enactment transaction:
0x592d68a259af899fb435da0ac08c2fd500cb423f37f1d8ce8e3120cb84186b21

was retrieved with quorum and maps to:
block 17,266,004

At the activation block:
- getLastRequestId() was accessible on 3/3 providers.

Therefore the original failure was not a generic absence of archive RPC access. The frozen first 12:00 snapshot precedes the canonical V2 WithdrawalQueue state required by the experiment.

## Adjudication

The exact frozen V0.1 lab cannot satisfy its own source boundary.

Do NOT:
- shift the source start;
- drop the first daily snapshot;
- move the 12:00 UTC clock;
- start after V2 enactment;
- silently change expected snapshot count 597.

Any such design would be a new prospectively frozen experiment, not remediation of STETH-REDEMPTION-BASIS-001 V0.1.

## Safety

No Curve quote values opened.
No redemption predictor computed.
No ETH/stETH basis opened.
No market prices or returns opened.
No PnL, PF, win rate or drawdown.
No 2025/2026 access.
No live trading.
No wallets/orders/exchange mutation.
No main merge.

## Operational hardening

The legacy source-gate workflow was restricted to explicit trigger files so unrelated diagnostic-document commits no longer relaunch the obsolete source gate.

Hardening commit:
4a38b382fd64c948e20fc4f4d0d9d312bf4b7991
