# PERP-CROWDING-UNWIND-001 — FULL-COVERAGE TRANSPORT AMENDMENT V0.1B

Date: 2026-09-19
Parent full-coverage run: `35471800502`

The first full-period coverage attempt was non-adjudicative for economics: all 48 monthly funding archives and all 48 monthly 1h kline archives were available, but Binance does not publish the `metrics` product as monthly ZIPs. Every monthly metrics URL returned HTTP 404, even though the prior representative-date gate proved the daily metrics product exists.

V0.1B changes only source packaging:
- funding remains monthly;
- 1h klines remain monthly;
- aggregate-open-interest metrics are reconstructed from the canonical **daily** Binance metrics archives in parallel.

Prospectively frozen completeness semantics:
- a metrics month is FULL at >=95% calendar-day archive coverage;
- a metrics month is USABLE at >=80% calendar-day archive coverage;
- overall PCU_COVERAGE_FULL still requires >=46 FULL common months and >=11 per year;
- PCU_COVERAGE_LIMITED requires >=36 USABLE common months and >=8 per year.

No economic feature, 95/5 funding tail, 80th-percentile OI rule, horizon, direction, cost, outcome, or promotion gate changes. No outcome was opened in run 35471800502.
