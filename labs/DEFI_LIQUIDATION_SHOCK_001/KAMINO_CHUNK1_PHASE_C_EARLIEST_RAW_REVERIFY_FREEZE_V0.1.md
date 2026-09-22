# DEFI-LIQUIDATION-SHOCK-001 — KAMINO CHUNK #1 PHASE-C EARLIEST RAW REVERIFY FREEZE V0.1

Date: 2026-09-22  
Status: **FROZEN BEFORE PHASE-B OUTCOME IS OPENED / SOURCE-ONLY**

## Trigger

Phase C is executable only if Phase B finishes with:
- all 10,560 frozen transaction bodies resolved;
- zero source-consistency anomalies; and
- at least one `SUCCESSFUL_REALIZED_KAMINO_LIQUIDATION_REFERENCE`.

If Phase B is incomplete, source-blocked, or contains zero successful matches, this phase MUST NOT manufacture a candidate.

## Deterministic candidate selection

From Phase B successful realized reference rows, sort exactly by:

1. `blockTime` ascending;
2. `slot` ascending;
3. `signature` lexicographically ascending;
4. outer instruction before inner instruction;
5. parent instruction index ascending, with null before integers;
6. instruction position ascending.

Select exactly the first row.

No alternative candidate may be substituted after re-fetch.

## Independent RAW re-fetch

Endpoint:
`https://api.mainnet-beta.solana.com`

Method:
`getTransaction`

Configuration:
- commitment: finalized
- encoding: jsonParsed
- maxSupportedTransactionVersion: 0

The independently re-fetched transaction must satisfy all:

- returned result is non-null;
- signature is the deterministic Phase B earliest candidate;
- returned slot equals the Phase B slot;
- returned blockTime equals the Phase B blockTime;
- `meta.err == null`;
- top-level/inner instructions contain exact Kamino program ID
  `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`;
- the exact matching instruction data base58-decodes to prefix
  `b1479abce2854a37`.

## Adjudication

If all checks pass:

`KAMINO_FIRST_SUCCESS_BOUNDARY_RAW_VERIFIED`

The accepted Kamino first-success boundary is the candidate's on-chain `blockTime`, because chunk #1 begins exactly at the frozen source-supported boundary and Phase A + Phase B establish exhaustive coverage of the entire preceding eligible interval inside that first chunk.

If any check fails:

`KAMINO_FIRST_SUCCESS_BOUNDARY_REVERIFY_FAIL_CLOSED`

No fallback to the second row is permitted.

## Firewalls

This phase does not open or compute prices, future returns, PnL, market direction, event-size thresholds, economic edge, 2025/2026 market outcomes, live trading, orders, wallets, exchange mutation, paid sources, or main merge.
