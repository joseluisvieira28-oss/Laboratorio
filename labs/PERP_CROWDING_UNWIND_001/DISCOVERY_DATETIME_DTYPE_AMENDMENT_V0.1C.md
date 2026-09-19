# PERP-CROWDING-UNWIND-001 — DISCOVERY DATETIME-DTYPE AMENDMENT V0.1C

Date: 2026-09-19
Parent run: `35471936589`

Full source coverage passed before the Discovery step:
- 48 / 48 FULL common months;
- 12 / 12 months in each year 2021, 2022, 2023, 2024.

The Discovery then stopped before constructing any economic signal or future return because pandas rejected an `merge_asof` between two timezone-aware datetime columns stored at different internal resolutions: `datetime64[ms, UTC]` versus `datetime64[us, UTC]`.

V0.1C normalizes all parsed timestamps to `datetime64[ns, UTC]` before joins.

This is representation-only. No timestamp value, alignment tolerance, feature, threshold, signal direction, horizon, cost, gate, sample period, or protected-period rule changes. Run 35471936589 is non-adjudicative for economics.
