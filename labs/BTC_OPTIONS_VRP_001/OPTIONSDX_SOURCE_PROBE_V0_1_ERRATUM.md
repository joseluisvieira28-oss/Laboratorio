# BTC-OPTIONS-VRP-001 — optionsDX Source Probe V0.1 Erratum

Date: 2026-09-19

V0.1 is preserved unchanged with terminal classification:

`SOURCE_ROUTE_SCHEMA_INSUFFICIENT`

The public sample downloaded successfully (HTTP 200, 21,385,261 bytes, 94,066 rows, 28 columns). The failure was parser normalization only: optionsDX wraps CSV headers in square brackets and leading spaces (for example `[QUOTE_UNIXTIME]`, ` [BID_PRICE]`) and names the option-right field `OPTION_RIGHT`.

No quote values, returns, PnL or performance outcomes were emitted.

V0.2 changes only header normalization:
- strip whitespace;
- strip surrounding square brackets;
- map `OPTION_RIGHT` as the option-right field.

The source hypothesis, sample URL, safety firewall and zero-purchase rule remain unchanged.
