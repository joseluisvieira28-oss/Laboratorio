# BTC-OPTIONS-VRP-BINANCE-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-19
Branch: `btc-options-vrp-binance-eoh-source-v0.1`
Probe: `BOVRP-BINANCE-EOH-SOURCE-001`
Canonical run: `35461157545`
Canonical head: `bb5da64694c1e6588b01822e306e3055d71cb7d1`
Artifact: `BTC_OPTIONS_VRP_BINANCE_001_SOURCE_V0_1`
Artifact ID: `10589823998`
Artifact ZIP digest: `sha256:aa62cdef0f4e3c66f675607cc6ba9eaaf91ff6c0b15472d8361625bfd611e176`

## Final classification

**BINANCE_EOH_SOURCE_FEASIBLE**

This is a source-feasibility result only. It is not evidence of a volatility-risk-premium edge, not an execution result, and not a promotion.

## Frozen coverage result

Envelope: 2023-05-18 through 2023-10-23 inclusive.

- calendar days in envelope: 159
- available source days: 147
- missing days: 12
- frozen minimum available days: 100 — PASS
- first available day: 2023-05-18
- last available day: 2023-10-23

Missing dates:
2023-09-08 through 2023-09-18 inclusive, plus 2023-09-25.

## Frozen sample/schema result

All three prospectively frozen sample dates were available and parsed:

- 2023-05-18: 5,734 rows
- 2023-07-01: 6,720 rows
- 2023-10-23: 5,498 rows

For every row in all three samples, the source gate proved:

- point-in-time clock reconstructable from source date + hour;
- option identity present;
- expiry deterministically parseable from the Binance option symbol;
- strike present;
- option right present;
- best bid price present;
- best ask price present;
- best bid quantity present;
- best ask quantity present.

The samples also expose venue implied-volatility and Greeks fields.

The EOH source does not independently prove a numeric underlying/index-price field under this gate. Any future economic MVE requiring spot/index prices must prospectively bind a separate point-in-time underlying source before outcomes are opened.

## Scientific interpretation

This creates a genuine zero-cash-cost historical BBO lane for a **new independent Binance options laboratory**.

It does **not** rescue, extend, substitute into, or rewrite the Deribit parent `BTC-OPTIONS-VRP-001`. Venue, source history and available period differ materially.

The 147-day history is also too short to assume that a robust independent VRP strategy verdict is possible. A later design must freeze horizon, observation independence/effective sample treatment, cost model and underlying source before looking at any economic outcome.

## Safety receipt

- strategy PnL: not opened
- returns: not opened
- VRP: not computed
- future realized variance: not computed
- parameter tuning: not performed
- 2025 accessed: false
- 2026 accessed: false
- API key/authentication: none
- wallet access: false
- exchange mutation/live trading: false
- merge to main: false

## Next gate

Do not open economic outcomes automatically.

Next authorized research step is **PRE-DISCOVERY DESIGN ONLY**:
1. quantify the effective independent sample available under candidate non-overlapping clocks without reading outcomes;
2. bind a point-in-time BTC underlying source;
3. choose and freeze one economically coherent VRP definition and horizon;
4. pre-register inference, costs/tail-risk accounting and pass/fail gates;
5. only then decide whether the Binance history is scientifically adequate for Discovery.
