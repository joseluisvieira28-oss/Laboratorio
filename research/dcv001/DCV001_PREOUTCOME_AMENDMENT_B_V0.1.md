# DCV-001 — PRE-OUTCOME AMENDMENT B V0.1

Date: 2026-09-23
State when frozen: SOURCE_GATE_V0.1 PASS. First full-census attempt stopped before any economic value/outcome parsing because early-2021 Binance metrics archives contain repeated create_time rows. Source-only diagnostic runs 35857096844 and 35857174683 opened no funding/OI/price values or returns.

## Observed structural anomaly

Fixed source-only diagnostics showed:
- 2021-01-01: 576 rows, 288 unique create_time values, every timestamp exactly duplicated;
- 2021-01-03: same structure;
- 2021-01-22: same structure;
- 2021-06-15: 288 rows, 288 unique timestamps;
- for all examined duplicate groups, the entire CSV row was exactly identical;
- conflicting duplicate group count = 0;
- no economic values were printed or interpreted.

## Frozen provenance normalization

For Binance Vision daily BTCUSDT metrics archives only:

1. Group rows by create_time inside each daily object.
2. If a create_time occurs once, keep the row.
3. If it occurs more than once, the rows may be collapsed to one ONLY when every CSV field is exactly identical across the duplicate group.
4. Any duplicate create_time group containing two non-identical rows is SOURCE_PROVENANCE_CONFLICT and fails closed.
5. The source census must record:
   - raw row count;
   - unique row count after exact-duplicate collapse;
   - exact duplicate rows removed;
   - conflicting duplicate group count.
6. Economic parsing later uses the exact-deduplicated structural rows. No averaging, first/last preference among conflicting rows, interpolation or value-based resolution is permitted.
7. This normalization applies only to exact duplicate rows. It does not authorize removal of unique timestamps or conflicting records.

## Scientific invariants

No hypothesis, expected sign, feature, 90-day normalization, 7-day RV window, outcome horizon, bootstrap, gate, year attribution, asset, source family, protected-period rule or replication rule changes.

2024 remains locked unless 2021-2023 Discovery passes.
2025/2026 remain forbidden.
