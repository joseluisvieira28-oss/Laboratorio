# DEFI-LIQUIDATION-SHOCK-001 — SOLSCAN ENHANCED ENTITLEMENT PROBE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose
Determine whether an already-authorized free Solscan API credential is available to GitHub Actions and whether the Solscan Enhanced playground route can return one known Kamino liquidation row under the frozen decoder. This is a transport/source entitlement probe only.

## Fixed scientific identity
Program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
Instruction discriminator: `b1479abce2854a37`
Known calibration day: `2024-12-15 UTC`
Success filter: successful transactions only.

## Allowed actions
- detect presence/absence of secret names without printing values;
- one read-only HTTP GET to the Solscan playground enhanced transactions endpoint;
- retain HTTP status and a redacted response body;
- no account creation, subscription, billing, or key generation.

## Routing
- usable pre-existing key + HTTP 200 + non-empty valid response: `SOLSCAN_FREE_ENTITLEMENT_SOURCE_PROBE_PASS`
- no pre-existing key: `SOLSCAN_FREE_ENTITLEMENT_CREDENTIAL_ABSENT`
- key present but 401/403: `SOLSCAN_FREE_ENTITLEMENT_AUTH_BLOCKED`
- transport/server error: `SOLSCAN_FREE_ENTITLEMENT_TRANSPORT_BLOCKED`
- schema/content inconsistency: `SOLSCAN_FREE_ENTITLEMENT_SCHEMA_FAIL_CLOSED`

A PASS authorizes only a later prospectively frozen historical source walk. It does not grant SOURCE_DATA_PASS or any economic result.

## Firewall
prices=false; returns=false; pnl=false; direction=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
