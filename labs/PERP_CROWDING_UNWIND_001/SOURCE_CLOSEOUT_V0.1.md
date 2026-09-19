# PERP-CROWDING-UNWIND-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-19
Canonical source run: `35471232464`
Transport amendment: `SOURCE_TRANSPORT_AMENDMENT_V0.1A`

## Classification

**PCU_SOURCE_FULL**

Five prospectively frozen representative dates spanning 2021–2024 all passed for the three zero-cost Binance USD-M Futures sources:

- aggregate open-interest metrics: 5/5;
- funding-rate archives: 5/5;
- BTCUSDT 1h futures klines: 5/5;
- open-interest field present;
- funding-rate field present;
- timestamps parseable;
- no credentials;
- no cash spend.

The first run's funding failure was a packaging-path issue only. V0.1A changed the same Binance funding source from nonexistent daily ZIP packaging to the public monthly ZIP packaging and required the exact representative date to exist inside each month. The corrected run passed with zero errors.

No outcomes, future returns, PnL, 2025/2026 data, exchange mutation, or live trading were opened by the source gate.
