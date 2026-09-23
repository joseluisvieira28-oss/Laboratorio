# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 OFFICIAL API SOURCE PROBE V0.1

Date: 2026-09-23
Status: SOURCE-ROUTE DISCOVERY ONLY / OUTCOME-BLIND / FAIL-CLOSED

Target provider:
Save/Solend official HTTP API `https://api.solend.fi`.

Target route:
`GET /history-v2/liquidation-attempts`.

Purpose:
Determine whether the official protocol API exposes a historically queryable liquidation-attempt record surface that can serve only as a candidate locator for the Save/Solend 0x11 census.

This probe MUST NOT treat API rows as authoritative realized liquidations. Any future candidate obtained from this API still requires exact program + tag `0x11` RAW on-chain verification under the frozen census rules.

Allowed persisted evidence:
- HTTP status;
- content type;
- response byte count;
- JSON structural schema only (key names, container/scalar types, array lengths);
- error class / textual API validation message if a request is rejected.

Forbidden persisted evidence:
- prices;
- token amounts;
- USD values;
- liquidation sizes;
- PnL/returns/direction;
- user balances or wallet values;
- any economic field values.

Probe variants are transport/schema discovery only:
1. bare endpoint;
2. `limit=1`;
3. `page=1&limit=1`;
4. `offset=0&limit=1`;
5. frozen first-chunk timestamp bounds with `start`/`end` plus `limit=1`.

If a successful response exists, only its schema is persisted; scalar values are redacted to type names.

Classification:
- `SAVE11_OFFICIAL_API_SCHEMA_ROUTE_PASS` if at least one request returns JSON 2xx;
- `SAVE11_OFFICIAL_API_SCHEMA_ROUTE_VALIDATION_BLOCKED` if route exists but all requests require missing documented parameters/auth;
- `SAVE11_OFFICIAL_API_SCHEMA_ROUTE_TRANSPORT_BLOCKED` on network/service failure;
- any accidental economic-value persistence => fail closed.

No account creation, credentials, paid access, prices, returns, PnL, live trading, orders, wallets, exchange mutation or main merge are authorized.
