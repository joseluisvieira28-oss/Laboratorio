# LIQUIDATION-PRESSURE-001 — Multi-Venue Source Probe V0.1 Erratum

Date: 2026-09-19

V0.1 is preserved unchanged with terminal classification:

`MULTIVENUE_SOURCE_ROUTE_INSUFFICIENT`

The failure was caused by an over-strict source-feasibility rule: V0.1 required at least one BTC liquidation record on **every** frozen sample date for a venue to pass.

For an event stream, a valid HTTP 200 file can legitimately contain zero target liquidation events on a quiet day. Treating zero observed events as source failure confuses event incidence with source availability.

No forward prices, returns, PnL, continuation/reversal labels or strategy outcomes were opened.

V0.2 changes only the source feasibility adjudication:
- every frozen date must be addressable with HTTP 200;
- any non-empty file must expose the required schema;
- zero-event dates are valid;
- the target BTC symbol must be observed on at least two frozen dates across the 2021-2024 sample;
- venue selection remains forbidden from using event counts or forward performance.

This is a source-engineering correction, not an economic or outcome-driven rescue.
