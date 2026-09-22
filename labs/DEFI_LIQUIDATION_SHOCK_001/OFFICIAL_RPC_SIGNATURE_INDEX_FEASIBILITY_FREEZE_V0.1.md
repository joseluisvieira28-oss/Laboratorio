# DEFI-LIQUIDATION-SHOCK-001 — OFFICIAL RPC SIGNATURE INDEX FEASIBILITY FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-ACCESS / SOURCE-ONLY / OUTCOME-BLIND / ZERO-COST

Purpose: determine whether official Solana JSON-RPC getSignaturesForAddress is a technically feasible exhaustive transport index for the frozen Kamino first-success search.

This does not amend the scientific authority yet.

Endpoint:
https://api.mainnet-beta.solana.com

Method:
getSignaturesForAddress

Frozen address:
KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD

Frozen upper anchor:
2JT9QV2zqYiYwDFVwbv6aPhRQkxi5Ynyq9sWi3i3nY18rqewZ3eiuNrHwHKsdcjaz6vm54EsTuh4AAwpTTM6pVwr
known timestamp 2024-12-15T23:24:40Z, slot 307726933.

Probe:
exactly one page with limit 1000 and before=<frozen upper anchor>.

Measurements allowed:
- HTTP/RPC status;
- count;
- unique signature count;
- newest/oldest returned slot and blockTime;
- elapsed historical span;
- error/null blockTime counts;
- overlap with the already-open 41 corrected Kamino smoke signatures.

No transaction bodies are opened by this feasibility probe.

Acceptance for further equivalence work:
- exactly 1000 or natural exhaustion with no RPC error;
- monotonically backwards compatible slots/times;
- known smoke signatures prior to the anchor appear where expected;
- historical span per page is operationally tractable.

Final liquidation classification remains separate public-RPC getTransaction verification with program ID + discriminator b1479abce2854a37 + meta.err.

No market/economic outcomes are authorized.
