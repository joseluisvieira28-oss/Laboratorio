# MEXC Live Execution Preparation V0.2 — Current API

Status: **INFRASTRUCTURE / FAIL-CLOSED EXECUTION TRANSPORT — NO ACTIVE CANDIDATE AUTHORITY**

This package is deliberately split into two truths:

1. **MEXC authenticated preflight** — exchange/account/transport state.
2. **Candidate feasibility** — whether a frozen strategy can legally fit the venue minimum and its own risk envelope.

A candidate sizing failure must not be misreported as an exchange authentication failure.

## Current MEXC Futures API bindings

- Place order: `POST /api/v1/private/order/create`
- Cancel by external ID: `POST /api/v1/private/order/cancel_with_external`
- Query by external ID: `GET /api/v1/private/order/external/{symbol}/{external_oid}`
- Open orders: `GET /api/v1/private/order/list/open_orders`
- Fee details: `GET /api/v1/private/account/tiered_fee_rate/v2`
- Leverage state/change: current documented private position endpoints
- Auto-Add Margin: `POST /api/v1/private/position/change_auto_add_im`

## Entry sequence

A real order remains unreachable unless every gate passes:

authenticated exchange preflight → candidate capital feasibility → account risk firewall → canonical SHORT signal → information-safe time → healthy source/Radar → immutable ACTIVE candidate authority → current API schema → frozen STRESS20 friction → exact timing → duplicate lock → fresh account reconciliation → isolated 1x configure+verify → order/create → fill lookup by externalOid → post-fill isolated 1x verify → Auto Margin Add OFF verify.

If post-fill margin protection cannot be verified, the executor immediately attempts to flatten and marks execution failure.

## Exit sequence

The active trade carries an immutable exact +7d exit target. The local exit guard:
- waits prospectively;
- closes using the position ID;
- uses bounded market-close attempts;
- cancels an unresolved attempt by external ID;
- verifies no short position remains;
- writes EXIT_RECEIPT and POST_TRADE_RECONCILIATION;
- treats kill-switch or late exit beyond tolerance as execution failure.

## Account risk firewall

Frozen existing policy:
- validation allocation: 0.10% equity;
- maximum concurrent planned risk: 0.30% equity;
- daily halt: 0.30% equity;
- weekly halt: 0.75% equity.

No martingale, recovery sizing, win escalation or rounding above the strategy budget.

## Current account

With the operator's authenticated equity around 112.3763 USDT:
- MEXC auth itself can pass;
- ETF-CME Futures SHORT remains capital-incompatible because the venue minimum is far above the frozen 0.10% allocation;
- the executor therefore remains unreachable by design.

No template in this package authorizes an order.

Validation trigger: final V0.2 current-API safety suite after entry/exit/risk hardening.
