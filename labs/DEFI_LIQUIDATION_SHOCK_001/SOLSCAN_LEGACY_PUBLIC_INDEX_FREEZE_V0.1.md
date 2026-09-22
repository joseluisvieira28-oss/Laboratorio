# DEFI-LIQUIDATION-SHOCK-001 — SOLSCAN LEGACY PUBLIC INDEX FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-ACCESS / SOURCE-ONLY / OUTCOME-BLIND / ZERO-COST

Purpose: evaluate the legacy/public Solscan account-transactions route as a transport index only.

Endpoint candidate:
https://public-api.solscan.io/account/transactions

No token, account, payment, wallet, identity submission or subscription is authorized.

Frozen program:
KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD

Frozen upper anchor for backwards transport audit:
2JT9QV2zqYiYwDFVwbv6aPhRQkxi5Ynyq9sWi3i3nY18rqewZ3eiuNrHwHKsdcjaz6vm54EsTuh4AAwpTTM6pVwr
(BigQuery corrected Kamino candidate, 2024-12-15 23:24:40 UTC, slot 307726933)

Frozen source boundary:
2023-11-17T13:25:35Z

The legacy route may only enumerate transaction identities backwards from the fixed upper anchor. Final liquidation classification remains public Solana getTransaction + exact program ID + discriminator b1479abce2854a37 + meta.err semantics.

Initial access/equivalence probe:
- request max provider page size from the fixed upper anchor;
- confirm historical rows are returned without authentication;
- confirm signatures, slots and block times are exposed;
- subsequent equivalence must recover known 2024-12-15 BigQuery candidates below the anchor.

Any auth/paywall => SOLSCAN_LEGACY_ACCESS_BLOCKED.
Endpoint retirement/transport failure => SOLSCAN_LEGACY_TRANSPORT_BLOCKED.
Only proven known-candidate coverage permits a prospective exhaustive-walk amendment.

No market outcomes are authorized.
