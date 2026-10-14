# OPENMARKET NEGATIVE CONTROL V0.1

Frozen: 2026-09-24
Lab: INFORMATION-PROPAGATION-GRAPH-001
Purpose: method validation / negative control only.

## Public corpus

Project: OpenMarket
Repository: gregyoung14/openmarket
Paper: arXiv:2607.26245
Source tag to pin: v0.5.2
Dataset release to pin: v0.4.3-unified

The published corpus reports:
- 727,098,247 deduplicated rows;
- 202 source snapshots;
- 54 Polymarket days and 57 Binance days;
- 2,936,031 lead-lag pairs;
- explicit source and ingestion timestamp semantics;
- a 43-feature walk-forward model with null out-of-sample forecasting value relative to the market's own implied probability;
- collector-clock evidence of a Polymarket response to large Binance moves on the order of hundreds of milliseconds;
- an unresolved constant source-clock offset ambiguity that must not be silently corrected.

These values are reference targets from the published artifact, not IPG-001 outcomes.

## Why this belongs in IPG-001

The lab needs a dataset on which:
1. a tempting high-frequency relationship exists;
2. clock alignment is non-trivial;
3. the published predictive result is null;
4. source/ingest timestamps are documented.

If our pipeline manufactures strong predictive edge here by careless alignment, the pipeline fails validation.

## Required pin before execution

No computation may start until all are recorded:
- exact Git commit for source tag v0.5.2;
- exact dataset revision/hash for v0.4.3-unified;
- file manifest;
- row-count verification;
- timestamp-field semantics.

If the exact public revision cannot be pinned, verdict = BLOCKED.

## Reproduction gate

PASS requires:
- corpus metadata/row counts reconcile within documented release semantics;
- source_ts_ms vs ingest_ts_ms are kept separate;
- at least one published timing statistic can be reproduced within a pre-declared tolerance;
- constant-offset sensitivity is explicitly tested;
- jitter sensitivity includes +/-50ms, 100ms, 250ms, 500ms and 1s;
- the published null predictive result is not relabelled as an edge.

## IPG-001 use after reproduction

Only after PASS:
- use the corpus to validate asynchronous event-study code;
- run propagation-state diagnostics as a method test;
- treat any apparent edge as suspect unless it survives clock-offset sensitivity and a frozen OOS split.

This is not a candidate for promotion. It is a calibration instrument.
