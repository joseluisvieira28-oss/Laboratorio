# BTC-OPTIONS-VRP-001 — OFFICIAL MARK-HISTORY SOURCE CLOSEOUT V0.1

Date: 2026-09-18
Probe: OVRP-MARK-HISTORY-SOURCE-PROBE-001
Probe run: 35310604584
Diagnostic run: 35310686562

## FINAL CLASSIFICATION

MARK_HISTORY_SOURCE_ROUTE_UNAVAILABLE_FOR_EXPIRED_OPTIONS

## EVIDENCE

The canonical probe reached Deribit's public endpoint but the first expired 2021 option returned HTTP 400.

A separate source-only host diagnostic preserved only status/error metadata:
- https://www.deribit.com/api/v2/public/get_mark_price_history
  - HTTP 400
  - error code -32602
  - param = instrument_name
  - reason = instrument is not active
- https://history.deribit.com/api/v2/public/get_mark_price_history
  - HTTP 400
  - non-JSON response; endpoint not usable through that historical host

No mark-price values, returns, PnL, 2025/2026 data, authentication or paid data were opened.

## ADJUDICATION

This free official route cannot recover historical mark-price series for the expired option instruments needed by BTC-OPTIONS-VRP-001. Do not relabel the parent VRP NO_EDGE: parent Discovery remains DISCOVERY_PASS_VRP_EXISTS. The higher-quality Tardis BBO route remains PAID_SOURCE_ROUTE_FEASIBLE, but full-history access is commercial.

The free-source recovery attempts now consist of:
1. public trade-print execution MVE: insufficient executable sample;
2. Tardis free monthly-to-expiry route: 34/36 source threshold, insufficient;
3. official mark-history route: expired instruments rejected.

No paid access was purchased and no protected-period outcome was opened.
