# LIQUIDATION-PRESSURE-001 — Tardis Source Probe V0.3 Erratum

Date: 2026-09-19

V0.3 is preserved unchanged with terminal receipt:

`SOURCE_ACQUISITION_TECHNICAL_FAILURE — HTTP 404`

Cause: the probe corrected the dataset symbol to `BTCUSDT` but still used an incorrect date path shape `/{YYYY-MM-DD}/{symbol}.csv.gz`.

Tardis' documented datasets API path is:

`/:exchange/:dataType/:year/:month/:day/:symbol.csv.gz`

No market outcome was opened.

V0.4 changes **only** URL construction to the documented nested `YYYY/MM/DD` path. Dataset, symbol, dates, schema rules and all outcome firewalls remain unchanged.
