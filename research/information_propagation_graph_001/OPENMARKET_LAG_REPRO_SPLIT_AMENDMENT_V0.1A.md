# OPENMARKET LAG REPRODUCTION — SPLIT SEMANTICS AMENDMENT V0.1A

Date: 2026-09-24
Stage: negative-control source correction, before any IPG outcome.

## Preserved failed run

The original V0.1 reproduction incorrectly read:
full/lag_pairs_ms/

It returned:
- 4,117,576 rows
- median 13 ms
- p5 -263 ms
- p95 356 ms

and is permanently preserved as NEGATIVE_CONTROL_LAG_REPRODUCTION_FAIL.

## Why the path was wrong

Pinned OpenMarket release documentation explicitly distinguishes:
- unified/ = v0.4.3-unified, deduplicated analytic timeline;
- full/ = v0.2-full, complete per-snapshot archive.

The published 2,936,031 / 16 / -186 / 316 targets are tied to the
v0.4.3-unified split.

Therefore mapping semantic version v0.4.3-unified to full/ was a source-path
interpretation error, not a statistical failure.

## Corrected execution

Read every:
unified/lag_pairs_ms/**/*.parquet

at the same immutable dataset SHA.

All published targets and PASS rules remain unchanged:
- n = 2,936,031
- median = 16 ms
- p5 = -186 ms
- p95 = 316 ms
- zero lead_lag identity violations

No tolerance or target changes are authorized.
