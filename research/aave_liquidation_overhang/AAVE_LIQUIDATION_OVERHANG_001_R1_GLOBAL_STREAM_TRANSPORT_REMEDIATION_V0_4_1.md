# AAVE-LIQUIDATION-OVERHANG-001 — R1 GLOBAL STREAM TRANSPORT REMEDIATION V0.4.1

Status: **FROZEN BEFORE V0.4.1 EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

The active V0.4 global-state diagnostic run `35384377212` remains in progress.
No V0.4 scientific result has been inspected.

A source-code audit of `r1_global_state_v01.py` identified the same transport
failure mode already observed in the R1 scaled-ledger audit:

- `post()` retries request establishment/status failures;
- after HTTP 200, `stream()` yields directly from `Response.iter_lines()`;
- a response-body `requests.RequestException` such as
  `ChunkedEncodingError` can terminate the entire historical acquisition;
- a partially-read HTTP page is not independently retryable.

The previous V0.3 global run executed 4,475 Portal HTTP attempts and 4,402
successful HTTP responses before terminating technically. Its wrapper destroyed
the original base exception, so V0.4 exists specifically to preserve the exact
base failure cause.

Given the high number of streamed responses, body-stream retry is a legitimate
prospective transport hardening independent of any scientific result.

## Exact V0.4.1 remediation

For every fixed Portal request window:

1. Keep the exact endpoint, request body, filters, block boundaries and fields.
2. Buffer the complete HTTP response page before yielding any row to state
   reconstruction.
3. If response-body iteration raises `requests.RequestException`, discard the
   incomplete page buffer.
4. Retry the exact same request body and exact same boundaries.
5. Maximum response-body stream attempts per page: **8**.
6. Deterministic backoff before retry:
   `min(20.0, 1.5 * 2**attempt)` seconds.
7. JSON, ABI, provenance, ordering and semantic errors are not converted into
   transport retries and remain fail-closed.
8. Empty successful windows retain the exact V0.1 behaviour: advance to the
   fixed request end and increment the empty-window diagnostic.

No partially-read response is ever applied to eMode/provider/oracle state.

## Scientific invariants unchanged

V0.4.1 MUST preserve exactly:

- frozen block envelope `16,490,000..21,525,890`;
- audit blocks `17,748,972`, `19,007,945`, `20,266,917`,
  `21,525,890`;
- Pool, PoolConfigurator and PoolAddressesProvider identities;
- activation oracle and provider/oracle transition semantics;
- eMode event semantics;
- oracle source/configuration event semantics;
- canonical 37-reserve R0 bootstrap;
- canonical V0.2E `R1_AUDIT_PASS`;
- V0.4 archive provider set:
  `https://eth-mainnet.public.blastapi.io`,
  `https://rpc.mevblocker.io`,
  `https://ethereum.blinklabs.xyz/`;
- quorum = 2;
- exact agreement and positive Aave-oracle-price rules;
- all terminal classifications and precedence.

No source substitution.
No target dropping.
No event dropping.
No result-dependent retry logic.
No alternate block ranges.

## Required static QA

Before V0.4.1 source execution, a deterministic synthetic test MUST prove:

- a valid response prefix followed by `ChunkedEncodingError` is discarded;
- the exact request body and bounds are retried;
- only the complete retry response is yielded;
- retry diagnostics are incremented exactly once;
- empty-window semantics remain unchanged;
- scientific event/reconstruction semantics are untouched.

## Lineage

V0.4 run `35384377212` remains immutable and authoritative for its own result.

V0.4.1 executes as an independent diagnostic-preserving transport lineage.
If both V0.4 and V0.4.1 pass, V0.4.1 is redundant confirmation.
If V0.4 fails only from the hardened transport defect and V0.4.1 passes,
V0.4.1 may be consumed by a separately frozen canonical continuation.

## Hard firewall

Until canonical `RECONSTRUCTION_DATA_PASS`:

- no health factor;
- no liquidation distance/overhang;
- no adverse-shock threshold;
- no future liquidation outcomes;
- no market returns;
- no PnL, win rate, PF, Sharpe or drawdown;
- no scientific 2025/2026 data;
- no live trading, orders, wallets, exchange mutation, alerts/webhooks;
- no capital deployment;
- no merge to main.
