# LIQUIDATION-PRESSURE-001 — Tardis Source Probe V0.2 Erratum

Date: 2026-09-19

V0.2 is preserved unchanged with terminal receipt:

`SOURCE_ACQUISITION_TECHNICAL_FAILURE — HTTP 404`

Cause: the probe requested the grouped symbol `PERPETUALS` for Binance Futures liquidations. Tardis documentation defines dataset URLs by an allowed dataset symbol from exchange metadata; grouped symbols are data-type/exchange dependent. The source-only probe therefore did not establish that `PERPETUALS` is a valid liquidation dataset symbol for `binance-futures`.

No market outcome was opened.

V0.3 changes **only** the dataset symbol to the explicit frozen target `BTCUSDT`, retaining the same dates, schema requirements, safety firewalls and source-only purpose. This is a transport/source addressing correction, not an economic or outcome-driven change.
