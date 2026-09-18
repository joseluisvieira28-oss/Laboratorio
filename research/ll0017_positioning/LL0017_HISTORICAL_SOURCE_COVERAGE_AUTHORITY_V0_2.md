# LL-0017 — HISTORICAL SOURCE COVERAGE CENSUS AUTHORITY V0.2

Date: 2026-09-18
Status: **FROZEN BEFORE FULL COVERAGE CENSUS / OUTCOME-BLIND**
Branch: `ll-0017-positioning-ratio-v0.1`

Precondition:
`LL0017_SOURCE_SCHEMA_CLOSEOUT_V0_1A.md` = SOURCE_SCHEMA_PASS.

## Scope

Lab: `LL-0017-POSITIONING-RATIO-001`
Census MVE: `LL17-BTCUSDT-METRICS-COVERAGE-2021-2024-001`

Source:
`https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/`

Frozen date envelope:
2021-01-01 through 2024-12-31 inclusive.
Expected UTC calendar days: exactly 1,461.

2025 and 2026 are forbidden.

## Allowed source inspection

For every expected day:
- ZIP and .CHECKSUM accessibility;
- provider SHA-256;
- CSV member identity;
- exact header;
- row count;
- timestamp field only;
- exact raw-line SHA-256 only for duplicate adjudication;
- normalized unique timestamp count;
- cadence/gap structure.

All metric numeric values remain opaque.

## Frozen normalization

Use only V0.1A exact-byte duplicate collapse:
- rows sharing a timestamp may be collapsed only if their complete original raw CSV lines have identical SHA-256;
- any non-identical duplicate timestamp group fails provenance;
- no averaging, preference, field comparison, first/last-value rule or metric parsing.

## Coverage PASS gates

`SOURCE_COVERAGE_PASS` requires ALL:

1. all 1,461 expected ZIP objects accessible;
2. all 1,461 matching CHECKSUM sidecars accessible;
3. all provider checksums verify exactly;
4. every ZIP contains exactly one CSV;
5. every CSV has the exact schema already passed in V0.1A;
6. no non-identical duplicate timestamp group anywhere;
7. each calendar day has at least 280 normalized unique timestamps;
8. at least 99.5% of days have exactly 288 normalized unique timestamps;
9. every day's median cadence <= 600 seconds;
10. no normalized timestamp lies outside its expected UTC date;
11. no unexpected calendar date is admitted;
12. no 2025/2026 source is requested or opened.

This census may report missing/short-day identities, but may not inspect or infer positioning values.

Permitted terminal states:
- `SOURCE_COVERAGE_PASS`
- `SOURCE_ACCESS_BLOCKED`
- `SOURCE_CHECKSUM_FAILURE`
- `SOURCE_SCHEMA_INADEQUATE`
- `SOURCE_TEMPORAL_COVERAGE_INADEQUATE`
- `PROVENANCE_FAILURE`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`

No source-stage result is NO_EDGE.

## Execution architecture

Use 8 deterministic, disjoint, contiguous calendar-date shards covering the exact 1,461-day envelope.

Shard execution may run in parallel because shards are source-only and independent.

Only the aggregate receipt can emit SOURCE_COVERAGE_PASS.

## Post-pass

A coverage pass authorizes only a separate FINAL PRE-DISCOVERY MECHANISM PROTOCOL.

Before any ratio values or market outcomes are opened, that later protocol must prospectively freeze:
- exact ratio transform(s);
- economic mechanism;
- sign/direction if any;
- timing/lookback;
- outcome definition;
- costs if trading is later proposed;
- statistical inference;
- multiple-testing family;
- promotion gates;
- protected OOS/holdout.

No live trading, exchange authentication, orders, wallets, alerts/webhooks or main merge.
