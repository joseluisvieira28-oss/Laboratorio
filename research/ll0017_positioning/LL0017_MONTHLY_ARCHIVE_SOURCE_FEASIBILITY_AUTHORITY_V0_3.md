# LL-0017 — MONTHLY ARCHIVE SOURCE FEASIBILITY AUTHORITY V0.3

Date: 2026-09-18
Status: FROZEN BEFORE MONTHLY-ARCHIVE PROBE / SOURCE-ONLY / OUTCOME-BLIND

Parent exact daily-source census remains closed as SOURCE_TEMPORAL_COVERAGE_INADEQUATE.
This V0.3 does not modify or rescue that verdict.

## Purpose

Test whether the official Binance Data Vision monthly BTCUSDT metrics archives provide a materially better structural source for the calendar days that failed the frozen daily-source minimum of 280 unique 5-minute timestamps.

## Frozen monthly archives

- 2021-01
- 2021-02
- 2021-04
- 2021-06
- 2021-11
- 2024-02

Canonical route candidate:
https://data.binance.vision/data/futures/um/monthly/metrics/BTCUSDT/BTCUSDT-metrics-YYYY-MM.zip
with matching .CHECKSUM sidecar.

## Frozen target days and daily-source structural counts

- 2021-01-20: 271
- 2021-02-05: 279
- 2021-02-11: 276
- 2021-02-19: 218
- 2021-02-20: 272
- 2021-04-27: 258
- 2021-06-22: 126
- 2021-06-23: 275
- 2021-06-24: 279
- 2021-11-26: 276
- 2024-02-16: 163

These dates were selected only from source-coverage failure metadata. No ratio values or market outcomes were opened.

## Allowed inspection

- ZIP and CHECKSUM accessibility;
- exact provider SHA-256;
- ZIP member identity;
- exact CSV header;
- timestamp column only;
- raw-row SHA-256 for exact duplicate normalization;
- unique timestamp count for the 11 frozen target UTC dates;
- comparison of monthly-source structural count versus already-recorded daily-source structural count.

All metric numeric fields remain opaque strings and may not be parsed.

## Exact duplicate rule

Same V0.1A rule: duplicate rows sharing a timestamp may be collapsed only if the complete raw CSV row bytes have identical SHA-256. Any non-identical duplicate timestamp group is PROVENANCE_FAILURE.

## Feasibility classifications

- MONTHLY_SOURCE_ROUTE_RECOVERY_PLAUSIBLE: at least one frozen target day has a higher normalized unique timestamp count than the daily-source count, with all checksums/schema/provenance valid.
- MONTHLY_SOURCE_ROUTE_NO_INCREMENTAL_COVERAGE: all 11 target days are structurally identical or no better than the daily source, with valid provenance.
- SOURCE_ACCESS_BLOCKED
- SOURCE_CHECKSUM_FAILURE
- SOURCE_SCHEMA_INADEQUATE
- PROVENANCE_FAILURE
- SOURCE_ACQUISITION_TECHNICAL_FAILURE

No classification here is NO_EDGE.

## Post-probe rule

If and only if MONTHLY_SOURCE_ROUTE_RECOVERY_PLAUSIBLE is observed, a separate prospective V0.4 authority may enumerate and recover every non-full day required to test a new combined-source coverage MVE. The original daily-source V0.2 failure remains immutable.

Still forbidden: ratio values, prices, returns, PnL, 2025/2026, live trading, exchange mutation, wallets, orders, alerts/webhooks, main merge.