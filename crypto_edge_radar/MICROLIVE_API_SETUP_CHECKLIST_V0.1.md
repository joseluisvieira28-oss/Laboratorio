# CED1D-0031 — API + UNATTENDED MICRO-LIVE SETUP CHECKLIST V0.1

Status: **PREPARED FOR CREDENTIAL SESSION / NOT ARMED**

Execution branch:
`crypto-edge-radar-microlive-executor-v0.1-2026-09-18`

## Architecture for Monday

Two long-running processes:

1. Public radar:
`python -m radar service --interval 5`

2. Isolated execution daemon:
`python -m radar microlive`

Flow:
public Binance USD-M data → exact AVAX20 signal → append-only signal receipt → pending queue → exact 00:01 UTC entry window → Binance authenticated preflight → one 25-USDT max market entry → persistent state → automatic reduce-only H1 exit → reconciliation lock.

The executor starts at the end of the existing notification file and cannot replay old signals.

## Binance setup later today

Create a dedicated API key for this research executor.

Required posture:
- USD-M Futures trading permission only as needed
- withdrawals disabled
- transfers/wallet actions disabled where separable
- IP allowlist if the deployed service has stable egress
- do not paste the secret into Git, Drive, chat messages, logs or screenshots

Runtime secrets:
- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`

Account configuration required before arming:
- AVAXUSDT available on USD-M
- one-way position mode (hedge mode rejected)
- isolated margin for AVAXUSDT
- leverage exactly 1x
- no existing AVAXUSDT position
- no existing AVAXUSDT open order
- actual taker commission <= 0.05% / 5 bps per fill

The bot does not change leverage or margin mode automatically. It verifies them and fails closed.

## Safe no-fill credential test

After secrets are installed, run:

`python -m radar microlive-preflight`

This performs:
- clock check
- signed account access
- one-way mode check
- isolated / 1x verification
- fee-rate verification
- open-order / open-position check
- venue quantity/min-notional calculation
- Binance `/fapi/v1/order/test` validation

The test-order endpoint does not submit to the matching engine.

Do not arm real execution unless this returns:
`BINANCE_MICROLIVE_CREDENTIAL_PREFLIGHT_PASS`

## Final runtime arm

Only after preflight PASS:

- `MICROLIVE_EXECUTION_ENABLED=1`
- `MICROLIVE_ARM_TOKEN=CED1D-0031-MICROLIVE-V0.1-ONE-EVENT`
- `MICROLIVE_VENUE=binance_usdm`

Persistent paths must survive process restarts:
- `RADAR_NOTIFICATIONS`
- `MICROLIVE_STATE`
- `MICROLIVE_CURSOR`
- `MICROLIVE_PENDING`
- `MICROLIVE_RECEIPTS`

Do not use ephemeral storage for the one-event state/cursor.

## Monday timing

First permitted micro-live reference entry:
`2026-09-21T00:01:00Z`
= 02:01 Switzerland (CEST).

The radar should already be running before 00:00 UTC.
A valid signal generated during 00:00–00:01 UTC is queued.
The executor does not enter early.
At 00:01 UTC it runs the authenticated guards and may submit the one governed order.

No valid on-time signal = no trade.
Failure of any guard = no trade.
No catch-up/backfill trade later in the day.

## Automatic exit

The daemon persists the exact H1 reference exit and sends a reduce-only market close when due.
If the service restarts after the exact exit instant, it closes as soon as possible and marks a LATE_EXIT_INCIDENT rather than deliberately leaving risk open.

## MEXC setup

MEXC credentials can be prepared separately:
- `MEXC_API_KEY`
- `MEXC_API_SECRET`
- Futures trading permission only
- withdrawals/transfers disabled
- IP allowlist if available

Important:
CED1D-0031 is Binance USD-M provider-bound. MEXC is **not** an execution fallback for this candidate.

The MEXC connector shell is intentionally blocked from private order submission until the current Futures private-order schema is pinned and smoke-tested. It can later support a separately authorized MEXC-native candidate.

## Non-negotiable safeguards

- maximum 25 USDT notional
- maximum one real event under V0.1
- isolated margin
- maximum 1x
- deterministic client-order IDs
- query-before-retry/idempotent recovery
- no pyramiding
- no averaging
- no martingale
- no venue substitution
- no withdrawals/transfers
- no second real event before reconciliation
- no automatic scale-up after a win
