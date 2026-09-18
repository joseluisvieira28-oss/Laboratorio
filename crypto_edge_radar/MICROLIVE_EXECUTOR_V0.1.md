# CRYPTO EDGE RADAR — MICRO-LIVE EXECUTOR V0.1

Status: **PREPARED / NOT ARMED**

Branch:
`crypto-edge-radar-microlive-executor-v0.1-2026-09-18`

## Scope

This layer prepares unattended execution for the exact promoted candidate:

- CED1D-0031
- AVAXUSDT
- Binance USD-M perpetual
- 20-calendar-day momentum
- CONTINUATION
- H1
- first micro-live eligibility: 2026-09-21T00:01:00Z
- maximum one real event under V0.1
- maximum 25 USDT notional
- isolated margin required
- leverage must already be 1x
- market entry / reduce-only market exit
- no parameter changes, rescue, pyramiding, averaging or venue substitution

The code is deliberately **not armed by default**. It requires both:
- `MICROLIVE_EXECUTION_ENABLED=1`
- exact `MICROLIVE_ARM_TOKEN`

and exchange credentials supplied only through runtime secrets.

## Binance adapter

Prepared:
- HMAC-SHA256 signed REST requests
- server-clock check
- public book ticker and exchange rules
- authenticated symbol-config verification
- leverage=1x verification
- isolated-margin verification
- no-existing-position guard
- no-existing-open-order guard
- market-order test endpoint
- actual market entry/exit endpoint
- deterministic client order IDs
- 25-USDT cap with quantity rounding
- one-event state machine
- automatic governed 24h exit
- restart-safe local state
- append-only execution receipts

No API key or secret is stored in Git.

## MEXC

MEXC Futures API support is acknowledged, but CED1D-0031 is scientifically provider-bound to Binance USD-M and **MEXC may not be used as a fallback venue for this candidate**.

A MEXC connector shell exists for later independent candidates. Private order placement remains fail-closed until the current post-March-2026 Futures private order schema is re-verified and pinned. This prevents silently coding against an outdated legacy contract endpoint.

## Deployment model

The intended unattended architecture is:

Radar service
→ append-only VALID_SHADOW_SIGNAL
→ micro-live daemon tails only new notifications
→ exact candidate/venue/time/risk preflight
→ deterministic one-event Binance entry
→ persistent OPEN state
→ automatic reduce-only exit at governed H1 deadline
→ mandatory reconciliation
→ hard stop before any second real event

First boot starts its notification cursor at EOF, so stale historical signals cannot be replayed into a real order.

## Secret policy

Never commit credentials. At setup time use deployment/repository secret storage only.

Minimum Binance key posture:
- Futures trading only
- no withdrawal permission
- no wallet/transfer permission where separable
- IP allowlist when deployment egress IP is stable

The executor does not contain withdrawal or transfer endpoints.
