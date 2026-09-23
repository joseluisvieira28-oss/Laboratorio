# DCV-001 — OFFICIAL DAILY MARK ARCHIVE SOURCE REMEDIATION AUTHORITY V0.2

Date: 2026-09-23
Status: FROZEN_PRE_REMEDIATION_PROBE / OUTCOME_BLIND

## Parent state

DCV-001 V0.1 monthly markPriceKlines route failed its frozen full-source census before any economic outcome was opened.

Observed timestamp-only gaps in the official monthly BTCUSDT 1h mark-price archive:
- 2021-07-01
- 2021-07-24 through 2021-07-27
- 2022-07-31
- 2022-10-02
- 2023-02-24

Total missing = 192 hours.

No funding/OI/price values, returns, regression coefficients, PnL or 2024 replication outcomes have been opened.

## Remediation question

Can the exact missing monthly timestamps be recovered from Binance Vision's official DAILY markPriceKlines archive for the same instrument, same 1h interval and same UTC dates, with published checksum verification and byte/schema/timestamp integrity?

This is a source-route remediation only. It does not change the scientific hypothesis or sample rules.

## Authorized exact route

For each missing date D only:

`https://data.binance.vision/data/futures/um/daily/markPriceKlines/BTCUSDT/1h/BTCUSDT-1h-D.zip`

plus its published `.CHECKSUM`.

No REST API fallback.
No alternate venue.
No spot/index/trade-price substitution.
No 2024 full-source acquisition.
No 2025/2026 access.

## Source-only probe requirements

For each exact date above:
1. ZIP returns HTTP 200.
2. Published SHA256 sidecar exists and matches downloaded bytes.
3. ZIP CRC passes.
4. Exactly one CSV payload.
5. Schema is standard Binance kline structure with at least 6 fields.
6. Exactly 24 unique hourly open_time timestamps.
7. Timestamps are exactly D 00:00 through D 23:00 UTC at 1h cadence.
8. No protected timestamp >=2025-01-01.
9. No economic values are printed, summarized or interpreted.

Any failed date => DAILY_REMEDIATION_SOURCE_FAIL and DCV-001 remains SOURCE_DATA_INSUFFICIENT. No Discovery.

## Merge semantics if source probe passes

Only after DAILY_REMEDIATION_SOURCE_PASS:

- Monthly archive remains primary.
- Daily archive may contribute rows ONLY for timestamps absent from the verified monthly archive.
- If a daily timestamp already exists in monthly, the values must not overwrite or replace it; no patch is needed.
- If a recovered daily row would conflict in timestamp identity with another recovered row, fail closed.
- After patching, rerun the original full-source census thresholds unchanged:
  - mark coverage >=99.5%;
  - no unresolved duplicate open_time;
  - no gap >3 consecutive hours.
- All other source gates and scientific rules remain unchanged.

## Governance

This authority is source-informed but not outcome-informed. It is frozen after observing only timestamp availability and before any economic values/outcomes.

No threshold relaxation.
No science change.
No live trading.
No exchange mutation.
No main merge.
