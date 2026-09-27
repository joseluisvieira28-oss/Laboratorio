# POLY-COMBINATORIAL-ARB-001 — SOURCE REMEDIATION FREEZE V0.7

Date: 2026-09-27
Status: FROZEN_PRE_RUN / SOURCE-ONLY / NO ECONOMICS
Parent V0.6 closeout commit: 92504ff48f49e98efd2d39bcee9a3dcabeaf1c32

## Purpose
Resolve the two execution-provenance blockers exposed prospectively by V0.6 without recalculating or rescuing V0.6:
1. fee provenance/formula;
2. book timestamp/current-state semantics.

No package sum, margin, PnL, profitability or trade signal is allowed in V0.7.

## A. Fee provenance
Pin the current official Polymarket py-clob-client-v2 source at:
292c11005d748c21342a9457d7c0ac89afc2e3f2

Snapshot and SHA256:
- py_clob_client_v2/client.py
- py_clob_client_v2/fees.py
- py_clob_client_v2/endpoints.py

For every frozen condition ID in events 32228, 48292 and 51456:
- query public GET /clob-markets/{condition_id};
- record only fee descriptor fd={r,e}, neg-risk flag, tick/minimum-size metadata and token identifiers;
- do not record prices or compute fees.

Fee provenance passes if all frozen conditions resolve and the response semantics can be mapped deterministically to the pinned official client:
- missing/null fd -> official client default FeeInfo(rate=0, exponent=0);
- present fd must expose finite numeric r and e;
- token IDs returned by CLOB metadata must map to the frozen Gamma tokens.

This is source provenance only. V0.7 does not apply the fee formula to any market price.

## B. Current-book synchronization semantics
Use the same frozen 25 YES token IDs.

REST side:
- one public POST /books batch request;
- preserve only token/asset ID, provider hash, provider timestamp and bid/ask level counts;
- discard prices/sizes from the receipt.

WebSocket side:
- one public market-channel connection;
- subscribe to all frozen YES token IDs;
- collect initial/current book messages for up to 30 seconds;
- preserve only asset ID, provider hash, provider timestamp, bid/ask counts and local receive UTC.

No book price or package economics may be serialized.

## C. Synchronization source gate
SYNC_SOURCE_PASS iff:
- REST returns all frozen tokens;
- WS provides current book state for >= 95% of frozen tokens;
- among tokens present on both routes, >=95% have identical provider book hash OR a separately flagged current-state-equivalence outcome shows a newer WS hash after the REST receipt without transport errors;
- no authenticated endpoints or orders are used.

The purpose is to determine whether provider timestamp dispersion is a last-state/update property rather than a valid cross-leg acquisition clock. V0.7 must not simply loosen the old 2s gate.

## D. Outputs
Allowed:
- counts;
- hashes;
- timestamps;
- fd.r / fd.e source descriptors;
- current-state equality/mismatch counts;
- source/provenance verdicts.

Forbidden:
- bid/ask prices;
- sizes;
- package price sums;
- fee dollar calculations;
- margins;
- arbitrage labels;
- PnL;
- orders/capital/authentication;
- retroactive V0.6 rescue.

## E. Adjudication
FEE_PROVENANCE_PASS / BLOCKED
SYNC_SOURCE_PASS / BLOCKED
SOURCE_REMEDIATION_PASS only if both pass.

A PASS authorizes only a new separately frozen prospective MVE V0.8. It does not authorize using V0.6 snapshots.
