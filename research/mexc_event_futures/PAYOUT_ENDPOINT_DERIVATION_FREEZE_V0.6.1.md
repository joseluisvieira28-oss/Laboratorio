# MEXC EVENT FUTURES LAB — PUBLIC PAYOUT ENDPOINT DERIVATION FREEZE V0.6.1

Date: 2026-10-02
Status: SOURCE-ONLY / READ-ONLY / FAIL-CLOSED

## Prior result

V0.6 achieved PASS_EXACT_CURRENT_PAYOUT from the public Event Futures trading page DOM for all five displayed assets without authentication or trading.

Observed in the V0.6 source gate:
- BTCUSDT: Up 70%, Down 70%
- ETHUSDT: Up 80%, Down 80%
- NVDAUSDT: Up 80%, Down 80%
- MUUSDT: Up 80%, Down 80%
- SPCXUSDT: Up 80%, Down 80%

Those values are time-local observations only, not historical constants.

Static bundle reconnaissance also exposed an Event/Prediction service pattern including:
`https://prediction.<MEXC domain>/api/platform`
and an Event-market route fragment:
`/predict/market/web/event/teams`

## V0.6.1 mission

Derive the reproducible public read-only endpoint(s) and payload field(s) that feed:
- asset identity;
- Up payout;
- Down payout;
- Event Futures time unit / horizon;
- Event Futures index / reference price where exposed.

## Hard boundaries

- GET only.
- No private keys, API keys, cookies or authenticated session.
- Abort all POST/PUT/PATCH/DELETE.
- No order endpoints.
- No clicking Up/Down.
- No quantity entry.
- No account mutation.
- No strategy testing.
- No payout-edge inference.
- No merge to main.

## PASS rule

PASS_PUBLIC_PAYOUT_ENDPOINT requires:
1. a reproducible public GET or websocket source;
2. payout fields mapped to a displayed asset;
3. the values reconcile to the public DOM in the same observation session.

If only DOM remains defensible, verdict is DOM_ONLY_SOURCE.
