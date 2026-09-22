# CRYPTO EDGE RADAR — LOCAL FORWARD LOOP RUNTIME V0.1

Status: FROZEN TECHNICAL CONTINUITY REMEDIATION / NO SCIENTIFIC CHANGE

## Purpose

Provide an always-on, non-HTTP local execution surface for the exact existing
ForwardShadowRuntime. This is intended as a continuity alternative to a free
web service that may sleep.

## Exact behavior

The new `forward-loop` command:
- loads Settings.from_env();
- instantiates the existing ForwardShadowRuntime unchanged;
- calls its existing run_loop(interval_seconds=...);
- uses the same evidence backend and idempotency keys;
- opens no HTTP listener;
- creates no orders and enables no capital.

Default interval remains 30 seconds, matching the current canonical Render
shadow loop floor. The existing runtime itself enforces its 30-second minimum.

## Credential firewall

RADAR_DATABASE_URL must be supplied only through the local process environment.
No credential is committed, printed, copied to logs, or embedded in scripts.
If absent, the existing Settings fallback uses local SQLite; the provided
Windows launcher therefore fails closed before startup unless
RADAR_DATABASE_URL is present, preventing accidental evidence-fork operation.

## Scientific firewall

All strategy rules, sources, timing boundaries, costs, signals, thresholds,
risk scaling, idempotency keys and promotion gates are unchanged.

authenticated_exchange_api=false
orders=false
wallets=false
exchange_mutation=false
live_capital=false
main_merge=false
