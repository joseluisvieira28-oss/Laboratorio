# CRYPTO EDGE RADAR — FORWARD-ONCE RUNTIME REMEDIATION V0.1

Date: 2026-09-22
Status: FROZEN TECHNICAL RUNTIME REMEDIATION / NO SCIENTIFIC CHANGE

## Problem

The canonical Render free web service can sleep after inbound inactivity and the evidence ledger has already recorded a multi-hour runtime gap. The scientific watchers themselves are replay-safe/idempotent over their frozen boundaries, but the CLI currently exposes them only through the persistent web-service loop.

## Authorized technical change

Add a `forward-once` CLI command that:
1. loads the exact existing `Settings.from_env()`;
2. instantiates the exact existing `ForwardShadowRuntime`;
3. calls exactly one existing `run_cycle()`;
4. prints the resulting state;
5. exits 0 only when `health == "OK"`, otherwise exits 2.

No watcher rule, source, symbol, threshold, timing boundary, costs, signal, risk scaling, evidence key, retry rule or promotion gate changes.

## Credential policy

A GitHub Actions probe may bind `RADAR_DATABASE_URL` only through an existing Actions secret of the same name.
- Secret value is never printed.
- If absent, the workflow records `AUTH_REQUIRED_NOT_EXECUTED`.
- No secret is created or copied by this change.

## Timing firewall

V0.1 authorizes MANUAL / QA one-shot execution only.
No recurring GitHub schedule is authorized here.
Any scheduled cadence requires a separate prospective timing authority because BNB and other watchers have different operational polling needs.

## Safety firewall

authenticated_exchange_api=false
orders=false
wallets=false
exchange_mutation=false
live_capital=false
main_merge=false
