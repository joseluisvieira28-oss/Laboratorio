# USOPEN-STRADDLE-001 — RETROSPECTIVE PRICE-ONLY CLOSEOUT

Date: 2026-09-24
Branch: `us-open-straddle-monetization-v0.1`
Canonical run: `35958059556`
Classification: **RETROSPECTIVE_PRICE_ONLY_NO_SUPPORT**
Promotion credit: **ZERO**

## Frozen implementation

On regular U.S. cash-market days inside the free 2024H1 Cryptarbitrage Deribit BTC-options parquet:
- exact 09:00 ET entry;
- nearest 7–14 DTE expiry;
- nearest-ATM same-strike call+put;
- buy both legs at ask;
- exact 11:00 ET exit;
- sell same legs at bid;
- historical standard Deribit option fees applied per trade;
- stress adds one extra adverse spread per leg.

## Result

- source rows: 4,498,832
- executable episodes: 134
- mean gross BTC per 1-BTC straddle: **-0.0019701493**
- mean fees: **0.0012000000 BTC**
- mean base net: **-0.0031701493 BTC**
- median base net: **-0.0032000000 BTC**
- base PF: **0.0777247**
- win rate: **8.21%**
- bootstrap 95% mean base net: **[-0.0035993, -0.0027037] BTC**
- mean stress net: **-0.0058492537 BTC**
- stress PF: **0.0177945**
- nonnegative calendar-month means: **0 / 7**
- max single positive episode share: **32.96%**

Every month from January through July 2024 had a negative mean base-net result.

## Interpretation

This exact long-vol implementation is not supported even before capacity is considered.

The failure is not explained by fees alone: mean gross PnL is already negative before the 0.0012 BTC average round-trip fees. Crossing the spread and fees worsen an implementation that is economically negative at the quoted price level.

The result is retrospective/contaminated and therefore had zero promotion credit by construction; nevertheless, it is strong negative diagnostic evidence against spending money to recreate this exact 09:00→11:00 long ATM-straddle implementation.

## No rescue

Do not:
- invert to short straddle on the same 2024H1 block;
- change entry/exit clocks;
- alter DTE band;
- select profitable months/days;
- use midpoint fills;
- reduce fees;
- switch strike rule;
- claim capacity from price-only quotes.

A short-vol or DVOL-specific hypothesis requires a new LAB_ID and independent/prospective evidence.

## Firewall

- 2025 opened: false
- pre-boundary 2026 outcomes opened: false
- capacity claim: false
- live trading: false
- exchange mutation: false
- merge to main: false

Source parquet SHA256:
`6ed2162288d177d3c3a5443456c3fb78ed2c175249f0a0ff1665a5dd9c89800b`
