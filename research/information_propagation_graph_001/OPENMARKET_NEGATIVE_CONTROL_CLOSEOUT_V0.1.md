# OPENMARKET NEGATIVE CONTROL CLOSEOUT V0.1

Date: 2026-09-24
Lab: INFORMATION-PROPAGATION-GRAPH-001
Stage: METHOD / CLOCK NEGATIVE CONTROL
Promotion credit: ZERO

## Final verdict

NEGATIVE_CONTROL_PASS / CLOCK_OFFSET_SENSITIVE

This closeout validates source handling and timing caution. It does not test the
IPG-001 propagation hypothesis and cannot promote the candidate.

## Immutable authority pins

OpenMarket source:
- repository: gregyoung14/openmarket
- commit: 6e6cc240f32ab9fd2f8fa602bd0aba823b24bfee

Dataset:
- repository: gregyoung14/openmarket-btc-polymarket
- semantic split: v0.4.3-unified
- immutable revision: 74502466d1a7cef56395bfd8d0b465fbebc849cf

## Reproduction chain

1. Exact dataset revision: PASS.
2. Manifest inventory: PASS.
3. Deterministic parquet schema fixture: PASS.
4. First lag reproduction against full/ archive: FAIL, preserved.
   - 4,117,576 rows
   - median 13 ms
   - p5 -263 ms
   - p95 356 ms
   - zero lead-lag identity violations
5. Source-semantics correction:
   OpenMarket documentation distinguishes full/ v0.2 archive from unified/
   v0.4.3 deduplicated analytic split. Published targets are tied to unified/.
   Published targets were NOT changed.
6. Correct unified/ reproduction: PASS, exact:
   - n = 2,936,031
   - median = 16 ms
   - p5 = -186 ms
   - p95 = 316 ms
   - lead_lag identity violations = 0
   - sampling = false
7. Frozen constant clock-offset sensitivity grid:
   -1000, -500, -250, -100, -50, 0, +50, +100, +250, +500, +1000 ms
   PASS.
   - base median: +16 ms
   - at -50 ms offset: median -34 ms
   - at +50 ms offset: median +66 ms
   - both apparent lead directions occur inside the frozen grid
   - shift identity exact

## Scientific interpretation

The public OpenMarket corpus and our independent pipeline reproduce the
published source-clock lag statistics exactly when the correct immutable
unified split is used.

However, the sign of the apparent median reverses under a small constant clock
offset well inside the frozen sensitivity grid. Therefore a raw cross-venue
source-clock ordering must not be interpreted as absolute causal latency.

IPG-001 consequently retains its original requirements:
- preserve source timestamps and local monotonic receive timestamps separately;
- log clock-sync evidence;
- run jitter / offset sensitivity;
- require an upstream event to survive target contemporaneous-move controls;
- never promote an edge that disappears or reverses under plausible timing
  uncertainty.

## What remains open

IPG-001 itself remains:
SOURCE_PARTIAL / PRE-DISCOVERY

No options->perp->microstructure->spot predictive propagation result has been
opened or claimed.

No IPG market outcome, PnL, live trading, exchange mutation or merge occurred.
