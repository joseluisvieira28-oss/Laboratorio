# L2R-OVERLAY-ETF-CME-PRET0-001 — SPARSE TRANSPORT REMEDIATION V0.1.1

Date: 2026-09-30  
Status: **FROZEN BEFORE ANY PRET0 COMBINED OUTCOME ACCESS**

Parent protocol:
`research/l2_resiliency_overlay_pret0/L2R_OVERLAY_ETF_CME_PRET0_001_2025_DEVELOPMENT_PROTOCOL_V0_1.md`

Parent implementation lock:
`research/l2_resiliency_overlay_pret0/L2R_OVERLAY_ETF_CME_PRET0_001_IMPLEMENTATION_LOCK_V0_1.json`

## Purpose

Replace the impractical full-calendar execution transport with a causally equivalent sparse replay. This is an implementation/transport correction only. The PRET0 scientific rule remains exactly:

`MID_PRET0 = last accepted normalized midpoint at-or-before T0, max staleness 1,100 ms`.

No combined PRET0 residual, cell result, support gate or classification has been opened before this freeze.

## Frozen scientific invariants

Unchanged:
- LAB_ID `L2R-OVERLAY-ETF-CME-PRET0-001`;
- immutable ETF-CME parent artifact SHA256 `40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`;
- canonical L2 parent manifest identity `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`;
- parent direction and exact T0;
- six R/Y cells;
- WEAK iff RR < 1.0;
- horizon lateness <= 1,100 ms;
- ALIGNED / OPPOSED / NO_ACTIVE_WEAK / SOURCE_GATED semantics;
- PRET0 max reference staleness 1,100 ms;
- five support gates and sample minima;
- development-only status;
- 2026 CLOSED;
- no parent PnL filtering;
- no live trading, orders, exchange mutation, wallet mutation, leverage deployment, main merge, or post-outcome rescue.

## Sparse equivalence boundary

The largest frozen Y horizon is 60 seconds. An event can influence a cell at T0 only if its event timestamp is later than T0-60s.

For every source-evaluable parent T0, sparse replay reads exactly:
1. the complete UTC hour immediately preceding T0; and
2. the complete UTC hour containing T0.

This is sufficient for PRET0 because:
- every potentially selectable event is inside the final 60 seconds before T0;
- every selected event's frozen Y observation lies no later than T0+60 seconds;
- `MID_PRET0` can only use an accepted state within 1,100 ms before T0, necessarily inside the prior/current-hour pair;
- the prior complete hour provides normalization and previous-book warm-up.

Before T0-60s, replay must prove normalization convergence with a non-future accepted payload whose payload timestamp is at least the prior-hour start. If convergence is not proved before the causal cutoff, that T0 fails closed.

## Source binding frozen before outcomes

Drive transport was audited source-only:
- 35/35 220 MiB transport parts SHA256 verified;
- 3/3 logical source ZIP SHA256 identities verified exactly;
- BTC L2 archive members: 3,600 + 2,400 + 2,400 = 8,400;
- 92 sparse RAW objects extracted with ZIP CRC verification and locally SHA256/MD5-bound;
- source-gated parent dates inherited from the canonical pre-outcome source gate:
  - 2025-10-22
  - 2025-11-18
  - 2025-11-26
- no combined directional residual was computed;
- no 2026 data was accessed.

Sparse source manifest:
`L2R_OVERLAY_ETF_CME_PRET0_001_SPARSE_SOURCE_MANIFEST_V0_1_1.csv`

Source binding:
`L2R_OVERLAY_ETF_CME_PRET0_001_SPARSE_SOURCE_BINDING_V0_1_1.json`

## Outcome authority

After the sparse runner is committed, synthetic QA passes, source-only normalization preflight passes, and exact implementation identities are frozen, exactly one 2025 PRET0 development execution is authorized.

The first valid terminal classification is immutable for this LAB_ID:
- `DEVELOPMENT_OVERLAY_SIGNAL_SUPPORTED`
- `DEVELOPMENT_OVERLAY_NO_SUPPORT`
- `DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`

No rerun rescue, best-cell selection, threshold change, sample-gate change or sign-based retry is allowed.
