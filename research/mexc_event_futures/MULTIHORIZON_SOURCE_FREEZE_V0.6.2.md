# MEXC EVENT FUTURES LAB — MULTI-HORIZON CURRENT PAYOUT SOURCE FREEZE V0.6.2

Date: 2026-10-02
Status: SOURCE-ONLY / PUBLIC DOM / READ-ONLY / FAIL-CLOSED

## Prior source result

V0.6 proved that the public Event Futures page exposes exact current Up/Down payout values in the rendered DOM for all five displayed assets without authentication.

V0.6.1 preserved the public/read-only boundary and confirmed the page can be observed with all non-GET network requests aborted. No trading endpoint is required for current payout observation.

## V0.6.2 mission

Determine whether exact current payouts can be collected for every displayed asset across all documented Event Futures horizons:

- 10m
- 30m
- 1h
- 1d

Assets:
- BTCUSDT
- ETHUSDT
- NVDAUSDT
- MUUSDT
- SPCXUSDT

## Interaction boundary

The browser may only:
- GET-navigate to the public Event Futures page;
- read DOM text;
- click an exact, unique visible horizon selector with text 10m, 30m, 1h, or 1d.

The browser MUST NOT:
- click Up or Down;
- type an amount;
- submit a form;
- authenticate;
- allow POST/PUT/PATCH/DELETE;
- open/close a position;
- mutate any account state.

If a horizon label is ambiguous (more than one exact visible element), that horizon is marked SELECTOR_AMBIGUOUS and is not clicked.

## PASS rule

PASS_MULTI_HORIZON_DOM_SOURCE requires exact numeric Up and Down payout values for all 20 asset × horizon combinations in one run.

PARTIAL means at least one but fewer than 20 combinations are defensible.

BLOCKED means none are defensible.

No strategy test or economic promotion is allowed in V0.6.2.
