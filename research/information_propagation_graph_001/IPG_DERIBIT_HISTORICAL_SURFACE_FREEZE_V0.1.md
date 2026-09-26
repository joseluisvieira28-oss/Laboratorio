# IPG-001 DERIBIT HISTORICAL SURFACE SOURCE PROBE FREEZE V0.1

Frozen: 2026-09-24
Stage: SOURCE CAPABILITY ONLY
Target-price outcomes: CLOSED

## Authority

Current official Deribit API documentation exposes public endpoints for:
- get_instruments (including expired instruments);
- get_last_trades_by_instrument_and_time;
- get_mark_price_history (5-minute historical mark-price data);
- get_volatility_index_data;
- get_funding_rate_history.

This probe tests retention and temporal granularity only.

## Frozen fixture

Calendar fixture:
2024-06-01T00:00:00Z through 2024-06-01T23:59:59.999Z

Deterministic option selection:
- get expired BTC option instruments;
- keep expirations in June 2024;
- sort instrument_name lexicographically;
- select the first instrument.

Additional instruments:
- BTC-PERPETUAL for mark/funding capability.
- BTC DVOL history via volatility-index endpoint.

## Allowed outputs

- method success/failure;
- selected instrument identity and expiry;
- returned row count;
- minimum/maximum returned timestamp;
- inferred timestamp spacing where available;
- response field names;
- response SHA256.

Do NOT persist price, IV, mark, trade amount, direction or any BTC/option return.

## Verdicts

DERIBIT_HISTORICAL_SURFACE_PASS:
- at least one June-2024 expired option returns historical mark or trade records;
- BTC-PERP historical method works;
- DVOL historical method works.

DERIBIT_HISTORICAL_SURFACE_PARTIAL:
- only some surfaces retain official public history.

DERIBIT_HISTORICAL_SURFACE_BLOCKED:
- no usable historical upstream surface from the official public API.

No result is an IPG edge.
