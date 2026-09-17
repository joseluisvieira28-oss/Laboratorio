# BTC-OPTIONS-VRP-001 — Tardis Source Probe V0.1 Erratum

Date: 2026-09-17

## Preserved V0.1 result

Run `35273908796` remains permanently recorded as `SOURCE_ROUTE_SCHEMA_INSUFFICIENT` under its frozen V0.1 authority. It is not rewritten.

The follow-up source-schema diagnostic run `35274231199` established that the Tardis Deribit `options_chain` sample was successfully accessible and structurally rich on 2021-06-01:

- 750,000 rows scanned;
- 316,441 BTC option rows observed;
- schema included `symbol`, `timestamp`, `type`, `strike_price`, `expiration`, `open_interest`, `bid_price`, `ask_price`, IV and Greeks;
- zero rows fell inside the frozen 25–35 DTE band.

## Root cause

The V0.1 free-sample calendar was incompatible with the frozen DTE band. On 2021-06-01 the standard June monthly BTC option expiry was 2021-06-25, only 24 calendar days away, while the next major monthly expiry was outside the 35-day upper bound. Thus a zero-count 25–35 DTE result on that sample date cannot adjudicate whether the source route contains suitable option-chain/BBO data.

This is a source-feasibility calendar-design defect, not a market outcome and not an economic result. No returns, strategy PnL, PF, drawdown, 2025 or 2026 data were opened.

## Authorized correction scope

A new V0.2 source probe may change only the free first-day-of-month sample dates to January 1 of 2021, 2022, 2023 and 2024, where the standard late-January monthly expiry prospectively lies approximately 25–28 days away. All other source-feasibility requirements remain unchanged:

- same 25–35 DTE band;
- same-strike BTC call+put pair;
- nonempty option-chain BBO for both legs;
- nonempty dedicated `quotes` BBO for both legs;
- no API key or paid subscription;
- source-only / outcome-blind;
- 2025/2026 forbidden;
- no performance computation.

V0.2 is a new source-probe version and does not modify the closed execution MVE `OVRP-EXEC-ATM30-7D-STATICDELTA-001`.
